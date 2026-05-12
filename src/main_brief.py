"""Daily brief pipeline — 08:30 Paris, 7j/7."""
import json
import logging
import os
import sys
from datetime import datetime

import pytz

from src.alert_detector import detect_hot_alerts
from src.analyzer import analyze_news, post_verify_llm_output
from src.archiver import git_commit_and_push, load_brief, mark_brief_sent, save_brief
from src.collectors.rss_collector import collect_all_sources, resolve_gnews_urls
from src.emailer import get_recipients, send_email
from src.enrichment import enrich_all
from src.filters import apply_filters
from src.market_snapshot import fetch_market_snapshot
from src.verifier import verify_news_batch

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

_PARIS = pytz.timezone("Europe/Paris")
_MAX_CANDIDATES = 80


def _already_sent_today(date_str: str) -> bool:
    """Return True if today's brief was already successfully emailed (dedup guard).
    Prevents double-sends when both UTC+1/+2 crons fire on the same day.
    """
    brief = load_brief(date_str)
    return bool(brief and brief.get("stats", {}).get("email_sent"))


def render_email(brief_data: dict, streamlit_url: str) -> tuple[str, str]:
    """Render HTML and plain-text email from brief data."""
    from jinja2 import Environment, FileSystemLoader
    from pathlib import Path

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("email_brief.html")

    import pytz
    paris = pytz.timezone("Europe/Paris")
    generated_at = datetime.now(paris).strftime("%d/%m/%Y à %H:%M")

    html = template.render(
        brief=brief_data,
        streamlit_url=streamlit_url,
        generated_at=generated_at,
        market=brief_data.get("market_snapshot", {}),
    )

    # Plain text fallback
    news_list = brief_data.get("news", [])
    lines = [
        f"DAILY FINANCE BRIEF — {brief_data.get('date', '')}",
        f"Dashboard : {streamlit_url}",
        "=" * 60,
    ]
    for item in news_list:
        lines.append(f"\n#{item.get('rank', '')} [{item.get('category', '')}] {item.get('headline', '')}")
        lines.append(f"Source : {item.get('source', '')} | {item.get('date', '')}")
        lines.append(f"Résumé : {item.get('summary', '')}")
        lines.append(f"So what : {item.get('so_what', '')}")
        lines.append(f"Lire : {item.get('url', '')}")
    lines.append(f"\n{'=' * 60}\nGénéré automatiquement — {generated_at}")

    return html, "\n".join(lines)


def build_subject(news: list[dict], date: str) -> str:
    top = news[0].get("headline", "") if news else "Coffee Economics News"
    day_str = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m")
    return f"📊 Daily Finance Brief — {day_str} — {top[:60]}"


def main() -> None:
    force_send = os.environ.get("FORCE_SEND", "false").lower() == "true"

    # Compute today's date early for dedup check
    paris = pytz.timezone("Europe/Paris")
    date_str = datetime.now(paris).strftime("%Y-%m-%d")

    # Dedup guard: skip if brief was already sent today (handles both UTC+1/+2 crons)
    if not force_send and _already_sent_today(date_str):
        logger.info('"Brief already sent today (%s) — skipping duplicate run"', date_str)
        sys.exit(0)

    streamlit_url = os.environ.get("STREAMLIT_URL", "https://your-app.streamlit.app")
    recipients = get_recipients()

    logger.info('"=== DAILY BRIEF PIPELINE START ==="')

    # 0. Market snapshot (best-effort, non-blocking)
    logger.info('"Fetching market snapshot..."')
    market_snapshot = fetch_market_snapshot()

    # 1. Collect
    raw = collect_all_sources(max_workers=10, lookback_hours=24)
    stats = {"collected": len(raw)}

    # 2. Verify (URL checks disabled in Actions for speed; enabled via env var)
    check_urls = os.environ.get("CHECK_URLS", "false").lower() == "true"
    verified = verify_news_batch(raw, check_urls=check_urls)
    stats["verified"] = len(verified)

    # 3. Filter (whitelist / blacklist / dedup)
    filtered = apply_filters(verified)
    stats["filtered"] = len(filtered)
    stats["deduplicated"] = len(filtered)

    # 4. Enrich
    enriched = enrich_all(filtered)

    # 5. Cap at 80 candidates for LLM
    candidates = enriched[:_MAX_CANDIDATES]
    stats["sent_to_llm"] = len(candidates)

    # 6. Gemini analysis
    selected = analyze_news(candidates)
    stats["returned"] = len(selected)

    # 7. Post-verify LLM output
    final = post_verify_llm_output(selected, enriched)
    stats["post_verified"] = len(final)

    # 7b. Resolve Google News proxy URLs → real article URLs
    final = resolve_gnews_urls(final)

    # Fallback banner if low volume
    low_volume = len(final) < 3

    # 8. Archive
    save_brief(final, stats, date=date_str, market_snapshot=market_snapshot)
    stats["archive_written"] = True

    # 9. Build brief data
    brief_data = {
        "date": date_str,
        "generated_at": datetime.now(paris).isoformat(),
        "stats": stats,
        "news": final,
        "low_volume": low_volume,
        "market_snapshot": market_snapshot,
    }

    # 10. Render + send
    html, plain = render_email(brief_data, streamlit_url)
    subject = build_subject(final, date_str)
    sent = send_email(subject, html, plain, recipients)
    stats["email_sent"] = sent

    # Update brief with final stats (email result) — always commit regardless of email outcome
    save_brief(final, stats, date=date_str, market_snapshot=market_snapshot)

    # Mark brief as sent so duplicate cron runs skip cleanly
    if sent:
        mark_brief_sent(date_str)
    else:
        logger.warning('"Email failed — brief archived, will retry on next cron run"')

    # 11. Git push (best-effort — GitHub Actions commit step also handles this)
    pushed = git_commit_and_push(f"Brief {date_str}")
    stats["git_pushed"] = pushed

    logger.info('"=== PIPELINE COMPLETE: %s"', json.dumps(stats))


if __name__ == "__main__":
    main()
