"""Backfill so_what via Gemini pour les briefs avec texte heuristique.

Usage :
  python -m scripts.regenerate_so_what               # N derniers jours (défaut 7)
  python -m scripts.regenerate_so_what --days 30     # 30 derniers jours
  python -m scripts.regenerate_so_what --date 2026-05-24  # Date précise
  python -m scripts.regenerate_so_what --all         # Tous les briefs

Prérequis : GEMINI_API_KEY valide dans l'environnement.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Ajouter le repo root au path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.analyzer import _generate_item_so_what, _is_heuristic, _heuristic_so_what
from src.archiver import BRIEFS_DIR, git_commit_and_push


def regenerate_brief(path: Path, dry_run: bool = False) -> int:
    """Regenerate so_what for all heuristic items in one brief. Returns count updated."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Failed to load %s: %s", path, exc)
        return 0

    news = data.get("news", [])
    updated = 0

    for i, item in enumerate(news):
        sw = item.get("so_what", "") or ""
        if not _is_heuristic(sw):
            continue  # Already real analysis

        headline = item.get("headline", "")[:60]
        logger.info("  [%d/%d] Regenerating: %s", i + 1, len(news), headline)

        if dry_run:
            logger.info("  -> [DRY RUN] would call Gemini")
            updated += 1
            continue

        try:
            new_sw = _generate_item_so_what(item)
            if new_sw and not _is_heuristic(new_sw):
                news[i] = {**item, "so_what": new_sw}
                updated += 1
                logger.info("  OK Updated")
            else:
                logger.warning("  WARNING Gemini returned heuristic again -- keeping")
        except Exception as exc:
            logger.error("  FAIL: %s", str(exc)[:120])

        time.sleep(7)  # Respecter les rate limits Gemini (~8 RPM sécurisé pour gemini-2.5-flash)

    if updated > 0 and not dry_run:
        data["news"] = news
        data.setdefault("stats", {})["so_what_regenerated"] = True
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("  -> Saved %s (%d updated)", path.name, updated)

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill so_what via Gemini")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--days", type=int, default=7, help="N derniers jours (defaut: 7)")
    group.add_argument("--date", help="Date precise YYYY-MM-DD")
    group.add_argument("--all", action="store_true", help="Tous les briefs")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans modifier")
    args = parser.parse_args()

    if not BRIEFS_DIR.exists():
        logger.error("data/briefs/ introuvable -- aucun brief a traiter")
        sys.exit(1)

    all_briefs = sorted(BRIEFS_DIR.glob("????-??-??.json"), reverse=True)
    if not all_briefs:
        logger.warning("Aucun brief trouve dans %s", BRIEFS_DIR)
        sys.exit(0)

    if args.date:
        targets = [p for p in all_briefs if p.stem == args.date]
        if not targets:
            logger.error("Brief %s introuvable", args.date)
            sys.exit(1)
    elif args.all:
        targets = all_briefs
    else:
        targets = all_briefs[:args.days]

    logger.info("=== Regenerate so_what (%s) ===", "DRY RUN" if args.dry_run else "LIVE")
    logger.info("Briefs a traiter : %d", len(targets))

    total_updated = 0
    for path in targets:
        logger.info("\n--- %s ---", path.stem)
        n = regenerate_brief(path, dry_run=args.dry_run)
        total_updated += n

    logger.info("\n=== TERMINE : %d so_what regeneres sur %d briefs ===", total_updated, len(targets))

    if total_updated > 0 and not args.dry_run:
        logger.info("Push des changements vers Git...")
        pushed = git_commit_and_push(f"Regenerate so_what ({total_updated} items updated)")
        if pushed:
            logger.info("OK Push reussi")
        else:
            logger.warning("WARNING Push echoue -- fichiers mis a jour localement")


if __name__ == "__main__":
    main()
