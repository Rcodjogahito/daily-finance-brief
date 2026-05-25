"""Gemini API integration for news analysis with anti-hallucination controls."""
import json
import logging
import os
import re
import time
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Model fallback chain — du plus récent au plus ancien
# Mise à jour 2026 : Gemini 2.5 en tête, 2.0/1.5 en fallback de dernier recours
_MODEL_PREFERENCE = [
    os.environ.get("GEMINI_MODEL", ""),           # Override env var (priorité absolue)
    "gemini-2.5-flash",                            # Stable 2026 (meilleur rapport perf/coût)
    "gemini-2.5-flash-preview-05-20",              # Preview daté
    "gemini-2.5-flash-preview-04-17",              # Preview daté antérieur
    "gemini-2.5-pro",                              # Plus capable si quota disponible
    "gemini-2.0-flash",                            # Génération précédente
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-latest",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
]
_MODEL_NAME = next((m for m in _MODEL_PREFERENCE if m), "gemini-2.5-flash")

SYSTEM_PROMPT = """Tu es un analyste senior en banque d'investissement (Leveraged Finance / M&A / Energy / DCM) au sein d'un CIB Tier-1 européen.
Tu prépares un brief quotidien pour ton équipe deal team et tes seniors.
Style : dense, factuel, technique, direct. Pas de bla-bla, pas d'évidences, pas de paraphrase creuse.

RÈGLES DE FIABILITÉ ABSOLUES :
- N'invente JAMAIS un fait, un chiffre, un nom ou un montant qui n'apparaît pas explicitement dans la source
- Si une donnée est ambiguë, écris "à confirmer" plutôt que d'affirmer
- Si tu n'as pas assez de matière fiable pour 10 news, mets-en moins (5-9 OK) plutôt que de remplir avec du faible
- Pour l'analyse d'impact : tu peux faire des déductions raisonnables à partir des faits (ex: "ce downgrade implique une sortie des mandats IG") mais sans inventer de nouveaux faits"""

USER_PROMPT_TEMPLATE = """À partir des news ci-dessous (dernières 24h), sélectionne les 10 max les plus pertinentes pour un professionnel CIB. Mets MOINS si le matériel ne le justifie pas.

CRITÈRES DE SÉLECTION (priorité décroissante) :
1. Deal flow structurant : M&A >500M€, LBO, IPO, mandats exclusifs
2. Leveraged Finance / DCM : refis HY, TLB, distressed, breach covenants, CLO
3. Énergie : O&G majors, project finance, renewables, transition énergétique
4. Commodities : mouvements OPEC, prix pétrole/gaz/métaux, marchés agricoles, LME, CFTC, chocs offre/demande sur matières premières
5. Crédit & ratings : downgrades/upgrades grands corporates, profit warnings, fallen angels
6. Macro & banques centrales : BCE/Fed/BoE, inflation, CPI, taux directeurs, FX
7. Géopolitique à impact financier direct : sanctions, tariffs, conflits, reshoring
8. Nominations importantes : CEOs/CFOs/DGs de grandes institutions financières ou corporates
9. Actualité bancaire : résultats banques, consolidation bancaire, régulation prudentielle, CET1, MREL
10. Sectoriel structurant : défense, tech (deals/earnings Big Tech), aviation, luxe, pharma, real estate
11. Régulation financière à impact deal/marché : Bâle IV, CSRD, taxonomie

EXCLURE : politique sans angle économique, faits divers, sport, lifestyle, tech grand public sans angle financier.

BONUS : privilégie les news avec source_count ≥ 2 (corroborées par plusieurs sources).

POUR CHAQUE NEWS RETENUE, FORMAT JSON STRICT :
{{
  "rank": <int, 1=plus important>,
  "category": <"M&A"|"LevFin"|"Energy"|"Credit"|"Macro"|"Geo"|"Reg"|"Sector"|"Nominations"|"Banking">,
  "headline": "<titre concis et impactant en français, 12 mots max>",
  "source": "<nom du média original>",
  "date": "<YYYY-MM-DD>",
  "url": "<lien original exact — NE PAS modifier>",
  "sector": "<secteur>",
  "geography": "<géographie>",
  "deal_size_eur": <null OU montant EUR si EXPLICITEMENT dans la source>,
  "confidence": <"high"|"medium">,
  "summary": "<2-3 phrases factuelles : qui, quoi, combien, quand. Paraphrase uniquement des faits de la source.>",
  "so_what": "<Analyse structurée en 3 points : (1) Impact immédiat sur les marchés ou l'opération concernée. (2) Conséquences potentielles pour les acteurs (banques, investisseurs, emprunteurs, concurrents). (3) Signal pour le deal flow CIB — opportunité ou risque à surveiller. Déductions raisonnables autorisées si fondées sur les faits du résumé.>"
}}

CONTRAINTES :
- Réponds UNIQUEMENT en JSON valide : {{"news": [...]}}
- Aucun texte hors JSON, aucun markdown, aucun ```
- Analyse so_what : 3-5 phrases structurées, niveau banquier senior, directes et actionnables

NEWS À ANALYSER :
{news_json}
"""

ALERT_PROMPT_TEMPLATE = """Tu es un analyste senior CIB. Rédige une analyse d'impact pour l'alerte suivante.

RÈGLES : Appuie-toi sur les faits du résumé. Des déductions raisonnables sont autorisées (ex: impact CLO pour un fallen angel) mais n'invente aucun fait nouveau.

News :
- Titre : {title}
- Source : {source}
- Résumé : {summary}
- Type d'alerte : {alert_type}
- Raison : {alert_reason}

Réponds en JSON valide UNIQUEMENT :
{{"so_what": "<Analyse en 3-4 phrases : (1) Impact immédiat. (2) Conséquences pour les acteurs. (3) Signal deal flow CIB. Précis, technique, actionnable.>"}}
"""


def _get_client():
    """Build a Gemini client, trying google-genai (new SDK) first."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    try:
        from google import genai
        return genai.Client(api_key=api_key), "genai"
    except ImportError:
        pass
    try:
        import google.generativeai as genai_legacy
        genai_legacy.configure(api_key=api_key)
        return genai_legacy, "legacy"
    except ImportError:
        raise ImportError("Neither google-genai nor google-generativeai is installed")


def _extract_json(text: str) -> dict:
    """Robust JSON extraction — handle Gemini preamble or markdown wrapping."""
    if not text:
        raise ValueError("Empty response from Gemini")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    text_clean = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text_clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Cannot extract JSON from Gemini response: {text[:200]}")


def _call_gemini_new_sdk(client, model: str, prompt: str, system: str) -> str:
    """Call Gemini via google-genai (new SDK ≥1.0)."""
    from google.genai import types
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2,
            max_output_tokens=16000,
            response_mime_type="application/json",
        ),
    )
    return response.text


def _call_gemini_legacy_sdk(client, model: str, prompt: str, system: str) -> str:
    """Call Gemini via google-generativeai (legacy SDK)."""
    m = client.GenerativeModel(
        model_name=model,
        system_instruction=system,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 16000,
            "response_mime_type": "application/json",
        }
    )
    response = m.generate_content(prompt)
    return response.text


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=15, max=120),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_gemini(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """Call Gemini with automatic SDK detection and model fallback chain.

    Rate limiting strategy:
    - On 429 (RESOURCE_EXHAUSTED): sleep 12s before trying next model (respects ~5 RPM safety margin)
    - If all models return 429, raise immediately to let tenacity backoff (15s → 30s → 60s)
    - On 404 (model not found): skip immediately, no delay needed
    """
    client, sdk_type = _get_client()
    last_exc = None
    rate_limited_count = 0

    for model in [m for m in _MODEL_PREFERENCE if m]:
        try:
            if sdk_type == "genai":
                result = _call_gemini_new_sdk(client, model, prompt, system)
            else:
                result = _call_gemini_legacy_sdk(client, model, prompt, system)
            if result:
                logger.info("Gemini success with model: %s (sdk: %s)", model, sdk_type)
                return result
        except Exception as exc:
            exc_str = str(exc)
            last_exc = exc
            if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                rate_limited_count += 1
                logger.warning("Model %s rate-limited (429) — trying next", model)
                if rate_limited_count >= 3:
                    # Trop de 429 consécutifs — laisser tenacity gérer le backoff
                    raise RuntimeError(f"Rate limit (429) on {rate_limited_count} models — backing off. Last: {exc}")
                time.sleep(12)  # Respecter ~5 RPM avant de tenter le prochain modèle
            else:
                logger.warning("Model %s failed: %s — trying next", model, exc_str[:100])
            continue

    raise RuntimeError(f"All Gemini models failed. Last error: {last_exc}")


def analyze_news(candidates: list[dict]) -> list[dict]:
    """Send candidates to Gemini for ranking and analysis. Returns selected news."""
    if not candidates:
        return []

    news_for_llm = [
        {
            "title": item.get("title", ""),
            "source": item.get("source", ""),
            "published": item.get("published", "")[:10],
            "url": item.get("url", ""),
            "summary": item.get("summary", "")[:400],
            "sector": item.get("sector", ""),
            "geography": item.get("geography", ""),
            "deal_size_eur": item.get("deal_size_eur"),
            "source_count": item.get("source_count", 1),
            "confidence": item.get("confidence", "medium"),
        }
        for item in candidates
    ]

    prompt = USER_PROMPT_TEMPLATE.replace("{news_json}", json.dumps(news_for_llm, ensure_ascii=False, indent=2))

    try:
        raw = _call_gemini(prompt)
        parsed = _extract_json(raw)
        selected = parsed.get("news", [])
        logger.info("Gemini returned %d news items", len(selected))
        return selected
    except Exception as exc:
        logger.error("Gemini analysis failed: %s — using fallback", exc)
        return _fallback_selection(candidates)


def generate_alert_so_what(item: dict) -> str:
    """Generate 'So what?' for a hot alert using Gemini."""
    flags = item.get("alert_flags", [{}])
    alert_type = flags[0].get("type", "ALERT") if flags else "ALERT"
    alert_reason = flags[0].get("reason", "") if flags else ""

    prompt = ALERT_PROMPT_TEMPLATE.format(
        title=item.get("title", ""),
        source=item.get("source", ""),
        summary=item.get("summary", "")[:500],
        alert_type=alert_type,
        alert_reason=alert_reason,
    )

    try:
        raw = _call_gemini(prompt)
        parsed = _extract_json(raw)
        return parsed.get("so_what", "Analyse indisponible.")
    except Exception as exc:
        logger.error("Alert so_what generation failed: %s", exc)
        return "Analyse indisponible — vérifier la source directement."


_ITEM_SO_WHAT_PROMPT = """Tu es un analyste senior en banque d'investissement (M&A / Leveraged Finance / DCM / Energy) dans un CIB Tier-1 européen.

Rédige une analyse d'impact rigoureuse pour cette news.

News :
- Titre : {headline}
- Résumé : {summary}
- Catégorie : {category} | Secteur : {sector} | Géographie : {geography}
- Sources : {source_count} source(s) | Confiance : {confidence}

RÈGLES :
- 3-4 phrases structurées, niveau banquier senior, directes et actionnables
- (1) Impact immédiat : marchés, spreads, cours ou conditions de financement directement affectés
- (2) Conséquences pour les acteurs : banques, investisseurs, emprunteurs, concurrents — qui gagne, qui perd
- (3) Signal deal flow CIB : opportunité ou risque à surveiller dans les prochains jours
- Factuel et déductif (déductions raisonnables à partir du résumé OK), sans paraphrase
- JAMAIS d'affirmations sans base factuelle dans le résumé

Réponds en JSON valide UNIQUEMENT :
{{"so_what": "<analyse>"}}
"""

_HEURISTIC_MARKERS = (
    "Développement sectoriel",
    "Transaction M&A",
    "Event crédit leveraged",
    "Event de crédit affectant",
    "Développement énergétique",
    "Signal macro (",
    "Risque géopolitique (",
    "Développement réglementaire",
    "Nomination dans le secteur",
    "Actualité bancaire (",
    "News ",
)


def _is_heuristic(text: str) -> bool:
    return not text or any(text.startswith(m) for m in _HEURISTIC_MARKERS)


def _generate_item_so_what(item: dict) -> str:
    """Generate a rigorous so_what for a single news item via Gemini."""
    prompt = _ITEM_SO_WHAT_PROMPT.format(
        headline=item.get("headline", ""),
        summary=(item.get("summary", "") or "")[:400],
        category=item.get("category", "Sector"),
        sector=item.get("sector", ""),
        geography=item.get("geography", ""),
        source_count=item.get("source_count", 1),
        confidence=item.get("confidence", "medium"),
    )
    raw = _call_gemini(prompt)
    parsed = _extract_json(raw)
    result = parsed.get("so_what", "")
    return result if result and not _is_heuristic(result) else _heuristic_so_what(item)


def enrich_so_what(items: list[dict]) -> list[dict]:
    """For each item whose so_what is a heuristic fallback, regenerate via Gemini.

    Fail-fast: if the first attempt fails, marks Gemini as unavailable and
    skips further calls (avoids 10× useless retries if the API key is invalid).
    """
    import time
    result = []
    gemini_available = True   # Présumé disponible jusqu'à preuve du contraire

    for item in items:
        if _is_heuristic(item.get("so_what", "")):
            if gemini_available:
                try:
                    item = {**item, "so_what": _generate_item_so_what(item)}
                    logger.info(
                        "so_what enriched via Gemini for '%s'",
                        item.get("headline", "")[:50],
                    )
                except Exception as exc:
                    logger.warning(
                        "so_what enrichment failed for '%s': %s — Gemini indisponible, skip restants",
                        item.get("headline", "")[:50], str(exc)[:120],
                    )
                    item = {**item, "so_what": _heuristic_so_what(item)}
                    gemini_available = False   # Ne plus appeler Gemini pour ce run
                else:
                    time.sleep(1)   # Respecter les rate limits Gemini seulement si succès
            else:
                # Gemini déjà échoué — garder l'heuristique directement
                item = {**item, "so_what": _heuristic_so_what(item)}
        result.append(item)

    if not gemini_available:
        logger.error(
            "enrich_so_what: Gemini indisponible — %d item(s) avec analyse heuristique. "
            "Vérifier GEMINI_API_KEY et lancer le workflow 'Regenerate so_what' manuellement.",
            sum(1 for it in result if _is_heuristic(it.get("so_what", ""))),
        )
    return result


def _heuristic_so_what(item: dict) -> str:
    """Generate a category-based heuristic analysis when Gemini is unavailable."""
    cat    = item.get("category", "Sector")
    sector = item.get("sector", "Other")
    geo    = item.get("geography", "Global")
    deal   = item.get("deal_size_eur")
    sc     = item.get("source_count", 1)

    deal_str = f" ({deal/1e9:.1f} Md€)" if deal else ""
    multi    = f" — corroboré par {sc} sources" if sc >= 2 else ""

    templates = {
        "M&A":         f"Transaction M&A{deal_str} dans le secteur {sector} ({geo}){multi}. Évaluer structure de financement, valorisation et timeline de closing. Impact deal flow à surveiller.",
        "LevFin":      f"Event crédit leveraged{deal_str} ({sector}, {geo}){multi}. Surveiller les conditions de pricing HY, l'appétit du marché et les implications pour le pipeline DCM.",
        "Credit":      f"Event de crédit affectant {sector} ({geo}){multi}. Analyser l'impact sur les spreads, les mandats IG/HY et le repricing des actifs comparables.",
        "Energy":      f"Développement énergétique{deal_str} ({geo}). Watch : project finance, conditions d'offtake, implications commodités et financement transition.",
        "Macro":       f"Signal macro ({geo}). Implications pour les conditions de financement, les taux de référence et le sentiment de marché à court terme.",
        "Geo":         f"Risque géopolitique ({geo}). Surveiller l'impact sur les flux de capitaux, les spreads souverains et les opérations exposées à cette zone.",
        "Reg":         f"Développement réglementaire impactant {sector} ({geo}). Évaluer les effets sur les structures de deal, les exigences de capital et les délais d'exécution.",
        "Nominations": f"Nomination dans le secteur {sector} ({geo}). Signal d'orientation stratégique : surveiller la continuité ou l'inflexion de la politique d'allocation et de risque.",
        "Banking":     f"Actualité bancaire ({geo}). Impact potentiel sur les conditions de crédit, les ratios de capital et la posture de risque des établissements concernés.",
        "Sector":      f"Développement sectoriel — {sector} ({geo}){deal_str}{multi}. Analyser les implications concurrentielles, l'impact sur les marges et le deal flow associé.",
    }
    return templates.get(cat, f"News {sector}/{geo} — vérifier les implications pour le deal flow et les actifs exposés.")


def _fallback_selection(candidates: list[dict]) -> list[dict]:
    """Fallback when Gemini is unavailable: return top N by source priority + source_count.
    Caps at 2 items per source to enforce diversity."""
    from src.filters import _source_priority

    def score(item: dict) -> float:
        return _source_priority(item.get("source", "")) + item.get("source_count", 1) * 0.5

    sorted_candidates = sorted(candidates, key=score, reverse=True)

    # Apply per-source cap (max 2 per source) for diversity
    source_counts: dict[str, int] = {}
    diverse: list[dict] = []
    for item in sorted_candidates:
        src = item.get("source", "")
        if source_counts.get(src, 0) < 2:
            diverse.append(item)
            source_counts[src] = source_counts.get(src, 0) + 1
        if len(diverse) >= 10:
            break

    result = []
    for i, item in enumerate(diverse, 1):
        enriched = {
            "rank": i,
            "category": item.get("category", "Sector"),
            "headline": item.get("title", "")[:80],
            "source": item.get("source", ""),
            "date": item.get("published", "")[:10],
            "url": item.get("url", ""),
            "sector": item.get("sector", "Other"),
            "geography": item.get("geography", "Global"),
            "deal_size_eur": item.get("deal_size_eur"),
            "confidence": item.get("confidence", "medium"),
            "source_count": item.get("source_count", 1),
            "summary": item.get("summary", "")[:300],
            "alert_flags": [],
        }
        enriched["so_what"] = _heuristic_so_what(enriched)
        result.append(enriched)
    return result


def post_verify_llm_output(llm_news: list[dict], original_news: list[dict]) -> list[dict]:
    """Reject/sanitize news where Gemini fabricated amounts not in original source.

    NOTE: URL matching is best-effort. Items with unmatched URLs are kept
    (not rejected) to avoid dropping valid news due to URL normalization
    differences between Gemini output and original source.
    """
    from src.enrichment import extract_amount_eur

    url_index = {item.get("url", ""): item for item in original_news}
    # Also index by normalized URL (without query params) for fuzzy matching
    url_index_normalized = {}
    for item in original_news:
        url = item.get("url", "")
        base = url.split("?")[0].rstrip("/")
        url_index_normalized[base] = item

    verified: list[dict] = []

    for item in llm_news:
        url = item.get("url", "")
        base_url = url.split("?")[0].rstrip("/")

        original = url_index.get(url) or url_index_normalized.get(base_url)
        if not original:
            # Keep the item but log a warning — don't reject valid news
            logger.debug(
                "Gemini returned URL not in original set (keeping anyway): %s", url[:80]
            )
            item["source_count"] = item.get("source_count", 1)
            item.setdefault("alert_flags", [])
            verified.append(item)
            continue

        if item.get("deal_size_eur"):
            orig_text = (original.get("title", "") + " " + original.get("summary", "")).lower()
            orig_amount = extract_amount_eur(orig_text)
            if orig_amount is None:
                logger.warning("Hallucinated amount removed from: %s", item.get("headline", "")[:60])
                item["deal_size_eur"] = None
                item["confidence"] = "medium"

        item["source_count"] = original.get("source_count", 1)
        item["alert_flags"] = original.get("alert_flags", [])

        verified.append(item)

    logger.info("Post-verification: %d/%d passed", len(verified), len(llm_news))
    return verified
