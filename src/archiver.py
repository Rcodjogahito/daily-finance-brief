"""JSON archive writing and git commit/push."""
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
BRIEFS_DIR = DATA_DIR / "briefs"
ALERTS_DIR = DATA_DIR / "alerts"


def _today() -> str:
    import pytz
    paris = pytz.timezone("Europe/Paris")
    return datetime.now(paris).strftime("%Y-%m-%d")


def save_brief(news: list[dict], stats: dict, date: str | None = None, market_snapshot: dict | None = None) -> Path:
    """Write daily brief to data/briefs/YYYY-MM-DD.json."""
    date = date or _today()
    path = BRIEFS_DIR / f"{date}.json"
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)

    import pytz
    paris = pytz.timezone("Europe/Paris")
    generated_at = datetime.now(paris).isoformat()

    payload = {
        "date": date,
        "generated_at": generated_at,
        "stats": stats,
        "market_snapshot": market_snapshot or {},
        "news": news,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Brief archived: %s (%d news)", path, len(news))
    return path


def mark_brief_sent(date_str: str) -> None:
    """Update brief JSON to record that email was successfully sent (dedup guard)."""
    path = BRIEFS_DIR / f"{date_str}.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("stats", {})["email_sent"] = True
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Brief marked as sent: %s", date_str)
    except Exception as exc:
        logger.warning("Could not mark brief as sent: %s", exc)


def save_alerts(alerts: list[dict], date: str | None = None) -> tuple[Path, list[dict]]:
    """Append new alerts to data/alerts/YYYY-MM-DD.json."""
    date = date or _today()
    path = ALERTS_DIR / f"{date}.json"
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    import pytz
    paris = pytz.timezone("Europe/Paris")
    generated_at = datetime.now(paris).isoformat()

    # Load existing to avoid duplicates
    existing: list[dict] = []
    existing_urls: set[str] = set()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            existing = data.get("alerts", [])
            existing_urls = {a.get("url", "") for a in existing}
        except Exception as exc:
            logger.warning("Could not load existing alerts: %s", exc)

    new_alerts = [a for a in alerts if a.get("url", "") not in existing_urls]
    all_alerts = existing + new_alerts

    payload = {
        "date": date,
        "generated_at": generated_at,
        "alerts": all_alerts,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Alerts archived: %s (%d new / %d total)", path, len(new_alerts), len(all_alerts))
    return path, new_alerts


def load_brief(date: str) -> dict | None:
    """Load a brief JSON by date string (YYYY-MM-DD)."""
    path = BRIEFS_DIR / f"{date}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Failed to load brief %s: %s", date, exc)
        return None


def load_alerts(date: str) -> dict | None:
    """Load alerts JSON by date string."""
    path = ALERTS_DIR / f"{date}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Failed to load alerts %s: %s", date, exc)
        return None


def list_brief_dates() -> list[str]:
    """Return all available brief dates, sorted descending."""
    if not BRIEFS_DIR.exists():
        return []
    dates = [f.stem for f in sorted(BRIEFS_DIR.glob("????-??-??.json"), reverse=True)]
    return dates


def list_alert_dates() -> list[str]:
    """Return all available alert dates, sorted descending."""
    if not ALERTS_DIR.exists():
        return []
    return [f.stem for f in sorted(ALERTS_DIR.glob("????-??-??.json"), reverse=True)]


def git_commit_and_push(message: str) -> bool:
    """Commit data/ directory and push to origin main."""
    repo_root = Path(__file__).parent.parent

    def run(cmd: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd, cwd=str(repo_root), capture_output=True, text=True
        )

    # Stage data/
    run(["git", "add", "data/"])

    # Check if there's anything staged
    status = run(["git", "diff", "--staged", "--quiet"])
    if status.returncode == 0:
        logger.info("No changes to commit")
        return True

    # Commit
    result = run(["git", "commit", "-m", message])
    if result.returncode != 0:
        logger.error("git commit failed: %s", result.stderr)
        return False

    # Pull --rebase before push to avoid conflicts
    run(["git", "pull", "--rebase"])

    # Push
    result = run(["git", "push"])
    if result.returncode != 0:
        logger.error("git push failed: %s", result.stderr)
        return False

    logger.info("Git commit+push: %s", message)
    return True
