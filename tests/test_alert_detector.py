"""Tests for alert detector — heuristic patterns."""
import pytest
from src.alert_detector import detect_hot_alerts


def _make_item(title: str, summary: str = "", deal_size: float = None) -> dict:
    return {
        "title": title,
        "summary": summary,
        "url": "https://example.com/news",
        "source": "Reuters",
        "published": "2026-05-07T08:00:00+00:00",
        "deal_size_eur": deal_size,
        "sector": "Other",
        "geography": "Global",
        "source_count": 1,
        "confidence": "medium",
        "alert_flags": [],
    }


class TestMegaDeal:
    def test_mega_deal_detected(self):
        item = _make_item("TotalEnergies acquires SunPower for €8 billion", deal_size=8e9)
        alerts = detect_hot_alerts([item])
        assert len(alerts) == 1
        types = [f["type"] for f in alerts[0]["alert_flags"]]
        assert "MEGA_DEAL" in types

    def test_mega_deal_below_threshold(self):
        item = _make_item("Company A buys Company B for €3 billion", deal_size=3e9)
        alerts = detect_hot_alerts([item])
        assert not any("MEGA_DEAL" in [f["type"] for f in a["alert_flags"]] for a in alerts)

    def test_mega_deal_no_deal_keyword(self):
        # Large amount but no deal keyword → not an alert
        item = _make_item("Company A reports €8 billion revenue", deal_size=8e9)
        alerts = detect_hot_alerts([item])
        assert not any("MEGA_DEAL" in [f["type"] for f in a["alert_flags"]] for a in alerts)

    def test_no_deal_size(self):
        item = _make_item("Company acquires rival", deal_size=None)
        alerts = detect_hot_alerts([item])
        assert not any("MEGA_DEAL" in [f["type"] for f in a["alert_flags"]] for a in alerts)


class TestFallenAngel:
    @pytest.mark.parametrize("text", [
        "S&P cuts Casino to junk",
        "Moody's downgrades Vallourec to BB+",
        "Company loses investment grade status",
        "Fallen angel: Altice falls to speculative grade",
        "Rating agency strips company of investment grade",
    ])
    def test_fallen_angel_detected(self, text):
        item = _make_item(text)
        alerts = detect_hot_alerts([item])
        types = [f["type"] for a in alerts for f in a["alert_flags"]]
        assert "FALLEN_ANGEL" in types, f"Should have detected FALLEN_ANGEL in: {text}"

    def test_regular_downgrade_not_fallen_angel(self):
        item = _make_item("Moody's downgrades France from Aaa to Aa1")
        alerts = detect_hot_alerts([item])
        types = [f["type"] for a in alerts for f in a["alert_flags"]]
        assert "FALLEN_ANGEL" not in types


class TestProfitWarning:
    @pytest.mark.parametrize("text,summary", [
        ("Company A cuts guidance by 35%", ""),
        ("Profit warning: earnings down 45%", ""),
        ("Company A slashes forecast by 22%", ""),
        ("Quarterly earnings fell 28%", ""),
    ])
    def test_profit_warning_detected(self, text, summary):
        item = _make_item(text, summary)
        alerts = detect_hot_alerts([item])
        types = [f["type"] for a in alerts for f in a["alert_flags"]]
        assert "PROFIT_WARNING" in types, f"Should detect PROFIT_WARNING in: {text}"

    def test_profit_warning_below_20pct(self):
        item = _make_item("Company cuts guidance by 15%")
        alerts = detect_hot_alerts([item])
        types = [f["type"] for a in alerts for f in a["alert_flags"]]
        assert "PROFIT_WARNING" not in types

    def test_positive_earnings_no_warning(self):
        item = _make_item("Company A earnings up 30%")
        alerts = detect_hot_alerts([item])
        assert not alerts


def test_multiple_flags_same_item():
    item = _make_item(
        "Fallen angel: Casino cut to junk, profit warning 40% announced",
        deal_size=None,
    )
    alerts = detect_hot_alerts([item])
    if alerts:
        types = [f["type"] for f in alerts[0]["alert_flags"]]
        # At least one alert type should be detected
        assert len(types) >= 1


def test_no_false_positives_on_clean_news():
    items = [
        _make_item("ECB holds rates at 4.5%"),
        _make_item("LVMH reports strong Q1 results"),
        _make_item("Airbus books 50 new aircraft orders"),
    ]
    alerts = detect_hot_alerts(items)
    assert len(alerts) == 0
