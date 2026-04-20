"""
INE API Client
Base client for interacting with the Instituto Nacional de Estadística API.
"""

import requests
import pandas as pd
from typing import Optional, Dict, Any, List
import time
import logging

logger = logging.getLogger(__name__)


class INEClient:
    """Client for the INE JSON API."""

    BASE_URL = "https://servicios.ine.es/wstempus/js/ES"

    def __init__(self, delay: float = 0.5):
        """
        Initialize the INE client.

        Args:
            delay: Seconds to wait between requests (be respectful to the API)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "CdE-Dashboard/1.0"
        })

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make a request to the INE API.

        Args:
            endpoint: API endpoint (e.g., 'DATOS_TABLA/30679')
            params: Query parameters

        Returns:
            JSON response data
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            time.sleep(self.delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    def get_table_data(
        self,
        table_id: int,
        nult: Optional[int] = None,
        date_range: Optional[tuple] = None,
        tip: str = None
    ) -> List[Dict]:
        """
        Get data from a specific table.

        Args:
            table_id: INE table identifier
            nult: Number of last observations to retrieve
            date_range: Tuple of (start_date, end_date) in YYYYMMDD format
            tip: Response type (A=friendly, M=metadata, AM=both)

        Returns:
            List of data records
        """
        endpoint = f"DATOS_TABLA/{table_id}"
        params = {}

        if tip:
            params["tip"] = tip
        if nult:
            params["nult"] = nult
        if date_range:
            params["date"] = f"{date_range[0]}:{date_range[1]}"

        # Default to last 10 years if no range specified
        if not nult and not date_range:
            params["date"] = "20150101:20261231"

        return self._request(endpoint, params)

    def get_series_data(
        self,
        series_id: str,
        nult: Optional[int] = None,
        date_range: Optional[tuple] = None
    ) -> List[Dict]:
        """
        Get data from a specific series.

        Args:
            series_id: INE series identifier
            nult: Number of last observations
            date_range: Tuple of (start_date, end_date) in YYYYMMDD format

        Returns:
            List of data records
        """
        endpoint = f"DATOS_SERIE/{series_id}"
        params = {}

        if nult:
            params["nult"] = nult
        if date_range:
            params["date"] = f"{date_range[0]}:{date_range[1]}"

        return self._request(endpoint, params)

    def get_table_series(self, table_id: int) -> List[Dict]:
        """
        Get list of series in a table.

        Args:
            table_id: INE table identifier

        Returns:
            List of series metadata
        """
        endpoint = f"SERIES_TABLA/{table_id}"
        return self._request(endpoint)

    def get_operation_tables(self, operation_code: str) -> List[Dict]:
        """
        Get tables for a statistical operation.

        Args:
            operation_code: Operation code (e.g., 'IPC', 'EPA', 'ICE')

        Returns:
            List of tables
        """
        endpoint = f"TABLAS_OPERACION/{operation_code}"
        return self._request(endpoint)

    def get_available_operations(self) -> List[Dict]:
        """Get list of all available statistical operations."""
        return self._request("OPERACIONES_DISPONIBLES")


def parse_ine_data(raw_data: List[Dict]) -> pd.DataFrame:
    """
    Parse INE API response into a pandas DataFrame.

    Args:
        raw_data: Raw JSON response from INE API

    Returns:
        Parsed DataFrame with columns: date, year, value, series_code, series_name
    """
    records = []

    for item in raw_data:
        # Extract series metadata
        series_code = item.get("COD", "")
        series_name = item.get("Nombre", "").strip()

        # Extract data points
        data_points = item.get("Data", [])

        for point in data_points:
            record = {
                "series_code": series_code,
                "series_name": series_name,
                "date_ms": point.get("Fecha"),
                "year": point.get("Anyo"),
                "value": point.get("Valor"),
            }
            records.append(record)

    df = pd.DataFrame(records)

    # Convert date from milliseconds to datetime
    # INE timestamps are in UTC but represent Spanish local time (Europe/Madrid)
    # We need to convert to Spain timezone to get the correct date
    if "date_ms" in df.columns and not df.empty:
        df["date"] = pd.to_datetime(df["date_ms"], unit="ms", utc=True, errors="coerce")
        # Convert to Spain timezone to get correct local date
        df["date"] = df["date"].dt.tz_convert("Europe/Madrid").dt.tz_localize(None)
        df = df.drop(columns=["date_ms"])

    # Reorder columns
    cols = ["date", "year", "value", "series_code", "series_name"]
    df = df[[c for c in cols if c in df.columns]]

    return df
