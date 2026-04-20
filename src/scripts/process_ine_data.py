"""
Process INE Data
Script to clean and transform raw INE data for dashboard use.

Usage:
    python -m src.scripts.process_ine_data           # Process all indicators
    python -m src.scripts.process_ine_data gdp       # Process specific indicator
    python -m src.scripts.process_ine_data --summary # Create summary dataset only
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.processors import INEProcessor


AVAILABLE_INDICATORS = [
    "gdp",
    "industrial_production",
    "unemployment",
    "cpi",
    "retail_sales",
    "house_prices",
]


def main():
    processor = INEProcessor(
        input_dir="data/raw/ine",
        output_dir="data/processed"
    )

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--summary":
            summary = processor.create_summary_dataset()
            print("\nSummary:")
            print(summary.to_string())
            return

        if arg == "--help":
            print(__doc__)
            return

        # Process specific indicator
        if arg in AVAILABLE_INDICATORS:
            method = getattr(processor, f"process_{arg}")
            df = method()
            print(f"\nProcessed {len(df)} records for {arg}")
            print(df.tail(10).to_string())
        else:
            print(f"Unknown indicator: {arg}")
            print(f"Available: {', '.join(AVAILABLE_INDICATORS)}")
            sys.exit(1)
    else:
        # Process all indicators
        results = processor.process_all()

        print("\nSummary:")
        print("-" * 40)
        for name, df in results.items():
            if not df.empty:
                latest = df.sort_values("date").iloc[-1]
                print(f"{name}: {len(df)} records, latest: {latest['date'].strftime('%Y-%m-%d') if hasattr(latest['date'], 'strftime') else latest['date']}")
            else:
                print(f"{name}: No data after filtering")

        # Create summary dataset
        print("\n")
        summary = processor.create_summary_dataset()
        print("\nLatest values:")
        print(summary.to_string())


if __name__ == "__main__":
    main()
