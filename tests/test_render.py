"""Tests for Jinja2 template rendering — validates HTML output."""
from pathlib import Path
from datetime import datetime

import pytest
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup


TEMPLATE_DIR = Path(__file__).parent.parent / "src" / "templates"

MOCK_BRIEF = {
    "date": "2026-05-07",
    "generated_at": "2026-05-07T08:31:00+02:00",
    "stats": {"collected": 85, "verified": 72, "filtered": 40, "post_verified": 10},
    "low_volume": False,
    "news": [
        {
            "rank": 1,
            "category": "M&A",
            "headline": "KKR finalise le LBO de SunEnergy pour 6.5 Md€",
            "source": "Reuters",
            "date": "2026-05-07",
            "url": "https://reuters.com/kkr-sunenergy",
            "sector": "Energy",
            "geography": "France",
            "deal_size_eur": 6_500_000_000,
            "confidence": "high",
            "source_count": 3,
            "summary": "KKR et ses co-investisseurs ont finalisé l'acquisition de SunEnergy pour 6,5 milliards d'euros.",
            "so_what": "Transaction structurante pour le marché du LevFin européen.",
            "alert_flags": [],
        },
        {
            "rank": 2,
            "category": "Macro",
            "headline": "La BCE maintient ses taux directeurs à 4,5%",
            "source": "ECB Press",
            "date": "2026-05-07",
            "url": "https://ecb.europa.eu/press/test",
            "sector": "Financials",
            "geography": "Other Europe",
            "deal_size_eur": None,
            "confidence": "high",
            "source_count": 4,
            "summary": "Le Conseil des gouverneurs de la BCE a décidé de maintenir les taux inchangés.",
            "so_what": "Signal accommodant pour le refinancement high yield.",
            "alert_flags": [],
        },
    ],
}

MOCK_ALERT = {
    "headline": "S&P dégrade Casino en catégorie spéculative",
    "title": "S&P cuts Casino to junk amid liquidity concerns",
    "source": "S&P Ratings",
    "date": "2026-05-07",
    "published": "2026-05-07T10:15:00+00:00",
    "url": "https://spglobal.com/casino-downgrade",
    "sector": "Consumer",
    "geography": "France",
    "deal_size_eur": None,
    "confidence": "high",
    "source_count": 2,
    "summary": "S&P Global Ratings a abaissé la note de Casino de BBB- à BB+.",
    "so_what": "Fallen angel avec impact immédiat sur CLO et mandats IG.",
    "alert_flags": [{"type": "FALLEN_ANGEL", "severity": "high", "reason": "Downgrade IG→HY"}],
}


def _get_env() -> Environment:
    return Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


def test_brief_template_renders():
    env = _get_env()
    template = env.get_template("email_brief.html")
    html = template.render(
        brief=MOCK_BRIEF,
        streamlit_url="https://test.streamlit.app",
        generated_at="07/05/2026 à 08:31",
    )
    assert html
    assert len(html) > 1000


def test_brief_template_valid_html():
    env = _get_env()
    template = env.get_template("email_brief.html")
    html = template.render(
        brief=MOCK_BRIEF,
        streamlit_url="https://test.streamlit.app",
        generated_at="07/05/2026 à 08:31",
    )
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("body") is not None
    assert soup.find("h1") is not None


def test_brief_template_contains_news():
    env = _get_env()
    template = env.get_template("email_brief.html")
    html = template.render(
        brief=MOCK_BRIEF,
        streamlit_url="https://test.streamlit.app",
        generated_at="07/05/2026 à 08:31",
    )
    assert "KKR" in html
    assert "BCE" in html
    assert "M&amp;A" in html or "M&A" in html


def test_brief_template_links_present():
    env = _get_env()
    template = env.get_template("email_brief.html")
    html = template.render(
        brief=MOCK_BRIEF,
        streamlit_url="https://test.streamlit.app",
        generated_at="07/05/2026 à 08:31",
    )
    soup = BeautifulSoup(html, "html.parser")
    links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
    assert any("reuters.com" in (link or "") for link in links)
    assert any("streamlit.app" in (link or "") for link in links)


def test_alert_template_renders():
    env = _get_env()
    template = env.get_template("email_alert.html")
    html = template.render(
        item=MOCK_ALERT,
        alert_type="FALLEN_ANGEL",
        alert_reason="Downgrade IG→HY (fallen angel) détecté",
        streamlit_url="https://test.streamlit.app",
        generated_at="07/05/2026 à 10:15",
    )
    assert html
    assert "HOT ALERT" in html
    assert "Casino" in html


def test_alert_template_valid_html():
    env = _get_env()
    template = env.get_template("email_alert.html")
    html = template.render(
        item=MOCK_ALERT,
        alert_type="FALLEN_ANGEL",
        alert_reason="Downgrade IG→HY",
        streamlit_url="https://test.streamlit.app",
        generated_at="07/05/2026 à 10:15",
    )
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("body") is not None
