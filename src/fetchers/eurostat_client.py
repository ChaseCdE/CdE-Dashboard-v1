"""
Eurostat API Client

One request per dataset against the Eurostat Statistics API (JSON-stat 2.0), with every
dimension pinned server-side. The `eurostat` Python package was dropped: it issued an extra
request to read the dataset's dimension order and one data request per combination of filter
values (100 requests for 24 datasets); this client needs 24 and no extra dependency.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import itertools
import re
import logging

from .http_session import make_session

logger = logging.getLogger(__name__)

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"


class EurostatError(Exception):
    """A Eurostat response is unusable (error, unexpected dimensions, no data)."""


def jsonstat_to_long(js: dict, dataset_code: str, pinned: List[str]) -> pd.DataFrame:
    """
    Convert a JSON-stat 2.0 response to the long format of the raw files: one column per
    dimension (in the dataset's dimension order), `period` and `value`. Missing observations
    are absent from JSON-stat, so they are absent here.

    Every dimension except geo and time must be pinned to one category by the request
    (`pinned` lists the filter keys); otherwise the series would be ambiguous and this raises.
    """
    ids, sizes = js["id"], js["size"]
    dims = {d: js["dimension"][d]["category"]["index"] for d in ids}
    # category index is a dict code -> position, or a list of codes
    cats = {d: (list(ix) if isinstance(ix, list) else sorted(ix, key=ix.get)) for d, ix in dims.items()}
    for d in ids:
        if d not in ("geo", "time") and len(cats[d]) > 1 and d not in pinned:
            raise EurostatError(f"{dataset_code}: dimension {d} has {len(cats[d])} categories and was not filtered")
    values = js.get("value", {})
    if isinstance(values, list):
        values = {i: v for i, v in enumerate(values) if v is not None}
    other = [d for d in ids if d != "time"]
    n_time = len(cats["time"])
    rows = []
    # JSON-stat is row-major over `id` with time last: position = combo_index * n_time + t
    combos = list(itertools.product(*[range(len(cats[d])) for d in other]))
    for ci, combo in enumerate(combos):
        for t in range(n_time):
            v = values.get(str(ci * n_time + t), values.get(ci * n_time + t))
            if v is None:
                continue
            rows.append([cats[d][k] for d, k in zip(other, combo)] + [cats["time"][t], float(v)])
    return pd.DataFrame(rows, columns=other + ["period", "value"])


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
        self.session = make_session(headers={"Accept": "application/json"})

    def get_data(
        self,
        dataset_code: str,
        filter_pars: Dict[str, Any],
        include_start_period: bool = True
    ) -> pd.DataFrame:
        """
        Fetch one dataset, filtered on the server.

        Args:
            dataset_code: Eurostat dataset code (e.g., 'namq_10_gdp')
            filter_pars: dimension -> value or list of values; 'startPeriod' sets the first period
            include_start_period: Whether to default startPeriod to the client's start year

        Returns:
            Long DataFrame (dimensions, period, value); empty on failure (logged as an error)
        """
        params = {}
        pinned = []
        for key, val in filter_pars.items():
            if key == "startPeriod":
                continue
            params[key] = list(val) if isinstance(val, (list, tuple)) else [val]
            pinned.append(key)
        start = filter_pars.get("startPeriod", self.start_period if include_start_period else None)
        if start is not None:
            params["sinceTimePeriod"] = str(start)
        params["format"] = "JSON"
        params["lang"] = "EN"

        try:
            resp = self.session.get(BASE_URL + dataset_code, params=params)
            resp.raise_for_status()
            js = resp.json()
            if "error" in js:
                raise EurostatError(f"{dataset_code}: {js['error']}")
            return jsonstat_to_long(js, dataset_code, pinned)
        except Exception as e:
            logger.error(f"Error fetching {dataset_code}: {e}")
            return pd.DataFrame()


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
