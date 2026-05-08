"""Subscriber management — persist email list in data/subscribers.json."""
import json
import re
from pathlib import Path

_FILE = Path("data/subscribers.json")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _load() -> list[str]:
    if not _FILE.exists():
        return []
    try:
        return json.loads(_FILE.read_text(encoding="utf-8")).get("subscribers", [])
    except Exception:
        return []


def _save(emails: list[str]) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps({"subscribers": emails}, indent=2, ensure_ascii=False), encoding="utf-8")


def load_subscribers() -> list[str]:
    return _load()


def add_subscriber(email: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        return False, "Adresse email invalide."
    subs = _load()
    if email in subs:
        return False, "Cette adresse est déjà inscrite."
    subs.append(email)
    _save(subs)
    return True, f"{email} inscrit avec succès."


def remove_subscriber(email: str) -> tuple[bool, str]:
    email = email.strip().lower()
    subs = _load()
    if email not in subs:
        return False, "Adresse introuvable dans la liste."
    subs.remove(email)
    _save(subs)
    return True, f"{email} désinscrit avec succès."
