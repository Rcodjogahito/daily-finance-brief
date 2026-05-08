"""Gmail SMTP email sending with HTML + plain-text fallback."""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


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
        logger.info("Email sent to %s | Subject: %s", recipients, subject[:80])
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
    """Merge RECIPIENTS env var with data/subscribers.json (deduped)."""
    from src.subscribers import load_subscribers
    env_raw = os.environ.get("RECIPIENTS", "")
    env_list = [r.strip().lower() for r in env_raw.split(",") if r.strip()]
    sub_list = [e.lower() for e in load_subscribers()]
    seen: set[str] = set()
    merged: list[str] = []
    for e in env_list + sub_list:
        if e not in seen:
            seen.add(e)
            merged.append(e)
    return merged
