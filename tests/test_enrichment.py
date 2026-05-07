"""Tests for enrichment module — sector, geography, deal size extraction."""
import pytest
from src.enrichment import extract_amount_eur, detect_sector, detect_geography, enrich_news, SECTOR_MAP, GEO_MAP


@pytest.mark.parametrize("text,expected_min,expected_max", [
    ("TotalEnergies acquires SunPower for $8.2 billion", 7e9, 8e9),
    ("KKR closes €4.5Md LBO", 4e9, 5e9),
    ("Deal valued at £3.1bn", 3e9, 4.5e9),
    ("Transaction of 2.5 billion EUR", 2e9, 3e9),
    ("No amount here", None, None),
    ("$500 million acquisition", 400e6, 600e6),
])
def test_extract_amount_eur(text, expected_min, expected_max):
    result = extract_amount_eur(text.lower())
    if expected_min is None:
        assert result is None
    else:
        assert result is not None
        assert expected_min <= result <= expected_max


@pytest.mark.parametrize("text,expected_sector", [
    ("TotalEnergies oil gas lng pipeline project finance", "Energy"),
    ("KKR private equity buyout leveraged loan", "Financials"),
    ("Airbus Boeing aircraft airline deal", "Aviation"),
    ("Rheinmetall defense military contract NATO", "Defense"),
    ("LVMH Kering luxury fashion merger", "Luxury"),
    ("Netflix Disney streaming entertainment deal", "Entertainment"),
    ("pharma biotech clinical drug acquisition", "Healthcare"),
    ("real estate REIT property fund", "Real Estate"),
])
def test_detect_sector(text, expected_sector):
    result = detect_sector(text.lower(), SECTOR_MAP)
    assert result == expected_sector, f"Expected {expected_sector}, got {result}"


@pytest.mark.parametrize("text,expected_geo", [
    ("French company Paris France deal", "France"),
    ("London UK British bank merger", "UK"),
    ("Frankfurt Germany Volkswagen acquisition", "Germany"),
    ("Wall Street US Federal Reserve rate hike", "USA"),
    ("Saudi Arabia Aramco MENA deal", "MENA"),
    ("China Beijing Asia acquisition", "Asia"),
    ("ECB European rate decision", "Other Europe"),
])
def test_detect_geography(text, expected_geo):
    result = detect_geography(text.lower(), GEO_MAP)
    assert result == expected_geo, f"Expected {expected_geo}, got {result}"


def test_enrich_news_complete():
    item = {
        "title": "KKR acquires French energy company for €5.5 billion",
        "summary": "Private equity firm KKR completes LBO of Engie subsidiary for 5.5 billion euros in project finance deal.",
    }
    enriched = enrich_news(item)
    assert enriched["sector"] in ("Energy", "Financials")
    assert enriched["geography"] in ("France", "Other Europe")
    assert enriched["deal_size_eur"] is not None
    assert enriched["deal_size_eur"] > 4e9


def test_enrich_news_no_amount():
    item = {
        "title": "ECB holds interest rates steady",
        "summary": "European Central Bank decides to maintain rates at 4.5%.",
    }
    enriched = enrich_news(item)
    assert enriched["sector"] is not None
    assert enriched["deal_size_eur"] is None
