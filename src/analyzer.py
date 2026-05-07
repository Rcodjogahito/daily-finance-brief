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

SYSTEM_PROMPT = """Tu es un analyste senior en banque d'investissement (Leveraged Finance / M&A / Energy) au sein d'un CIB Tier-1.
Tu prépares un brief quotidien pour ton équipe deal team.
Style : dense, factuel, technique. Pas de bla-bla, pas d'évidences, pas de paraphrase creuse.

RÈGLES DE FIABILITÉ ABSOLUES :
- N'invente JAMAIS un fait, un chiffre, un nom ou un montant qui n'apparaît pas explicitement dans la news source fournie
- Si une donnée est ambiguë ou incertaine, écris "à confirmer" plutôt que d'affirmer
- Le "So what?" doit s'appuyer UNIQUEMENT sur les faits du résumé, jamais en extrapoler de nouveaux
- Si tu n'as pas assez de matière fiable pour 10 news, mets-en moins (5, 7, etc.) plutôt que de remplir avec du faible"""

USER_PROMPT_TEMPLATE = """À partir des news ci-dessous (collectées dans les dernières 24h), sélectionne les 10 max les plus pertinentes pour un professionnel CIB. Mets MOINS si le matériel ne le justifie pas.

CRITÈRES DE SÉLECTION (priorité décroissante) :
1. Deal flow structurant : M&A >500M€, LBO majeurs, IPO sizables, mandates exclusifs
2. Leveraged Finance / DCM : refis HY, leveraged loans, distressed, breach covenants
3. Énergie : O&G majors, project finance, renewables, transition
4. Crédit & ratings : downgrades/upgrades grands corporates, profit warnings
5. Macro & banques centrales : décisions BCE/Fed/BoE, inflation, FX, taux
6. Géopolitique à impact financier immédiat (sanctions, tariffs, conflits)
7. Sectoriel structurant : défense (méga-contrats), tech (deals/earnings Big Tech), aviation (commandes >2Md€), luxe (M&A, profit warnings), retail/divertissement (consolidation), healthcare (deals pharma/biotech)
8. Régulation financière à impact deal/marché

EXCLURE : politique non-éco, faits divers, sport, lifestyle, tech grand public sans angle financier, news redondantes.

BONUS PERTINENCE : privilégie les news avec source_count ≥ 2 (corroborées).

POUR CHAQUE NEWS RETENUE, FORMAT JSON STRICT :
{
  "rank": <int, 1=plus important>,
  "category": <"M&A"|"LevFin"|"Energy"|"Credit"|"Macro"|"Geo"|"Reg"|"Sector">,
  "headline": "<titre concis et impactant en français, 12 mots max>",
  "source": "<nom du média original>",
  "date": "<YYYY-MM-DD>",
  "url": "<lien original exact — NE PAS modifier>",
  "sector": "<secteur>",
  "geography": "<géographie>",
  "deal_size_eur": <null OU montant EUR si EXPLICITEMENT dans la source>,
  "confidence": <"high"|"medium">,
  "summary": "<2-3 phrases factuelles : qui, quoi, combien, quand. PARAPHRASE uniquement. UNIQUEMENT faits présents dans la source.>",
  "so_what": "<2-3 phrases analyse niveau senior banker. S'appuie UNIQUEMENT sur les faits du summary.>"
}

CONTRAINTES :
- Réponds UNIQUEMENT en JSON valide : {"news": [...]}
- Aucun texte hors JSON, aucun markdown, aucun ```
- Si <10 news pertinentes : ne mets que ce qui mérite (5-9 OK)
- Si incohérences : confidence "medium" et "à confirmer" dans le summary

NEWS À ANALYSER :
{news_json}
"""

ALERT_PROMPT_TEMPLATE = """Tu es un analyste senior CIB. Rédige un "So what?" pour l'alerte suivante.

RÈGLE ABSOLUE : Appuie-toi UNIQUEMENT sur les faits présents dans le résumé. N'invente aucun fait.

News :
- Titre : {title}
- Source : {source}
- Résumé : {summary}
- Type d'alerte : {alert_type}
- Raison : {alert_reason}

Réponds en JSON valide UNIQUEMENT :
{{"so_what": "<2-3 phrases d'analyse. Précis, technique, actionnable pour un banquier CIB.>"}}
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
            max_output_tokens=4096,
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


def _fallback_selection(candidates: list[dict]) -> list[dict]:
    """Fallback when Gemini is unavailable: return top N by source priority + source_count."""
    from src.filters import _source_priority

    def score(item: dict) -> float:
        return _source_priority(item.get("source", "")) + item.get("source_count", 1) * 0.5

    sorted_items = sorted(candidates, key=score, reverse=True)[:10]
    result = []
    for i, item in enumerate(sorted_items, 1):
        result.append({
            "rank": i,
            "category": "Sector",
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
            "so_what": "[Analyse LLM indisponible — Gemini API hors service]",
            "alert_flags": [],
        })
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
