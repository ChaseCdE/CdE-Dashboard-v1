"""
Banco de Espana Data Processor
Clean and transform raw BdE data for dashboard use.
Produces individual indicator files, comparison datasets, and summary metrics.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .series_ops import asof_values

# Configure logging
logger = logging.getLogger(__name__)


def _check_time_gaps(df: pd.DataFrame, expected_freq: str, indicator_name: str):
    """Warn if time series has unexpected gaps that could affect YoY calculations."""
    if df.empty or 'date' not in df.columns or len(df) < 2:
        return
    dates = df['date'].sort_values()
    diffs = dates.diff().dropna()
    if expected_freq == "Q":
        max_expected = pd.Timedelta(days=120)  # ~4 months
    elif expected_freq == "M":
        max_expected = pd.Timedelta(days=45)   # ~1.5 months
    elif expected_freq == "A":
        max_expected = pd.Timedelta(days=400)  # ~13 months
    else:
        return
    gaps = diffs[diffs > max_expected]
    if len(gaps) > 0:
        logger.warning(
            f"{indicator_name}: {len(gaps)} gap(s) detected in time series. "
            f"Largest gap: {gaps.max().days} days. YoY calculations may be affected."
        )


def _to_local_naive(series: pd.Series) -> pd.Series:
    """
    Parse dates to naive local (Europe/Madrid) calendar dates at midnight.

    Raw files written before the client fix carry timestamps such as
    '2026-10-26 09:15:00+00:00'. They are converted to Madrid time and the
    time zone is dropped, so no observation can shift to another day.
    """
    parsed = pd.to_datetime(series, utc=True)
    return parsed.dt.tz_convert("Europe/Madrid").dt.tz_localize(None).dt.normalize()


_PERIOD_FREQ = {"M": "MS", "Q": "QS", "A": "YS"}


class BdeProcessor:
    """Processor for Banco de Espana economic data."""

    def __init__(
        self,
        input_dir: str = "data/raw/bde",
        output_dir: str = "data/processed/bde"
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
            logger.warning(f"{filepath} not found")
            print(f"  Warning: {filepath} not found")
            return pd.DataFrame()
        df = pd.read_csv(filepath)
        if 'date' in df.columns:
            df['date'] = _to_local_naive(df['date'])
        return df

    def _save_processed(self, df: pd.DataFrame, filename: str) -> Path:
        """Save processed DataFrame to CSV."""
        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Saved: {filepath}")
        print(f"  Saved: {filepath}")
        return filepath

    def standardize_dates(self, df: pd.DataFrame, frequency: str = "M") -> pd.DataFrame:
        """
        Standardize the date column and align it to the series frequency.

        Dates are naive local dates. Monthly, quarterly and annual series are
        put on the first day of the period and reindexed to the complete
        period range, so a missing period appears as a row with NaN value.
        Growth rates computed afterwards by shifting therefore never span a
        gap (they are NaN there). Call `_drop_filler` once all calculations
        are done to remove these placeholder rows.

        Args:
            df: DataFrame with date column
            frequency: Expected frequency (D, M, Q, A)

        Returns:
            DataFrame with standardized dates
        """
        if df.empty or 'date' not in df.columns:
            return df

        df = df.copy()
        df['date'] = _to_local_naive(df['date'])
        df = df[df['date'].notna()].sort_values('date')

        if frequency == "M":
            df['date'] = df['date'].dt.to_period('M').dt.to_timestamp()
        elif frequency == "Q":
            df['date'] = df['date'].dt.to_period('Q').dt.to_timestamp()
        elif frequency == "A":
            df['date'] = df['date'].dt.to_period('Y').dt.to_timestamp()

        # One observation per period/day (keep the latest published)
        df = df.drop_duplicates('date', keep='last')

        if frequency in _PERIOD_FREQ and len(df) > 1:
            full = pd.date_range(df['date'].min(), df['date'].max(), freq=_PERIOD_FREQ[frequency])
            df = df.set_index('date').reindex(full).rename_axis('date').reset_index()

        df = df.reset_index(drop=True)
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        if frequency == "Q":
            df['quarter'] = df['date'].dt.quarter

        return df

    @staticmethod
    def _drop_filler(df: pd.DataFrame) -> pd.DataFrame:
        """Remove placeholder rows (NaN value) added by standardize_dates."""
        if 'value' not in df.columns:
            return df
        return df[df['value'].notna()].reset_index(drop=True)

    @staticmethod
    def _lookup_asof(df: pd.DataFrame, keys: pd.Series, value_col: str = "value") -> pd.Series:
        """Value of the last observation dated on or before each key date (NaN if none)."""
        return asof_values(df, keys, value_col)

    def calculate_changes(
        self,
        df: pd.DataFrame,
        value_col: str = "value",
        frequency: str = "M"
    ) -> pd.DataFrame:
        """
        Calculate period-over-period and year-over-year changes.

        Args:
            df: DataFrame with value column
            value_col: Name of the value column
            frequency: Data frequency (D, M, Q, A)

        Returns:
            DataFrame with additional change columns
        """
        if df.empty or value_col not in df.columns:
            return df

        df = df.copy()
        df = df.sort_values('date').reset_index(drop=True)

        # Period-over-period change. fill_method=None: a missing observation
        # yields NaN instead of being forward-filled. Monthly/quarterly/annual
        # series were reindexed to a complete calendar in standardize_dates,
        # so shifts never span a gap.
        df['change_pct'] = df[value_col].pct_change(fill_method=None) * 100
        df['change_abs'] = df[value_col].diff()
        df['change_abs_k'] = df['change_abs'] / 1000  # thousands, for person counts

        if frequency == "D":
            # Daily data has no fixed number of observations per year: compare
            # with the last observation on or before the same date a year ago.
            prev = self._lookup_asof(df, df['date'] - pd.DateOffset(years=1), value_col)
            df['yoy_change_pct'] = (df[value_col] / prev - 1) * 100
            df['yoy_change_abs'] = df[value_col] - prev
            # Changes over the last 30 days and since the end of the previous
            # year, in the units of the series (pp for rates).
            p30 = self._lookup_asof(df, df['date'] - pd.Timedelta(days=30), value_col)
            pytd = self._lookup_asof(df, pd.to_datetime(df['date'].dt.year.astype(str) + "-01-01") - pd.Timedelta(days=1), value_col)
            df['change_30d_abs'] = df[value_col] - p30
            df['change_ytd_abs'] = df[value_col] - pytd
            return df

        periods_per_year = {"M": 12, "Q": 4}.get(frequency, 1)
        df['yoy_change_pct'] = df[value_col].pct_change(periods=periods_per_year, fill_method=None) * 100
        df['yoy_change_abs'] = df[value_col].diff(periods=periods_per_year)

        return df

    def calculate_moving_averages(
        self,
        df: pd.DataFrame,
        value_col: str = "value",
        windows: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Calculate moving averages.

        Args:
            df: DataFrame with value column
            value_col: Name of the value column
            windows: List of window sizes (defaults vary by data type)

        Returns:
            DataFrame with moving average columns
        """
        if df.empty or value_col not in df.columns:
            return df

        df = df.copy()

        if windows is None:
            windows = [3, 6, 12]  # Default: 3, 6, 12 periods

        for window in windows:
            if len(df) >= window:
                df[f'ma_{window}'] = df[value_col].rolling(window=window).mean()

        return df

    def process_interest_rate(
        self,
        df: pd.DataFrame,
        indicator_key: str,
        indicator_name: str
    ) -> pd.DataFrame:
        """
        Process interest rate data (EURIBOR, bond yields, lending rates).

        Args:
            df: Raw interest rate DataFrame
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
            logger.warning(f"No date column in {indicator_key}")
            return df

        # Get frequency from data
        frequency = df.get('frequency', pd.Series(['M'])).iloc[0]

        # Standardize dates
        df = self.standardize_dates(df, frequency)

        # Check for time gaps
        _check_time_gaps(df, frequency if frequency in ['D', 'M', 'Q', 'A'] else 'M', indicator_name)

        # Keep only relevant columns
        cols_to_keep = ['date', 'value', 'year', 'month']
        if 'quarter' in df.columns:
            cols_to_keep.append('quarter')
        available_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[available_cols].copy()

        # Calculate changes
        df = self.calculate_changes(df, 'value', frequency)

        # Calculate moving averages
        if frequency in ['D']:
            windows = [5, 20, 60]  # 1 week, 1 month, 3 months
        elif frequency == 'M':
            windows = [3, 6, 12]
        else:
            windows = [2, 4]

        df = self.calculate_moving_averages(df, 'value', windows)

        # Add spread from latest to historical average
        if len(df) > 0:
            historical_mean = df['value'].mean()
            df['spread_to_avg'] = df['value'] - historical_mean

        # Remove placeholder rows for missing periods (added by standardize_dates)
        df = self._drop_filler(df)

        # Add indicator metadata
        df['indicator'] = indicator_key
        df['name'] = indicator_name

        return df

    def process_credit_data(
        self,
        df: pd.DataFrame,
        indicator_key: str,
        indicator_name: str
    ) -> pd.DataFrame:
        """
        Process credit/lending volume data.

        Args:
            df: Raw credit data DataFrame
            indicator_key: Key for naming output files
            indicator_name: Human-readable name

        Returns:
            Processed DataFrame
        """
        if df.empty:
            return df

        df = df.copy()

        if 'date' not in df.columns:
            logger.warning(f"No date column in {indicator_key}")
            return df

        # Get frequency
        frequency = df.get('frequency', pd.Series(['M'])).iloc[0]

        # Standardize dates
        df = self.standardize_dates(df, frequency)

        # Check for time gaps
        _check_time_gaps(df, frequency if frequency in ['D', 'M', 'Q', 'A'] else 'M', indicator_name)

        # Keep only relevant columns
        cols_to_keep = ['date', 'value', 'year', 'month']
        available_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[available_cols].copy()

        # Calculate changes
        df = self.calculate_changes(df, 'value', frequency)

        # Calculate moving averages
        df = self.calculate_moving_averages(df, 'value', [3, 6, 12])

        # Calculate cumulative growth from start (find first non-zero value as base)
        if len(df) > 0:
            # Find first non-zero value as the base
            non_zero_mask = df['value'] != 0
            if non_zero_mask.any():
                first_non_zero_idx = non_zero_mask.idxmax()
                first_value = df.loc[first_non_zero_idx, 'value']
                df['cumulative_growth_pct'] = ((df['value'] / first_value) - 1) * 100
            else:
                logger.warning(f"All values are zero for {indicator_key}")
                df['cumulative_growth_pct'] = None

        # Remove placeholder rows for missing periods (added by standardize_dates)
        df = self._drop_filler(df)

        # Add indicator metadata
        df['indicator'] = indicator_key
        df['name'] = indicator_name

        return df

    def process_ratio_data(
        self,
        df: pd.DataFrame,
        indicator_key: str,
        indicator_name: str
    ) -> pd.DataFrame:
        """
        Process ratio data (debt-to-GDP, etc.).

        Args:
            df: Raw ratio data DataFrame
            indicator_key: Key for naming output files
            indicator_name: Human-readable name

        Returns:
            Processed DataFrame
        """
        if df.empty:
            return df

        df = df.copy()

        if 'date' not in df.columns:
            logger.warning(f"No date column in {indicator_key}")
            return df

        # Get frequency (usually quarterly)
        frequency = df.get('frequency', pd.Series(['Q'])).iloc[0]

        # Standardize dates
        df = self.standardize_dates(df, frequency)

        # Keep only relevant columns
        cols_to_keep = ['date', 'value', 'year', 'month', 'quarter']
        available_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[available_cols].copy()

        # Calculate changes
        df = self.calculate_changes(df, 'value', frequency)

        # Calculate moving averages
        df = self.calculate_moving_averages(df, 'value', [2, 4, 8])

        # Calculate distance from historical peak and trough
        if len(df) > 0:
            historical_max = df['value'].max()
            historical_min = df['value'].min()
            df['distance_from_peak'] = df['value'] - historical_max
            df['distance_from_trough'] = df['value'] - historical_min

        # Remove placeholder rows for missing periods (added by standardize_dates)
        df = self._drop_filler(df)

        # Add indicator metadata
        df['indicator'] = indicator_key
        df['name'] = indicator_name

        return df

    def process_balance_data(
        self,
        df: pd.DataFrame,
        indicator_key: str,
        indicator_name: str
    ) -> pd.DataFrame:
        """
        Process balance of payments data (current account, tourism receipts).

        Args:
            df: Raw balance data DataFrame
            indicator_key: Key for naming output files
            indicator_name: Human-readable name

        Returns:
            Processed DataFrame
        """
        if df.empty:
            return df

        df = df.copy()

        if 'date' not in df.columns:
            logger.warning(f"No date column in {indicator_key}")
            return df

        # Get frequency
        frequency = df.get('frequency', pd.Series(['M'])).iloc[0]

        # Standardize dates
        df = self.standardize_dates(df, frequency)

        # Keep only relevant columns
        cols_to_keep = ['date', 'value', 'year', 'month']
        available_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[available_cols].copy()

        # Calculate changes
        df = self.calculate_changes(df, 'value', frequency)

        # Calculate rolling sums (12-month cumulative)
        if len(df) >= 12:
            df['rolling_12m_sum'] = df['value'].rolling(window=12).sum()

        # Calculate moving averages
        df = self.calculate_moving_averages(df, 'value', [3, 6, 12])

        # Remove placeholder rows for missing periods (added by standardize_dates)
        df = self._drop_filler(df)

        # Add indicator metadata
        df['indicator'] = indicator_key
        df['name'] = indicator_name

        return df

    def _apply_published_growth(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Audit M3: use BdE's published transaction-based growth rate as the year-on-year change
        of a credit stock. The change of the stock itself (which includes reclassifications,
        write-offs and securitisations) is kept as `yoy_stock_change_pct`.
        """
        growth_key = config.get("growth_key")
        if not growth_key or df.empty:
            return df
        raw = self._load_raw(f"{growth_key}_raw.csv")
        if raw.empty:
            raise ValueError(f"BdE growth series {growth_key} is missing; cannot publish the year-on-year rate of {config.get('name')}")
        raw = raw.assign(date=pd.to_datetime(raw["date"])).drop_duplicates("date", keep="last")
        rate = pd.Series(raw["value"].values, index=raw["date"].values)
        df = df.copy()
        df["yoy_stock_change_pct"] = df["yoy_change_pct"]
        df["yoy_change_pct"] = df["date"].map(rate)
        last = df["date"].max()
        if pd.isna(df.loc[df["date"] == last, "yoy_change_pct"]).any():
            logger.error(f"BdE growth series {growth_key} has no value for {last:%Y-%m}; error in year-on-year rate")
        return df

    def process_indicator(
        self,
        key: str,
        indicators_config: Dict[str, Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Process a single indicator based on its category.

        Args:
            key: Indicator key
            indicators_config: Dictionary of indicator configurations

        Returns:
            Processed DataFrame
        """
        if key not in indicators_config:
            logger.warning(f"Unknown indicator: {key}")
            return pd.DataFrame()

        config = indicators_config[key]
        filename = f"{key}_raw.csv"

        print(f"Processing {config.get('name', key)}...")

        df = self._load_raw(filename)
        if df.empty:
            print(f"  Skipping {key} - no data")
            return df

        category = config.get("category", "")
        name = config.get("name", key)

        # Unit conversion (e.g. thousands of EUR to millions of EUR)
        divisor = config.get("value_divisor")
        if divisor and "value" in df.columns:
            df["value"] = df["value"] / divisor

        # Route to appropriate processor
        if category == "interest_rates":
            processed = self.process_interest_rate(df, key, name)
        elif category == "credit_banking":
            if "rate" in key.lower():
                processed = self.process_interest_rate(df, key, name)
            else:
                processed = self.process_credit_data(df, key, name)
                processed = self._apply_published_growth(processed, config)
        elif category == "credit_growth":
            # Growth rate in %: value and differences in pp
            processed = self.process_interest_rate(df, key, name)
        elif category == "debt_ratios":
            processed = self.process_ratio_data(df, key, name)
        elif category in ("external_sector", "new_business"):
            # Monthly flows: value, rolling 12m sum (NaN unless 12 consecutive months), yoy of the value
            processed = self.process_balance_data(df, key, name)
        elif category == "financial_stability":
            # Ratio in %: value and differences in pp (change_abs, yoy_change_abs)
            processed = self.process_interest_rate(df, key, name)
        elif category in ("labour_market", "public_finances"):
            # Stocks: value, mom and yoy as % changes
            processed = self.process_credit_data(df, key, name)
        else:
            # Generic processing
            processed = self.process_credit_data(df, key, name)

        if not processed.empty:
            output_filename = f"{key}_processed.csv"
            self._save_processed(processed, output_filename)

        return processed

    def process_all(
        self,
        indicators_config: Dict[str, Dict[str, Any]]
    ) -> Dict[str, pd.DataFrame]:
        """
        Process all BdE indicators.

        Args:
            indicators_config: Dictionary of indicator configurations

        Returns:
            Dictionary of processed DataFrames
        """
        results = {}

        for key in indicators_config:
            processed = self.process_indicator(key, indicators_config)
            if not processed.empty:
                results[key] = processed

        return results

    def create_summary_table(
        self,
        indicators_config: Dict[str, Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Create a summary table with latest values and key metrics.

        Args:
            indicators_config: Dictionary of indicator configurations

        Returns:
            Summary DataFrame
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
                'unit': config.get('unit', ''),
                'frequency': config.get('frequency', ''),
                'latest_date': latest['date'],
                'latest_value': latest.get('value', None),
                'change_pct': latest.get('change_pct', None),
                'yoy_change_pct': latest.get('yoy_change_pct', None),
                'historical_mean': df['value'].mean() if 'value' in df.columns else None,
                'historical_min': df['value'].min() if 'value' in df.columns else None,
                'historical_max': df['value'].max() if 'value' in df.columns else None,
            }
            summary_rows.append(row)

        summary = pd.DataFrame(summary_rows)
        if not summary.empty:
            self._save_processed(summary, "bde_summary.csv")

        return summary

    def create_comparison_dataset(
        self,
        indicators: List[str],
        output_name: str,
        normalize: bool = False
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
            filepath = self.output_dir / filename
            if not filepath.exists():
                continue

            df = pd.read_csv(filepath)
            if df.empty:
                continue

            df['date'] = pd.to_datetime(df['date'])
            df = df[['date', 'value']].copy()
            df = df.rename(columns={'value': key})
            dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        # Merge all on date
        result = dfs[0]
        for df in dfs[1:]:
            result = result.merge(df, on='date', how='outer')

        result = result.sort_values('date').reset_index(drop=True)

        # Normalize to 100 at first common date if requested
        if normalize:
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

    def create_yield_curve(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Create yield curve data for Spanish government bonds.

        Args:
            date: Optional specific date (defaults to latest available)

        Returns:
            DataFrame with maturities and yields
        """
        # Define yield curve points
        yield_curve_indicators = [
            ("spain_tbill_3m", 0.25),   # 3 months
            ("spain_tbill_6m", 0.5),    # 6 months
            ("spain_tbill_1y", 1.0),    # 1 year
            # spain_2y_bond is excluded: the BdE series is "bonds with more than 2 years to
            # maturity" (an average over all longer maturities), not a 2-year yield, and it
            # produced a false kink between 1 and 3 years.
            ("spain_3y_bond", 3.0),     # 3 years
            ("spain_5y_bond", 5.0),     # 5 years
            ("spain_10y_bond", 10.0),   # 10 years
            ("spain_15y_bond", 15.0),   # 15 years
        ]

        frames = {}
        for key, maturity in yield_curve_indicators:
            filepath = self.output_dir / f"{key}_processed.csv"
            if not filepath.exists():
                continue
            df = pd.read_csv(filepath, parse_dates=['date'])
            df = df.dropna(subset=['date', 'value']).sort_values('date')
            if not df.empty:
                frames[key] = (maturity, df)

        if not frames:
            return pd.DataFrame()

        # One coherent snapshot: every maturity at the same date. Default is
        # the most recent date for which all maturities have an observation
        # (the earliest of the series' last dates); each maturity uses its last
        # observation on or before that date.
        if date:
            target = pd.to_datetime(date)
        else:
            target = min(df['date'].max() for _, df in frames.values())

        curve_data = []
        for key, (maturity, df) in frames.items():
            sub = df[df['date'] <= target]
            if sub.empty:
                continue
            row = sub.iloc[-1]
            curve_data.append({
                'maturity_years': maturity,
                'yield': row['value'],
                'date': row['date'],
                'indicator': key
            })

        curve_df = pd.DataFrame(curve_data)
        if not curve_df.empty:
            # Remove rows with NaT dates to prevent corruption
            curve_df = curve_df[curve_df['date'].notna()].copy()
            self._save_processed(curve_df, "yield_curve.csv")

        return curve_df

    def create_euribor_comparison(self) -> pd.DataFrame:
        """
        Create comparison dataset for EURIBOR maturities.

        Returns:
            DataFrame with all EURIBOR maturities
        """
        euribor_indicators = [
            "ester_daily",
            "euribor_1w_daily",
            "euribor_1m_daily",
            "euribor_3m_daily",
            "euribor_6m_daily",
            "euribor_12m_daily"
        ]

        return self.create_comparison_dataset(
            indicators=euribor_indicators,
            output_name="euribor_comparison",
            normalize=False
        )

    def create_lending_rates_comparison(self) -> pd.DataFrame:
        """
        Create comparison dataset for bank lending rates.

        Returns:
            DataFrame with lending rate comparison
        """
        lending_indicators = [
            "mortgage_rate",
            "consumer_credit_rate",
            "corporate_lending_rate",
            "household_deposit_rate"
        ]

        return self.create_comparison_dataset(
            indicators=lending_indicators,
            output_name="lending_rates_comparison",
            normalize=False
        )

    def create_spread_datasets(
        self,
        derived_config: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Build the sovereign spreads (Spain minus a peer) from processed series.

        Both inputs are monthly BdE "Economia internacional" series (Maastricht
        long-term yield, monthly average). The spread is computed on the dates
        both series share (inner join, no forward fill), in percentage points,
        and rounded to the 2 decimals the sources are published with. Changes
        are differences against the previous month (`change_abs`) and the
        same month one year earlier (`yoy_change_abs`) on a complete monthly
        calendar, so a missing month yields NaN instead of a change across the gap.
        """
        if derived_config is None:
            from ..fetchers.bde_indicators import BDE_DERIVED
            derived_config = BDE_DERIVED

        results = {}
        for key, cfg in derived_config.items():
            print(f"Creating spread {key}...")
            frames = {}
            for role in ("minuend", "subtrahend"):
                fp = self.output_dir / f"{cfg[role]}_processed.csv"
                if not fp.exists():
                    logger.warning(f"{fp} not found, skipping {key}")
                    print(f"  Skipping {key} - {fp.name} missing")
                    break
                d = pd.read_csv(fp, usecols=['date', 'value'])
                d['date'] = pd.to_datetime(d['date'])
                frames[role] = d.set_index('date')['value']
            else:
                both = pd.concat([frames['minuend'], frames['subtrahend']], axis=1, keys=['a', 'b']).dropna()
                if both.empty:
                    continue
                spread = (both['a'] - both['b']).round(2)
                full = pd.date_range(spread.index.min(), spread.index.max(), freq='MS')
                spread = spread.reindex(full)
                df = pd.DataFrame({'date': full, 'value': spread.values})
                df['change_abs'] = df['value'].diff().round(2)
                df['yoy_change_abs'] = df['value'].diff(12).round(2)
                df = self._drop_filler(df)
                df['year'] = df['date'].dt.year
                df['month'] = df['date'].dt.month
                df['indicator'] = key
                df['name'] = key
                self._save_processed(df, f"{key}_processed.csv")
                results[key] = df
        return results

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
        monthly = df[['value']].resample('ME').agg({
            'value': 'last'  # Use last value of month
        }).dropna()

        monthly = monthly.reset_index()

        # Recalculate changes
        monthly['change_pct'] = monthly['value'].pct_change(fill_method=None) * 100
        monthly['yoy_change_pct'] = monthly['value'].pct_change(periods=12, fill_method=None) * 100

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
    print("BANCO DE ESPANA DATA PROCESSING")
    print("="*60 + "\n")

    processor = BdeProcessor()

    # Process all individual indicators
    print("Processing individual indicators...")
    processor.process_all(indicators_config)

    # Create summary table
    print("\nCreating summary table...")
    processor.create_summary_table(indicators_config)

    # Create comparison datasets
    print("\nCreating comparison datasets...")

    # EURIBOR comparison
    processor.create_euribor_comparison()

    # Lending rates comparison
    processor.create_lending_rates_comparison()

    # Sovereign spreads (Spain minus Germany / Italy)
    print("\nCreating sovereign spreads...")
    processor.create_spread_datasets()

    # Yield curve
    print("\nCreating yield curve...")
    processor.create_yield_curve()

    # Debt ratios comparison
    debt_indicators = ['household_debt_gdp', 'nfc_debt_gdp']
    processor.create_comparison_dataset(
        indicators=debt_indicators,
        output_name="debt_ratios_comparison"
    )

    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    from ..fetchers.bde_indicators import BDE_INDICATORS
    run_processing(BDE_INDICATORS)
