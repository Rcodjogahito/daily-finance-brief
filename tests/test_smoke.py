"""Smoke tests — all imports must work."""


def test_import_collectors():
    from src.collectors.sources import SOURCES
    from src.collectors.rss_collector import collect_all_sources, collect_one_source
    assert isinstance(SOURCES, dict)
    assert len(SOURCES) > 0


def test_import_filters():
    from src.filters import apply_filters, passes_whitelist, passes_blacklist, deduplicate
    assert callable(apply_filters)


def test_import_verifier():
    from src.verifier import verify_news_batch, is_url_alive, is_date_in_window
    assert callable(verify_news_batch)


def test_import_enrichment():
    from src.enrichment import enrich_news, extract_amount_eur, detect_sector, detect_geography
    assert callable(enrich_news)


def test_import_alert_detector():
    from src.alert_detector import detect_hot_alerts
    assert callable(detect_hot_alerts)


def test_import_analyzer():
    from src.analyzer import analyze_news, post_verify_llm_output
    assert callable(analyze_news)


def test_import_emailer():
    from src.emailer import send_email, get_recipients
    assert callable(send_email)


def test_import_archiver():
    from src.archiver import save_brief, save_alerts, load_brief, list_brief_dates
    assert callable(save_brief)


def test_sources_all_have_urls():
    from src.collectors.sources import SOURCES
    for name, url in SOURCES.items():
        assert url.startswith("http"), f"Source '{name}' has invalid URL: {url}"
