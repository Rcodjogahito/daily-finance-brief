"""URL validation, date checks, anti-spam, and cross-source fact checking."""
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_SPAM_PATTERNS = [
    r"\bclick\s+here\b",
    r"\bsubscribe\s+now\b",
    r"\bwin\s+a\b",
    r"\bfree\s+gift\b",
    r"\blimited\s+time\s+offer\b",
    r"\bact\s+now\b",
    r"!!+",
    r"\?\?+",
]

_SPAM_RE = [re.compile(p, re.IGNORECASE) for p in _SPAM_PATTERNS]


def is_url_alive(url: str, timeout: int = 5) -> bool:
    """HEAD request with 5s timeout; accept HTTP 200-399."""
    if not url or not url.startswith("http"):
        return False
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True, headers={
            "User-Agent": "DailyFinanceBrief/1.0"
        })
        return resp.status_code < 400
    except Exception:
        # Fallback: try GET if HEAD fails (some servers block HEAD)
        try:
            resp = requests.get(url, timeout=timeout, stream=True, headers={
                "User-Agent": "DailyFinanceBrief/1.0"
            })
            return resp.status_code < 400
        except Exception:
            return False


def is_date_in_window(published: Optional[str], max_age_hours: int = 72) -> bool:
    """Returns True if the published date is within the allowed window."""
    if not published:
        return True  # Give benefit of the doubt if no date
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - dt
        return age <= timedelta(hours=max_age_hours)
    except Exception:
        return True


def has_spam_pattern(title: str) -> bool:
    return any(p.search(title) for p in _SPAM_RE)


def verify_news_batch(news: list[dict], check_urls: bool = True) -> list[dict]:
    """Filter news items that don't pass reliability checks."""
    verified = []
    for item in news:
        # 1. Title sanity
        title = item.get("title", "")
        if not (10 < len(title) < 300):
            logger.debug("Title length rejected: %s", title[:60])
            continue

        # 2. Spam patterns
        if has_spam_pattern(title):
            logger.debug("Spam pattern rejected: %s", title[:60])
            continue

        # 3. Date window (72h to cover weekends)
        if not is_date_in_window(item.get("published"), max_age_hours=72):
            logger.debug("Date out of window: %s", item.get("published"))
            continue

        # 4. URL alive (optional, slow — enable for final run)
        if check_urls and item.get("url"):
            if not is_url_alive(item["url"]):
                logger.warning("Dead URL rejected: %s", item["url"])
                continue

        verified.append(item)

    logger.info("Verification: %d/%d passed", len(verified), len(news))
    return verified


def count_similar_titles(item: dict, all_news: list[dict], threshold: float = 0.7) -> int:
    """Count how many other items have similar title (for multi-source corroboration)."""
    import difflib
    from unidecode import unidecode

    def norm(t: str) -> str:
        return unidecode(t.lower()).strip()

    target = norm(item.get("title", ""))
    count = 0
    for other in all_news:
        if other is item:
            continue
        ratio = difflib.SequenceMatcher(None, target, norm(other.get("title", ""))).ratio()
        if ratio >= threshold:
            count += 1
    return count


def cross_check_facts(news_item: dict, all_news: list[dict]) -> dict:
    """Tag 'multi_source' if the news is confirmed by 2+ sources."""
    similar = count_similar_titles(news_item, all_news, threshold=0.7)
    news_item["source_count"] = max(news_item.get("source_count", 1), similar + 1)
    news_item["confidence"] = "high" if news_item["source_count"] >= 2 else "medium"
    return news_item
