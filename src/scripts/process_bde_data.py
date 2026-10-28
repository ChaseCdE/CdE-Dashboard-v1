"""
Process Banco de Espana Data Script
Cleans and transforms raw BdE data for dashboard use.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetchers.bde_indicators import BDE_INDICATORS, list_categories
from processors.bde_processor import BdeProcessor, run_processing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Process Banco de Espana data."""
    parser = argparse.ArgumentParser(
        description="Process raw Banco de Espana data for dashboard use"
    )
    parser.add_argument(
        "--indicator",
        type=str,
        help="Process only a specific indicator by key"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Process only indicators in a specific category"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Custom input directory for raw data files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for processed data files"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only create summary table (skip individual processing)"
    )
    parser.add_argument(
        "--comparisons-only",
        action="store_true",
        help="Only create comparison datasets (skip individual processing)"
    )
    parser.add_argument(
        "--yield-curve",
        action="store_true",
        help="Generate yield curve data"
    )
    parser.add_argument(
        "--yield-curve-date",
        type=str,
        help="Date for yield curve snapshot (YYYY-MM-DD). Default: latest"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories"
    )

    args = parser.parse_args()

    # List categories if requested
    if args.list_categories:
        print("\nAvailable categories:")
        print("-" * 30)
        for category in list_categories():
            indicators = [k for k, v in BDE_INDICATORS.items() if v.get('category') == category]
            print(f"  {category} ({len(indicators)} indicators)")
        return

    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Determine directories
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = str(project_root / "data" / "raw" / "bde")

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = str(project_root / "data" / "processed" / "bde")

    # Initialize processor
    processor = BdeProcessor(input_dir=input_dir, output_dir=output_dir)

    # Determine which processing to run
    if args.summary_only:
        # Only create summary table
        print("\n" + "=" * 60)
        print("CREATING SUMMARY TABLE")
        print("=" * 60 + "\n")
        processor.create_summary_table(BDE_INDICATORS)
        print("\nSummary table created.")

    elif args.comparisons_only:
        # Only create comparison datasets
        print("\n" + "=" * 60)
        print("CREATING COMPARISON DATASETS")
        print("=" * 60 + "\n")

        print("Creating EURIBOR comparison...")
        processor.create_euribor_comparison()

        print("Creating lending rates comparison...")
        processor.create_lending_rates_comparison()

        print("Creating sovereign spreads...")
        processor.create_spread_datasets()

        print("Creating yield curve...")
        processor.create_yield_curve(args.yield_curve_date)

        print("Creating debt ratios comparison...")
        debt_indicators = ['household_debt_gdp', 'nfc_debt_gdp']
        processor.create_comparison_dataset(
            indicators=debt_indicators,
            output_name="debt_ratios_comparison"
        )

        print("\nComparison datasets created.")

    elif args.yield_curve:
        # Only generate yield curve
        print("\n" + "=" * 60)
        print("GENERATING YIELD CURVE")
        print("=" * 60 + "\n")

        curve = processor.create_yield_curve(args.yield_curve_date)
        if not curve.empty:
            print("\nYield Curve Data:")
            print("-" * 40)
            for _, row in curve.iterrows():
                print(f"  {row['maturity_years']:>5.2f}Y: {row['yield']:>6.3f}%")
        else:
            print("No yield curve data available.")

    elif args.indicator:
        # Process single indicator
        print(f"\nProcessing indicator: {args.indicator}")
        result = processor.process_indicator(args.indicator, BDE_INDICATORS)
        if not result.empty:
            print(f"Processed {len(result)} rows")
        else:
            print("No data processed")

    elif args.category:
        # Process indicators in category
        print(f"\nProcessing category: {args.category}")
        indicators = {k: v for k, v in BDE_INDICATORS.items() if v.get('category') == args.category}
        if not indicators:
            print(f"Unknown category: {args.category}")
            return

        results = processor.process_all(indicators)
        print(f"\nProcessed {len(results)} indicators")

    else:
        # Run full processing pipeline
        run_processing(BDE_INDICATORS)


if __name__ == "__main__":
    main()
