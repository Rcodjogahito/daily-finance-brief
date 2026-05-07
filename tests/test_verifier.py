"""Tests for verifier module."""
from datetime import datetime, timezone, timedelta

import pytest
from src.verifier import is_date_in_window, has_spam_pattern, verify_news_batch


def _make_item(title: str, published_offset_hours: int = 0, url: str = "https://example.com/valid") -> dict:
    dt = datetime.now(timezone.utc) - timedelta(hours=published_offset_hours)
    return {
        "title": title,
        "url": url,
        "summary": "Test summary",
        "published": dt.isoformat(),
        "source": "Reuters",
    }


class TestDateWindow:
    def test_fresh_news_passes(self):
        assert is_date_in_window(datetime.now(timezone.utc).isoformat(), max_age_hours=72)

    def test_48h_old_passes(self):
        dt = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        assert is_date_in_window(dt, max_age_hours=72)

    def test_80h_old_fails(self):
        dt = (datetime.now(timezone.utc) - timedelta(hours=80)).isoformat()
        assert not is_date_in_window(dt, max_age_hours=72)

    def test_none_date_passes(self):
        assert is_date_in_window(None)

    def test_future_date_passes(self):
        dt = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        assert is_date_in_window(dt)


class TestSpamPatterns:
    @pytest.mark.parametrize("title", [
        "CLICK HERE to read more!!!",
        "Subscribe now for free gift",
        "Limited time offer: act now",
        "News?? What news??",
    ])
    def test_spam_detected(self, title):
        assert has_spam_pattern(title)

    @pytest.mark.parametrize("title", [
        "ECB holds rates at 4.5% amid inflation concerns",
        "KKR completes €5.5bn LBO of French energy company",
        "S&P downgrades Casino to junk status",
    ])
    def test_clean_news_no_spam(self, title):
        assert not has_spam_pattern(title)


class TestVerifyNewsBatch:
    def test_valid_item_passes(self):
        item = _make_item("KKR acquires French utility for €5 billion")
        result = verify_news_batch([item], check_urls=False)
        assert len(result) == 1

    def test_too_short_title_rejected(self):
        item = _make_item("Hi")
        result = verify_news_batch([item], check_urls=False)
        assert len(result) == 0

    def test_too_long_title_rejected(self):
        item = _make_item("A" * 400)
        result = verify_news_batch([item], check_urls=False)
        assert len(result) == 0

    def test_old_news_rejected(self):
        item = _make_item("KKR acquires firm for €5bn", published_offset_hours=80)
        result = verify_news_batch([item], check_urls=False)
        assert len(result) == 0

    def test_spam_title_rejected(self):
        item = _make_item("Subscribe now for free financial news!!!")
        result = verify_news_batch([item], check_urls=False)
        assert len(result) == 0

    def test_batch_mixed(self):
        items = [
            _make_item("ECB rate decision: hold at 4.5%"),
            _make_item("Hi"),
            _make_item("LVMH Q1 earnings beat consensus by 12%"),
            _make_item("Old news", published_offset_hours=80),
        ]
        result = verify_news_batch(items, check_urls=False)
        assert len(result) == 2
