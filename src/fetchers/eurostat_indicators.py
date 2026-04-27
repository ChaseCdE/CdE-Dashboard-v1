"""
Eurostat Indicator Fetchers
Functions to fetch specific economic indicators from Eurostat.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List
import logging
from .eurostat_client import (
    EurostatClient,
    parse_eurostat_data,
    convert_period_to_date,
    melt_eurostat_data,
)

logger = logging.getLogger(__name__)


# Dataset codes for each indicator
DATASET_CODES = {
    # Economic Activity
    "gdp_growth": "namq_10_gdp",
    "industrial_production": "sts_inpr_m",
    "economic_sentiment": "ei_bssi_m_r2",

    # Labor Market
    "unemployment": "une_rt_m",
    "employment_growth": "namq_10_a10_e",
    "labor_participation": "lfsi_emp_q",

    # Prices & Inflation
    "hicp": "prc_hicp_manr",
    "core_inflation": "prc_hicp_manr",  # Same dataset, different coicop filter
    "producer_prices": "sts_inppd_m",

    # External Sector
    "trade_balance": "ext_lt_intratrd",

    # Public Finances
    "government_debt": "gov_10q_ggdebt",
    "budget_deficit": "gov_10dd_edpt1",

    # Consumer & Household
    "consumer_confidence": "ei_bsco_m",
    "retail_trade": "sts_trtu_m",
    "house_prices": "prc_hpi_q",
}


class EurostatIndicatorFetcher:
    """Fetcher for Eurostat economic indicators."""

    def __init__(
        self,
        output_dir: str = "data/raw/eurostat",
        start_period: int = 2015,
        geo_codes: List[str] = None
    ):
        """
        Initialize the fetcher.

        Args:
            output_dir: Directory to save CSV files
            start_period: Start year for data fetching
            geo_codes: Geographic codes to fetch (default: ES, EU27_2020)
        """
        self.client = EurostatClient(start_period=start_period)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.geo_codes = geo_codes or [EurostatClient.GEO_SPAIN, EurostatClient.GEO_EU27]

    def _save_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Save DataFrame to CSV. Skips writing if df is empty to preserve cached data."""
        filepath = self.output_dir / filename
        if df.empty:
            logger.warning(f"Skipping save of empty DataFrame to {filepath} (preserving cached data)")
            return filepath
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Saved: {filepath}")
        return filepath

    def _process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw data: melt if needed, parse dates, clean."""
        if df.empty:
            return df

        # Melt wide format to long format (time periods as columns -> rows)
        df = melt_eurostat_data(df)

        # Parse, filter by geography, and convert dates
        df = parse_eurostat_data(df, self.geo_codes)

        return df

    # === Economic Activity Indicators ===

    def fetch_gdp_growth(self) -> pd.DataFrame:
        """
        Fetch GDP Growth data (quarterly).

        Returns:
            DataFrame with GDP growth data for Spain and EU27
        """
        logger.info("Fetching GDP Growth...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['CLV_PCH_PRE'],  # Chain linked volumes, % change
            's_adj': ['SCA'],  # Seasonally and calendar adjusted
            'na_item': ['B1GQ']  # GDP at market prices
        }
        df = self.client.get_data(DATASET_CODES["gdp_growth"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "gdp_growth_raw.csv")
        return df

    def fetch_industrial_production(self) -> pd.DataFrame:
        """
        Fetch Industrial Production Index (monthly).

        Returns:
            DataFrame with IPI data for Spain and EU27
        """
        logger.info("Fetching Industrial Production Index...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['I21'],  # Index, 2021=100
            's_adj': ['SCA'],
            'nace_r2': ['B-D']  # Industry except construction
        }
        df = self.client.get_data(DATASET_CODES["industrial_production"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "industrial_production_raw.csv")
        return df

    def fetch_economic_sentiment(self) -> pd.DataFrame:
        """
        Fetch Economic Sentiment Indicator (monthly).

        Returns:
            DataFrame with ESI data for Spain and EU27
        """
        logger.info("Fetching Economic Sentiment Indicator...")
        filter_pars = {
            'geo': self.geo_codes,
            'indic': ['BS-ESI-I'],
            's_adj': ['SA']
        }
        df = self.client.get_data(DATASET_CODES["economic_sentiment"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "economic_sentiment_raw.csv")
        return df

    # === Labor Market Indicators ===

    def fetch_unemployment(self) -> pd.DataFrame:
        """
        Fetch Unemployment Rate (monthly).

        Returns:
            DataFrame with unemployment data for Spain and EU27
        """
        logger.info("Fetching Unemployment Rate...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['PC_ACT'],  # % of active population
            's_adj': ['SA'],
            'sex': ['T'],  # Total
            'age': ['Y25-74']  # 25-74 years (Y15-74 not available)
        }
        df = self.client.get_data(DATASET_CODES["unemployment"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "unemployment_raw.csv")
        return df

    def fetch_employment_growth(self) -> pd.DataFrame:
        """
        Fetch Employment Growth (quarterly).

        Returns:
            DataFrame with employment growth data for Spain and EU27
        """
        logger.info("Fetching Employment Growth...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['PCH_PRE_PER'],  # % change on previous period
            's_adj': ['SCA'],
            'nace_r2': ['TOTAL'],
            'na_item': ['EMP_DC']  # Total employment domestic concept
        }
        df = self.client.get_data(DATASET_CODES["employment_growth"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "employment_growth_raw.csv")
        return df

    def fetch_labor_participation(self) -> pd.DataFrame:
        """
        Fetch Labor Force Participation Rate (quarterly).

        Returns:
            DataFrame with participation rate data for Spain and EU27
        """
        logger.info("Fetching Labor Force Participation Rate...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['PC_POP'],  # % of population
            's_adj': ['SA'],
            'sex': ['T'],
            'age': ['Y15-64'],
            'indic_em': ['ACT']  # Activity rate
        }
        df = self.client.get_data(DATASET_CODES["labor_participation"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "labor_participation_raw.csv")
        return df

    # === Prices & Inflation Indicators ===

    def fetch_hicp(self) -> pd.DataFrame:
        """
        Fetch HICP Inflation (monthly, annual rate of change).

        Returns:
            DataFrame with HICP data for Spain and EU27
        """
        logger.info("Fetching HICP Inflation...")
        filter_pars = {
            'geo': self.geo_codes,
            'coicop': ['CP00'],  # All items
            'unit': ['RCH_A']  # Annual rate of change
        }
        df = self.client.get_data(DATASET_CODES["hicp"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "hicp_raw.csv")
        return df

    def fetch_core_inflation(self) -> pd.DataFrame:
        """
        Fetch Core Inflation - HICP excluding energy and food (monthly).

        Returns:
            DataFrame with core inflation data for Spain and EU27
        """
        logger.info("Fetching Core Inflation...")
        filter_pars = {
            'geo': self.geo_codes,
            'coicop': ['TOT_X_NRG_FOOD'],  # Excluding energy and food
            'unit': ['RCH_A']
        }
        df = self.client.get_data(DATASET_CODES["core_inflation"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "core_inflation_raw.csv")
        return df

    def fetch_producer_prices(self) -> pd.DataFrame:
        """
        Fetch Producer Price Index (monthly).

        Returns:
            DataFrame with PPI data for Spain and EU27
        """
        logger.info("Fetching Producer Price Index...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['I21'],  # Index, 2021=100
            'nace_r2': ['B-D']
        }
        df = self.client.get_data(DATASET_CODES["producer_prices"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "producer_prices_raw.csv")
        return df

    # === External Sector Indicators ===

    def fetch_trade_balance(self) -> pd.DataFrame:
        """
        Fetch Trade Balance (monthly, Spain only).

        Returns:
            DataFrame with trade balance data for Spain
        """
        logger.info("Fetching Trade Balance...")
        filter_pars = {
            'geo': ['ES'],  # Spain only
            'partner': ['WORLD'],
            'indic_et': ['MIO_BAL_VAL', 'MIO_EXP_VAL', 'MIO_IMP_VAL']  # Million EUR
        }
        df = self.client.get_data(DATASET_CODES["trade_balance"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "trade_balance_raw.csv")
        return df

    # === Public Finances Indicators ===

    def fetch_government_debt(self) -> pd.DataFrame:
        """
        Fetch Government Debt-to-GDP (quarterly).

        Returns:
            DataFrame with debt data for Spain and EU27
        """
        logger.info("Fetching Government Debt-to-GDP...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['PC_GDP'],
            'na_item': ['GD'],  # Government gross debt
            'sector': ['S13']  # General government
        }
        df = self.client.get_data(DATASET_CODES["government_debt"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "government_debt_raw.csv")
        return df

    def fetch_budget_deficit(self) -> pd.DataFrame:
        """
        Fetch Budget Deficit as % of GDP (annual).

        Returns:
            DataFrame with deficit data for Spain and EU27
        """
        logger.info("Fetching Budget Deficit...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['PC_GDP'],
            'na_item': ['B9'],  # Net lending/borrowing
            'sector': ['S13']
        }
        df = self.client.get_data(DATASET_CODES["budget_deficit"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "budget_deficit_raw.csv")
        return df

    # === Consumer & Household Indicators ===

    def fetch_consumer_confidence(self) -> pd.DataFrame:
        """
        Fetch Consumer Confidence Indicator (monthly).

        Returns:
            DataFrame with consumer confidence data for Spain and EU27
        """
        logger.info("Fetching Consumer Confidence...")
        filter_pars = {
            'geo': self.geo_codes,
            'indic': ['BS-CSMCI'],  # Consumer confidence indicator
            's_adj': ['SA']
        }
        df = self.client.get_data(DATASET_CODES["consumer_confidence"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "consumer_confidence_raw.csv")
        return df

    def fetch_retail_trade(self) -> pd.DataFrame:
        """
        Fetch Retail Trade Volume Index (monthly).

        Returns:
            DataFrame with retail trade data for Spain and EU27
        """
        logger.info("Fetching Retail Trade Volume...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['I21'],
            's_adj': ['SCA'],
            'nace_r2': ['G47'],
            'indic_bt': ['VOL_SLS']  # Volume of sales (deflated turnover)
        }
        df = self.client.get_data(DATASET_CODES["retail_trade"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "retail_trade_raw.csv")
        return df

    def fetch_house_prices(self) -> pd.DataFrame:
        """
        Fetch House Price Index (quarterly).

        Returns:
            DataFrame with house price data for Spain and EU27
        """
        logger.info("Fetching House Price Index...")
        filter_pars = {
            'geo': self.geo_codes,
            'unit': ['I15_Q'],  # Index 2015=100, quarterly
            'purchase': ['TOTAL']
        }
        df = self.client.get_data(DATASET_CODES["house_prices"], filter_pars)
        df = self._process_data(df)
        self._save_csv(df, "house_prices_raw.csv")
        return df

    def fetch_gdp_index_comparison(self) -> pd.DataFrame:
        """
        Fetch GDP index data for European comparison (ES, FR, IT, DE, EU27).
        Uses chain-linked volumes (2010 prices) for level comparison.

        Returns:
            DataFrame with GDP index data for multiple countries
        """
        logger.info("Fetching GDP Index Comparison (ES, FR, IT, DE, EU27)...")
        comparison_geos = ['ES', 'FR', 'IT', 'DE', 'EU27_2020']
        filter_pars = {
            'geo': comparison_geos,
            'unit': ['CLV10_MNAC'],  # Chain linked volumes (2010), million units of national currency
            's_adj': ['SCA'],  # Seasonally and calendar adjusted
            'na_item': ['B1GQ']  # GDP at market prices
        }
        df = self.client.get_data(DATASET_CODES["gdp_growth"], filter_pars)
        df = melt_eurostat_data(df)
        df = parse_eurostat_data(df, comparison_geos)
        self._save_csv(df, "gdp_index_comparison_raw.csv")
        return df

    def fetch_all(self) -> dict:
        """
        Fetch all available indicators.

        Returns:
            Dictionary with indicator names as keys and DataFrames as values
        """
        results = {}

        logger.info("=" * 60)
        logger.info("Fetching all Eurostat indicators...")
        logger.info("=" * 60)

        # Economic Activity
        logger.info("[Economic Activity]")
        results["gdp_growth"] = self.fetch_gdp_growth()
        results["gdp_index_comparison"] = self.fetch_gdp_index_comparison()
        results["industrial_production"] = self.fetch_industrial_production()
        results["economic_sentiment"] = self.fetch_economic_sentiment()

        # Labor Market
        logger.info("[Labor Market]")
        results["unemployment"] = self.fetch_unemployment()
        results["employment_growth"] = self.fetch_employment_growth()
        results["labor_participation"] = self.fetch_labor_participation()

        # Prices & Inflation
        logger.info("[Prices & Inflation]")
        results["hicp"] = self.fetch_hicp()
        results["core_inflation"] = self.fetch_core_inflation()
        results["producer_prices"] = self.fetch_producer_prices()

        # External Sector
        logger.info("[External Sector]")
        results["trade_balance"] = self.fetch_trade_balance()

        # Public Finances
        logger.info("[Public Finances]")
        results["government_debt"] = self.fetch_government_debt()
        results["budget_deficit"] = self.fetch_budget_deficit()

        # Consumer & Household
        logger.info("[Consumer & Household]")
        results["consumer_confidence"] = self.fetch_consumer_confidence()
        results["retail_trade"] = self.fetch_retail_trade()
        results["house_prices"] = self.fetch_house_prices()

        logger.info("=" * 60)
        logger.info("All Eurostat indicators fetched successfully!")
        logger.info("=" * 60)

        # Summary
        logger.info("Summary:")
        for name, df in results.items():
            rows = len(df) if not df.empty else 0
            logger.info(f"{name}: {rows} rows")

        return results
