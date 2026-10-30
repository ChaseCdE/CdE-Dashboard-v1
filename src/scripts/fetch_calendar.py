"""Fetch the release calendars (INE, Eurostat, Banco de España, Trabajo e Inclusión). See src/fetchers/calendars.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.fetchers.calendars import CalendarFetcher


def main():
    root = Path(__file__).resolve().parent.parent.parent
    counts = CalendarFetcher(str(root / "data" / "raw" / "calendar")).fetch_all()
    print("Calendar events: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
