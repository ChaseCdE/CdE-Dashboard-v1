"""
Process Eurostat Data Script
Processes raw Eurostat data for dashboard use.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.eurostat_processor import EurostatProcessor


def main():
    """Process all Eurostat indicators."""
    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Initialize processor
    input_dir = project_root / "data" / "raw" / "eurostat"
    output_dir = project_root / "data" / "processed" / "eurostat"

    processor = EurostatProcessor(
        input_dir=str(input_dir),
        output_dir=str(output_dir)
    )

    # Process all indicators
    results = processor.process_all()

    # Create summary dataset
    summary = processor.create_summary_dataset()

    # Print final summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Indicators processed: {len(results)}")
    print("\nSummary (Spain vs EU27):")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
