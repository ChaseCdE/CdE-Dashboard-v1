"""
Data Fetchers Package
Modules for fetching data from various sources.
"""

from .ine_client import INEClient, parse_ine_data
from .ine_indicators import INEIndicatorFetcher, fetch_operation_tables, TABLE_IDS
from .eurostat_client import (
    EurostatClient,
    parse_eurostat_data,
    convert_period_to_date,
    melt_eurostat_data,
)
from .eurostat_indicators import EurostatIndicatorFetcher, DATASET_CODES
from .yahoo_client import YahooFinanceClient
from .yahoo_indicators import YahooIndicatorFetcher, YAHOO_INDICATORS
from .bde_client import BdeClient, get_appropriate_range
from .bde_indicators import BdeIndicatorFetcher, BDE_INDICATORS, INDICATOR_GROUPS as BDE_INDICATOR_GROUPS

__all__ = [
    # INE
    "INEClient",
    "parse_ine_data",
    "INEIndicatorFetcher",
    "fetch_operation_tables",
    "TABLE_IDS",
    # Eurostat
    "EurostatClient",
    "parse_eurostat_data",
    "convert_period_to_date",
    "melt_eurostat_data",
    "EurostatIndicatorFetcher",
    "DATASET_CODES",
    # Yahoo Finance
    "YahooFinanceClient",
    "YahooIndicatorFetcher",
    "YAHOO_INDICATORS",
    # Banco de Espana
    "BdeClient",
    "get_appropriate_range",
    "BdeIndicatorFetcher",
    "BDE_INDICATORS",
    "BDE_INDICATOR_GROUPS",
]
