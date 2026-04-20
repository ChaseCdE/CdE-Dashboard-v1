"""
Fetch Yahoo Finance Data Script
Downloads all financial market indicators for the dashboard.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetchers.yahoo_indicators import YahooIndicatorFetcher, INDICATOR_GROUPS


def main():
    """Fetch Yahoo Finance indicators."""
    parser = argparse.ArgumentParser(
        description="Fetch financial market data from Yahoo Finance"
    )
    parser.add_argument(
        "--group",
        type=str,
        help="Fetch only a specific group (e.g., stock_indices, currencies, commodities)"
    )
    parser.add_argument(
        "--indicators",
        type=str,
        nargs="+",
        help="Fetch specific indicators by key (e.g., ibex_35 sp_500)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for data (YYYY-MM-DD). Default: 5 years ago"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for data (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="List available indicator groups"
    )

    args = parser.parse_args()

    # List groups if requested
    if args.list_groups:
        print("\nAvailable indicator groups:")
        print("-" * 40)
        for group_name, indicators in INDICATOR_GROUPS.items():
            print(f"\n{group_name}:")
            for ind in indicators:
                print(f"  - {ind}")
        return

    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Initialize fetcher with output directory
    output_dir = project_root / "data" / "raw" / "yahoo"
    fetcher = YahooIndicatorFetcher(
        output_dir=str(output_dir),
        start_date=args.start_date,
        end_date=args.end_date
    )

    # Fetch based on arguments
    if args.indicators:
        # Fetch specific indicators
        results = fetcher.fetch_selected(args.indicators)
    elif args.group:
        # Fetch a group
        results = fetcher.fetch_group(args.group)
    else:
        # Fetch all
        results = fetcher.fetch_all()

    # Print final summary
    print("\n" + "=" * 60)
    print("FETCH COMPLETE")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Indicators fetched: {len(results)}")

    non_empty = sum(1 for df in results.values() if not df.empty)
    print(f"Non-empty datasets: {non_empty}/{len(results)}")


if __name__ == "__main__":
    main()
