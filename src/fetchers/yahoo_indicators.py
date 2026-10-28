"""
Yahoo Finance Indicators Configuration
Defines all financial market indicators to fetch from Yahoo Finance.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from .yahoo_client import YahooFinanceClient

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

    "fed_funds": {
        "ticker": "^IRX",
        "name": "Fed Funds Rate (proxy)",
        "category": "interest_rates",
        "description": "13-week T-Bill rate as proxy for Fed Funds effective rate",
        "geography": "US",
        "currency": "%",
        "frequency": "daily"
    },

    # ==========================================================================
    # US TREASURY YIELDS
    # ==========================================================================

    "us_treasury_10y": {
        "ticker": "^TNX",
        "name": "US Treasury 10Y Yield",
        "category": "interest_rates",
        "description": "10-year US Treasury yield",
        "geography": "US",
        "currency": "%",
        "frequency": "daily"
    },

    "us_treasury_5y": {
        "ticker": "^FVX",
        "name": "US Treasury 5Y Yield",
        "category": "interest_rates",
        "description": "5-year US Treasury yield",
        "geography": "US",
        "currency": "%",
        "frequency": "daily"
    },

    "us_treasury_30y": {
        "ticker": "^TYX",
        "name": "US Treasury 30Y Yield",
        "category": "interest_rates",
        "description": "30-year US Treasury yield",
        "geography": "US",
        "currency": "%",
        "frequency": "daily"
    },

    # ==========================================================================
    # CURRENCY EXCHANGE RATES
    # ==========================================================================

    "eur_usd": {
        "ticker": "EURUSD=X",
        "name": "EUR/USD",
        "category": "currencies",
        "description": "Euro to US Dollar exchange rate",
        "geography": "International",
        "currency": "USD",
        "frequency": "daily"
    },

    "eur_gbp": {
        "ticker": "EURGBP=X",
        "name": "EUR/GBP",
        "category": "currencies",
        "description": "Euro to British Pound exchange rate",
        "geography": "International",
        "currency": "GBP",
        "frequency": "daily"
    },

    "eur_jpy": {
        "ticker": "EURJPY=X",
        "name": "EUR/JPY",
        "category": "currencies",
        "description": "Euro to Japanese Yen exchange rate",
        "geography": "International",
        "currency": "JPY",
        "frequency": "daily"
    },

    "eur_chf": {
        "ticker": "EURCHF=X",
        "name": "EUR/CHF",
        "category": "currencies",
        "description": "Euro to Swiss Franc exchange rate",
        "geography": "International",
        "currency": "CHF",
        "frequency": "daily"
    },

    "dxy": {
        "ticker": "DX-Y.NYB",
        "name": "US Dollar Index",
        "category": "currencies",
        "description": "Index measuring value of USD against basket of major currencies",
        "geography": "International",
        "currency": "Index",
        "frequency": "daily"
    },

    "gbp_usd": {
        "ticker": "GBPUSD=X",
        "name": "GBP/USD",
        "category": "currencies",
        "description": "British Pound to US Dollar exchange rate",
        "geography": "International",
        "currency": "USD",
        "frequency": "daily"
    },

    "usd_jpy": {
        "ticker": "JPY=X",
        "name": "USD/JPY",
        "category": "currencies",
        "description": "US Dollar to Japanese Yen exchange rate",
        "geography": "International",
        "currency": "JPY",
        "frequency": "daily"
    },

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

    "brent_crude": {
        "ticker": "BZ=F",
        "name": "Brent Crude Oil",
        "category": "commodities",
        "description": "Brent crude oil futures price",
        "geography": "International",
        "currency": "USD",
        "frequency": "daily"
    },

    "wti_crude": {
        "ticker": "CL=F",
        "name": "WTI Crude Oil",
        "category": "commodities",
        "description": "West Texas Intermediate crude oil futures price",
        "geography": "International",
        "currency": "USD",
        "frequency": "daily"
    },

    "natural_gas": {
        "ticker": "NG=F",
        "name": "Natural Gas",
        "category": "commodities",
        "description": "Natural gas futures price (Henry Hub)",
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

    "spain_govt_bond_etf": {
        "ticker": "SPGB.L",
        "name": "Spain Government Bond ETF",
        "category": "bonds",
        "description": "iShares Spain Government Bond UCITS ETF tracking Spanish government bonds",
        "geography": "Spain",
        "currency": "EUR",
        "frequency": "daily"
    },

    "euro_govt_bond_etf": {
        "ticker": "IBGE.AS",
        "name": "Euro Government Bond ETF",
        "category": "bonds",
        "description": "iShares Core Euro Government Bond ETF",
        "geography": "Eurozone",
        "currency": "EUR",
        "frequency": "daily"
    },

    "us_treasury_20y_etf": {
        "ticker": "TLT",
        "name": "US Treasury 20+ Year ETF",
        "category": "bonds",
        "description": "iShares 20+ Year Treasury Bond ETF",
        "geography": "US",
        "currency": "USD",
        "frequency": "daily"
    },

    "us_treasury_7_10y_etf": {
        "ticker": "IEF",
        "name": "US Treasury 7-10 Year ETF",
        "category": "bonds",
        "description": "iShares 7-10 Year Treasury Bond ETF",
        "geography": "US",
        "currency": "USD",
        "frequency": "daily"
    },

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

    "vstoxx": {
        "ticker": "^V2X",
        "name": "VSTOXX",
        "category": "volatility",
        "description": "Euro STOXX 50 Volatility Index",
        "geography": "Eurozone",
        "currency": "Index",
        "frequency": "daily"
    },

    # ==========================================================================
    # SECTOR INDICES (SPAIN-FOCUSED)
    # ==========================================================================

    "spanish_banks_etf": {
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
    "interest_rates": [
        "us_treasury_5y", "us_treasury_10y", "us_treasury_30y"
    ],
    "currencies": [
        "eur_usd", "eur_gbp", "eur_jpy", "eur_chf", "dxy"
    ],
    "commodities": [
        "gold", "brent_crude", "wti_crude", "natural_gas", "silver"
    ],
    "bonds": [
        "spain_govt_bond_etf", "euro_govt_bond_etf",
        "us_treasury_20y_etf", "us_treasury_7_10y_etf"
    ],
    "volatility": [
        "vix", "vstoxx"
    ],
    "sector": [
        "spanish_banks_etf", "european_banks_etf"
    ],
    # Key indicators for dashboard overview
    "dashboard_summary": [
        "ibex_35", "euro_stoxx_50", "sp_500",
        "eur_usd", "brent_crude", "gold", "vix"
    ],
    # Spain-focused view
    "spain_focus": [
        "ibex_35", "spanish_banks_etf", "spain_govt_bond_etf", "eur_usd"
    ]
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
            start_date: Start date for data (YYYY-MM-DD). Defaults to 5 years ago.
            end_date: End date for data (YYYY-MM-DD). Defaults to today.
        """
        self.client = YahooFinanceClient(start_date=start_date, end_date=end_date)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Save DataFrame to CSV. Skips writing if df is empty to preserve cached data."""
        filepath = self.output_dir / filename
        if df.empty:
            logger.warning(f"Skipping save of empty DataFrame to {filepath} (preserving cached data)")
            return filepath
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Saved: {filepath}")
        return filepath

    def fetch_indicator(self, key: str) -> pd.DataFrame:
        """
        Fetch a single indicator by its key.

        Args:
            key: Indicator key (e.g., 'ibex_35')

        Returns:
            DataFrame with OHLCV data
        """
        if key not in YAHOO_INDICATORS:
            logger.warning(f"Unknown indicator key: {key}")
            return pd.DataFrame()

        config = YAHOO_INDICATORS[key]
        ticker = config["ticker"]
        name = config["name"]

        logger.info(f"Fetching {name} ({ticker})...")

        df = self.client.get_historical_data(ticker)

        if df.empty:
            logger.warning(f"No data for {key}")
            return df

        # Add metadata columns
        df['indicator'] = key
        df['name'] = name
        df['ticker'] = ticker

        # Save to CSV
        filename = f"{key}_raw.csv"
        self._save_csv(df, filename)

        logger.info(f"Fetched {len(df)} rows")
        return df

    def fetch_group(self, group_name: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch all indicators in a group.

        Args:
            group_name: Name of the indicator group

        Returns:
            Dictionary mapping indicator keys to DataFrames
        """
        if group_name not in INDICATOR_GROUPS:
            logger.warning(f"Unknown group: {group_name}")
            return {}

        logger.info(f"\n{'='*60}")
        logger.info(f"Fetching group: {group_name}")
        logger.info(f"{'='*60}\n")

        results = {}
        keys = INDICATOR_GROUPS[group_name]

        for key in keys:
            df = self.fetch_indicator(key)
            results[key] = df

        return results

    def fetch_category(self, category: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch all indicators in a category.

        Args:
            category: Category name (e.g., 'stock_indices', 'currencies')

        Returns:
            Dictionary mapping indicator keys to DataFrames
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Fetching category: {category}")
        logger.info(f"{'='*60}\n")

        results = {}
        indicators = get_indicators_by_category(category)

        for key in indicators:
            df = self.fetch_indicator(key)
            results[key] = df

        return results

    def fetch_all(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch all configured indicators.

        Returns:
            Dictionary mapping indicator keys to DataFrames
        """
        logger.info("\n" + "="*60)
        logger.info("YAHOO FINANCE DATA FETCH")
        logger.info("="*60 + "\n")

        results = {}

        for key in YAHOO_INDICATORS:
            df = self.fetch_indicator(key)
            results[key] = df

        # Log summary
        logger.info("\n" + "="*60)
        logger.info("FETCH SUMMARY")
        logger.info("="*60)
        success = sum(1 for df in results.values() if not df.empty)
        logger.info(f"Total indicators: {len(results)}")
        logger.info(f"Successfully fetched: {success}")
        logger.info(f"Failed: {len(results) - success}")

        return results

    def fetch_selected(self, keys: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch selected indicators by key.

        Args:
            keys: List of indicator keys to fetch

        Returns:
            Dictionary mapping indicator keys to DataFrames
        """
        results = {}
        for key in keys:
            df = self.fetch_indicator(key)
            results[key] = df
        return results
