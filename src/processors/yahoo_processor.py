"""
Yahoo Finance Data Processor
Clean and transform raw Yahoo Finance data for dashboard use.
Produces individual indicator files, comparison datasets, and summary metrics.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from .series_ops import diff_asof, pct_change_asof

logger = logging.getLogger(__name__)


class YahooProcessor:
    """Processor for Yahoo Finance market data."""

    def __init__(
        self,
        input_dir: str = "data/raw/yahoo",
        output_dir: str = "data/processed/yahoo"
    ):
        """
        Initialize the processor.

        Args:
            input_dir: Directory with raw CSV files
            output_dir: Directory for processed output
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_raw(self, filename: str) -> pd.DataFrame:
        """Load a raw CSV file."""
        filepath = self.input_dir / filename
        if not filepath.exists():
            print(f"  Warning: {filepath} not found")
            return pd.DataFrame()
        df = pd.read_csv(filepath)
        # Parse date column, handling timezone-aware dates
        if 'date' not in df.columns:
            logger.warning(f"Date column not found in {filepath}. Columns: {df.columns.tolist()}")
            return pd.DataFrame()
        try:
            df['date'] = pd.to_datetime(df['date']).dt.normalize()
        except Exception as e:
            logger.error(f"Failed to parse dates: {e}")
            return pd.DataFrame()
        return df

    def _save_processed(self, df: pd.DataFrame, filename: str) -> Path:
        """Save processed DataFrame to CSV."""
        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False, encoding="utf-8")
        print(f"  Saved: {filepath}")
        return filepath

    def process_price_data(
        self,
        df: pd.DataFrame,
        indicator_key: str,
        indicator_name: str
    ) -> pd.DataFrame:
        """
        Process raw price data with returns and technical indicators.

        Args:
            df: Raw price DataFrame (OHLCV)
            indicator_key: Key for naming output files
            indicator_name: Human-readable name

        Returns:
            Processed DataFrame
        """
        if df.empty:
            return df

        df = df.copy()

        # Ensure date column exists and is datetime
        if 'date' not in df.columns:
            print(f"  Warning: No date column in {indicator_key}")
            return df

        # Date already converted in _load_raw(), no need to convert again
        df = df.sort_values('date').reset_index(drop=True)

        # Keep only relevant columns
        cols_to_keep = ['date', 'Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[available_cols].copy()

        # Calculate returns
        if 'Close' in df.columns:
            # Daily returns
            df['daily_return_pct'] = df['Close'].pct_change(fill_method=None) * 100

            # Cumulative returns (from start of data)
            if not df.empty and pd.notna(df['Close'].iloc[0]) and df['Close'].iloc[0] != 0:
                first_close = df['Close'].iloc[0]
                df['cumulative_return_pct'] = ((df['Close'] / first_close) - 1) * 100
            else:
                df['cumulative_return_pct'] = float('nan')

            # Year-to-date returns: change vs the last close of the previous
            # calendar year. The first year in the sample has no prior
            # year-end close and is left empty (NaN) rather than measured from
            # the first available day.
            df['year'] = df['date'].dt.year
            prev_year_end = df.groupby('year')['Close'].last().shift(1)
            base = df['year'].map(prev_year_end)
            df['ytd_return_pct'] = ((df['Close'] / base) - 1) * 100
            df.loc[~(base > 0), 'ytd_return_pct'] = float('nan')

            # Rolling returns
            df['return_1w_pct'] = df['Close'].pct_change(periods=5, fill_method=None) * 100
            df['return_1m_pct'] = df['Close'].pct_change(periods=21, fill_method=None) * 100
            df['return_3m_pct'] = df['Close'].pct_change(periods=63, fill_method=None) * 100
            # 1 year = calendar year (last close on or before the same date a year earlier), not 252 sessions (audit L3)
            df['return_1y_pct'] = pct_change_asof(df, 'Close', pd.DateOffset(years=1))

            # Absolute changes, used for yields: a yield moving from 4,0 % to
            # 4,2 % is +0,2 pp, not "+5 %" (contract v1.1, chg_* fields).
            df['daily_change_abs'] = df['Close'].diff()
            df['change_1w_abs'] = df['Close'].diff(5)
            df['change_1m_abs'] = df['Close'].diff(21)
            df['change_1y_abs'] = diff_asof(df, 'Close', pd.DateOffset(years=1))
            df['ytd_change_abs'] = df['Close'] - base
            df.loc[~(base > 0), 'ytd_change_abs'] = float('nan')

            # Moving averages
            df['sma_20'] = df['Close'].rolling(window=20).mean()
            df['sma_50'] = df['Close'].rolling(window=50).mean()
            df['sma_200'] = df['Close'].rolling(window=200).mean()

            # Volatility (20-day rolling std of returns, annualized)
            df['volatility_20d'] = df['daily_return_pct'].rolling(window=20).std() * np.sqrt(252)

            # Remove helper columns
            df = df.drop(columns=['year'], errors='ignore')

        # Add indicator metadata
        df['indicator'] = indicator_key
        df['name'] = indicator_name

        return df

    def process_all_indicators(self, indicators_config: Dict[str, Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
        """
        Process all Yahoo Finance indicators.

        Args:
            indicators_config: Dictionary of indicator configurations

        Returns:
            Dictionary of processed DataFrames
        """
        results = {}

        for key, config in indicators_config.items():
            filename = f"{key}_raw.csv"
            print(f"Processing {config.get('name', key)}...")

            df = self._load_raw(filename)
            if df.empty:
                print(f"  Skipping {key} - no data")
                continue

            # Process the data
            processed = self.process_price_data(
                df,
                indicator_key=key,
                indicator_name=config.get('name', key)
            )

            if not processed.empty:
                # Save individual file
                output_filename = f"{key}_processed.csv"
                self._save_processed(processed, output_filename)
                results[key] = processed

        return results

    def create_comparison_dataset(
        self,
        indicators: List[str],
        output_name: str,
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Create a wide-format comparison dataset for multiple indicators.

        Args:
            indicators: List of indicator keys to include
            output_name: Name for output file
            normalize: Whether to normalize values to 100 at start

        Returns:
            Wide-format DataFrame for comparison charts
        """
        dfs = []

        for key in indicators:
            filename = f"{key}_processed.csv"
            df = pd.read_csv(self.output_dir / filename)
            if df.empty:
                continue

            df['date'] = pd.to_datetime(df['date'])
            df = df[['date', 'Close', 'indicator']].copy()
            df = df.rename(columns={'Close': key})
            dfs.append(df[['date', key]])

        if not dfs:
            return pd.DataFrame()

        # Merge all on date
        result = dfs[0]
        for df in dfs[1:]:
            result = result.merge(df, on='date', how='outer')

        result = result.sort_values('date').reset_index(drop=True)

        # Normalize to 100 at first common date if requested
        if normalize:
            # Find first date where all indicators have data
            first_valid_idx = result.dropna().index[0] if not result.dropna().empty else 0
            for col in result.columns:
                if col != 'date':
                    first_val = result.loc[first_valid_idx, col]
                    if pd.notna(first_val) and first_val != 0:
                        result[col] = (result[col] / first_val) * 100

        # Remove rows with NaT dates to prevent corruption
        result = result[result['date'].notna()].copy()

        self._save_processed(result, f"{output_name}.csv")
        return result

    def create_summary_table(self, indicators_config: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        Create a summary table with latest values and key metrics for all indicators.

        Args:
            indicators_config: Dictionary of indicator configurations

        Returns:
            Summary DataFrame for dashboard KPI cards
        """
        summary_rows = []

        for key, config in indicators_config.items():
            filename = f"{key}_processed.csv"
            filepath = self.output_dir / filename
            if not filepath.exists():
                continue

            df = pd.read_csv(filepath)
            if df.empty:
                continue

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # Get latest row
            latest = df.iloc[-1]

            row = {
                'indicator': key,
                'name': config.get('name', key),
                'category': config.get('category', ''),
                'geography': config.get('geography', ''),
                'currency': config.get('currency', ''),
                'latest_date': latest['date'],
                'latest_close': latest.get('Close', None),
                'daily_return_pct': latest.get('daily_return_pct', None),
                'return_1w_pct': latest.get('return_1w_pct', None),
                'return_1m_pct': latest.get('return_1m_pct', None),
                'return_3m_pct': latest.get('return_3m_pct', None),
                'return_1y_pct': latest.get('return_1y_pct', None),
                'ytd_return_pct': latest.get('ytd_return_pct', None),
                'volatility_20d': latest.get('volatility_20d', None),
            }
            summary_rows.append(row)

        summary = pd.DataFrame(summary_rows)
        if not summary.empty:
            self._save_processed(summary, "market_summary.csv")

        return summary

    def create_correlation_matrix(
        self,
        indicators: List[str],
        lookback_days: int = 252
    ) -> pd.DataFrame:
        """
        Create correlation matrix of returns for selected indicators.

        Args:
            indicators: List of indicator keys
            lookback_days: Number of days to use for correlation

        Returns:
            Correlation matrix DataFrame
        """
        returns_dfs = []

        for key in indicators:
            filename = f"{key}_processed.csv"
            filepath = self.output_dir / filename
            if not filepath.exists():
                continue

            df = pd.read_csv(filepath)
            if df.empty:
                continue

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').tail(lookback_days)

            if 'daily_return_pct' in df.columns:
                returns_df = df[['date', 'daily_return_pct']].copy()
                returns_df = returns_df.rename(columns={'daily_return_pct': key})
                returns_dfs.append(returns_df)

        if not returns_dfs:
            return pd.DataFrame()

        # Merge all on date
        result = returns_dfs[0]
        for df in returns_dfs[1:]:
            result = result.merge(df, on='date', how='inner')

        # Calculate correlation
        corr_matrix = result.drop(columns=['date']).corr()
        self._save_processed(corr_matrix.reset_index(), "correlation_matrix.csv")

        return corr_matrix

    def resample_to_monthly(self, indicator_key: str) -> pd.DataFrame:
        """
        Resample daily data to monthly for an indicator.

        Args:
            indicator_key: Indicator key

        Returns:
            Monthly resampled DataFrame
        """
        filename = f"{indicator_key}_processed.csv"
        filepath = self.output_dir / filename
        if not filepath.exists():
            return pd.DataFrame()

        df = pd.read_csv(filepath)
        if df.empty:
            return df

        df['date'] = pd.to_datetime(df['date'])
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

        # Recalculate returns for monthly data
        monthly['monthly_return_pct'] = monthly['Close'].pct_change() * 100
        monthly['return_3m_pct'] = monthly['Close'].pct_change(periods=3) * 100
        monthly['return_1y_pct'] = monthly['Close'].pct_change(periods=12) * 100

        output_filename = f"{indicator_key}_monthly.csv"
        self._save_processed(monthly, output_filename)

        return monthly


def run_processing(indicators_config: Dict[str, Dict[str, Any]]) -> None:
    """
    Run the complete processing pipeline.

    Args:
        indicators_config: Dictionary of indicator configurations
    """
    print("\n" + "="*60)
    print("YAHOO FINANCE DATA PROCESSING")
    print("="*60 + "\n")

    processor = YahooProcessor()

    # Process all individual indicators
    print("Processing individual indicators...")
    processor.process_all_indicators(indicators_config)

    # Create summary table
    print("\nCreating summary table...")
    processor.create_summary_table(indicators_config)

    # Create comparison datasets
    print("\nCreating comparison datasets...")

    # Stock indices comparison (normalized)
    stock_indices = ['ibex_35', 'euro_stoxx_50', 'sp_500', 'dax', 'ftse_100']
    processor.create_comparison_dataset(
        indicators=stock_indices,
        output_name="stock_indices_comparison"
    )

    # Commodity comparison and the correlation matrix were dropped on 2026-10-29: oil and
    # EUR/USD now come from official sources and neither output was published.

    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    from ..fetchers.yahoo_indicators import YAHOO_INDICATORS
    run_processing(YAHOO_INDICATORS)
