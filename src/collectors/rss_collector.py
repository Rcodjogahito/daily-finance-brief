"""Parallel RSS collection from all configured sources."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

import feedparser
import requests

from src.collectors.sources import SOURCES

logger = logging.getLogger(__name__)

_RESOLVE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def _resolve_one_url(url: str, timeout: int = 6) -> str:
    """Follow HTTP redirects for a Google News proxy URL to get the real article URL."""
    if "news.google.com" not in url:
        return url
    try:
        resp = requests.get(url, allow_redirects=True, timeout=timeout, headers=_RESOLVE_HEADERS)
        final = resp.url
        if "news.google.com" not in final and final.startswith("http"):
            return final
    except Exception as exc:
        logger.debug("URL resolve failed for %s: %s", url[:60], exc)
    return url


def resolve_gnews_urls(items: list[dict], max_workers: int = 8) -> list[dict]:
    """Resolve Google News proxy URLs in parallel. Call this on the final selected items."""
    gnews_items = [(i, item) for i, item in enumerate(items) if "news.google.com" in item.get("url", "")]
    if not gnews_items:
        return items

    result = list(items)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_resolve_one_url, item["url"]): i
            for i, item in gnews_items
        }
        for future in as_completed(futures):
            i = futures[future]
            resolved_url = future.result()
            if resolved_url != result[i]["url"]:
                result[i] = dict(result[i])
                result[i]["url"] = resolved_url
                logger.info("Resolved GNews URL → %s", resolved_url[:80])

    return result

_HEADERS = {"User-Agent": "DailyFinanceBrief/1.0 (+https://github.com/daily-finance-brief)"}


def _parse_date(entry) -> str:
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def collect_one_source(name: str, url: str, timeout: int = 15) -> list[dict]:
    """Fetch and parse one RSS source. Returns list of raw news items."""
    try:
        feed = feedparser.parse(url, request_headers=_HEADERS)
        if feed.bozo and not feed.entries:
            logger.warning("[%s] Feed parse error: %s", name, getattr(feed, "bozo_exception", "unknown"))
            return []

        items: list[dict] = []
        for entry in feed.entries[:30]:
            title = entry.get("title", "").strip()
            url_item = entry.get("link", "").strip()
            if not title or not url_item:
                continue
            summary = (entry.get("summary", "") or entry.get("description", "")).strip()
            # Strip basic HTML from summary
            import re
            summary = re.sub(r"<[^>]+>", " ", summary)
            summary = re.sub(r"\s+", " ", summary).strip()[:1000]

            # For Google News proxy URLs, also store the publisher domain
            publisher_domain = ""
            if "news.google.com" in url_item:
                src_info = entry.get("source", {})
                publisher_domain = src_info.get("href", "") if isinstance(src_info, dict) else ""

            items.append({
                "source": name,
                "url": url_item,
                "publisher_domain": publisher_domain,
                "title": title,
                "summary": summary,
                "published": _parse_date(entry),
                "source_count": 1,
                "confidence": "medium",
                "alert_flags": [],
            })
        return items

    except Exception as exc:
        logger.warning("[%s] Collection failed: %s", name, exc)
        return []


def collect_all_sources(max_workers: int = 10, lookback_hours: int = 24) -> list[dict]:
    """Collect from all sources in parallel, return raw unfiltered items."""
    all_items: list[dict] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(collect_one_source, name, url): name
            for name, url in SOURCES.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                items = future.result(timeout=20)
                all_items.extend(items)
                logger.info("[%s] %d items collected", name, len(items))
            except Exception as exc:
                logger.warning("[%s] Future error: %s", name, exc)

    logger.info("Total collected: %d items from %d sources", len(all_items), len(SOURCES))
    return all_items
