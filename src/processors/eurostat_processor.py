"""
Eurostat Data Processor
Clean and transform raw Eurostat data for dashboard use.
Produces separate files for Spain and EU27 data, and comparison datasets.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
import logging

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


class EurostatProcessor:
    """Processor for Eurostat economic indicators."""

    GEO_SPAIN = "ES"
    GEO_EU27 = "EU27_2020"

    def __init__(
        self,
        input_dir: str = "data/raw/eurostat",
        output_dir: str = "data/processed/eurostat"
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
        """Load a raw CSV file. Returns empty DataFrame if missing or empty."""
        filepath = self.input_dir / filename
        if not filepath.exists():
            print(f"  Warning: {filepath} not found")
            return pd.DataFrame()
        try:
            df = pd.read_csv(filepath)
        except pd.errors.EmptyDataError:
            print(f"  Warning: {filepath} is empty (no data)")
            return pd.DataFrame()
        if df.empty:
            print(f"  Warning: {filepath} has no rows")
            return pd.DataFrame()
        # Parse date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        # Eurostat publishes placeholder periods with no value (e.g. the latest
        # month for one geography). Drop them: a missing observation must not be
        # carried forward into growth rates nor extend the series.
        if 'value' in df.columns:
            df = df.dropna(subset=['value']).reset_index(drop=True)
        return df

    def _save_processed(self, df: pd.DataFrame, filename: str) -> Path:
        """Save processed DataFrame to CSV. Preserves existing file if df is empty."""
        filepath = self.output_dir / filename
        if df.empty and filepath.exists():
            print(f"  Skipping save of empty data to {filepath} (preserving existing)")
            return filepath
        df.to_csv(filepath, index=False, encoding="utf-8")
        print(f"  Saved: {filepath}")
        return filepath

    def _calculate_yoy_change(
        self,
        df: pd.DataFrame,
        value_col: str = "value",
        periods: int = 4,
        geo_col: str = "geo",
        kind: str = "pct"
    ) -> pd.DataFrame:
        """
        Calculate the change versus the same period one year earlier, by geography.

        The comparison is by calendar date (value at t vs value at t - 12 months),
        not by row position, so a missing period yields NaN instead of silently
        comparing against a different period. Nothing is forward-filled.

        Args:
            df: DataFrame with date and value columns
            value_col: Name of the value column
            periods: Kept for compatibility (periods per year: 4 or 12); the
                lag is always one calendar year
            geo_col: Name of geography column
            kind: "pct" = percent change (levels and indices);
                  "diff" = difference in percentage points (rates, balances)

        Returns:
            DataFrame with added 'yoy_change' column
        """
        df = df.sort_values([geo_col, "date"]).reset_index(drop=True).copy()
        parts = []
        for _, g in df.groupby(geo_col, sort=False):
            s = g.set_index("date")[value_col]
            prior = s.copy()
            prior.index = prior.index + pd.DateOffset(years=1)
            prior = prior[~prior.index.duplicated(keep="last")].reindex(s.index)
            if kind == "diff":
                yoy = s - prior
            else:
                yoy = (s / prior - 1) * 100
            parts.append(pd.Series(yoy.values, index=g.index))
        df["yoy_change"] = pd.concat(parts) if parts else float("nan")
        return df

    def _split_by_geography(
        self,
        df: pd.DataFrame,
        value_col: str,
        indicator_name: str,
        geo_col: str = "geo"
    ) -> Dict[str, pd.DataFrame]:
        """
        Split data by geography and save separate files.

        Args:
            df: Processed DataFrame
            value_col: Name of the value column
            indicator_name: Base name for output files
            geo_col: Name of geography column

        Returns:
            Dictionary with geo codes as keys and DataFrames as values
        """
        results = {}

        for geo in df[geo_col].unique():
            geo_df = df[df[geo_col] == geo].copy()
            geo_df = geo_df.drop(columns=[geo_col], errors='ignore')
            geo_df = geo_df.sort_values("date").reset_index(drop=True)

            # Create filename with geography suffix
            geo_suffix = geo.lower().replace("_", "").replace("27", "27_")
            if geo == self.GEO_SPAIN:
                filename = f"{indicator_name}_spain.csv"
            elif geo == self.GEO_EU27:
                filename = f"{indicator_name}_eu27.csv"
            else:
                filename = f"{indicator_name}_{geo_suffix}.csv"

            self._save_processed(geo_df, filename)
            results[geo] = geo_df

        return results

    def _create_comparison_dataset(
        self,
        df: pd.DataFrame,
        value_col: str,
        indicator_name: str,
        geo_col: str = "geo"
    ) -> pd.DataFrame:
        """
        Create a wide-format comparison dataset with Spain and EU27 columns.

        Args:
            df: Processed DataFrame
            value_col: Name of the value column
            indicator_name: Name for output file

        Returns:
            Wide-format DataFrame with Spain and EU27 columns
        """
        # Determine which columns to pivot
        pivot_values = [value_col]
        if "yoy_change" in df.columns:
            pivot_values.append("yoy_change")

        # Pivot to wide format
        pivot_df = df.pivot_table(
            index="date",
            columns=geo_col,
            values=pivot_values,
            aggfunc="first"
        ).reset_index()

        # Flatten column names
        pivot_df.columns = [
            f"{col[0]}_{col[1]}".lower().replace(self.GEO_EU27.lower(), "eu27")
            if isinstance(col, tuple) and col[1] else col[0]
            for col in pivot_df.columns
        ]

        # Clean up column names
        pivot_df.columns = [
            col.replace("eu27_2020", "eu27").replace("__", "_").rstrip("_")
            for col in pivot_df.columns
        ]

        self._save_processed(pivot_df, f"{indicator_name}_comparison.csv")
        return pivot_df

    # === Economic Activity Indicators ===

    def process_gdp_growth(self) -> Dict[str, pd.DataFrame]:
        """Process GDP Growth data (QoQ % change)."""
        print("Processing GDP Growth...")
        df = self._load_raw("gdp_growth_raw.csv")

        if df.empty:
            return {}

        # Rename value column
        df = df.rename(columns={"value": "gdp_growth_qoq"})

        # Check for time gaps before YoY calculation
        _check_time_gaps(df, "Q", "GDP Growth")

        # No yoy_change: the input is already a quarter-on-quarter growth rate and
        # the difference between two such rates is not an economic quantity.

        # Select relevant columns
        cols = ["geo", "date", "gdp_growth_qoq", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        # Create comparison dataset
        self._create_comparison_dataset(df, "gdp_growth_qoq", "gdp_growth")

        # Split by geography
        return self._split_by_geography(df, "gdp_growth_qoq", "gdp_growth")

    def process_industrial_production(self) -> Dict[str, pd.DataFrame]:
        """Process Industrial Production Index."""
        print("Processing Industrial Production...")
        df = self._load_raw("industrial_production_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "ipi_index"})

        # Check for time gaps before YoY calculation
        _check_time_gaps(df, "M", "Industrial Production")

        df = self._calculate_yoy_change(df, "ipi_index", periods=12)

        cols = ["geo", "date", "ipi_index", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "ipi_index", "industrial_production")
        return self._split_by_geography(df, "ipi_index", "industrial_production")

    def process_economic_sentiment(self) -> Dict[str, pd.DataFrame]:
        """Process Economic Sentiment Indicator."""
        print("Processing Economic Sentiment...")
        df = self._load_raw("economic_sentiment_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "esi"})
        df = self._calculate_yoy_change(df, "esi", periods=12)

        cols = ["geo", "date", "esi", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "esi", "economic_sentiment")
        return self._split_by_geography(df, "esi", "economic_sentiment")

    def process_gdp_index_comparison(self) -> pd.DataFrame:
        """
        Process GDP index comparison (ES, FR, IT, DE, EU27).
        Rebases each country's GDP to 2019Q1 = 100.
        """
        print("Processing GDP Index Comparison...")
        df = self._load_raw("gdp_index_comparison_raw.csv")

        if df.empty:
            return pd.DataFrame()

        df = df.rename(columns={"value": "gdp_level"})
        df = df.sort_values(["geo", "date"]).reset_index(drop=True)

        # Rebase each country to 2019Q1 = 100
        geo_mapping = {
            'ES': 'spain',
            'FR': 'france',
            'IT': 'italy',
            'DE': 'germany',
            'EU27_2020': 'eu27'
        }

        result_dfs = []
        for geo_code, geo_name in geo_mapping.items():
            geo_df = df[df["geo"] == geo_code].copy()
            if geo_df.empty:
                continue

            # Find 2019Q1 value for rebasing
            base_mask = (geo_df["date"].dt.year == 2019) & (geo_df["date"].dt.quarter == 1)
            base_val = geo_df.loc[base_mask, "gdp_level"].values
            if len(base_val) == 0 or pd.isna(base_val[0]) or base_val[0] == 0:
                print(f"  Warning: No 2019Q1 data for {geo_code}, skipping")
                continue

            # Rebase to 2019Q1 = 100
            geo_df[f"gdp_index_{geo_name}"] = (geo_df["gdp_level"] / base_val[0] * 100).round(2)
            geo_df = geo_df[["date", f"gdp_index_{geo_name}"]].copy()
            result_dfs.append(geo_df)

        if not result_dfs:
            return pd.DataFrame()

        # Merge all countries on date
        merged = result_dfs[0]
        for rdf in result_dfs[1:]:
            merged = merged.merge(rdf, on="date", how="outer")

        merged = merged.sort_values("date").reset_index(drop=True)

        # Base stays 2019Q1 = 100; earlier quarters are kept (5 more years of history).
        merged = merged[merged["date"] >= "2014-01-01"]

        self._save_processed(merged, "gdp_index_comparison.csv")
        return merged

    # === Labor Market Indicators ===

    def process_unemployment(self) -> Dict[str, pd.DataFrame]:
        """Process Unemployment Rate (monthly)."""
        print("Processing Unemployment Rate...")
        df = self._load_raw("unemployment_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "unemployment_rate"})
        df = self._calculate_yoy_change(df, "unemployment_rate", periods=12, kind="diff")

        cols = ["geo", "date", "unemployment_rate", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "unemployment_rate", "unemployment")
        return self._split_by_geography(df, "unemployment_rate", "unemployment")

    def process_employment_growth(self) -> Dict[str, pd.DataFrame]:
        """Process Employment Growth (quarterly)."""
        print("Processing Employment Growth...")
        df = self._load_raw("employment_growth_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "employment_growth"})
        # No yoy_change (input is already a quarter-on-quarter growth rate).

        cols = ["geo", "date", "employment_growth", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "employment_growth", "employment_growth")
        return self._split_by_geography(df, "employment_growth", "employment_growth")

    def process_labor_participation(self) -> Dict[str, pd.DataFrame]:
        """Process Labor Force Participation Rate (quarterly)."""
        print("Processing Labor Participation...")
        df = self._load_raw("labor_participation_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "participation_rate"})
        df = self._calculate_yoy_change(df, "participation_rate", periods=4, kind="diff")

        cols = ["geo", "date", "participation_rate", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "participation_rate", "labor_participation")
        return self._split_by_geography(df, "participation_rate", "labor_participation")

    # === Prices & Inflation Indicators ===

    def process_hicp(self) -> Dict[str, pd.DataFrame]:
        """Process HICP Inflation (monthly, annual rate of change)."""
        print("Processing HICP...")
        df = self._load_raw("hicp_raw.csv")

        if df.empty:
            return {}

        # This is already annual rate of change
        df = df.rename(columns={"value": "hicp_inflation"})
        df["yoy_change"] = df["hicp_inflation"]

        cols = ["geo", "date", "hicp_inflation", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "hicp_inflation", "hicp")
        return self._split_by_geography(df, "hicp_inflation", "hicp")

    def process_core_inflation(self) -> Dict[str, pd.DataFrame]:
        """Process Core Inflation (excluding energy and food)."""
        print("Processing Core Inflation...")
        df = self._load_raw("core_inflation_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "core_inflation"})
        df["yoy_change"] = df["core_inflation"]

        cols = ["geo", "date", "core_inflation", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "core_inflation", "core_inflation")
        return self._split_by_geography(df, "core_inflation", "core_inflation")

    def process_producer_prices(self) -> Dict[str, pd.DataFrame]:
        """Process Producer Price Index."""
        print("Processing Producer Prices...")
        df = self._load_raw("producer_prices_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "ppi_index"})
        df = self._calculate_yoy_change(df, "ppi_index", periods=12)

        cols = ["geo", "date", "ppi_index", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "ppi_index", "producer_prices")
        return self._split_by_geography(df, "ppi_index", "producer_prices")

    # === External Sector ===

    def process_trade_balance(self) -> Dict[str, pd.DataFrame]:
        """Process trade in goods (Spain only, monthly, million EUR, NSA)."""
        print("Processing Trade Balance...")
        df = self._load_raw("trade_balance_raw.csv")

        if df.empty:
            return {}

        if "stk_flow" not in df.columns:
            print("  Warning: trade_balance_raw.csv has the old annual layout; refetch required")
            return {}

        df = df[df["geo"] == self.GEO_SPAIN]
        wide = df.pivot_table(index="date", columns="stk_flow", values="value", aggfunc="first")
        wide = wide.rename(columns={"EXP": "exports", "IMP": "imports"})
        # Only months where both flows are published (the balance needs both)
        wide = wide.dropna(subset=["exports", "imports"])
        wide["trade_balance"] = wide["exports"] - wide["imports"]
        wide.columns.name = None
        df_spain = wide.reset_index()[["date", "trade_balance", "exports", "imports"]]
        df_spain = df_spain.sort_values("date").reset_index(drop=True)

        self._save_processed(df_spain, "trade_balance_spain.csv")
        return {"ES": df_spain}

    # === Public Finances ===

    def process_government_debt(self) -> Dict[str, pd.DataFrame]:
        """Process Government Debt-to-GDP (quarterly)."""
        print("Processing Government Debt...")
        df = self._load_raw("government_debt_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "debt_to_gdp"})
        df = self._calculate_yoy_change(df, "debt_to_gdp", periods=4, kind="diff")

        cols = ["geo", "date", "debt_to_gdp", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "debt_to_gdp", "government_debt")
        return self._split_by_geography(df, "debt_to_gdp", "government_debt")

    def process_budget_deficit(self) -> Dict[str, pd.DataFrame]:
        """Process Budget Deficit as % of GDP (annual)."""
        print("Processing Budget Deficit...")
        df = self._load_raw("budget_deficit_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "deficit_gdp"})

        cols = ["geo", "date", "deficit_gdp"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "deficit_gdp", "budget_deficit")
        return self._split_by_geography(df, "deficit_gdp", "budget_deficit")

    # === Consumer & Household ===

    def process_consumer_confidence(self) -> Dict[str, pd.DataFrame]:
        """Process Consumer Confidence Indicator (monthly)."""
        print("Processing Consumer Confidence...")
        df = self._load_raw("consumer_confidence_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "consumer_confidence"})
        df = self._calculate_yoy_change(df, "consumer_confidence", periods=12, kind="diff")

        cols = ["geo", "date", "consumer_confidence", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "consumer_confidence", "consumer_confidence")
        return self._split_by_geography(df, "consumer_confidence", "consumer_confidence")

    def process_retail_trade(self) -> Dict[str, pd.DataFrame]:
        """Process Retail Trade Volume Index (monthly)."""
        print("Processing Retail Trade...")
        df = self._load_raw("retail_trade_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "retail_index"})
        df = self._calculate_yoy_change(df, "retail_index", periods=12)

        cols = ["geo", "date", "retail_index", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "retail_index", "retail_trade")
        return self._split_by_geography(df, "retail_index", "retail_trade")

    def process_house_prices(self) -> Dict[str, pd.DataFrame]:
        """Process House Price Index (quarterly)."""
        print("Processing House Prices...")
        df = self._load_raw("house_prices_raw.csv")

        if df.empty:
            return {}

        df = df.rename(columns={"value": "hpi_index"})
        df = self._calculate_yoy_change(df, "hpi_index", periods=4)

        cols = ["geo", "date", "hpi_index", "yoy_change"]
        df = df[[c for c in cols if c in df.columns]].copy()

        self._create_comparison_dataset(df, "hpi_index", "house_prices")
        return self._split_by_geography(df, "hpi_index", "house_prices")

    # === Extension indicators (ext/eurostat) ===

    def _process_simple(self, raw: str, value_col: str, name: str, yoy: Optional[str] = None,
                        yoy_is_value: bool = False) -> Dict[str, pd.DataFrame]:
        """Generic: load raw, rename value, optional yoy (pct/diff), save comparison + per-geo files."""
        df = self._load_raw(raw)
        if df.empty:
            return {}
        df = df.rename(columns={"value": value_col})
        cols = ["geo", "date", value_col]
        if yoy_is_value:
            df["yoy_change"] = df[value_col]
            cols.append("yoy_change")
        elif yoy:
            df = self._calculate_yoy_change(df, value_col, kind=yoy)
            cols.append("yoy_change")
        df = df[[c for c in cols if c in df.columns]].copy()
        _check_time_gaps(df, "A" if name in ("gdp_per_capita_pps", "labour_productivity_pps", "rd_expenditure")
                         else ("Q" if name == "long_term_unemployment" else "M"), name)
        self._create_comparison_dataset(df, value_col, name)
        return self._split_by_geography(df, value_col, name)

    def process_gdp_per_capita_pps(self):
        print("Processing GDP per capita (PPS)...")
        return self._process_simple("gdp_per_capita_pps_raw.csv", "gdp_pc_pps", "gdp_per_capita_pps")

    def process_labour_productivity_pps(self):
        print("Processing labour productivity (PPS)...")
        return self._process_simple("labour_productivity_pps_raw.csv", "productivity_pps", "labour_productivity_pps")

    def process_rd_expenditure(self):
        print("Processing R&D expenditure...")
        return self._process_simple("rd_expenditure_raw.csv", "rd_pct_gdp", "rd_expenditure")

    def process_youth_unemployment(self):
        print("Processing youth unemployment...")
        return self._process_simple("youth_unemployment_raw.csv", "youth_unemployment_rate",
                                    "youth_unemployment", yoy="diff")

    def process_long_term_unemployment(self):
        print("Processing long-term unemployment...")
        return self._process_simple("long_term_unemployment_raw.csv", "ltu_rate",
                                    "long_term_unemployment", yoy="diff")

    def process_hicp_energy(self):
        print("Processing HICP energy...")
        return self._process_simple("hicp_energy_raw.csv", "hicp_energy", "hicp_energy", yoy_is_value=True)

    def process_all(self) -> dict:
        """
        Process all indicators.

        Returns:
            Dictionary with indicator names as keys and geography dicts as values
        """
        results = {}

        print("=" * 60)
        print("Processing all Eurostat indicators...")
        print("=" * 60)

        # Economic Activity
        print("\n[Economic Activity]")
        results["gdp_growth"] = self.process_gdp_growth()
        results["gdp_index_comparison"] = self.process_gdp_index_comparison()
        results["industrial_production"] = self.process_industrial_production()
        results["economic_sentiment"] = self.process_economic_sentiment()

        # Labor Market
        print("\n[Labor Market]")
        results["unemployment"] = self.process_unemployment()
        results["employment_growth"] = self.process_employment_growth()
        results["labor_participation"] = self.process_labor_participation()

        # Prices & Inflation
        print("\n[Prices & Inflation]")
        results["hicp"] = self.process_hicp()
        results["core_inflation"] = self.process_core_inflation()
        results["producer_prices"] = self.process_producer_prices()

        # External Sector
        print("\n[External Sector]")
        results["trade_balance"] = self.process_trade_balance()

        # Public Finances
        print("\n[Public Finances]")
        results["government_debt"] = self.process_government_debt()
        results["budget_deficit"] = self.process_budget_deficit()

        # Consumer & Household
        print("\n[Consumer & Household]")
        results["consumer_confidence"] = self.process_consumer_confidence()
        results["retail_trade"] = self.process_retail_trade()
        results["house_prices"] = self.process_house_prices()

        # Extension indicators
        print("\n[Extension]")
        results["gdp_per_capita_pps"] = self.process_gdp_per_capita_pps()
        results["labour_productivity_pps"] = self.process_labour_productivity_pps()
        results["rd_expenditure"] = self.process_rd_expenditure()
        results["youth_unemployment"] = self.process_youth_unemployment()
        results["long_term_unemployment"] = self.process_long_term_unemployment()
        results["hicp_energy"] = self.process_hicp_energy()

        print("\n" + "=" * 60)
        print("All Eurostat indicators processed successfully!")
        print("=" * 60)

        return results

    def create_summary_dataset(self) -> pd.DataFrame:
        """
        Create a combined summary dataset with latest values from all indicators.
        Useful for dashboard KPI cards.
        """
        print("\nCreating summary dataset...")

        summary_data = []

        # Load each processed comparison file and get latest values
        indicators = [
            ("gdp_growth_comparison.csv", "GDP Growth (QoQ)", "gdp_growth_qoq"),
            ("industrial_production_comparison.csv", "Industrial Production", "ipi_index"),
            ("economic_sentiment_comparison.csv", "Economic Sentiment", "esi"),
            ("unemployment_comparison.csv", "Unemployment Rate", "unemployment_rate"),
            ("hicp_comparison.csv", "HICP Inflation", "hicp_inflation"),
            ("core_inflation_comparison.csv", "Core Inflation", "core_inflation"),
            ("government_debt_comparison.csv", "Gov Debt/GDP", "debt_to_gdp"),
            ("consumer_confidence_comparison.csv", "Consumer Confidence", "consumer_confidence"),
            ("retail_trade_comparison.csv", "Retail Trade", "retail_index"),
            ("house_prices_comparison.csv", "House Prices", "hpi_index"),
        ]

        for filename, name, value_col in indicators:
            filepath = self.output_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath, parse_dates=["date"])
                df = df.sort_values("date", ascending=False)
                latest = df.iloc[0]

                # Get Spain and EU27 values
                es_col = f"{value_col}_es"
                eu_col = f"{value_col}_eu27"

                summary_data.append({
                    "indicator": name,
                    "latest_date": latest["date"],
                    "spain_value": latest.get(es_col),
                    "eu27_value": latest.get(eu_col),
                    "spain_vs_eu27": (latest.get(es_col, 0) or 0) - (latest.get(eu_col, 0) or 0),
                })

        summary_df = pd.DataFrame(summary_data)
        self._save_processed(summary_df, "summary.csv")
        return summary_df
