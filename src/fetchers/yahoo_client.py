"""
Yahoo Finance API Client
Client for fetching financial market data using the yfinance library.
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for fetching data from Yahoo Finance."""

    def __init__(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Initialize the Yahoo Finance client.

        Args:
            start_date: Start date for data fetching (YYYY-MM-DD format). Defaults to 5 years ago.
            end_date: End date for data fetching (YYYY-MM-DD format). Defaults to today.
        """
        if start_date is None:
            self.start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
        else:
            self.start_date = start_date

        if end_date is None:
            self.end_date = datetime.now().strftime('%Y-%m-%d')
        else:
            self.end_date = end_date

    def get_historical_data(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical price data for a ticker.

        Args:
            ticker: Yahoo Finance ticker symbol (e.g., '^IBEX', 'EURUSD=X')
            start: Start date (YYYY-MM-DD). Uses client default if None.
            end: End date (YYYY-MM-DD). Uses client default if None.
            interval: Data interval ('1d', '1wk', '1mo')

        Returns:
            DataFrame with OHLCV data (Open, High, Low, Close, Volume)
        """
        start = start or self.start_date
        end = end or self.end_date

        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start, end=end, interval=interval)

            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()

            # Reset index to make Date a column
            df = df.reset_index()

            # Standardize column names
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'date'})
            elif 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'date'})

            # Normalize to date-only (YYYY-MM-DD), dropping timezone and time components
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], utc=True).dt.date
                df['date'] = pd.to_datetime(df['date'])

            return df

        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            return pd.DataFrame()

    def get_multiple_tickers(
        self,
        tickers: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple tickers.

        Args:
            tickers: List of Yahoo Finance ticker symbols
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            interval: Data interval

        Returns:
            Dictionary mapping ticker symbols to their DataFrames
        """
        results = {}
        for ticker in tickers:
            logger.info(f"Fetching {ticker}...")
            results[ticker] = self.get_historical_data(ticker, start, end, interval)
        return results

    def get_ticker_info(self, ticker: str) -> Dict:
        """
        Get metadata/info for a ticker.

        Args:
            ticker: Yahoo Finance ticker symbol

        Returns:
            Dictionary with ticker information (name, currency, market, etc.)
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            return ticker_obj.info
        except Exception as e:
            logger.error(f"Error getting info for {ticker}: {e}")
            return {}

    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get the current/latest price for a ticker.

        Args:
            ticker: Yahoo Finance ticker symbol

        Returns:
            Current price or None if unavailable
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            # Try different price fields
            for field in ['regularMarketPrice', 'currentPrice', 'previousClose']:
                if field in info and info[field] is not None:
                    return info[field]
            return None
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return None


def calculate_returns(df: pd.DataFrame, price_col: str = 'Close') -> pd.DataFrame:
    """
    Calculate daily and cumulative returns from price data.

    Args:
        df: DataFrame with price data
        price_col: Name of the price column to use

    Returns:
        DataFrame with additional return columns
    """
    if df.empty or price_col not in df.columns:
        return df

    df = df.copy()

    # Daily returns (percentage change)
    df['daily_return'] = df[price_col].pct_change() * 100

    # Cumulative returns from start
    if df.empty:
        return df
    first_price = df[price_col].iloc[0]
    if pd.isna(first_price) or first_price == 0:
        df['cumulative_return'] = float('nan')
        return df
    df['cumulative_return'] = ((df[price_col] / first_price) - 1) * 100

    return df


def calculate_volatility(df: pd.DataFrame, window: int = 20, price_col: str = 'Close') -> pd.DataFrame:
    """
    Calculate rolling volatility (standard deviation of returns).

    Args:
        df: DataFrame with price data
        window: Rolling window size (default: 20 days)
        price_col: Name of the price column

    Returns:
        DataFrame with volatility column
    """
    if df.empty or price_col not in df.columns:
        return df

    df = df.copy()

    # Calculate daily returns if not present
    if 'daily_return' not in df.columns:
        df['daily_return'] = df[price_col].pct_change() * 100

    # Rolling volatility (annualized)
    df[f'volatility_{window}d'] = df['daily_return'].rolling(window=window).std() * (252 ** 0.5)

    return df


def calculate_moving_averages(
    df: pd.DataFrame,
    windows: List[int] = [20, 50, 200],
    price_col: str = 'Close'
) -> pd.DataFrame:
    """
    Calculate simple moving averages.

    Args:
        df: DataFrame with price data
        windows: List of window sizes
        price_col: Name of the price column

    Returns:
        DataFrame with moving average columns
    """
    if df.empty or price_col not in df.columns:
        return df

    df = df.copy()

    for window in windows:
        df[f'sma_{window}'] = df[price_col].rolling(window=window).mean()

    return df


def resample_to_monthly(df: pd.DataFrame, price_col: str = 'Close') -> pd.DataFrame:
    """
    Resample daily data to monthly (end of month).

    Args:
        df: DataFrame with daily price data
        price_col: Name of the price column

    Returns:
        DataFrame with monthly data
    """
    if df.empty:
        return df

    df = df.copy()

    # Ensure date is the index
    if 'date' in df.columns:
        df = df.set_index('date')

    # Resample to month-end
    monthly = df.resample('ME').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()

    monthly = monthly.reset_index()
    monthly = monthly.rename(columns={'index': 'date'})

    return monthly
