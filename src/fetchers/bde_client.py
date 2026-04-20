"""
Banco de Espana (BdE) API Client
Client for fetching economic and financial data from the BdE statistics API.
"""

import requests
import pandas as pd
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class BdeClient:
    """Client for fetching data from Banco de Espana API."""

    BASE_URL = "https://app.bde.es/bierest/resources/srdatosapp"

    # Default time ranges by frequency
    DEFAULT_RANGES = {
        "D": "12M",    # Daily: 12 months
        "M": "60M",    # Monthly: 60 months (5 years)
        "Q": "MAX",    # Quarterly: Maximum available
        "A": "MAX"     # Annual: Maximum available
    }

    def __init__(
        self,
        language: str = "EN",
        request_delay: float = 0.5,
        timeout: int = 30
    ):
        """
        Initialize the BdE API client.

        Args:
            language: Language code ('EN' for English, 'ES' for Spanish)
            request_delay: Delay between requests in seconds to avoid rate limiting
            timeout: Request timeout in seconds
        """
        self.language = language
        self.request_delay = request_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate"
        })
        self._last_request_time = 0

    def _wait_for_rate_limit(self) -> None:
        """Enforce delay between API requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict[str, str]) -> Optional[List[Dict]]:
        """
        Make a request to the BdE API.

        Args:
            endpoint: API endpoint ('favoritas' or 'listaSeries')
            params: Query parameters

        Returns:
            JSON response as a list of dictionaries, or None if request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        self._wait_for_rate_limit()

        try:
            logger.debug(f"Requesting: {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Received {len(data) if isinstance(data, list) else 1} records")
            return data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON decode error for {url}: {e}")
            return None

    def get_latest(self, series_codes: Union[str, List[str]]) -> Optional[List[Dict[str, Any]]]:
        """
        Get the latest values for specified series.

        Args:
            series_codes: Single series code or list of series codes

        Returns:
            List of dictionaries with latest values, or None if request fails

        Response fields:
            - serie: Series identification code
            - descripcionCorta: Brief description
            - codFrecuencia: Frequency (D, M, Q, A)
            - decimales: Decimal places
            - simbolo: Unit symbol
            - tendencia: Trend indicator (+, -, =)
            - fechaValor: Timestamp
            - valor: Latest value
        """
        if isinstance(series_codes, str):
            series_codes = [series_codes]

        params = {
            "idioma": self.language,
            "series": ",".join(series_codes)
        }

        logger.info(f"Fetching latest values for {len(series_codes)} series...")
        data = self._make_request("favoritas", params)

        if data is None:
            logger.warning("Failed to fetch latest values")
            return None

        return data

    def get_series(
        self,
        series_codes: Union[str, List[str]],
        time_range: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get full time series data for specified series.

        Args:
            series_codes: Single series code or list of series codes
            time_range: Time range specification. Options depend on frequency:
                       - Daily: '3M', '12M', '36M'
                       - Monthly/Quarterly: '30M', '60M', 'MAX'
                       - Annual: '60M', 'MAX'
                       If None, uses default based on inferred frequency.

        Returns:
            List of dictionaries with time series data, or None if request fails

        Response fields:
            - serie: Series identification code
            - descripcion: Extended description
            - descripcionCorta: Brief description
            - codFrecuencia: Frequency code
            - decimales: Decimal places
            - simbolo: Unit symbol
            - informacion: Additional metadata
            - fechaInicio: Start date
            - fechaFin: End date
            - fechas: Array of timestamps
            - valores: Array of data values
        """
        if isinstance(series_codes, str):
            series_codes = [series_codes]

        # If no range specified, use default (60M for most cases)
        if time_range is None:
            time_range = "60M"

        params = {
            "idioma": self.language,
            "series": ",".join(series_codes),
            "rango": time_range
        }

        logger.info(f"Fetching time series for {len(series_codes)} series with range {time_range}...")
        data = self._make_request("listaSeries", params)

        if data is None:
            logger.warning("Failed to fetch time series")
            return None

        return data

    def series_to_dataframe(self, series_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert a single series response to a pandas DataFrame.

        Args:
            series_data: Dictionary containing series data from API response

        Returns:
            DataFrame with columns: date, value, and metadata columns
        """
        if not series_data:
            return pd.DataFrame()

        fechas = series_data.get("fechas", [])
        valores = series_data.get("valores", [])

        if not fechas or not valores:
            logger.warning(f"Empty data for series {series_data.get('serie', 'unknown')}")
            return pd.DataFrame()

        df = pd.DataFrame({
            "date": pd.to_datetime(fechas),
            "value": pd.to_numeric(valores, errors="coerce")
        })

        # Add metadata columns
        df["series_code"] = series_data.get("serie", "")
        df["description"] = series_data.get("descripcionCorta", "")
        df["frequency"] = series_data.get("codFrecuencia", "")
        df["unit"] = series_data.get("simbolo", "")
        df["decimals"] = series_data.get("decimales", 0)

        # Sort by date (newest first in API response, we want oldest first)
        df = df.sort_values("date").reset_index(drop=True)

        return df

    def get_series_as_dataframe(
        self,
        series_code: str,
        time_range: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch a single series and return as DataFrame.

        Args:
            series_code: BdE series code
            time_range: Time range specification

        Returns:
            DataFrame with time series data
        """
        data = self.get_series(series_code, time_range)

        if not data or len(data) == 0:
            return pd.DataFrame()

        return self.series_to_dataframe(data[0])

    def get_multiple_series_as_dataframes(
        self,
        series_codes: List[str],
        time_range: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch multiple series and return as dictionary of DataFrames.

        Args:
            series_codes: List of BdE series codes
            time_range: Time range specification

        Returns:
            Dictionary mapping series codes to DataFrames
        """
        data = self.get_series(series_codes, time_range)

        if not data:
            return {}

        result = {}
        for series_data in data:
            code = series_data.get("serie", "")
            df = self.series_to_dataframe(series_data)
            if not df.empty:
                result[code] = df

        return result

    def get_latest_as_dataframe(
        self,
        series_codes: Union[str, List[str]]
    ) -> pd.DataFrame:
        """
        Fetch latest values and return as DataFrame.

        Args:
            series_codes: Single series code or list of series codes

        Returns:
            DataFrame with latest values for each series
        """
        data = self.get_latest(series_codes)

        if not data:
            return pd.DataFrame()

        rows = []
        for item in data:
            rows.append({
                "series_code": item.get("serie", ""),
                "description": item.get("descripcionCorta", ""),
                "frequency": item.get("codFrecuencia", ""),
                "unit": item.get("simbolo", ""),
                "date": pd.to_datetime(item.get("fechaValor", None)),
                "value": pd.to_numeric(item.get("valor"), errors="coerce"),
                "trend": item.get("tendencia", ""),
                "decimals": item.get("decimales", 0)
            })

        return pd.DataFrame(rows)

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def parse_bde_date(date_str: str, frequency: str) -> datetime:
    """
    Parse BdE date string based on frequency.

    Args:
        date_str: Date string from API (format: yyyy-mm-ddThh:mm:ssZ)
        frequency: Frequency code (D, M, Q, A)

    Returns:
        Parsed datetime object

    Notes:
        - Daily (D): Reference date
        - Monthly (M): 1st of reference month
        - Quarterly (Q): 1st of first month of quarter
        - Annual (A): January 1st of reference year
    """
    return pd.to_datetime(date_str)


def get_appropriate_range(frequency: str, years: int = 5) -> str:
    """
    Get appropriate time range parameter for a given frequency.

    Args:
        frequency: Frequency code (D, M, Q, A)
        years: Desired years of history

    Returns:
        Range parameter string for BdE API
    """
    if frequency == "D":
        # Daily: 3M, 12M, 36M
        if years <= 0.25:
            return "3M"
        elif years <= 1:
            return "12M"
        else:
            return "36M"
    else:
        # Monthly/Quarterly/Annual: 30M, 60M, MAX
        months = years * 12
        if months <= 30:
            return "30M"
        elif months <= 60:
            return "60M"
        else:
            return "MAX"
