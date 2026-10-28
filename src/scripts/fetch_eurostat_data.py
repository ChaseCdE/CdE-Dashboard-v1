"""
Fetch Eurostat Data Script
Downloads all Eurostat indicators for the dashboard.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root: packages are imported as src.*

from src.fetchers.eurostat_indicators import EurostatIndicatorFetcher


def main():
    """Fetch all Eurostat indicators."""
    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Initialize fetcher with output directory
    output_dir = project_root / "data" / "raw" / "eurostat"
    fetcher = EurostatIndicatorFetcher(
        output_dir=str(output_dir),
        start_period=2015
    )

    # Fetch all indicators
    results = fetcher.fetch_all()

    # Print final summary
    print("\n" + "=" * 60)
    print("FETCH COMPLETE")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Indicators fetched: {len(results)}")

    non_empty = sum(1 for df in results.values() if not df.empty)
    print(f"Non-empty datasets: {non_empty}/{len(results)}")

    # Latest observation per indicator: a silently frozen dataset (like
    # prc_hicp_manr after the 2026 ECOICOP 2 switch) shows up here.
    print("\nLatest observation per indicator:")
    for name, df in results.items():
        if df.empty or "date" not in df.columns:
            print(f"  {name}: EMPTY (cached raw file kept, if any)")
            continue
        last = df.dropna(subset=["value"])["date"].max()
        print(f"  {name}: {last:%Y-%m-%d}")


if __name__ == "__main__":
    main()
