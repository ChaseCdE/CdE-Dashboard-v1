"""
Fetch INE Data
Script to download all INE indicators.

Usage:
    python -m src.scripts.fetch_ine_data           # Fetch all indicators
    python -m src.scripts.fetch_ine_data gdp       # Fetch specific indicator
    python -m src.scripts.fetch_ine_data --list    # List available indicators
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.fetchers import INEIndicatorFetcher


AVAILABLE_INDICATORS = [
    "gdp",
    "gdp_demand",
    "industrial_production",
    "industry_turnover",
    "services_turnover",
    "services_production",
    "unemployment",
    "employment_rate",
    "activity_rate",
    "employed",
    "temporary_rate",
    "parttime_rate",
    "youth_unemployment",
    "labor_cost",
    "labor_cost_hour",
    "cpi",
    "cpi_special_groups",
    "cpi_ecoicop_groups",
    "cpi_weights",
    "cpi_special_weights",
    "retail_sales",
    "house_prices",
    "ipri",
    "cntr_employment",
    "population_age",
    "cpi_ccaa",
    "business_confidence",
]


def main():
    fetcher = INEIndicatorFetcher(output_dir="data/raw/ine")

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--list":
            print("Available indicators:")
            for ind in AVAILABLE_INDICATORS:
                print(f"  - {ind}")
            return

        if arg == "--help":
            print(__doc__)
            return

        # Fetch specific indicator
        if arg in AVAILABLE_INDICATORS:
            method = getattr(fetcher, f"fetch_{arg}")
            df = method()
            print(f"\nFetched {len(df)} records for {arg}")
            print(df.head())
        else:
            print(f"Unknown indicator: {arg}")
            print(f"Available: {', '.join(AVAILABLE_INDICATORS)}")
            sys.exit(1)
    else:
        # Fetch all indicators
        results = fetcher.fetch_all()

        print("\nSummary:")
        print("-" * 40)
        for name, df in results.items():
            print(f"{name}: {len(df)} records")


if __name__ == "__main__":
    main()
