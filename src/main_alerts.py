"""Hourly hot alerts pipeline — Mon-Fri 09:00-19:00 Paris."""
import json
import logging
import os
import sys
from datetime import datetime

import pytz

from src.alert_detector import detect_hot_alerts
from src.analyzer import generate_alert_so_what
from src.archiver import git_commit_and_push, save_alerts
from src.collectors.rss_collector import collect_all_sources
from src.emailer import get_recipients, send_email
from src.enrichment import enrich_all
from src.filters import apply_filters
from src.verifier import verify_news_batch

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

_PARIS = pytz.timezone("Europe/Paris")


def _is_in_alert_window() -> bool:
    """Monday-Friday 09:00-19:30 Paris."""
    now = datetime.now(_PARIS)
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return (9, 0) <= (now.hour, now.minute) <= (19, 30)


def render_alert_email(item: dict, streamlit_url: str) -> tuple[str, str]:
    """Render HTML and plain-text for a hot alert email."""
    from jinja2 import Environment, FileSystemLoader
    from pathlib import Path

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("email_alert.html")

    paris = pytz.timezone("Europe/Paris")
    generated_at = datetime.now(paris).strftime("%d/%m/%Y à %H:%M")

    flags = item.get("alert_flags", [{}])
    alert_type = flags[0].get("type", "ALERT") if flags else "ALERT"
    alert_reason = flags[0].get("reason", "") if flags else ""

    html = template.render(
        item=item,
        alert_type=alert_type,
        alert_reason=alert_reason,
        streamlit_url=streamlit_url,
        generated_at=generated_at,
    )

    plain = (
        f"🚨 HOT ALERT — {alert_type}\n"
        f"{'=' * 60}\n"
        f"{item.get('headline', item.get('title', ''))}\n"
        f"Source : {item.get('source', '')} | {item.get('date', '')}\n\n"
        f"Résumé : {item.get('summary', '')}\n\n"
        f"So what : {item.get('so_what', '')}\n\n"
        f"Raison alerte : {alert_reason}\n"
        f"Lire : {item.get('url', '')}\n\n"
        f"Toutes les alertes : {streamlit_url}\n"
        f"Généré le {generated_at}"
    )
    return html, plain


def build_alert_subject(item: dict) -> str:
    flags = item.get("alert_flags", [{}])
    alert_type = flags[0].get("type", "ALERT") if flags else "ALERT"
    headline = item.get("headline", item.get("title", ""))[:50]
    return f"🚨 HOT ALERT — {alert_type} — {headline}"


def main() -> None:
    force_send = os.environ.get("FORCE_SEND", "false").lower() == "true"

    if not force_send and not _is_in_alert_window():
        logger.info('"Alerts: outside trading hours — skipping"')
        sys.exit(0)

    streamlit_url = os.environ.get("STREAMLIT_URL", "https://your-app.streamlit.app")
    recipients = get_recipients()

    logger.info('"=== HOURLY ALERTS PIPELINE START ==="')

    # 1. Collect (90-min lookback for intraday)
    raw = collect_all_sources(max_workers=10, lookback_hours=2)

    # 2. Verify (fast, no URL checks)
    verified = verify_news_batch(raw, check_urls=False)

    # 3. Filter
    filtered = apply_filters(verified)

    # 4. Enrich (especially deal_size_eur needed for alert detection)
    enriched = enrich_all(filtered)

    # 5. Detect hot alerts (pure heuristics — no LLM)
    alerts = detect_hot_alerts(enriched)
    logger.info('"Alerts detected: %d"', len(alerts))

    if not alerts:
        logger.info('"No alerts this cycle"')
        sys.exit(0)

    # 6. Load existing alerts to dedup by URL
    paris = pytz.timezone("Europe/Paris")
    date_str = datetime.now(paris).strftime("%Y-%m-%d")

    # Save + get only new ones
    _, new_alerts = save_alerts(alerts, date=date_str)

    if not new_alerts:
        logger.info('"All alerts already sent — no new ones"')
        sys.exit(0)

    # 7. For each new alert: generate so_what + send email
    emails_sent = 0
    for alert in new_alerts:
        # Generate so_what via Gemini (1 req per alert)
        try:
            so_what = generate_alert_so_what(alert)
            alert["so_what"] = so_what
        except Exception as exc:
            logger.warning('"so_what generation failed: %s"', exc)
            alert["so_what"] = "Analyse indisponible."

        alert.setdefault("headline", alert.get("title", "")[:80])

        html, plain = render_alert_email(alert, streamlit_url)
        subject = build_alert_subject(alert)
        sent = send_email(subject, html, plain, recipients)
        if sent:
            emails_sent += 1

    # 8. Re-save with so_what populated
    save_alerts(new_alerts, date=date_str)

    # 9. Git push
    git_commit_and_push(f"Alerts {datetime.now(paris).strftime('%Y-%m-%dT%H:%M')}")

    logger.info('"=== ALERTS PIPELINE COMPLETE: %d emails sent ==="', emails_sent)


if __name__ == "__main__":
    main()
