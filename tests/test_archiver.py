"""Tests for archiver — JSON roundtrip."""
import json
from pathlib import Path
import pytest


def test_brief_roundtrip(tmp_path, monkeypatch):
    """Save a brief and load it back."""
    from src import archiver

    monkeypatch.setattr(archiver, "BRIEFS_DIR", tmp_path / "briefs")
    monkeypatch.setattr(archiver, "ALERTS_DIR", tmp_path / "alerts")

    news = [
        {
            "rank": 1,
            "category": "M&A",
            "headline": "KKR acquiert une société française pour 5 Md€",
            "source": "Reuters",
            "date": "2026-05-07",
            "url": "https://reuters.com/test",
            "sector": "Energy",
            "geography": "France",
            "deal_size_eur": 5_000_000_000,
            "confidence": "high",
            "source_count": 3,
            "summary": "KKR a finalisé l'acquisition.",
            "so_what": "Impact crédit positif pour le secteur.",
            "alert_flags": [],
        }
    ]
    stats = {"collected": 87, "verified": 74, "filtered": 42, "post_verified": 10}

    path = archiver.save_brief(news, stats, date="2026-05-07")
    assert path.exists()

    loaded = archiver.load_brief("2026-05-07")
    assert loaded is not None
    assert loaded["date"] == "2026-05-07"
    assert len(loaded["news"]) == 1
    assert loaded["news"][0]["deal_size_eur"] == 5_000_000_000
    assert loaded["stats"]["collected"] == 87


def test_alerts_dedup(tmp_path, monkeypatch):
    """Saving the same alert twice should not duplicate."""
    from src import archiver

    monkeypatch.setattr(archiver, "BRIEFS_DIR", tmp_path / "briefs")
    monkeypatch.setattr(archiver, "ALERTS_DIR", tmp_path / "alerts")

    alert = {
        "url": "https://reuters.com/alert1",
        "title": "Casino downgraded to junk",
        "summary": "S&P cuts Casino to BB+",
        "alert_flags": [{"type": "FALLEN_ANGEL", "severity": "high", "reason": "IG→HY"}],
    }

    archiver.save_alerts([alert], date="2026-05-07")
    archiver.save_alerts([alert], date="2026-05-07")  # Second save — should dedup

    loaded = archiver.load_alerts("2026-05-07")
    assert loaded is not None
    assert len(loaded["alerts"]) == 1  # Not 2


def test_list_brief_dates(tmp_path, monkeypatch):
    from src import archiver

    monkeypatch.setattr(archiver, "BRIEFS_DIR", tmp_path / "briefs")
    monkeypatch.setattr(archiver, "ALERTS_DIR", tmp_path / "alerts")

    (tmp_path / "briefs").mkdir(parents=True)
    for date in ["2026-05-05", "2026-05-06", "2026-05-07"]:
        (tmp_path / "briefs" / f"{date}.json").write_text('{"date": "' + date + '", "news": [], "stats": {}}')

    dates = archiver.list_brief_dates()
    assert dates == ["2026-05-07", "2026-05-06", "2026-05-05"]
