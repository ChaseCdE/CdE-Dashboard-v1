#!/usr/bin/env python3
"""
Rebuild site/data/releases.json ("Últimos datos") from the git history of site/data/manifest.json.

Each commit that changed the manifest is compared with the previous one, exactly as the export
does on every refresh (src/export/releases.py), using the commit date (Spanish time) as the
publication date. Flash-estimate flags only exist in manifests written since they were added.

Usage:  python scripts/backfill_releases.py [--since 2026-09-01]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.export import releases  # noqa: E402
from src.export.export_site_data import write_json  # noqa: E402

MANIFEST = "site/data/manifest.json"


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--since", help="ignore commits before this date (YYYY-MM-DD)")
    args = ap.parse_args()

    log = git("log", "--reverse", "--format=%H %cI", "--", MANIFEST).split("\n")
    commits = [line.split() for line in log if line.strip()]
    events, previous = [], None
    for sha, when in commits:
        try:
            current = json.loads(git("show", f"{sha}:{MANIFEST}"))
        except (subprocess.CalledProcessError, ValueError):
            continue
        detected = releases.today_madrid(datetime.fromisoformat(when))
        if previous is not None and (not args.since or detected >= args.since):
            events = releases.update_events(events, previous, current, detected)
        previous = current

    # Finally the working-tree manifest (an export not committed yet).
    path = ROOT / MANIFEST
    current = json.loads(path.read_text(encoding="utf-8"))
    if previous is not None and current != previous:
        events = releases.update_events(events, previous, current, releases.today_madrid())

    out = {"generated_at": current["generated_at"], "highlights": releases.HIGHLIGHTS, "events": events}
    write_json(ROOT / "site" / "data" / "releases.json", out)
    print(f"{len(events)} events from {len(commits)} manifest versions")
    for e in events[:15]:
        print(f"  {e['detected']}  {e['id']:<34} {e['period']}  {e['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
