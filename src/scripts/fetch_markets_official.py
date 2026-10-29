"""Fetch ECB reference rates and FRED (Federal Reserve, EIA) series. See src/fetchers/official_markets.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.fetchers.official_markets import ECB_CURRENCIES, FRED_SERIES, OfficialMarketsFetcher


def main():
    out = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "markets_official"
    res = OfficialMarketsFetcher(str(out)).fetch_all()
    print(f"ECB reference rates saved: {res['ecb']}/{len(ECB_CURRENCIES)}")
    print(f"FRED series saved: {res['fred']}/{len(FRED_SERIES)}")


if __name__ == "__main__":
    main()
