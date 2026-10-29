"""
Fetch housing price data that INE does not cover: MIVAU appraised values (via the BdE API)
and Colegio de Registradores prices (open-data portal). See src/fetchers/housing_indicators.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.fetchers.housing_indicators import HousingFetcher


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "data" / "raw" / "housing"
    results = HousingFetcher(str(output_dir)).fetch_all()
    print(f"MIVAU series saved: {results['mivau']}/3")
    print(f"Registradores CSV saved: {results['registradores']}")


if __name__ == "__main__":
    main()
