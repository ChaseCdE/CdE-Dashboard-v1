"""
Fetch the Observatorio de Márgenes Empresariales (AEAT) quarterly series.
See src/fetchers/aeat_ome.py (needs Playwright and its Chromium build).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.fetchers.aeat_ome import OmeFetcher


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    ok = OmeFetcher(str(project_root / "data" / "raw" / "aeat")).fetch()
    print(f"OME (AEAT) quarterly series: {'available' if ok else 'not refreshed'}")


if __name__ == "__main__":
    main()
