"""
Eurostat API Client
Base client for fetching data from Eurostat using the eurostat Python package.
"""

import eurostat
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class EurostatClient:
    """Client for fetching data from Eurostat."""

    # Geographic codes
    GEO_SPAIN = "ES"
    GEO_EU27 = "EU27_2020"
    GEO_EUROZONE = "EA20"

    def __init__(self, start_period: int = 2015):
        """
        Initialize the Eurostat client.

        Args:
            start_period: Start year for data fetching (default: 2015)
        """
        self.start_period = start_period

    def get_data(
        self,
        dataset_code: str,
        filter_pars: Dict[str, Any],
        include_start_period: bool = True
    ) -> pd.DataFrame:
        """
        Fetch data from Eurostat.

        Args:
            dataset_code: Eurostat dataset code (e.g., 'namq_10_gdp')
            filter_pars: Dictionary of filter parameters
            include_start_period: Whether to include startPeriod in filters

        Returns:
            DataFrame with the fetched data
        """
        if include_start_period and 'startPeriod' not in filter_pars:
            filter_pars['startPeriod'] = self.start_period

        try:
            df = eurostat.get_data_df(dataset_code, filter_pars=filter_pars)
            return df
        except Exception as e:
            logger.error(f"Error fetching {dataset_code}: {e}")
            return pd.DataFrame()

    def get_dataset_info(self, dataset_code: str) -> Dict:
        """
        Get available parameters for a dataset.

        Args:
            dataset_code: Eurostat dataset code

        Returns:
            Dictionary with parameter information
        """
        try:
            pars = eurostat.get_pars(dataset_code)
            return {"parameters": pars}
        except Exception as e:
            logger.error(f"Error getting parameters for {dataset_code}: {e}")
            return {}

    def get_parameter_values(self, dataset_code: str, parameter: str) -> List[str]:
        """
        Get possible values for a parameter.

        Args:
            dataset_code: Eurostat dataset code
            parameter: Parameter name (e.g., 'geo', 'unit')

        Returns:
            List of possible values
        """
        try:
            values = eurostat.get_par_values(dataset_code, parameter)
            return values
        except Exception as e:
            logger.error(f"Error getting values for {parameter}: {e}")
            return []


def melt_eurostat_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Melt wide-format Eurostat data to long format.

    Eurostat returns data with time periods as columns (e.g., '2024-Q1', '2024-01').
    This function converts to long format with 'period' and 'value' columns.

    Args:
        df: Wide-format DataFrame from eurostat.get_data_df()

    Returns:
        Long-format DataFrame with 'period' and 'value' columns
    """
    if df.empty:
        return df

    df = df.copy()

    # Fix geo column name (eurostat uses 'geo\TIME_PERIOD')
    geo_col = None
    for col in df.columns:
        if 'geo' in col.lower():
            geo_col = col
            if col != 'geo':
                df = df.rename(columns={col: 'geo'})
            break

    # Find time-like columns (e.g., '2024-Q1', '2024-01', '2024')
    time_pattern_cols = []
    id_cols = []

    for col in df.columns:
        col_str = str(col)
        # Check if column looks like a time period (starts with 4 digits)
        if re.match(r'^\d{4}', col_str):
            time_pattern_cols.append(col)
        else:
            id_cols.append(col)

    if not time_pattern_cols:
        # No melting needed, data might already be in long format
        return df

    # Melt the data
    df_melted = df.melt(
        id_vars=id_cols,
        value_vars=time_pattern_cols,
        var_name='period',
        value_name='value'
    )

    return df_melted


def convert_period_to_date(period) -> Optional[datetime]:
    """
    Convert Eurostat period format to datetime.

    Handles formats like:
    - '2024-Q1' -> 2024-01-01
    - '2024-01' -> 2024-01-01
    - '2024' -> 2024-01-01

    Args:
        period: Period string from Eurostat

    Returns:
        datetime object or None if parsing fails
    """
    # Handle None/NaN
    if period is None:
        return None

    try:
        # Check for NaN
        if pd.isna(period):
            return None
    except (ValueError, TypeError):
        pass

    period = str(period).strip()

    try:
        # Quarterly format: 2024-Q1, 2024Q1
        if 'Q' in period.upper():
            period = period.upper().replace('-Q', 'Q')
            year = int(period[:4])
            quarter = int(period[-1])
            month = (quarter - 1) * 3 + 1
            return datetime(year, month, 1)

        # Monthly format: 2024-01, 2024M01
        if 'M' in period.upper():
            period = period.upper().replace('M', '-')

        if '-' in period:
            parts = period.split('-')
            if len(parts) == 2:
                year = int(parts[0])
                month = int(parts[1])
                return datetime(year, month, 1)
            elif len(parts) == 3:
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))

        # Annual format: 2024
        if len(period) == 4 and period.isdigit():
            return datetime(int(period), 1, 1)

    except (ValueError, TypeError) as e:
        pass

    return None


def parse_eurostat_data(df: pd.DataFrame, geo_filter: List[str] = None) -> pd.DataFrame:
    """
    Parse and clean Eurostat data after melting.

    Args:
        df: Melted Eurostat DataFrame
        geo_filter: List of geographic codes to keep (default: ES, EU27_2020)

    Returns:
        Cleaned DataFrame with standardized columns
    """
    if df.empty:
        return df

    if geo_filter is None:
        geo_filter = [EurostatClient.GEO_SPAIN, EurostatClient.GEO_EU27]

    df = df.copy()

    # Filter by geography if 'geo' column exists
    if 'geo' in df.columns:
        df = df[df['geo'].isin(geo_filter)]

    # Convert period to date
    if 'period' in df.columns:
        df['date'] = df['period'].apply(convert_period_to_date)
        df = df.dropna(subset=['date'])

    # Ensure value is numeric
    if 'value' in df.columns:
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

    # Sort by geo and date
    if 'geo' in df.columns and 'date' in df.columns:
        df = df.sort_values(['geo', 'date']).reset_index(drop=True)

    return df
