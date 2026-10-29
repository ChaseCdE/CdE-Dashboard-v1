"""
Yahoo Finance Indicators Configuration
Defines all financial market indicators to fetch from Yahoo Finance.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from .yahoo_client import YahooFinanceClient
from .http_session import map_bounded

MAX_WORKERS = 4  # concurrent requests to query1.finance.yahoo.com

logger = logging.getLogger(__name__)

# Dictionary of all Yahoo Finance indicators
# Structure: indicator_key -> { ticker, name, category, description, geography, unit }

YAHOO_INDICATORS: Dict[str, Dict[str, Any]] = {
    # ==========================================================================
    # STOCK MARKET INDICES
    # ==========================================================================

    "ibex_35": {
        "ticker": "^IBEX",
        "name": "IBEX 35",
        "category": "stock_indices",
        "description": "Main benchmark stock index of the Bolsa de Madrid (Spanish stock exchange)",
        "geography": "Spain",
        "currency": "EUR",
        "frequency": "daily"
    },

    "euro_stoxx_50": {
        "ticker": "^STOXX50E",
        "name": "Euro Stoxx 50",
        "category": "stock_indices",
        "description": "Stock index of Eurozone stocks, covering 50 blue-chip companies",
        "geography": "Eurozone",
        "currency": "EUR",
        "frequency": "daily"
    },

    "stoxx_600": {
        "ticker": "^STOXX",
        "name": "STOXX Europe 600",
        "category": "stock_indices",
        "description": "Broad European stock index covering 600 companies across 17 countries",
        "geography": "Europe",
        "currency": "EUR",
        "frequency": "daily"
    },

    "sp_500": {
        "ticker": "^GSPC",
        "name": "S&P 500",
        "category": "stock_indices",
        "description": "Stock market index tracking 500 largest US companies",
        "geography": "US",
        "currency": "USD",
        "frequency": "daily"
    },

    "nasdaq_composite": {
        "ticker": "^IXIC",
        "name": "NASDAQ Composite",
        "category": "stock_indices",
        "description": "Stock market index of all stocks listed on the NASDAQ exchange",
        "geography": "US",
        "currency": "USD",
        "frequency": "daily"
    },

    "dax": {
        "ticker": "^GDAXI",
        "name": "DAX",
        "category": "stock_indices",
        "description": "German stock index representing 40 major German blue-chip companies",
        "geography": "Germany",
        "currency": "EUR",
        "frequency": "daily"
    },

    "cac_40": {
        "ticker": "^FCHI",
        "name": "CAC 40",
        "category": "stock_indices",
        "description": "French stock market index representing 40 largest companies on Euronext Paris",
        "geography": "France",
        "currency": "EUR",
        "frequency": "daily"
    },

    "ftse_100": {
        "ticker": "^FTSE",
        "name": "FTSE 100",
        "category": "stock_indices",
        "description": "Stock index of 100 companies with highest market cap on London Stock Exchange",
        "geography": "UK",
        "currency": "GBP",
        "frequency": "daily"
    },

    # ==========================================================================
    # US INTEREST RATES
    # ==========================================================================


    # ==========================================================================
    # US TREASURY YIELDS
    # ==========================================================================




    # ==========================================================================
    # CURRENCY EXCHANGE RATES
    # ==========================================================================








    # ==========================================================================
    # COMMODITIES
    # ==========================================================================

    "gold": {
        "ticker": "GC=F",
        "name": "Gold Futures",
        "category": "commodities",
        "description": "Gold futures contract price (COMEX)",
        "geography": "International",
        "currency": "USD",
        "frequency": "daily"
    },




    "silver": {
        "ticker": "SI=F",
        "name": "Silver Futures",
        "category": "commodities",
        "description": "Silver futures contract price (COMEX)",
        "geography": "International",
        "currency": "USD",
        "frequency": "daily"
    },

    # ==========================================================================
    # BOND MARKET PROXIES (ETFs)
    # ==========================================================================




    # ==========================================================================
    # VOLATILITY INDICES
    # ==========================================================================

    "vix": {
        "ticker": "^VIX",
        "name": "CBOE Volatility Index",
        "category": "volatility",
        "description": "VIX - Market's expectation of 30-day volatility (fear index)",
        "geography": "US",
        "currency": "Index",
        "frequency": "daily"
    },

    # ==========================================================================
    # SECTOR INDICES (SPAIN-FOCUSED)
    # ==========================================================================

    "msci_spain_etf": {
        "ticker": "EWP",
        "name": "iShares MSCI Spain ETF",
        "category": "sector",
        "description": "ETF tracking Spanish equity market (heavy in financials)",
        "geography": "Spain",
        "currency": "USD",
        "frequency": "daily"
    },

    "european_banks_etf": {
        "ticker": "EUFN",
        "name": "iShares MSCI Europe Financials ETF",
        "category": "sector",
        "description": "ETF tracking European financial sector companies",
        "geography": "Europe",
        "currency": "USD",
        "frequency": "daily"
    },
}


# Indicator groupings for different dashboard views
INDICATOR_GROUPS = {
    "stock_indices": [
        "ibex_35", "euro_stoxx_50", "stoxx_600", "sp_500",
        "nasdaq_composite", "dax", "cac_40", "ftse_100"
    ],
    # Exchange rates, US yields, oil and gas come from official sources since 2026-10-29
    # (src/fetchers/official_markets.py). Yahoo keeps only what has no free official source.
    "commodities": ["gold", "silver"],
    "volatility": ["vix"],
    "sector": ["msci_spain_etf", "european_banks_etf"],
    "dashboard_summary": ["ibex_35", "euro_stoxx_50", "sp_500", "gold", "vix"],
    "spain_focus": ["ibex_35", "msci_spain_etf"],
}


def get_indicator(key: str) -> Dict[str, Any]:
    """
    Get indicator configuration by key.

    Args:
        key: Indicator key (e.g., 'ibex_35')

    Returns:
        Dictionary with indicator configuration
    """
    return YAHOO_INDICATORS.get(key, {})


def get_all_tickers() -> Dict[str, str]:
    """
    Get mapping of all indicator keys to their Yahoo Finance tickers.

    Returns:
        Dictionary mapping indicator keys to ticker symbols
    """
    return {key: info["ticker"] for key, info in YAHOO_INDICATORS.items()}


def get_indicators_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all indicators for a specific category.

    Args:
        category: Category name (e.g., 'stock_indices', 'currencies')

    Returns:
        Dictionary of indicators in that category
    """
    return {
        key: info
        for key, info in YAHOO_INDICATORS.items()
        if info.get("category") == category
    }


def get_indicators_by_geography(geography: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all indicators for a specific geography.

    Args:
        geography: Geography name (e.g., 'Spain', 'US', 'Eurozone')

    Returns:
        Dictionary of indicators for that geography
    """
    return {
        key: info
        for key, info in YAHOO_INDICATORS.items()
        if info.get("geography") == geography
    }


def get_indicator_group(group_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Get indicators for a predefined group.

    Args:
        group_name: Name of the indicator group

    Returns:
        Dictionary of indicators in that group
    """
    if group_name not in INDICATOR_GROUPS:
        return {}

    keys = INDICATOR_GROUPS[group_name]
    return {key: YAHOO_INDICATORS[key] for key in keys if key in YAHOO_INDICATORS}


class YahooIndicatorFetcher:
    """Fetcher for Yahoo Finance market indicators."""

    def __init__(
        self,
        output_dir: str = "data/raw/yahoo",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Initialize the fetcher.

        Args:
            output_dir: Directory to save CSV files
            start_date: Start date for data (YYYY-MM-DD). Defaults to 10 years ago.
            end_date: End date for data (YYYY-MM-DD). Defaults to today.
        """
        self.client = YahooFinanceClient(start_date=start_date, end_date=end_date)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Write the raw CSV if its content changed. Never overwrite cached data with an empty frame."""
        filepath = self.output_dir / filename
        if df.empty:
            logger.warning(f"Skipping save of empty DataFrame to {filepath} (preserving cached data)")
            return filepath
        text = df.to_csv(index=False)
        if filepath.exists() and filepath.read_bytes() == text.encode("utf-8"):
            logger.info(f"Unchanged: {filepath}")
            return filepath
        filepath.write_text(text, encoding="utf-8", newline="")
        logger.info(f"Saved: {filepath}")
        return filepath

    def _fetch_frame(self, key: str) -> pd.DataFrame:
        """Download one indicator and add its metadata columns (no file I/O; runs in worker threads)."""
        config = YAHOO_INDICATORS[key]
        ticker, name = config["ticker"], config["name"]
        logger.info(f"Fetching {name} ({ticker})...")
        df = self.client.get_historical_data(ticker)
        if df.empty:
            logger.error(f"No data for {key} ({ticker}): fetch failed, keeping the previous {key}_raw.csv")
            return df
        df['indicator'] = key
        df['name'] = name
        df['ticker'] = ticker
        return df

    def fetch_keys(self, keys: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch several indicators, MAX_WORKERS at a time. (Yahoo's chart endpoint is one request per
        symbol; yf.download only runs the same requests in threads, so it gains nothing here.)
        A failed indicator keeps its previous raw file and logs an error (audit H1).
        """
        results: Dict[str, pd.DataFrame] = {}
        valid = []
        for key in keys:
            if key not in YAHOO_INDICATORS:
                logger.warning(f"Unknown indicator key: {key}")
                results[key] = pd.DataFrame()
            else:
                valid.append(key)
        for key, (df, exc) in zip(valid, map_bounded(self._fetch_frame, valid, MAX_WORKERS)):
            if exc is not None:
                logger.error(f"Yahoo {key}: fetch failed: {exc}")
                df = pd.DataFrame()
            if not df.empty:
                self._save_csv(df, f"{key}_raw.csv")
                logger.info(f"Fetched {key}: {len(df)} rows")
            results[key] = df
        return results

    def fetch_indicator(self, key: str) -> pd.DataFrame:
        """Fetch a single indicator by its key (e.g., 'ibex_35')."""
        return self.fetch_keys([key])[key]

    def fetch_group(self, group_name: str) -> Dict[str, pd.DataFrame]:
        """Fetch all indicators in a group."""
        if group_name not in INDICATOR_GROUPS:
            logger.warning(f"Unknown group: {group_name}")
            return {}
        return self.fetch_keys(list(INDICATOR_GROUPS[group_name]))

    def fetch_category(self, category: str) -> Dict[str, pd.DataFrame]:
        """Fetch all indicators in a category (e.g., 'stock_indices', 'currencies')."""
        return self.fetch_keys(list(get_indicators_by_category(category)))

    def fetch_all(self) -> Dict[str, pd.DataFrame]:
        """Fetch all configured indicators."""
        results = self.fetch_keys(list(YAHOO_INDICATORS))
        success = sum(1 for df in results.values() if not df.empty)
        logger.info(f"Yahoo fetch: {success} of {len(results)} indicators fetched")
        return results

    def fetch_selected(self, keys: List[str]) -> Dict[str, pd.DataFrame]:
        """Fetch selected indicators by key."""
        return self.fetch_keys(list(keys))
