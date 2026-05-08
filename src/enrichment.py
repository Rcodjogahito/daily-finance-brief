"""Sector, geography, deal size extraction, and regional grouping."""
import re
from typing import Optional

SECTOR_MAP: dict[str, list[str]] = {
    "Real Estate":   ["real estate", "reit", "property fund", "immobilier", "mortgage",
                      "commercial property", "office space", "logistics park"],
    "Energy":        ["oil", "gas", "lng", "renewable", "solar", "wind", "energy",
                      "hydrogen", "power", "utility", "nuclear", "petrochemi"],
    "Financials":    ["bank", "insurance", "asset manager", "fintech", "lender",
                      "broker", "capital market", "credit", "private equity",
                      "hedge fund", "investment fund"],
    "Healthcare":    ["pharma", "biotech", "hospital", "medtech", "drug", "vaccine",
                      "clinical", "therapeutics", "biopharma"],
    "TMT":           ["tech", "software", "telecom", "media", "saas", "cloud",
                      "semiconductor", "chip", "ai ", "artificial intelligence",
                      "data center", "cybersecurity"],
    "Industrials":   ["manufacturer", "industrial", "machinery", "chemical",
                      "engineering", "infrastructure"],
    "Aviation":      ["airline", "airbus", "boeing", "aircraft", "aviation", "airport",
                      "helicopter", "jet"],
    "Defense":       ["defense", "defence", "military", "weapons", "armament",
                      "nato", "army", "navy", "rheinmetall", "thales", "safran",
                      "lockheed", "raytheon", "bae system"],
    "Consumer":      ["retail", "consumer", "food", "beverage", "apparel", "restaurant",
                      "supermarket", "e-commerce"],
    "Luxury":        ["luxury", "lvmh", "kering", "hermes", "richemont", "fashion",
                      "cartier", "dior", "gucci", "prada", "chanel"],
    "Entertainment": ["disney", "netflix", "streaming", "studio", "entertainment",
                      "warner", "universal", "music", "gaming", "videogam"],
    "Real Estate":   ["real estate", "reit", "property", "immobilier", "mortgage",
                      "commercial property", "office", "logistics park"],
    "Materials":     ["mining", "steel", "cement", "commodity", "copper", "lithium",
                      "aluminium", "aluminum"],
    "Services":      ["consulting", "outsourcing", "services", "facility management"],
}

# Mapping geography → macro-region for the UI region filter
GEO_TO_REGION: dict[str, str] = {
    "France": "Europe", "UK": "Europe", "Germany": "Europe", "Italy": "Europe",
    "Spain": "Europe", "Nordics": "Europe", "Benelux": "Europe", "Other Europe": "Europe",
    "MENA": "EMEA", "Africa": "EMEA",
    "USA": "Amériques", "Canada": "Amériques", "LatAm": "Amériques",
    "Asia": "APAC",
    "Global": "Global",
}

# Region → set of geographies (used by Streamlit filters)
REGION_GEO_MAP: dict[str, set[str]] = {
    "Europe":    {"France", "UK", "Germany", "Italy", "Spain", "Nordics", "Benelux", "Other Europe"},
    "EMEA":      {"France", "UK", "Germany", "Italy", "Spain", "Nordics", "Benelux", "Other Europe", "MENA", "Africa"},
    "APAC":      {"Asia"},
    "Afrique":   {"Africa"},
    "Amériques": {"USA", "Canada", "LatAm"},
    "Global":    {"Global"},
}

GEO_MAP: dict[str, list[str]] = {
    "France":        ["france", "french", "paris", "lyon", "marseille", "française",
                      "edf", "totalenergies", "bnp", "axa", "engie", "renault",
                      "lvmh", "airbus"],
    "UK":            ["uk", "britain", "london", "british", "england", "scotland"],
    "Germany":       ["germany", "german", "berlin", "frankfurt", "munich",
                      "volkswagen", "siemens", "deutsche"],
    "Italy":         ["italy", "italian", "milan", "rome", "mediobanca"],
    "Spain":         ["spain", "spanish", "madrid", "barcelona", "santander", "bbva"],
    "Nordics":       ["sweden", "norway", "finland", "denmark", "nordic",
                      "stockholm", "oslo", "copenhagen"],
    "Benelux":       ["netherlands", "belgium", "luxembourg", "dutch", "amsterdam",
                      "brussels", "ing bank", "philips"],
    "Other Europe":  ["europe", "european", "eu ", "eurozone", "ecb", "continent"],
    "USA":           ["us ", "usa", "united states", "american", "wall street",
                      "new york", "silicon valley", "federal reserve", "fed "],
    "Canada":        ["canada", "canadian", "toronto", "montreal"],
    "MENA":          ["saudi", "uae", "qatar", "egypt", "middle east", "riyadh",
                      "abu dhabi", "dubai", "aramco", "adnoc"],
    "Africa":        ["africa", "african", "nigeria", "south africa", "kenya",
                      "morocco", "ghana"],
    "Asia":          ["china", "japan", "korea", "india", "asia", "singapore",
                      "hong kong", "taiwan", "beijing", "tokyo", "alibaba",
                      "softbank", "tata"],
    "LatAm":         ["brazil", "mexico", "argentina", "latin america", "colombia",
                      "chile", "sao paulo"],
    "Global":        ["global", "worldwide", "international", "cross-border"],
}

# Currency conversion (rough approximation, updated manually if needed)
_FX = {"$": 0.92, "€": 1.0, "£": 1.17, "chf": 1.03, "kr": 0.09}

_AMOUNT_PATTERN = re.compile(
    r"(?:€|EUR|£|GBP|\$|USD|CHF|NOK|SEK|DKK)\s*([\d,\.]+)\s*"
    r"(billion|bn|million|mn|Md|Mds|trillion|tr)?"
    r"|"
    r"([\d,\.]+)\s*"
    r"(billion|bn|million|mn|Md|Mds|trillion|tr)\s*"
    r"(?:€|EUR|£|GBP|\$|USD|CHF)?",
    re.IGNORECASE,
)


def _parse_multiplier(unit: str) -> float:
    unit = (unit or "").lower().strip()
    if unit in ("billion", "bn", "md", "mds"):
        return 1e9
    if unit in ("million", "mn"):
        return 1e6
    if unit in ("trillion", "tr"):
        return 1e12
    return 1.0


def extract_amount_eur(text: str) -> Optional[float]:
    """Extract the largest monetary amount found, converted to EUR."""
    amounts: list[float] = []
    for m in _AMOUNT_PATTERN.finditer(text):
        try:
            if m.group(1):  # currency then number (match starts with currency symbol)
                raw = float(m.group(1).replace(",", ""))
                mult = _parse_multiplier(m.group(2))
                # Read currency symbol from the match itself
                match_head = text[m.start() : m.start() + 4].lower()
                if "$" in match_head[:1] or "usd" in match_head:
                    fx = 0.92
                elif "£" in match_head[:1] or "gbp" in match_head:
                    fx = 1.17
                elif "chf" in match_head:
                    fx = 1.03
                else:
                    fx = 1.0
                amounts.append(raw * mult * fx)
            elif m.group(3):  # number then unit (and optional currency)
                raw = float(m.group(3).replace(",", ""))
                mult = _parse_multiplier(m.group(4))
                amounts.append(raw * mult)
        except (ValueError, TypeError):
            continue
    return max(amounts) if amounts else None


def detect_sector(text: str, sector_map: dict) -> Optional[str]:
    for sector, keywords in sector_map.items():
        if any(kw in text for kw in keywords):
            return sector
    return None


def detect_geography(text: str, geo_map: dict) -> Optional[str]:
    for geo, keywords in geo_map.items():
        if any(kw in text for kw in keywords):
            return geo
    return None


def detect_region(geography: str) -> str:
    """Map a geography string to its macro-region."""
    return GEO_TO_REGION.get(geography, "Global")


def enrich_news(item: dict) -> dict:
    """Enrich a news item with sector, geography, region, and deal size."""
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()

    item["sector"]      = detect_sector(text, SECTOR_MAP) or "Other"
    item["geography"]   = detect_geography(text, GEO_MAP) or "Global"
    item["region"]      = detect_region(item["geography"])
    item["deal_size_eur"] = extract_amount_eur(text)

    return item


def enrich_all(items: list[dict]) -> list[dict]:
    return [enrich_news(item) for item in items]
