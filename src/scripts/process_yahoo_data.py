"""
Process Yahoo Finance Data Script
Cleans and transforms raw Yahoo Finance data for dashboard use.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root: packages are imported as src.*

from src.fetchers.yahoo_indicators import YAHOO_INDICATORS
from src.processors.yahoo_processor import run_processing


def main():
    """Process all Yahoo Finance data."""
    run_processing(YAHOO_INDICATORS)


if __name__ == "__main__":
    main()
