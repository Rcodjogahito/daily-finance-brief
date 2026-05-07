"""Parallel RSS collection from all configured sources."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

import feedparser

from src.collectors.sources import SOURCES

logger = logging.getLogger(__name__)

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

            items.append({
                "source": name,
                "url": url_item,
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
