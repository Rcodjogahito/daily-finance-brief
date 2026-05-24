"""Gmail SMTP email sending with HTML + plain-text fallback."""
import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)

# Fichier de liste d'exclusion (emails à ne JAMAIS contacter)
_EXCLUDED_FILE = Path(__file__).parent.parent / "data" / "excluded_recipients.json"


def _load_excluded() -> set[str]:
    """Charge la liste des emails exclus (désabonnés ou supprimés)."""
    if not _EXCLUDED_FILE.exists():
        return set()
    try:
        data = json.loads(_EXCLUDED_FILE.read_text(encoding="utf-8"))
        return {e.strip().lower() for e in data.get("excluded", []) if e.strip()}
    except Exception:
        return set()


def send_email(
    subject: str,
    html_body: str,
    plain_body: str,
    recipients: list[str],
) -> bool:
    """Send email via Gmail SMTP (App Password). Returns True on success."""
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not gmail_user or not gmail_password:
        logger.error("GMAIL_USER or GMAIL_APP_PASSWORD not set")
        return False

    if not recipients:
        logger.error("No recipients specified")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Daily Finance Brief <{gmail_user}>"
    msg["To"] = ", ".join(recipients)
    msg["Reply-To"] = gmail_user

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipients, msg.as_string())
        logger.info("Email sent to %d recipients | Subject: %s", len(recipients), subject[:80])
        return True
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("Gmail auth failed — check App Password: %s", exc)
        return False
    except smtplib.SMTPException as exc:
        logger.error("SMTP error: %s", exc)
        return False
    except Exception as exc:
        logger.error("Unexpected email error: %s", exc)
        return False


def get_recipients() -> list[str]:
    """Merge RECIPIENTS env var with data/subscribers.json, minus excluded list (deduped)."""
    from src.subscribers import load_subscribers

    env_raw = os.environ.get("RECIPIENTS", "")
    env_list = [r.strip().lower() for r in env_raw.split(",") if r.strip()]
    sub_list = [e.lower() for e in load_subscribers()]
    excluded = _load_excluded()

    seen: set[str] = set()
    merged: list[str] = []
    for e in env_list + sub_list:
        if e and e not in seen and e not in excluded:
            seen.add(e)
            merged.append(e)

    if excluded:
        logger.info("Excluded %d recipient(s) from send list: %s", len(excluded & (seen | set(env_list + sub_list))), list(excluded)[:5])

    return merged
