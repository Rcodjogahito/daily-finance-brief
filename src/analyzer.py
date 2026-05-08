"""Gemini API integration for news analysis with anti-hallucination controls."""
import json
import logging
import os
import re
from typing import Optional

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-2.5-flash"  # Check https://ai.google.dev for latest free model

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
4. Crédit & ratings : downgrades/upgrades grands corporates, profit warnings, fallen angels
5. Macro & banques centrales : BCE/Fed/BoE, inflation, CPI, taux directeurs, FX
6. Géopolitique à impact financier direct : sanctions, tariffs, conflits, reshoring
7. Nominations importantes : CEOs/CFOs/DGs de grandes institutions financières ou corporates
8. Actualité bancaire : résultats banques, consolidation bancaire, régulation prudentielle, CET1, MREL
9. Sectoriel structurant : défense, tech (deals/earnings Big Tech), aviation, luxe, pharma, real estate
10. Régulation financière à impact deal/marché : Bâle IV, CSRD, taxonomie

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


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)


def _extract_json(text: str) -> dict:
    """Robust JSON extraction — handle Gemini preamble or markdown wrapping."""
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_gemini(prompt: str) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=_MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=16000,
            response_mime_type="application/json",
        ),
    )
    return response.text


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
    """Reject/sanitize news where Gemini fabricated amounts not in original source."""
    from src.enrichment import extract_amount_eur

    url_index = {item.get("url", ""): item for item in original_news}
    verified: list[dict] = []

    for item in llm_news:
        url = item.get("url", "")
        original = url_index.get(url)
        if not original:
            logger.warning("Gemini returned URL not in original set — rejected: %s", url[:80])
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
