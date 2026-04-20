"""
INE Data Processor
Clean and transform raw INE data for dashboard use.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
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


class INEProcessor:
    """Processor for INE economic indicators."""

    def __init__(
        self,
        input_dir: str = "data/raw/ine",
        output_dir: str = "data/processed"
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
        return pd.read_csv(filepath, parse_dates=["date"])

    def _save_processed(self, df: pd.DataFrame, filename: str) -> Path:
        """Save processed DataFrame to CSV."""
        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False, encoding="utf-8")
        print(f"Saved: {filepath}")
        return filepath

    def _calculate_yoy_change(self, df: pd.DataFrame, periods: int = 4) -> pd.DataFrame:
        """
        Calculate Year-over-Year change.

        Args:
            df: DataFrame with 'date' and 'value' columns
            periods: Number of periods for YoY (4 for quarterly, 12 for monthly)

        Returns:
            DataFrame with added 'yoy_change' column
        """
        df = df.sort_values("date").copy()
        nan_before = df["value"].isna().sum() if "value" in df.columns else 0
        df["yoy_change"] = df["value"].pct_change(periods=periods) * 100
        nan_after = df["yoy_change"].isna().sum() if "yoy_change" in df.columns else 0
        if nan_after > nan_before + periods:
            logger.warning(f"YoY calculation: NaN count went from {nan_before} to {nan_after} (expected increase: {periods})")
        return df

    def process_gdp(self) -> pd.DataFrame:
        """
        Process GDP data.
        Filters for: Total Nacional, seasonally adjusted (NOT "no ajustados"), PIB total.
        """
        print("Processing GDP...")
        df = self._load_raw("gdp_raw.csv")

        # Filter for seasonally adjusted GDP
        # Must contain "ajustados de estacionalidad" but NOT "no ajustados"
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("ajustados de estacionalidad", case=False, na=False) &
            ~df["series_name"].str.contains("no ajustados", case=False, na=False) &
            df["series_name"].str.contains("Producto interior bruto a precios de mercado", case=False, na=False) &
            df["series_name"].str.contains("Dato base", case=False, na=False)
        )
        filtered = df[mask].copy()

        # If no seasonally adjusted, fall back to unadjusted
        if filtered.empty:
            print("  Warning: No seasonally adjusted GDP found, using unadjusted")
            mask = (
                df["series_name"].str.contains("Total Nacional", case=False, na=False) &
                df["series_name"].str.contains("Producto interior bruto a precios de mercado", case=False, na=False) &
                df["series_name"].str.contains("Dato base", case=False, na=False)
            )
            filtered = df[mask].copy()

        # Take the first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Check for time gaps before YoY calculation
        _check_time_gaps(filtered, "Q", "GDP")

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        # Clean up
        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "gdp_index"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "gdp.csv")
        return result

    def process_industrial_production(self) -> pd.DataFrame:
        """
        Process Industrial Production Index (table 60280).
        Uses seasonally adjusted data with pre-calculated "Variación anual" for Total industria.
        Series structure: "Total Nacional. [Índice/Variación]. Datos ajustados... Total industria."
        """
        print("Processing Industrial Production...")
        df = self._load_raw("industrial_production_raw.csv")

        # Filter for Total Nacional + Total industria (aggregate IPI).
        # Table 60280 provides seasonally adjusted series (base 2021=100).
        total_mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Total industria", case=False, na=False)
        )
        filtered = df[total_mask].copy()

        # Separate the annual variation series from the index series
        # Series names: "Total Nacional. Índice. ..." vs "Total Nacional. Variación anual. ..."
        variation_mask = filtered["series_name"].str.contains("Variaci.n anual", case=False, na=False)
        index_mask = (
            filtered["series_name"].str.contains(r"\. *[ÍI]ndice\.", case=False, na=False, regex=True) &
            ~filtered["series_name"].str.contains("Variaci", case=False, na=False)
        )

        variation_df = filtered[variation_mask].copy()
        index_df = filtered[index_mask].copy()

        # Take first series if multiple matches
        if not index_df.empty:
            series_code = index_df["series_code"].iloc[0]
            index_df = index_df[index_df["series_code"] == series_code]

        if not variation_df.empty:
            var_code = variation_df["series_code"].iloc[0]
            variation_df = variation_df[variation_df["series_code"] == var_code]

        # Build result: index values + pre-calculated YoY from INE
        if not index_df.empty and not variation_df.empty:
            index_df = index_df[["date", "year", "value"]].rename(columns={"value": "ipi_index"})
            variation_df = variation_df[["date", "value"]].rename(columns={"value": "yoy_change"})
            result = index_df.merge(variation_df, on="date", how="left")
        elif not index_df.empty:
            # Fallback: calculate YoY ourselves if variation series not found
            _check_time_gaps(index_df, "M", "Industrial Production")
            index_df = self._calculate_yoy_change(index_df, periods=12)
            result = index_df[["date", "year", "value", "yoy_change"]].copy()
            result = result.rename(columns={"value": "ipi_index"})
        elif not variation_df.empty:
            # Only variation available — use as both value and yoy_change
            result = variation_df[["date"]].copy()
            result["year"] = variation_df["date"].dt.year
            result["ipi_index"] = pd.NA
            result["yoy_change"] = variation_df["value"].values
        else:
            print("  WARNING: No matching IPI series found for Total Nacional / Total Industria")
            result = pd.DataFrame(columns=["date", "year", "ipi_index", "yoy_change"])

        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "industrial_production.csv")
        return result

    def process_unemployment(self) -> pd.DataFrame:
        """
        Process unemployment data (EPA).
        Filters for: Tasa de paro, Total Nacional, Ambos sexos.
        """
        print("Processing Unemployment...")
        df = self._load_raw("unemployment_raw.csv")

        # Filter for unemployment rate (Tasa de paro), not activity rate
        mask = (
            df["series_name"].str.contains("Tasa de paro", case=False, na=False) &
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take the total (not by age groups)
        total_mask = filtered["series_name"].str.contains("Total\\.", case=False, na=False)
        if total_mask.any():
            filtered = filtered[total_mask]

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Check for time gaps before YoY calculation
        _check_time_gaps(filtered, "Q", "Unemployment")

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "unemployment_rate"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "unemployment.csv")
        return result

    def process_employment_rate(self) -> pd.DataFrame:
        """
        Process employment rate data (EPA).
        Tasa de empleo - % of working-age population employed.
        Filters for: Total Nacional, Ambos sexos, Total (all ages).
        """
        print("Processing Employment Rate...")
        df = self._load_raw("employment_rate_raw.csv")

        # Filter for employment rate
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take the total (not by age groups) - look for "Total" or "16 y más años"
        total_mask = (
            filtered["series_name"].str.contains("Total\\.", case=False, na=False) |
            filtered["series_name"].str.contains("16 y m", case=False, na=False)
        )
        if total_mask.any():
            filtered = filtered[total_mask]

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "employment_rate"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "employment_rate.csv")
        return result

    def process_activity_rate(self) -> pd.DataFrame:
        """
        Process labor force participation rate (EPA).
        Tasa de actividad - % of population in labor force.
        Filters for: Total Nacional, Ambos sexos, Total (all ages).
        """
        print("Processing Activity Rate...")
        df = self._load_raw("activity_rate_raw.csv")

        # Filter for activity rate
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take the total (not by age groups)
        total_mask = (
            filtered["series_name"].str.contains("Total\\.", case=False, na=False) |
            filtered["series_name"].str.contains("16 y m", case=False, na=False)
        )
        if total_mask.any():
            filtered = filtered[total_mask]

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "activity_rate"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "activity_rate.csv")
        return result

    def process_employed(self) -> pd.DataFrame:
        """
        Process total employed persons (EPA).
        Ocupados - absolute number of employed persons (thousands).
        Filters for: Total Nacional, Ambos sexos, Total.
        """
        print("Processing Employed Persons...")
        df = self._load_raw("employed_raw.csv")

        # Filter for total employed
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take the total (not by age groups)
        total_mask = filtered["series_name"].str.contains("Total\\.", case=False, na=False)
        if total_mask.any():
            filtered = filtered[total_mask]

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "employed"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "employed.csv")
        return result

    def process_temporary_rate(self) -> pd.DataFrame:
        """
        Process temporary contract rate (EPA).
        Tasa de temporalidad - % of employees on temporary contracts.
        Filters for: Total Nacional, Ambos sexos, Temporal.
        """
        print("Processing Temporary Contract Rate...")
        df = self._load_raw("temporary_rate_raw.csv")

        # Filter for temporary contracts percentage
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False) &
            df["series_name"].str.contains("Temporal", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Prefer percentage series if available
        pct_mask = filtered["series_name"].str.contains("porcentaje|%", case=False, na=False)
        if pct_mask.any():
            filtered = filtered[pct_mask]

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "temporary_rate"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "temporary_rate.csv")
        return result

    def process_parttime_rate(self) -> pd.DataFrame:
        """
        Process part-time employment rate (EPA).
        Tasa de parcialidad - % of workers in part-time employment.
        Calculates as: (part-time workers / total workers) * 100.
        """
        print("Processing Part-time Rate...")
        df = self._load_raw("parttime_rate_raw.csv")

        # Get total employed persons
        total_mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False) &
            df["series_name"].str.contains("Total\\.", case=False, na=False) &
            df["series_name"].str.contains("Personas", case=False, na=False) &
            ~df["series_name"].str.contains("parcial|completo", case=False, na=False)
        )
        total_df = df[total_mask].copy()

        # Get part-time employed persons
        parttime_mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False) &
            df["series_name"].str.contains("parcial", case=False, na=False) &
            df["series_name"].str.contains("Personas", case=False, na=False)
        )
        parttime_df = df[parttime_mask].copy()

        if total_df.empty or parttime_df.empty:
            print("  Warning: Could not find total or part-time employment data")
            return pd.DataFrame()

        # Take first matching series for each
        if total_df.empty:
            logger.warning("No total employment data found for parttime_rate")
            return pd.DataFrame()
        total_code = total_df["series_code"].iloc[0]
        total_df = total_df[total_df["series_code"] == total_code]

        if parttime_df.empty:
            logger.warning("No part-time employment data found for parttime_rate")
            return pd.DataFrame()
        parttime_code = parttime_df["series_code"].iloc[0]
        parttime_df = parttime_df[parttime_df["series_code"] == parttime_code]

        # Merge and calculate rate
        merged = pd.merge(
            total_df[["date", "year", "value"]],
            parttime_df[["date", "value"]],
            on="date",
            suffixes=("_total", "_parttime"),
            how="inner"
        )
        merged = merged[merged["value_total"] != 0].copy()
        if merged.empty:
            logger.warning("No valid data after removing zero-division cases in parttime_rate")
            return pd.DataFrame(columns=["date", "year", "parttime_rate", "yoy_change"])
        merged["parttime_rate"] = (merged["value_parttime"] / merged["value_total"]) * 100

        # Calculate YoY change (quarterly = 4 periods for quarterly data)
        merged = merged.sort_values("date")
        merged["yoy_change"] = merged["parttime_rate"].pct_change(periods=4) * 100

        result = merged[["date", "year", "parttime_rate", "yoy_change"]].copy()
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "parttime_rate.csv")
        return result

    def process_youth_unemployment(self) -> pd.DataFrame:
        """
        Process youth unemployment rate (EPA).
        Paro juvenil - unemployment rate for under-25s.
        Filters for: Total Nacional, Ambos sexos, Menos de 25 años.
        """
        print("Processing Youth Unemployment...")
        df = self._load_raw("youth_unemployment_raw.csv")

        # Filter for youth unemployment rate
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Ambos sexos", case=False, na=False) &
            (
                df["series_name"].str.contains("Menos de 25", case=False, na=False) |
                df["series_name"].str.contains("16 a 24", case=False, na=False) |
                df["series_name"].str.contains("menores de 25", case=False, na=False)
            )
        )
        filtered = df[mask].copy()

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "youth_unemployment_rate"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "youth_unemployment.csv")
        return result

    def process_labor_cost(self) -> pd.DataFrame:
        """
        Process labor cost per worker (ETCL).
        Coste laboral por trabajador - total labor cost per employee.
        Filters for: Total, national level.
        """
        print("Processing Labor Cost per Worker...")
        df = self._load_raw("labor_cost_raw.csv")

        # Filter for total labor cost (not by sector)
        mask = (
            df["series_name"].str.contains("Total", case=False, na=False) &
            ~df["series_name"].str.contains("Variaci", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take first matching series (should be the aggregate total)
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "labor_cost"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "labor_cost.csv")
        return result

    def process_labor_cost_hour(self) -> pd.DataFrame:
        """
        Process labor cost per hour worked (ETCL).
        Coste laboral por hora efectiva.
        Filters for: Total, national level.
        """
        print("Processing Labor Cost per Hour...")
        df = self._load_raw("labor_cost_hour_raw.csv")

        # Filter for total labor cost per hour
        mask = (
            df["series_name"].str.contains("Total", case=False, na=False) &
            ~df["series_name"].str.contains("Variaci", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "labor_cost_hour"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "labor_cost_hour.csv")
        return result

    def process_cpi(self) -> pd.DataFrame:
        """
        Process CPI data.
        Filters for: Total Nacional, Índice general.
        """
        print("Processing CPI...")
        df = self._load_raw("cpi_raw.csv")

        # Filter for general index
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("ndice general", case=False, na=False) &  # Índice general
            df["series_name"].str.endswith("ndice.", na=False)  # Ends with "Índice."
        )
        filtered = df[mask].copy()

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Check for time gaps before YoY calculation
        _check_time_gaps(filtered, "M", "CPI")

        # Calculate YoY change (monthly = 12 periods)
        filtered = self._calculate_yoy_change(filtered, periods=12)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "cpi_index", "yoy_change": "inflation_rate"})
        result["yoy_change"] = result["inflation_rate"]
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "cpi.csv")
        return result

    def process_retail_sales(self) -> pd.DataFrame:
        """
        Process Retail Sales Index (ICM).
        Filters for: Total Nacional, Índice general.
        """
        print("Processing Retail Sales...")
        df = self._load_raw("retail_sales_raw.csv")

        # Filter for index (not variations)
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("ndice", case=False, na=False) &
            ~df["series_name"].str.contains("Variaci", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (monthly = 12 periods)
        filtered = self._calculate_yoy_change(filtered, periods=12)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "retail_index"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "retail_sales.csv")
        return result

    def process_house_prices(self) -> pd.DataFrame:
        """
        Process House Price Index (IPV).
        Filters for: Total Nacional, General index.
        """
        print("Processing House Prices...")
        df = self._load_raw("house_prices_raw.csv")

        # Filter for general index
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("General", case=False, na=False) &
            df["series_name"].str.endswith("ndice.", na=False)
        )
        filtered = df[mask].copy()

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        # Calculate YoY change (quarterly = 4 periods)
        filtered = self._calculate_yoy_change(filtered, periods=4)

        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": "hpi_index"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "house_prices.csv")
        return result

    def process_industry_turnover(self) -> pd.DataFrame:
        """
        Process Industry Turnover Index (ICN).
        Índice de Cifra de Negocios de la Industria.
        Filters for: Total Nacional, Total industria, Variación anual.
        """
        print("Processing Industry Turnover...")
        df = self._load_raw("industry_turnover_raw.csv")

        # Filter for annual variation of total industry
        # Series ICN2412: Total Nacional. Total industria. Variación anual.
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Total industria", case=False, na=False) &
            df["series_name"].str.contains("Variaci", case=False, na=False) &
            df["series_name"].str.contains("anual", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        result = filtered[["date", "year", "value"]].copy()
        result = result.rename(columns={"value": "turnover_yoy"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "industry_turnover.csv")
        return result

    def process_services_turnover(self) -> pd.DataFrame:
        """
        Process Services Sector Turnover Index (IAS).
        Indicadores de Actividad del Sector Servicios - Cifra de Negocios.
        Filters for: Total Nacional, Total servicios, Variación anual.
        """
        print("Processing Services Turnover...")
        df = self._load_raw("services_turnover_raw.csv")

        # Filter for annual variation of total services turnover
        # Series IAS3856: Cifra de negocio... Total servicios. Total Nacional. Variación anual.
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Total servicios", case=False, na=False) &
            df["series_name"].str.contains("Variaci", case=False, na=False) &
            df["series_name"].str.contains("anual", case=False, na=False) &
            ~df["series_name"].str.contains("mensual", case=False, na=False) &
            ~df["series_name"].str.contains("media", case=False, na=False)
        )
        filtered = df[mask].copy()

        # Take first matching series
        if not filtered.empty:
            series_code = filtered["series_code"].iloc[0]
            filtered = filtered[filtered["series_code"] == series_code]

        result = filtered[["date", "year", "value"]].copy()
        result = result.rename(columns={"value": "turnover_yoy"})
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "services_turnover.csv")
        return result

    def process_services_production(self) -> pd.DataFrame:
        """
        Process Services Production Index (IPSS).
        Uses seasonally adjusted data with pre-calculated "Variación anual" for Total servicios.
        Table 60732: Corregido de efectos estacionales y de calendario.
        """
        print("Processing Services Production...")
        df = self._load_raw("services_production_raw.csv")

        # Filter for Total servicios (aggregate IPSS)
        total_mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("Total servicios", case=False, na=False)
        )
        filtered = df[total_mask].copy()

        # Separate the annual variation series from the index series
        variation_mask = filtered["series_name"].str.contains("Variaci.n anual", case=False, na=False)
        index_mask = (
            filtered["series_name"].str.contains(r"\. *[ÍI]ndice\.", case=False, na=False, regex=True) &
            ~filtered["series_name"].str.contains("Variaci", case=False, na=False)
        )

        variation_df = filtered[variation_mask].copy()
        index_df = filtered[index_mask].copy()

        # Take first series if multiple matches
        if not index_df.empty:
            series_code = index_df["series_code"].iloc[0]
            index_df = index_df[index_df["series_code"] == series_code]

        if not variation_df.empty:
            var_code = variation_df["series_code"].iloc[0]
            variation_df = variation_df[variation_df["series_code"] == var_code]

        # Build result: index values + pre-calculated YoY from INE
        if not index_df.empty and not variation_df.empty:
            index_df = index_df[["date", "year", "value"]].rename(columns={"value": "services_prod_index"})
            variation_df = variation_df[["date", "value"]].rename(columns={"value": "yoy_change"})
            result = index_df.merge(variation_df, on="date", how="left")
        elif not index_df.empty:
            # Fallback: calculate YoY ourselves if variation series not found
            index_df = self._calculate_yoy_change(index_df, periods=12)
            result = index_df[["date", "year", "value", "yoy_change"]].copy()
            result = result.rename(columns={"value": "services_prod_index"})
        else:
            print("  WARNING: No matching IPSS series found for Total servicios")
            result = pd.DataFrame(columns=["date", "year", "services_prod_index", "yoy_change"])

        result = result.sort_values("date").drop_duplicates(subset=["date"])

        self._save_processed(result, "services_production.csv")
        return result

    def process_gdp_demand(self) -> pd.DataFrame:
        """
        Process GDP demand-side breakdown using INE's pre-calculated annual contributions.
        Uses "Aportación anual" data which shows each component's contribution to GDP growth.
        Components: Private Consumption, Public Consumption, GFCF, External Demand.
        """
        print("Processing GDP Demand-Side (Annual Contributions)...")
        df = self._load_raw("gdp_demand_raw.csv")

        # Define components using INE's "Aportación anual" series
        # These are pre-calculated contributions to GDP growth (in percentage points)
        components = {
            "private_consumption": "Gasto en consumo final de los hogares y las ISFLSH. Aportación anual",
            "public_consumption": "Gasto en consumo final de las AAPP. Aportación anual",
            "gfcf": "Formación bruta de capital fijo (FBCF). Aportación anual",
            "external_demand": "Demanda externa. Aportación anual",
        }

        results = []

        for component_key, search_term in components.items():
            # Filter for the specific annual contribution series
            # Use regex=False to avoid issues with parentheses in search terms
            mask = (
                df["series_name"].str.contains("Total Nacional", case=False, na=False, regex=False) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=False)
            )
            filtered = df[mask].copy()

            if not filtered.empty:
                # Get first matching series
                series_code = filtered["series_code"].iloc[0]
                filtered = filtered[filtered["series_code"] == series_code]
                filtered = filtered[["date", "year", "value"]].copy()
                filtered = filtered.sort_values("date").drop_duplicates(subset=["date"])

                # The value IS the contribution (aportación), rename for clarity
                filtered = filtered.rename(columns={"value": "contribution"})
                filtered["component"] = component_key
                results.append(filtered)
                print(f"  Found {component_key}: {len(filtered)} records")

        if results:
            result = pd.concat(results, ignore_index=True)
            result = result.sort_values(["date", "component"]).drop_duplicates()
            self._save_processed(result, "gdp_demand.csv")
            return result

        return pd.DataFrame()

    def process_ipi_sectors(self) -> pd.DataFrame:
        """
        Process IPI sectoral breakdown.
        Extracts both YTD and YoY variation for each industrial sector.
        Sectors: Total, Bienes de consumo, Bienes de equipo, Bienes intermedios, Energia.
        """
        print("Processing IPI Sectors...")
        df = self._load_raw("industrial_production_raw.csv")

        # Define sectors to extract (including Total industria for overall industrial production)
        sectors = {
            "total": "Total industria\\.",
            "consumo": "Bienes de consumo\\.",  # Note: with dot to avoid matching sub-categories
            "equipo": "Bienes de equipo",
            "intermedios": "Bienes intermedios",
            "energia": "Energ",
        }

        sector_labels = {
            "total": "Total",
            "consumo": "Bienes de consumo",
            "equipo": "Bienes de equipo",
            "intermedios": "Bienes intermedios",
            "energia": "Energía",
        }

        results = []

        for sector_key, search_term in sectors.items():
            # Filter for YTD variation series
            ytd_mask = (
                df["series_name"].str.contains("Total Nacional", case=False, na=False) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=True) &
                df["series_name"].str.contains("Variaci.n de la media en lo que va de a", case=False, na=False)
            )
            ytd_df = df[ytd_mask].copy()

            # Filter for YoY variation series
            yoy_mask = (
                df["series_name"].str.contains("Total Nacional", case=False, na=False) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=True) &
                df["series_name"].str.contains("Variaci.n anual", case=False, na=False)
            )
            yoy_df = df[yoy_mask].copy()

            if not ytd_df.empty and not yoy_df.empty:
                # Get first matching series for each
                ytd_code = ytd_df["series_code"].iloc[0]
                ytd_df = ytd_df[ytd_df["series_code"] == ytd_code][["date", "year", "value"]].copy()
                ytd_df = ytd_df.rename(columns={"value": "ytd_change"})

                yoy_code = yoy_df["series_code"].iloc[0]
                yoy_df = yoy_df[yoy_df["series_code"] == yoy_code][["date", "value"]].copy()
                yoy_df = yoy_df.rename(columns={"value": "yoy_change"})

                # Merge YTD and YoY
                merged = ytd_df.merge(yoy_df, on="date", how="outer")
                merged = merged.sort_values("date")
                merged["sector"] = sector_key
                merged["sector_label"] = sector_labels[sector_key]
                results.append(merged)
                print(f"  Found {sector_key}: {len(merged)} records")

        if results:
            result = pd.concat(results, ignore_index=True)
            result = result.sort_values(["date", "sector"]).drop_duplicates(subset=["date", "sector"])
            self._save_processed(result, "ipi_sectors.csv")
            return result

        return pd.DataFrame()

    def process_ipss_sectors(self) -> pd.DataFrame:
        """
        Process IPSS sectoral breakdown.
        Extracts both YTD and YoY variation for selected service sectors.
        """
        print("Processing IPSS Sectors...")
        df = self._load_raw("services_production_raw.csv")

        # Define sectors to extract (user-specified selection)
        sectors = {
            "total": ("Total servicios", "Total servicios"),
            "vehiculos": ("Venta y reparaci.n de veh.culos", "Venta vehículos"),
            "mayoristas": ("Comercio al por mayor", "Comercio mayorista"),
            "minoristas": ("Comercio al por menor", "Comercio minorista"),
            "transporte": ("Transporte y almacenamiento\\.", "Transporte"),
            "hosteleria": ("Hosteler.a\\.", "Hostelería"),
            "tic": ("Informaci.n y comunicaciones\\.", "TIC"),
            "inmobiliarias": ("inmobiliarias\\.", "Inmobiliarias"),
            "profesionales": ("Actividades profesionales", "Profesionales"),
        }

        results = []

        for sector_key, (search_term, label) in sectors.items():
            # Filter for YTD variation series
            ytd_mask = (
                df["series_name"].str.contains("Total Nacional", case=False, na=False) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=True) &
                df["series_name"].str.contains("Variaci.n de la media en lo que va de a", case=False, na=False)
            )
            ytd_df = df[ytd_mask].copy()

            # Filter for YoY variation series
            yoy_mask = (
                df["series_name"].str.contains("Total Nacional", case=False, na=False) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=True) &
                df["series_name"].str.contains("Variaci.n anual", case=False, na=False)
            )
            yoy_df = df[yoy_mask].copy()

            if not ytd_df.empty and not yoy_df.empty:
                # Get first matching series for each
                ytd_code = ytd_df["series_code"].iloc[0]
                ytd_df = ytd_df[ytd_df["series_code"] == ytd_code][["date", "year", "value"]].copy()
                ytd_df = ytd_df.rename(columns={"value": "ytd_change"})

                yoy_code = yoy_df["series_code"].iloc[0]
                yoy_df = yoy_df[yoy_df["series_code"] == yoy_code][["date", "value"]].copy()
                yoy_df = yoy_df.rename(columns={"value": "yoy_change"})

                # Merge YTD and YoY
                merged = ytd_df.merge(yoy_df, on="date", how="outer")
                merged = merged.sort_values("date")
                merged["sector"] = sector_key
                merged["sector_label"] = label
                results.append(merged)
                print(f"  Found {sector_key}: {len(merged)} records")

        if results:
            result = pd.concat(results, ignore_index=True)
            result = result.sort_values(["date", "sector"]).drop_duplicates(subset=["date", "sector"])
            self._save_processed(result, "ipss_sectors.csv")
            return result

        return pd.DataFrame()

    def process_cpi_special_groups(self) -> pd.DataFrame:
        """
        Process CPI special groups (IPCA) data.
        Extracts headline and core inflation using INE's pre-calculated YoY values.
        """
        print("Processing CPI Special Groups...")
        df = self._load_raw("cpi_special_groups_raw.csv")

        # Define special groups - use specific search terms for YoY variation series
        # Series names: "Total Nacional. [group]. Variación anual."
        special_groups = {
            "headline": "ndice general",
            "core": "sin alimentos no elaborados ni productos energ",
        }

        results = []

        for group_key, search_term in special_groups.items():
            # Filter for YoY variation series specifically
            mask = (
                df["series_name"].str.contains(search_term, case=False, na=False) &
                df["series_name"].str.contains("Total Nacional", case=False, na=False) &
                df["series_name"].str.contains("Variaci.n anual", case=False, na=False)
            )
            filtered = df[mask].copy()

            if not filtered.empty:
                # Get first matching series
                series_code = filtered["series_code"].iloc[0]
                filtered = filtered[filtered["series_code"] == series_code]
                filtered = filtered.sort_values("date")

                # Use INE's pre-calculated YoY directly
                filtered["group"] = group_key
                filtered["yoy_change"] = filtered["value"]  # Value IS the YoY change
                filtered = filtered[["date", "year", "value", "yoy_change", "group"]]
                results.append(filtered)
                print(f"  Found {group_key}: {len(filtered)} records")

        if results:
            result = pd.concat(results, ignore_index=True)
            result = result.sort_values(["date", "group"]).drop_duplicates(subset=["date", "group"])
            self._save_processed(result, "cpi_special_groups.csv")
            return result

        return pd.DataFrame()

    def process_all(self) -> dict:
        """
        Process all indicators.

        Returns:
            Dictionary with indicator names as keys and DataFrames as values
        """
        results = {}

        print("=" * 50)
        print("Processing all INE indicators...")
        print("=" * 50)

        results["gdp"] = self.process_gdp()
        results["gdp_demand"] = self.process_gdp_demand()
        results["industrial_production"] = self.process_industrial_production()
        results["ipi_sectors"] = self.process_ipi_sectors()
        results["industry_turnover"] = self.process_industry_turnover()
        results["services_turnover"] = self.process_services_turnover()
        results["services_production"] = self.process_services_production()
        results["ipss_sectors"] = self.process_ipss_sectors()
        # Labor Market - EPA
        results["unemployment"] = self.process_unemployment()
        results["employment_rate"] = self.process_employment_rate()
        results["activity_rate"] = self.process_activity_rate()
        results["employed"] = self.process_employed()
        results["temporary_rate"] = self.process_temporary_rate()
        results["parttime_rate"] = self.process_parttime_rate()
        results["youth_unemployment"] = self.process_youth_unemployment()
        # Labor Market - Labor Costs
        results["labor_cost"] = self.process_labor_cost()
        results["labor_cost_hour"] = self.process_labor_cost_hour()
        # Prices
        results["cpi"] = self.process_cpi()
        results["cpi_special_groups"] = self.process_cpi_special_groups()
        results["retail_sales"] = self.process_retail_sales()
        results["house_prices"] = self.process_house_prices()

        print("=" * 50)
        print("All indicators processed successfully!")
        print("=" * 50)

        return results

    def create_summary_dataset(self) -> pd.DataFrame:
        """
        Create a combined summary dataset with latest values from all indicators.
        Useful for dashboard KPI cards.
        """
        print("Creating summary dataset...")

        summary_data = []

        # Load each processed file and get latest value
        indicators = [
            ("gdp.csv", "GDP Index", "gdp_index", "yoy_change", "Quarterly"),
            ("industrial_production.csv", "Industrial Production", "ipi_index", "yoy_change", "Monthly"),
            ("industry_turnover.csv", "Industry Turnover", "yoy_change", "yoy_change", "Monthly"),
            ("services_turnover.csv", "Services Turnover", "yoy_change", "yoy_change", "Monthly"),
            ("services_production.csv", "Services Production", "services_prod_index", "yoy_change", "Monthly"),
            ("unemployment.csv", "Unemployment Rate", "unemployment_rate", "yoy_change", "Quarterly"),
            ("cpi.csv", "Inflation (CPI)", "cpi_index", "inflation_rate", "Monthly"),
            ("retail_sales.csv", "Retail Sales", "retail_index", "yoy_change", "Monthly"),
            ("house_prices.csv", "House Price Index", "hpi_index", "yoy_change", "Quarterly"),
        ]

        for filename, name, value_col, change_col, frequency in indicators:
            filepath = self.output_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath, parse_dates=["date"])
                if df.empty:
                    continue
                # Skip if required columns are missing
                if value_col not in df.columns:
                    continue
                df = df.sort_values("date", ascending=False)
                latest = df.iloc[0]

                summary_data.append({
                    "indicator": name,
                    "latest_date": latest["date"],
                    "latest_value": latest[value_col],
                    "yoy_change": latest[change_col] if change_col in df.columns and pd.notna(latest.get(change_col)) else None,
                    "frequency": frequency,
                })

        summary_df = pd.DataFrame(summary_data)
        self._save_processed(summary_df, "summary.csv")
        return summary_df
