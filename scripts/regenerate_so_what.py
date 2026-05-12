"""Re-enrich so_what for all historical briefs.

Usage (local or GitHub Actions):
    GEMINI_API_KEY=<key> python -m scripts.regenerate_so_what

Reads every brief in data/briefs/, replaces heuristic so_what values
with proper Gemini analysis, saves in-place, then commits and pushes.
"""
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BRIEFS_DIR = Path(__file__).parent.parent / "data" / "briefs"


def main() -> None:
    from src.analyzer import enrich_so_what, _is_heuristic
    from src.archiver import git_commit_and_push

    paths = sorted(BRIEFS_DIR.glob("????-??-??.json"), reverse=True)
    if not paths:
        logger.info("No briefs found in %s", BRIEFS_DIR)
        return

    updated = 0
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Cannot read %s: %s", path.name, exc)
            continue

        news = data.get("news", [])
        needs_update = any(_is_heuristic(item.get("so_what", "")) for item in news)
        if not needs_update:
            logger.info("%s — so_what already enriched, skipping", path.name)
            continue

        logger.info("%s — enriching %d items…", path.name, sum(1 for i in news if _is_heuristic(i.get("so_what", ""))))
        try:
            enriched_news = enrich_so_what(news)
        except Exception as exc:
            logger.error("%s — enrichment failed: %s", path.name, exc)
            continue

        data["news"] = enriched_news
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("%s — saved", path.name)
        updated += 1

    logger.info("Done — %d brief(s) updated", updated)

    if updated:
        git_commit_and_push("chore: re-enrich so_what for historical briefs")


if __name__ == "__main__":
    main()
