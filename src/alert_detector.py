"""Heuristic alert detection — no LLM calls for reliability and quota economy."""
import logging
import re

logger = logging.getLogger(__name__)

_DEAL_KEYWORDS = [
    "acquires", "merger", "buyout", "lbo", "buys", "to buy", "deal",
    "tender", "takeover", "bid for", "acquire", "acquisition", "m&a",
]

_IG_TO_HY_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"cut\w*.{0,60}to\s+(junk|speculative[- ]grade|bb\+?|bb-)",
        r"downgrad\w+.{0,60}to\s+(junk|speculative[- ]grade|bb\+?|bb-)",
        r"loses?\s+investment[- ]grade",
        r"falls?\s+to\s+(junk|speculative[- ]grade)",
        r"strip\w+.{0,40}of\s+investment[- ]grade",
        r"fallen\s+angel",
        r"fallen-angel",
        r"tombé\s+en\s+catégorie\s+spéculative",
        r"dégradé\s+en\s+(junk|spéculatif)",
    ]
]

_PROFIT_WARNING_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"cuts?\s+(?:profit\s+)?guidance.{0,40}([2-9]\d)\s*%",
        r"profit\s+warning.{0,40}([2-9]\d)\s*%",
        r"earnings?\s+(?:down|fall|drop).{0,30}([2-9]\d)\s*%",
        r"slash\w*\s+(?:earnings?|forecast|guidance).{0,40}([2-9]\d)\s*%",
        r"avertissement.{0,40}([2-9]\d)\s*%",
        r"révise?\s+à\s+la\s+baisse.{0,40}([2-9]\d)\s*%",
        r"(?:net\s+)?(?:income|profit|earnings?)\s+(?:fell?|drop\w*|declin\w*).{0,30}([2-9]\d)\s*%",
    ]
]


def detect_hot_alerts(news_list: list[dict]) -> list[dict]:
    """Detect hot alerts using pure heuristics. No LLM calls."""
    alerts: list[dict] = []

    for item in news_list:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        flags: list[dict] = []

        # 1. Mega deal >5Md€
        deal_size = item.get("deal_size_eur")
        if deal_size and deal_size >= 5_000_000_000:
            if any(kw in text for kw in _DEAL_KEYWORDS):
                flags.append({
                    "type": "MEGA_DEAL",
                    "severity": "high",
                    "reason": f"Deal de {deal_size / 1e9:.1f} Md€ détecté",
                })

        # 2. Downgrade IG → HY (fallen angel)
        for pattern in _IG_TO_HY_PATTERNS:
            if pattern.search(text):
                flags.append({
                    "type": "FALLEN_ANGEL",
                    "severity": "high",
                    "reason": "Downgrade IG→HY (fallen angel) détecté",
                })
                break

        # 3. Profit warning ≥20%
        for pattern in _PROFIT_WARNING_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    pct = int(match.group(1))
                    if pct >= 20:
                        flags.append({
                            "type": "PROFIT_WARNING",
                            "severity": "high",
                            "reason": f"Profit warning ≥{pct}% détecté",
                        })
                        break
                except (IndexError, ValueError):
                    pass

        if flags:
            alert_item = dict(item)
            alert_item["alert_flags"] = flags
            alerts.append(alert_item)
            logger.info(
                "ALERT detected: %s — %s",
                item.get("title", "")[:80],
                [f["type"] for f in flags],
            )

    return alerts
