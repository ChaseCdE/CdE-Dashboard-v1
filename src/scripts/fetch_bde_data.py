"""
Fetch Banco de Espana Data Script
Downloads all BdE economic indicators for the dashboard.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetchers.bde_indicators import (
    BdeIndicatorFetcher,
    BDE_INDICATORS,
    INDICATOR_GROUPS,
    list_groups,
    list_categories
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Fetch Banco de Espana indicators."""
    parser = argparse.ArgumentParser(
        description="Fetch economic data from Banco de Espana API"
    )
    parser.add_argument(
        "--group",
        type=str,
        help="Fetch only a specific group (e.g., interest_rates, credit_banking, debt_ratios)"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Fetch only a specific category (e.g., interest_rates, credit_banking)"
    )
    parser.add_argument(
        "--indicators",
        type=str,
        nargs="+",
        help="Fetch specific indicators by key (e.g., euribor_12m_monthly spain_10y_bond)"
    )
    parser.add_argument(
        "--range",
        type=str,
        help="Time range for data (e.g., 12M, 36M, 60M, MAX). Default varies by frequency."
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="List available indicator groups"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories"
    )
    parser.add_argument(
        "--list-indicators",
        action="store_true",
        help="List all available indicators"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Fetch only latest values (no historical data)"
    )
    parser.add_argument(
        "--high-priority",
        action="store_true",
        help="Fetch only high priority indicators"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for data files"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="EN",
        choices=["EN", "ES"],
        help="Language for API responses (EN or ES). Default: EN"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between API requests in seconds. Default: 0.5"
    )

    args = parser.parse_args()

    # List groups if requested
    if args.list_groups:
        print("\nAvailable indicator groups:")
        print("-" * 50)
        for group_name in list_groups():
            indicators = INDICATOR_GROUPS.get(group_name, [])
            print(f"\n{group_name} ({len(indicators)} indicators):")
            for ind in indicators:
                config = BDE_INDICATORS.get(ind, {})
                name = config.get('name', ind)
                print(f"  - {ind}: {name}")
        return

    # List categories if requested
    if args.list_categories:
        print("\nAvailable categories:")
        print("-" * 50)
        for category in list_categories():
            indicators = [k for k, v in BDE_INDICATORS.items() if v.get('category') == category]
            print(f"\n{category} ({len(indicators)} indicators):")
            for ind in indicators:
                config = BDE_INDICATORS.get(ind, {})
                name = config.get('name', ind)
                print(f"  - {ind}: {name}")
        return

    # List all indicators if requested
    if args.list_indicators:
        print("\nAvailable indicators:")
        print("-" * 70)
        print(f"{'Key':<30} {'Name':<40}")
        print("-" * 70)
        for key, config in BDE_INDICATORS.items():
            name = config.get('name', key)[:38]
            freq = config.get('frequency', '')
            priority = config.get('priority', '')
            print(f"{key:<30} {name:<40} [{freq}] [{priority}]")
        print(f"\nTotal: {len(BDE_INDICATORS)} indicators")
        return

    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = project_root / "data" / "raw" / "bde"

    # Initialize fetcher
    fetcher = BdeIndicatorFetcher(
        output_dir=str(output_dir),
        language=args.language,
        request_delay=args.delay
    )

    try:
        # Determine which indicators to fetch
        if args.latest:
            # Fetch only latest values
            if args.indicators:
                keys = args.indicators
            elif args.high_priority:
                keys = INDICATOR_GROUPS.get('high_priority', [])
            else:
                keys = list(BDE_INDICATORS.keys())

            print(f"\nFetching latest values for {len(keys)} indicators...")
            results = fetcher.fetch_latest(keys)
            print(f"\nFetched latest values for {len(results)} indicators")

        elif args.indicators:
            # Fetch specific indicators
            results = fetcher.fetch_selected(args.indicators, time_range=args.range)

        elif args.group:
            # Fetch a group
            results = fetcher.fetch_group(args.group, time_range=args.range)

        elif args.category:
            # Fetch a category
            results = fetcher.fetch_category(args.category, time_range=args.range)

        elif args.high_priority:
            # Fetch high priority indicators
            results = fetcher.fetch_group('high_priority', time_range=args.range)

        else:
            # Fetch all
            results = fetcher.fetch_all(time_range=args.range)

        # Print final summary
        print("\n" + "=" * 60)
        print("FETCH COMPLETE")
        print("=" * 60)
        print(f"Output directory: {output_dir}")

        if isinstance(results, dict):
            print(f"Indicators fetched: {len(results)}")
            non_empty = sum(1 for df in results.values() if not df.empty)
            print(f"Non-empty datasets: {non_empty}/{len(results)}")

            if non_empty < len(results):
                failed = [k for k, df in results.items() if df.empty]
                print(f"\nFailed indicators: {', '.join(failed)}")
        else:
            # DataFrame result (from fetch_latest)
            print(f"Records fetched: {len(results)}")

    finally:
        fetcher.close()


if __name__ == "__main__":
    main()
