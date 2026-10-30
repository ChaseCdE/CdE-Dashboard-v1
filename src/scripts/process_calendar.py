"""Normalise the release calendars into data/processed/calendar/events.json (src/export/calendar.py)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.export.calendar import PROCESSED, RAW_DIR, build_events


def main():
    if not any(RAW_DIR.glob("*.json")):
        print(f"Calendar: no raw downloads in {RAW_DIR}; skipped, previous site file kept")
        return
    events = build_events()
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED.write_text(json.dumps(events, ensure_ascii=False, indent=0), encoding="utf-8")
    tracked = sum(e["tracked"] for e in events)
    print(f"Calendar: {len(events)} events ({tracked} of statistics shown on the site)")


if __name__ == "__main__":
    main()
