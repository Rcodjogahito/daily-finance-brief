"""
Monthly RSS source health check.
- Tests all sources with 3 attempts each
- Generates HEALTH_REPORT.md
- Prints DEAD_SOURCES list (>80% failure) for the workflow to act on
- Exit code 1 if any source is dead (signals the workflow to open a PR)
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import feedparser
import requests
from src.collectors.sources import SOURCES

_ATTEMPTS = 3
_TIMEOUT = 15
_DEAD_THRESHOLD = 0.80  # >80% failures = dead


def test_source(name: str, url: str) -> dict:
    results = []
    for attempt in range(_ATTEMPTS):
        if attempt > 0:
            time.sleep(2)
        try:
            # First try HEAD request on the URL itself
            r = requests.head(url, timeout=_TIMEOUT, headers={"User-Agent": "DailyFinanceBrief/1.0"}, allow_redirects=True)
            if r.status_code < 400:
                feed = feedparser.parse(url, request_headers={"User-Agent": "DailyFinanceBrief/1.0"})
                ok = bool(feed.entries) or not feed.bozo
                results.append(ok)
            else:
                results.append(False)
        except Exception:
            results.append(False)

    failures = results.count(False)
    failure_rate = failures / _ATTEMPTS
    return {
        "name": name,
        "url": url,
        "attempts": _ATTEMPTS,
        "failures": failures,
        "failure_rate": failure_rate,
        "status": "DEAD" if failure_rate >= _DEAD_THRESHOLD else ("DEGRADED" if failure_rate > 0 else "OK"),
    }


def main() -> int:
    print(f"RSS Health Check — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Testing {len(SOURCES)} sources ({_ATTEMPTS} attempts each)...")
    print()

    results = []
    for name, url in SOURCES.items():
        print(f"  [{name}] ...", end=" ", flush=True)
        r = test_source(name, url)
        results.append(r)
        status = r["status"]
        print(f"{status} ({r['failures']}/{_ATTEMPTS} failures)")

    # Sort: dead first, then degraded, then ok
    results.sort(key=lambda x: -x["failure_rate"])

    dead = [r for r in results if r["status"] == "DEAD"]
    degraded = [r for r in results if r["status"] == "DEGRADED"]
    ok = [r for r in results if r["status"] == "OK"]

    print()
    print(f"=== SUMMARY ===")
    print(f"  OK:       {len(ok)}/{len(results)}")
    print(f"  Degraded: {len(degraded)}/{len(results)}")
    print(f"  DEAD:     {len(dead)}/{len(results)}")

    # Write HEALTH_REPORT.md
    report_path = ROOT / "HEALTH_REPORT.md"
    lines = [
        "# RSS Source Health Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"| Status | Source | Failure Rate | URL |",
        f"|--------|--------|:------------:|-----|",
    ]
    for r in results:
        emoji = "🔴" if r["status"] == "DEAD" else ("🟡" if r["status"] == "DEGRADED" else "🟢")
        lines.append(f"| {emoji} {r['status']} | {r['name']} | {r['failure_rate']:.0%} | {r['url'][:60]}... |")

    if dead:
        lines += [
            "",
            "## Dead Sources (disabled in next PR)",
            "",
            "These sources failed in ≥80% of attempts and will be proposed for removal:",
            "",
        ]
        for r in dead:
            lines.append(f"- **{r['name']}**: {r['url']}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written: {report_path}")

    # Write JSON for programmatic use (GitHub Actions)
    json_path = ROOT / "health_results.json"
    json_path.write_text(json.dumps({"results": results, "dead": [r["name"] for r in dead]}, indent=2), encoding="utf-8")

    # Print dead sources in a machine-readable format for the workflow
    if dead:
        print("\nDEAD_SOURCES=" + ",".join(r["name"] for r in dead))
        return 1  # Signal workflow to open PR
    return 0


if __name__ == "__main__":
    sys.exit(main())
