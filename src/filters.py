"""Whitelist / blacklist filtering and near-duplicate removal."""
import difflib
import re

from unidecode import unidecode

SOURCE_PRIORITY: dict[str, int] = {
    "Reuters": 10,
    "FT": 10,
    "Bloomberg": 10,
    "WSJ": 9,
    "Economist": 8,
    "Les Echos": 7,
    "Le Monde": 7,
    "L'AGEFI": 7,
    "AGEFI": 7,
}

WHITELIST: list[str] = [
    # M&A / Deals
    "m&a", "merger", "acquisition", "acquires", "acquired", "buyout", "lbo",
    "private equity", "sponsor", "carve-out", "spin-off", "ipo", "tender offer",
    "fusion", "rachat", "opa", "ope", "takeover", "bid",
    # LevFin/DCM
    "leveraged loan", "high yield", "refinancing", "refinanced", "covenant",
    "term loan", "tlb", "syndicated", "bond issuance", "clo", "pik", "distressed",
    "restructuring", "chapter 11", "default", "refinancement", "mrel", "at1",
    "schuldschein", "green bond", "sustainability-linked",
    # Crédit/Ratings
    "downgrade", "upgrade", "outlook negative", "outlook positive", "profit warning",
    "guidance cut", "degradation", "rehaussement", "avertissement sur resultats",
    "fallen angel", "investment grade", "speculative grade", "junk",
    # Énergie
    "offtake", "ppa", "project finance", "fid", "lng", "oil major", "renewables",
    "wind farm", "solar", "transition energetique", "hydrogen",
    # Macro
    "ecb", "fed ", "boe", "bce", "rate hike", "rate cut", "inflation", "cpi", "pmi",
    "taux directeur", "quantitative", "yield curve", "basis points", "bps",
    # Nominations importantes
    "appointed ceo", "appointed cfo", "named ceo", "named cfo", "nommé directeur",
    "new chief executive", "new cfo", "president appointed", "chairman named",
    "chief financial officer", "chief executive officer", "directeur général",
    # Actualité bancaire
    "bank results", "banking sector", "cet1", "tier 1", "capital ratio",
    "stress test", "eba ", "ecb supervision", "npls", "non-performing",
    "bale iv", "basel iv", "banking union", "consolidation bancaire",
    "merger of banks", "bank acquisition", "banco", "résultats bancaires",
    # Sectoriel
    "earnings", "revenue", "guidance", "contract", "mandate", "order book", "backlog",
    "defense", "defence", "aerospace", "pharma", "luxury", "retail", "streaming",
    "dividend", "capital raise", "rights issue", "bond", "debt",
    # Géopolitique
    "sanctions", "tariffs", "trade war", "geopolitical", "reshoring", "conflict",
    # Commodities
    "opec", "wti", "brent crude", "crude oil price", "natural gas price", "lng price",
    "coal price", "gold price", "silver price", "copper price", "nickel price",
    "aluminium price", "zinc price", "iron ore", "platinum", "palladium",
    "wheat price", "corn price", "soybean", "cocoa price", "coffee price",
    "sugar price", "palm oil", "precious metal", "base metal",
    "lme ", "cme group", "cftc", "commodity futures", "commodity market",
    "commodity index", "oil market", "oil supply", "oil demand", "oil production",
]

BLACKLIST: list[str] = [
    "sport", "football", "tennis", "celebrity", "royal family", "weather",
    "horoscope", "recipe", "fashion week", "gossip", "dating", "entertainment award",
    "oscars", "grammy", "world cup", "olympic", "nba ", "nfl ", "nhl ",
    "cricket", "rugby score",
]


def _normalize(text: str) -> str:
    text = unidecode(text.lower())
    text = re.sub(r"[^\w\s&]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _source_priority(source_name: str) -> int:
    for key, val in SOURCE_PRIORITY.items():
        if key.lower() in source_name.lower():
            return val
    return 5


def passes_whitelist(item: dict) -> bool:
    text = _normalize(item.get("title", "") + " " + item.get("summary", ""))
    return any(kw in text for kw in WHITELIST)


def passes_blacklist(item: dict) -> bool:
    text = _normalize(item.get("title", ""))
    return not any(kw in text for kw in BLACKLIST)


def deduplicate(items: list[dict]) -> list[dict]:
    """Remove near-duplicate titles (ratio > 0.85), keeping higher-priority source.
    Also tags multi-source items with source_count > 1.
    """
    normalized = [_normalize(item.get("title", "")) for item in items]
    n = len(items)
    dominated = set()  # indices to drop

    # Build similarity clusters
    similar_to: dict[int, list[int]] = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if i in dominated or j in dominated:
                continue
            ratio = difflib.SequenceMatcher(None, normalized[i], normalized[j]).ratio()
            if ratio > 0.85:
                similar_to[i].append(j)
                similar_to[j].append(i)

    kept: list[dict] = []
    seen: set[int] = set()

    for i in range(n):
        if i in seen:
            continue
        cluster = [i] + similar_to[i]
        # Filter already-seen
        cluster = [c for c in cluster if c not in seen]
        # Pick the best source in the cluster
        cluster.sort(key=lambda c: _source_priority(items[c]["source"]), reverse=True)
        winner_idx = cluster[0]
        winner = dict(items[winner_idx])
        winner["source_count"] = len(cluster)
        winner["confidence"] = "high" if len(cluster) >= 2 else "medium"
        kept.append(winner)
        for c in cluster:
            seen.add(c)

    return kept


def apply_filters(items: list[dict]) -> list[dict]:
    after_blacklist = [it for it in items if passes_blacklist(it)]
    after_whitelist = [it for it in after_blacklist if passes_whitelist(it)]
    deduped = deduplicate(after_whitelist)
    return deduped
