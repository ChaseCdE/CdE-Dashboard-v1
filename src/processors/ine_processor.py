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


# INE renamed "Total Nacional" -> "Nacional" in the 2026 rebased tables; accept both.
NACIONAL_RE = r"^(?:Total )?Nacional\."


def _value_months_earlier(df: pd.DataFrame, col: str, months: int) -> pd.Series:
    """
    Value of `col` exactly `months` calendar months before each row's date.

    Gaps are handled deliberately: if the comparison period is missing the
    result is NaN. Positional shifts (pct_change(periods=n)) would silently
    compare against the wrong period when an observation is missing, and the
    default fill_method='pad' of pct_change would fill the gap with stale data.
    """
    base = df.drop_duplicates(subset=["date"], keep="last").set_index("date")[col]
    prior = pd.Series(base.values, index=base.index + pd.DateOffset(months=months))
    return df["date"].map(prior)


def pct_change_by_date(df: pd.DataFrame, col: str, months: int) -> pd.Series:
    """Percent change of `col` versus `months` calendar months earlier (NaN if that period is missing)."""
    prev = _value_months_earlier(df, col, months).replace(0, float("nan"))
    return (df[col] / prev - 1) * 100


def diff_by_date(df: pd.DataFrame, col: str, months: int) -> pd.Series:
    """Difference of `col` versus `months` calendar months earlier (percentage points for rates)."""
    return df[col] - _value_months_earlier(df, col, months)


def sum_by_date(df: pd.DataFrame, col: str, months: int = 12) -> pd.Series:
    """
    Rolling sum of `col` over the `months` calendar months ending at each row's date.

    Date-based, not positional: the sum is NaN unless every one of the `months`
    consecutive monthly periods (date, date - 1 month, ..., date - (months - 1))
    is present and not null. Intended for monthly series.
    """
    base = df.drop_duplicates(subset=["date"], keep="last").set_index("date")[col].dropna()
    lookup = base.to_dict()
    out = []
    for d in df["date"]:
        total = 0.0
        for k in range(months):
            v = lookup.get(d - pd.DateOffset(months=k))
            if v is None:
                total = float("nan")
                break
            total += v
        out.append(total)
    return pd.Series(out, index=df.index)


def select_series(df: pd.DataFrame, pattern: str, code: str, label: str) -> pd.DataFrame:
    """
    Rows of the raw frame for one INE series, chosen by an anchored regex on the series name.

    INE renames series now and then ("Total Nacional." -> "Nacional."), so if the name
    no longer matches, fall back to the known series code and warn. Returns an empty
    frame (and warns) if neither is found. Several distinct codes matching is an error
    in the pattern: the first one is used and a warning is logged.
    """
    mask = df["series_name"].str.contains(pattern, case=False, na=False, regex=True)
    codes = list(dict.fromkeys(df.loc[mask, "series_code"]))
    if len(codes) > 1:
        logger.warning(f"{label}: pattern matches {len(codes)} series {codes}; using {codes[0]}")
    if codes:
        return df[df["series_code"] == codes[0]].copy()
    if code in set(df["series_code"]):
        logger.warning(f"{label}: series name no longer matches the pattern, using code {code}")
        return df[df["series_code"] == code].copy()
    logger.warning(f"{label}: series not found (pattern {pattern!r}, code {code})")
    return df.iloc[0:0].copy()


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

    def _calculate_yoy_change(self, df: pd.DataFrame, periods: int = None) -> pd.DataFrame:
        """
        Calculate year-over-year % change of the 'value' column.

        The comparison is by calendar date (12 months earlier), independent of
        frequency, so quarterly, monthly and annual series are all handled the
        same way and a missing period gives NaN instead of a wrong comparison.
        `periods` is accepted for backwards compatibility and ignored.

        Returns:
            DataFrame with added 'yoy_change' column
        """
        df = df.sort_values("date").copy()
        df["yoy_change"] = pct_change_by_date(df, "value", 12)
        return df

    def _add_yoy_pp(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Add 'yoy_pp': year-over-year change of a rate in percentage points (rate minus rate 12 months earlier)."""
        df = df.sort_values("date").copy()
        df["yoy_pp"] = diff_by_date(df, col, 12)
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

        result["qoq_change"] = pct_change_by_date(result, "gdp_index", 3)
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

        result["mom_change"] = pct_change_by_date(result, "ipi_index", 1) if result["ipi_index"].notna().any() else float("nan")
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

        result = self._add_yoy_pp(result, "unemployment_rate")
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

        result = self._add_yoy_pp(result, "employment_rate")
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

        result = self._add_yoy_pp(result, "activity_rate")
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

        result = self._add_yoy_pp(result, "temporary_rate")
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

        # EPA table 65148 (quarterly). Series names: "Ocupados. Total Nacional. Ambos sexos.
        # Total. Total. Valor absoluto." and "... Total. Jornada a tiempo parcial. Valor absoluto."
        # (the former annual table 65970 used "16 y más años" and "Personas"; accepted too).
        age = r"Ambos sexos\. (?:Total|16 y más años)\. "
        absolute = r"(?:Personas|Valor absoluto)"

        # Get total employed persons
        total_mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains(age + r"Total\. " + absolute, case=False, na=False, regex=True)
        )
        total_df = df[total_mask].copy()

        # Get part-time employed persons
        parttime_mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains(age + r"Jornada a tiempo parcial\. " + absolute, case=False, na=False, regex=True)
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

        # YoY change versus the same quarter a year earlier (by date)
        merged = merged.sort_values("date")
        merged["yoy_change"] = pct_change_by_date(merged, "parttime_rate", 12)

        result = merged[["date", "year", "parttime_rate", "yoy_change"]].copy()
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        result = self._add_yoy_pp(result, "parttime_rate")
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

        result = self._add_yoy_pp(result, "youth_unemployment_rate")
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

    def process_labor_cost_components(self) -> pd.DataFrame:
        """
        Process Spanish labor cost (ETCL) split by component:
        Total (Coste laboral total) and Coste salarial total subcomponent.
        Output is long format with QoQ, YoY and an index rebased to 2019Q1=100.
        """
        print("Processing Labor Cost Components (Total + Coste Salarial)...")
        df = self._load_raw("labor_cost_raw.csv")

        # Sector aggregate: "Industria, construcción y servicios..."
        sector_prefix = "Industria, construcción y servicios"
        component_map = {
            "total": "Coste laboral total",
            "salarial": "Coste salarial total",
        }

        frames = []
        for component_key, component_label in component_map.items():
            mask = (
                df["series_name"].str.startswith(sector_prefix, na=False) &
                df["series_name"].str.contains(component_label, case=False, na=False, regex=False) &
                ~df["series_name"].str.contains("Variaci", case=False, na=False)
            )
            sub = df[mask].copy()
            if sub.empty:
                continue

            # Pick the canonical series_code (one row per quarter)
            series_code = sub["series_code"].iloc[0]
            sub = sub[sub["series_code"] == series_code].copy()
            sub = sub.sort_values("date").drop_duplicates(subset=["date"])

            # YoY (4 quarters) and QoQ (1 quarter)
            sub["yoy_change"] = pct_change_by_date(sub, "value", 12)
            sub["qoq_change"] = pct_change_by_date(sub, "value", 3)

            # Index, base = 2019Q1 (date 2019-01-01)
            base_row = sub[sub["date"] == pd.Timestamp("2019-01-01")]
            if not base_row.empty:
                base_val = base_row["value"].iloc[0]
                if base_val and base_val != 0:
                    sub["index_2019q1"] = (sub["value"] / base_val) * 100
                else:
                    sub["index_2019q1"] = pd.NA
            else:
                sub["index_2019q1"] = pd.NA

            sub["component"] = component_key
            frames.append(sub[["date", "year", "component", "value",
                               "yoy_change", "qoq_change", "index_2019q1"]])

        if not frames:
            result = pd.DataFrame(columns=["date", "year", "component", "value",
                                           "yoy_change", "qoq_change", "index_2019q1"])
        else:
            result = pd.concat(frames, ignore_index=True)
            result = result.sort_values(["component", "date"]).reset_index(drop=True)

        self._save_processed(result, "labor_cost_components.csv")
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
            # INE base-2026 tables renamed "Total Nacional" -> "Nacional"; accept both
            df["series_name"].str.contains(r"^(?:Total )?Nacional\.", case=False, na=False, regex=True) &
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

        # Headline index: retail trade excluding service stations, "General" aggregate,
        # constant prices, seasonally and calendar adjusted (ICM4062, table 67178).
        # The previously used table (75809) has no total, only distribution modes, so
        # "first matching series" silently picked the "Empresas unilocalizadas" subset.
        mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains(r"Estaciones de Servicio \(47 sin 473\)\. General\. [ÍI]ndice\.",
                                           case=False, na=False, regex=True)
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

        result["mom_change"] = pct_change_by_date(result, "retail_index", 1)
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
            # INE 2026 tables renamed "Total Nacional" -> "Nacional"; accept both
            df["series_name"].str.contains(r"(?:Total )?Nacional\.", case=False, na=False, regex=True) &
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
            # INE 2026 tables renamed "Total Nacional" -> "Nacional"; accept both
            df["series_name"].str.contains(r"(?:Total )?Nacional\.", case=False, na=False, regex=True) &
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
            # INE 2026 tables renamed "Total Nacional" -> "Nacional" and
            # "Total servicios" -> "Índice General"; accept both namings
            df["series_name"].str.contains(r"(?:Total )?Nacional\.", case=False, na=False, regex=True) &
            (
                df["series_name"].str.contains("Total servicios", case=False, na=False) |
                df["series_name"].str.contains("ndice General", case=False, na=False)
            ) &
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
        Uses seasonally adjusted data with pre-calculated "Variación anual" for Índice General.
        Table 60732: Corregido de efectos estacionales y de calendario.
        """
        print("Processing Services Production...")
        df = self._load_raw("services_production_raw.csv")

        # Filter for Índice General (aggregate services index)
        total_mask = (
            df["series_name"].str.contains("Total Nacional", case=False, na=False) &
            df["series_name"].str.contains("ndice General", case=False, na=False)
        )
        filtered = df[total_mask].copy()

        # Separate the annual variation series from the index series
        variation_mask = filtered["series_name"].str.contains("Variaci.n anual", case=False, na=False, regex=True)
        index_mask = (
            filtered["series_name"].str.contains(r"[ÍI]ndice\b", case=False, na=False, regex=True) &
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
            print(f"  Found services production: {len(result)} records")
        elif not index_df.empty:
            # Fallback: calculate YoY ourselves if variation series not found
            index_df = self._calculate_yoy_change(index_df, periods=12)
            result = index_df[["date", "year", "value", "yoy_change"]].copy()
            result = result.rename(columns={"value": "services_prod_index"})
            print(f"  Found services production (calculated YoY): {len(result)} records")
        else:
            print("  WARNING: No matching IPSS series found for Índice General")
            result = pd.DataFrame(columns=["date", "year", "services_prod_index", "yoy_change"])

        result = result.sort_values("date").drop_duplicates(subset=["date"])

        result["mom_change"] = pct_change_by_date(result, "services_prod_index", 1) if result["services_prod_index"].notna().any() else float("nan")
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

        # INE's headline contributions ("Aportación anual"), seasonally and calendar
        # adjusted, pinned by series code. Name matching previously took the first
        # match, which was the NON-adjusted series, and inventories were missing, so
        # the bars did not add up to the (adjusted) GDP growth (audit C3).
        components = {
            "private_consumption": "CNTR7160",
            "public_consumption": "CNTR7190",
            "gfcf": "CNTR7215",
            "inventories": "CNTR7262",
            "external_demand": "CNTR7264",
        }

        results = []

        for component_key, series_code in components.items():
            filtered = df[df["series_code"] == series_code].copy()
            if filtered.empty:
                raise ValueError(f"gdp_demand: INE series {series_code} ({component_key}) not found in table")
            if "ajustados de estacionalidad" not in str(filtered["series_name"].iloc[0]) or \
                    "no ajustados" in str(filtered["series_name"].iloc[0]):
                raise ValueError(f"gdp_demand: {series_code} is not seasonally adjusted: {filtered['series_name'].iloc[0]}")
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
            # Division 46. Plain "Comercio al por mayor" also matched section G
            # ("al por mayor y al por menor; reparación de vehículos") first (audit C2).
            "mayoristas": ("Comercio al por mayor e intermediarios", "Comercio mayorista"),
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
                # INE base-2026 tables renamed "Total Nacional" -> "Nacional"; accept both
                df["series_name"].str.contains(r"^(?:Total )?Nacional\.", case=False, na=False, regex=True) &
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

    def process_cpi_weights(self) -> pd.DataFrame:
        """
        Process CPI weights for ECOICOP groups.
        Returns the latest weights for each product group (used for pie chart).
        """
        print("Processing CPI Weights...")
        df = self._load_raw("cpi_weights_raw.csv")

        if df.empty:
            print("  WARNING: No CPI weights raw data found")
            return pd.DataFrame()

        # Filter for "Ponderación" series
        mask = df["series_name"].str.contains("Ponderaci", case=False, na=False)
        filtered = df[mask].copy()

        if filtered.empty:
            print("  WARNING: No weight series found")
            return pd.DataFrame()

        # Extract group name from series_name
        # Format: "Total Nacional. [Group Name]. Ponderación."
        def extract_group_name(s):
            parts = s.split(". ")
            if len(parts) >= 2:
                return parts[1]
            return s

        filtered["group_name"] = filtered["series_name"].apply(extract_group_name)

        # Get latest year's weights
        latest_year = filtered["year"].max()
        latest_weights = filtered[filtered["year"] == latest_year].copy()

        # Exclude "Índice general" as it's the total (1000)
        latest_weights = latest_weights[~latest_weights["group_name"].str.contains("ndice general", case=False, na=False)]

        result = latest_weights[["year", "group_name", "value"]].copy()
        result = result.rename(columns={"value": "weight"})
        result = result.sort_values("weight", ascending=False)

        print(f"  Found {len(result)} groups for year {latest_year}")
        # Extra columns for the site export: weight as % of the basket (INE gives per mille)
        # and the first day of the weights' year as the x value.
        result["weight_pct"] = result["weight"] / 10
        result["date"] = pd.to_datetime(result["year"].astype(int).astype(str) + "-01-01")
        self._save_processed(result, "cpi_weights.csv")
        return result

    def process_cpi_ecoicop_groups(self) -> pd.DataFrame:
        """
        Process CPI special groups with YoY variation and calculate contributions.
        Uses grupos especiales: Alimentos/bebidas/tabaco, Energía, Servicios, Bienes industriales.
        Contribution = (weight / 1000) * yoy_change
        """
        print("Processing CPI Special Groups Contributions...")
        df = self._load_raw("cpi_special_groups_raw.csv")
        weights_df = self._load_raw("cpi_special_weights_raw.csv")

        if df.empty:
            print("  WARNING: No CPI special groups raw data found")
            return pd.DataFrame()

        # Define the 4 groups we want
        target_groups = {
            "Alimentos, bebidas y tabaco": "Alimentos, bebidas y tabaco",
            "Productos energéticos": "Productos energéticos",
            "Servicios": "Servicios",
            "Bienes industriales sin productos energéticos": "Bienes industriales sin productos energéticos",
        }

        # Extract group name from series_name
        def extract_group_name(s):
            parts = s.split(". ")
            if len(parts) >= 2:
                return parts[1]
            return s

        # Define weight search terms (exact matching)
        weight_search = {
            "Alimentos, bebidas y tabaco": "Alimentos, bebidas y tabaco",
            "Productos energéticos": "Productos energ",
            "Servicios": "Servicios\\.",  # Use \. to avoid matching "Servicios sin"
            "Bienes industriales sin productos energéticos": "Bienes industriales sin productos energ",
        }

        # Get weights lookup
        weights_lookup = {}
        if not weights_df.empty:
            weights_mask = weights_df["series_name"].str.contains("Ponderaci", case=False, na=False)
            weights_data = weights_df[weights_mask].copy()
            latest_year = weights_data["year"].max()
            latest_weights = weights_data[weights_data["year"] == latest_year]

            for full_name, search in weight_search.items():
                for _, row in latest_weights.iterrows():
                    if search.replace("\\.", "") in row["series_name"] and "sin" not in row["series_name"].lower() or search.replace("\\.", "") == "Bienes industriales sin productos energ" and search.replace("\\.", "") in row["series_name"]:
                        # For Servicios, make sure it's exactly "Servicios" not "Servicios sin..."
                        if "Servicios" in full_name and "sin" in row["series_name"].lower():
                            continue
                        weights_lookup[full_name] = row["value"]
                        break

        # Manual weights assignment to ensure correctness
        # Based on INE data: Total = 1000
        expected_weights = {
            "Alimentos, bebidas y tabaco": 209.2,
            "Productos energéticos": 89.3,
            "Servicios": 503.1,
            "Bienes industriales sin productos energéticos": 198.4,
        }

        results = []
        for full_name, short_name in target_groups.items():
            # Filter for YoY variation series for this group
            # Use EXACT matching with regex to avoid wrong series
            if "Alimentos" in full_name:
                # Match exactly "Alimentos, bebidas y tabaco. Variación anual."
                mask = df["series_name"].str.contains(
                    r"(?:Total )?Nacional\. Alimentos, bebidas y tabaco\. Variaci.n anual\.",
                    case=False, na=False, regex=True
                )
            elif "Productos energ" in full_name:
                # Match exactly "Productos energéticos. Variación anual." (NOT "sin productos energéticos")
                mask = df["series_name"].str.contains(
                    r"(?:Total )?Nacional\. Productos energ.ticos\. Variaci.n anual\.",
                    case=False, na=False, regex=True
                )
            elif full_name == "Servicios":
                # Match exactly "Servicios. Variación anual." (NOT "Servicios sin...")
                mask = df["series_name"].str.contains(
                    r"(?:Total )?Nacional\. Servicios\. Variaci.n anual\.",
                    case=False, na=False, regex=True
                )
            elif "Bienes industriales" in full_name:
                # Match "Bienes industriales sin productos energéticos. Variación anual."
                mask = df["series_name"].str.contains(
                    r"(?:Total )?Nacional\. Bienes industriales sin productos energ.ticos\. Variaci.n anual\.",
                    case=False, na=False, regex=True
                )
            else:
                continue

            filtered = df[mask].copy()

            if filtered.empty:
                print(f"  WARNING: No data found for {full_name}")
                continue

            # Get unique series (take first if multiple)
            series_code = filtered["series_code"].iloc[0]
            group_data = filtered[filtered["series_code"] == series_code].copy()
            group_data = group_data.sort_values("date")

            # Use expected weights
            weight = expected_weights.get(full_name, 0)

            group_data["group_name"] = short_name
            group_data["yoy_change"] = group_data["value"]
            group_data["weight"] = weight
            # Calculate contribution (weight is in per mille, so divide by 1000)
            group_data["contribution"] = (weight / 1000) * group_data["yoy_change"]

            group_data = group_data[["date", "year", "group_name", "yoy_change", "weight", "contribution"]]
            results.append(group_data)
            print(f"  Found {short_name}: {len(group_data)} records, weight={weight:.1f}")

        if results:
            result = pd.concat(results, ignore_index=True)
            result = result.sort_values(["date", "group_name"]).drop_duplicates(subset=["date", "group_name"])
            print(f"  Processed {len(result['group_name'].unique())} groups")
            # Weights are per mille of the basket; export also as % of the basket
            result["weight_pct"] = result["weight"] / 10
            self._save_processed(result, "cpi_ecoicop_groups.csv")
            return result

        return pd.DataFrame()

    def process_ipri(self) -> pd.DataFrame:
        """
        Process Industrial Price Index (IPRI) - Índice de Precios Industriales.
        National index by economic destination: Total, Sin energía, Consumo, Equipo, Intermedios, Energía.
        Includes: Index, YoY change, MoM change.
        """
        print("Processing Industrial Price Index (IPRI)...")
        df = self._load_raw("ipri_raw.csv")

        if df.empty:
            print("  WARNING: No IPRI raw data found")
            return pd.DataFrame()

        # Categories we want (only national data). Since the 2026 rebase INE names
        # the series "Nacional. Mercado interior. ..." (before: "Total Nacional. ...").
        # Patterns are anchored on ". <category>. " so that "Energía" cannot match
        # "Total industria sin energía" and "Bienes de consumo" cannot match
        # "Bienes de consumo duradero".
        categories = {
            "total": r"\. Total industria\.",
            "total_sin_energia": r"\. Total industria sin energ.a\.",
            "consumo": r"\. Bienes de consumo\.",
            "equipo": r"\. Bienes de equipo\.",
            "intermedios": r"\. Bienes intermedios\.",
            "energia": r"\. Energ.a\.",
        }

        # Exclude subcategories like "Bienes de consumo duradero"
        exclude_terms = ["duradero", "no duradero"]

        results = []

        for cat_key, search_term in categories.items():
            # Get index series
            index_mask = (
                df["series_name"].str.contains(NACIONAL_RE, case=False, na=False, regex=True) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=True) &
                df["series_name"].str.contains(r"[ÍI]ndice", case=False, na=False, regex=True) &
                ~df["series_name"].str.contains("Variaci", case=False, na=False)
            )
            # Exclude subcategories
            for excl in exclude_terms:
                index_mask = index_mask & ~df["series_name"].str.contains(excl, case=False, na=False)

            # Get YoY variation series
            yoy_mask = (
                df["series_name"].str.contains(NACIONAL_RE, case=False, na=False, regex=True) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=True) &
                df["series_name"].str.contains("Variaci.n anual", case=False, na=False, regex=True)
            )
            for excl in exclude_terms:
                yoy_mask = yoy_mask & ~df["series_name"].str.contains(excl, case=False, na=False)

            # Get MoM variation series
            mom_mask = (
                df["series_name"].str.contains(NACIONAL_RE, case=False, na=False, regex=True) &
                df["series_name"].str.contains(search_term, case=False, na=False, regex=True) &
                df["series_name"].str.contains("Variaci.n mensual", case=False, na=False, regex=True)
            )
            for excl in exclude_terms:
                mom_mask = mom_mask & ~df["series_name"].str.contains(excl, case=False, na=False)

            index_df = df[index_mask].copy()
            yoy_df = df[yoy_mask].copy()
            mom_df = df[mom_mask].copy()

            if index_df.empty:
                print(f"  WARNING: No index data found for {cat_key}")
                continue

            # Take first matching series
            series_code = index_df["series_code"].iloc[0]
            index_df = index_df[index_df["series_code"] == series_code]

            for _, row in index_df.iterrows():
                date = row["date"]
                record = {
                    "date": date,
                    "year": row.get("year"),
                    "category": cat_key,
                    "ipri_index": row["value"],
                }

                # Add YoY
                yoy_row = yoy_df[yoy_df["date"] == date]
                if not yoy_row.empty:
                    record["yoy_change"] = yoy_row["value"].iloc[0]
                else:
                    record["yoy_change"] = None

                # Add MoM
                mom_row = mom_df[mom_df["date"] == date]
                if not mom_row.empty:
                    record["mom_change"] = mom_row["value"].iloc[0]
                else:
                    record["mom_change"] = None

                results.append(record)

        if not results:
            print("  WARNING: No IPRI data extracted")
            return pd.DataFrame()

        result = pd.DataFrame(results)
        result = result.sort_values(["category", "date"]).drop_duplicates(subset=["category", "date"])

        _check_time_gaps(result[result["category"] == "total"], "M", "IPRI")

        self._save_processed(result, "ipri.csv")
        return result

    def process_cntr_employment(self) -> pd.DataFrame:
        """
        Process CNTR employment data.
        Extracts: Ocupados (persons), FTE employment, and Hours worked.
        """
        print("Processing CNTR Employment...")
        filepath = self.input_dir / "cntr_employment_raw.csv"
        if not filepath.exists():
            print("  WARNING: No CNTR employment raw data found")
            return pd.DataFrame()

        df = pd.read_csv(filepath, parse_dates=["date"])

        # Map series codes to column names
        series_mapping = {
            "CNTR7659": "employed_persons",    # Ocupados - Personas
            "CNTR7818": "employed_fte",        # Puestos de trabajo equivalentes a tiempo completo
            "CNTR7896": "hours_worked",        # Horas trabajadas
        }

        results = []
        for series_code, col_name in series_mapping.items():
            series_df = df[df["series_code"] == series_code].copy()
            if series_df.empty:
                print(f"  WARNING: No data found for {series_code} ({col_name})")
                continue
            series_df = series_df[["date", "value"]].rename(columns={"value": col_name})
            series_df = series_df.sort_values("date").drop_duplicates(subset=["date"])
            results.append(series_df)
            print(f"  Found {col_name}: {len(series_df)} records")

        if not results:
            return pd.DataFrame()

        # Merge all series on date
        result = results[0]
        for r in results[1:]:
            result = result.merge(r, on="date", how="outer")

        result = result.sort_values("date")
        self._save_processed(result, "cntr_employment.csv")
        return result

    def process_population_age(self) -> pd.DataFrame:
        """
        Process EPA population by age.
        Calculates: Total population, Working-age population (16-64).
        """
        print("Processing Population by Age...")
        filepath = self.input_dir / "population_age_raw.csv"
        if not filepath.exists():
            print("  WARNING: No population age raw data found")
            return pd.DataFrame()

        df = pd.read_csv(filepath, parse_dates=["date"])

        # Age groups for working-age population (16-64)
        # EPA groups: "De 16 a 19", "De 20 a 24", "De 25 a 29", ..., "De 60 a 64"
        working_age_groups = [
            "De 16 a 19", "De 20 a 24", "De 25 a 29", "De 30 a 34", "De 35 a 39",
            "De 40 a 44", "De 45 a 49", "De 50 a 54", "De 55 a 59", "De 60 a 64"
        ]

        # Get total population
        # INE renamed the series in 2026: "Ambos sexos. Todas las edades. Personas."
        # became "Ambos sexos. Total. Valor absoluto."; accept both.
        total_mask = df["series_name"].str.contains(
            r"Ambos sexos\. (?:Todas las edades|Total)\.", case=False, na=False, regex=True)
        total_df = df[total_mask].copy()

        if total_df.empty:
            print("  WARNING: No total population series found")
            return pd.DataFrame()

        # Take first series
        total_code = total_df["series_code"].iloc[0]
        total_df = total_df[total_df["series_code"] == total_code]
        total_df = total_df[["date", "value"]].rename(columns={"value": "total_population"})
        total_df = total_df.sort_values("date").drop_duplicates(subset=["date"])
        print(f"  Found total population: {len(total_df)} records")

        # Calculate working-age population by summing age groups
        working_age_data = []
        for date in total_df["date"].unique():
            date_df = df[df["date"] == date]
            working_age_sum = 0
            for age_group in working_age_groups:
                mask = date_df["series_name"].str.contains(age_group, case=False, na=False)
                age_df = date_df[mask]
                if not age_df.empty:
                    working_age_sum += age_df["value"].iloc[0]
            working_age_data.append({"date": date, "working_age_population": working_age_sum})

        working_age_df = pd.DataFrame(working_age_data)
        print(f"  Calculated working-age population (16-64): {len(working_age_df)} records")

        # Merge total and working-age
        result = total_df.merge(working_age_df, on="date", how="left")
        result = result.sort_values("date")

        self._save_processed(result, "population.csv")
        return result

    def process_gdp_productivity(self) -> pd.DataFrame:
        """
        Process GDP productivity indices.
        Calculates indices for: PIB, PIB per capita, PIB per working-age person,
        PIB per occupied, PIB per hour worked.
        All rebased to 2019Q1 = 100.
        """
        print("Processing GDP Productivity Indices...")

        # Load required data
        gdp_path = self.output_dir / "gdp.csv"
        employment_path = self.output_dir / "cntr_employment.csv"
        population_path = self.output_dir / "population.csv"

        if not gdp_path.exists():
            print("  WARNING: GDP data not found, run process_gdp first")
            return pd.DataFrame()

        gdp_df = pd.read_csv(gdp_path, parse_dates=["date"])
        gdp_df = gdp_df[["date", "gdp_index"]].copy()

        if employment_path.exists():
            empl_df = pd.read_csv(employment_path, parse_dates=["date"])
        else:
            print("  WARNING: Employment data not found, run process_cntr_employment first")
            empl_df = pd.DataFrame()

        if population_path.exists():
            pop_df = pd.read_csv(population_path, parse_dates=["date"])
        else:
            print("  WARNING: Population data not found, run process_population_age first")
            pop_df = pd.DataFrame()

        # Merge all data
        result = gdp_df.copy()
        if not empl_df.empty:
            result = result.merge(empl_df, on="date", how="left")
        if not pop_df.empty:
            result = result.merge(pop_df, on="date", how="left")

        result = result.sort_values("date")

        # Find 2019Q1 for rebasing
        base_mask = (result["date"].dt.year == 2019) & (result["date"].dt.quarter == 1)
        if base_mask.sum() == 0:
            print("  WARNING: 2019Q1 not found for rebasing")
            return pd.DataFrame()

        base_row = result[base_mask].iloc[0]

        # Calculate productivity indices (2019Q1 = 100)
        # PIB index (already have this, just rebase)
        if "gdp_index" in result.columns and pd.notna(base_row["gdp_index"]):
            result["pib_index"] = (result["gdp_index"] / base_row["gdp_index"] * 100).round(2)
        else:
            result["pib_index"] = None

        # PIB per capita
        if "total_population" in result.columns and pd.notna(base_row.get("total_population")):
            base_pc = base_row["gdp_index"] / base_row["total_population"]
            result["gdp_per_capita_raw"] = result["gdp_index"] / result["total_population"]
            result["pib_per_capita_index"] = (result["gdp_per_capita_raw"] / base_pc * 100).round(2)
        else:
            result["pib_per_capita_index"] = None

        # PIB per working-age person
        if "working_age_population" in result.columns and pd.notna(base_row.get("working_age_population")):
            base_wa = base_row["gdp_index"] / base_row["working_age_population"]
            result["gdp_per_working_age_raw"] = result["gdp_index"] / result["working_age_population"]
            result["pib_per_working_age_index"] = (result["gdp_per_working_age_raw"] / base_wa * 100).round(2)
        else:
            result["pib_per_working_age_index"] = None

        # PIB per occupied (employment)
        if "employed_persons" in result.columns and pd.notna(base_row.get("employed_persons")):
            base_empl = base_row["gdp_index"] / base_row["employed_persons"]
            result["gdp_per_employed_raw"] = result["gdp_index"] / result["employed_persons"]
            result["pib_per_employed_index"] = (result["gdp_per_employed_raw"] / base_empl * 100).round(2)
        else:
            result["pib_per_employed_index"] = None

        # PIB per hour worked
        if "hours_worked" in result.columns and pd.notna(base_row.get("hours_worked")):
            base_hr = base_row["gdp_index"] / base_row["hours_worked"]
            result["gdp_per_hour_raw"] = result["gdp_index"] / result["hours_worked"]
            result["pib_per_hour_index"] = (result["gdp_per_hour_raw"] / base_hr * 100).round(2)
        else:
            result["pib_per_hour_index"] = None

        # Filter from 2019 onward
        result = result[result["date"] >= "2019-01-01"]

        # Select only the columns we need
        output_cols = ["date", "pib_index", "pib_per_capita_index", "pib_per_working_age_index",
                       "pib_per_employed_index", "pib_per_hour_index"]
        result = result[[c for c in output_cols if c in result.columns]]

        self._save_processed(result, "gdp_productivity.csv")
        return result

    def process_cpi_ccaa(self) -> pd.DataFrame:
        """
        Process CPI data by Autonomous Community (CCAA).
        Extracts: YoY change and MoM change for each CCAA.
        """
        print("Processing CPI by CCAA...")
        filepath = self.input_dir / "cpi_ccaa_raw.csv"
        if not filepath.exists():
            print("  WARNING: No CPI CCAA raw data found")
            return pd.DataFrame()

        df = pd.read_csv(filepath, parse_dates=["date"])

        # CCAA names mapping (INE name -> standardized code for GeoJSON)
        ccaa_mapping = {
            "Andalucía": "AN",
            "Aragón": "AR",
            "Asturias, Principado de": "AS",
            "Balears, Illes": "IB",
            "Canarias": "CN",
            "Cantabria": "CB",
            "Castilla y León": "CL",
            "Castilla - La Mancha": "CM",
            "Cataluña": "CT",
            "Comunitat Valenciana": "VC",
            "Extremadura": "EX",
            "Galicia": "GA",
            "Madrid, Comunidad de": "MD",
            "Murcia, Región de": "MC",
            "Navarra, Comunidad Foral de": "NC",
            "País Vasco": "PV",
            "Rioja, La": "RI",
            "Ceuta": "CE",
            "Melilla": "ML",
        }

        results = []

        for ccaa_name, ccaa_code in ccaa_mapping.items():
            # Find YoY series for this CCAA
            yoy_mask = (
                df["series_name"].str.contains(ccaa_name, case=False, na=False, regex=False) &
                df["series_name"].str.contains("Variaci.n anual", case=False, na=False, regex=True)
            )
            yoy_df = df[yoy_mask].copy()

            # Find MoM series for this CCAA
            mom_mask = (
                df["series_name"].str.contains(ccaa_name, case=False, na=False, regex=False) &
                df["series_name"].str.contains("Variaci.n mensual", case=False, na=False, regex=True)
            )
            mom_df = df[mom_mask].copy()

            if yoy_df.empty:
                continue

            # Take first matching series
            yoy_code = yoy_df["series_code"].iloc[0]
            yoy_df = yoy_df[yoy_df["series_code"] == yoy_code][["date", "value"]].copy()
            yoy_df = yoy_df.rename(columns={"value": "yoy_change"})

            if not mom_df.empty:
                mom_code = mom_df["series_code"].iloc[0]
                mom_df = mom_df[mom_df["series_code"] == mom_code][["date", "value"]].copy()
                mom_df = mom_df.rename(columns={"value": "mom_change"})
                merged = yoy_df.merge(mom_df, on="date", how="left")
            else:
                merged = yoy_df.copy()
                merged["mom_change"] = None

            merged["ccaa_code"] = ccaa_code
            merged["ccaa_name"] = ccaa_name
            results.append(merged)

        if not results:
            print("  WARNING: No CPI CCAA data extracted")
            return pd.DataFrame()

        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(["date", "ccaa_code"]).drop_duplicates(subset=["date", "ccaa_code"])

        # Count unique CCAA
        n_ccaa = result["ccaa_code"].nunique()
        print(f"  Found CPI data for {n_ccaa} CCAA")

        self._save_processed(result, "cpi_ccaa.csv")
        return result

    def process_business_confidence(self) -> pd.DataFrame:
        """
        Process Business Confidence Index (Índice de Confianza Empresarial).
        Extracts: Total National Index (main confidence index).
        Table 8027 contains: Índice, Situación trimestre anterior, Expectativas trimestre entrante.
        """
        print("Processing Business Confidence Index...")
        filepath = self.input_dir / "business_confidence_raw.csv"
        if not filepath.exists():
            print("  WARNING: No Business Confidence raw data found")
            return pd.DataFrame()

        df = pd.read_csv(filepath, parse_dates=["date"])

        # Filter for Total Nacional
        total_mask = df["series_name"].str.contains("Total Nacional", case=False, na=False)
        df = df[total_mask].copy()

        if df.empty:
            print("  WARNING: No Total Nacional data found")
            return pd.DataFrame()

        # Extract indicator type from series name
        results = []

        # Main Índice (ICE)
        # Look for "Índice. Base 2013" pattern (handles encoding issues with í -> ndice)
        ice_mask = df["series_name"].str.contains(r"ndice.*Base", case=False, na=False, regex=True)
        ice_df = df[ice_mask].copy()
        if not ice_df.empty:
            ice_df["indicator"] = "ice"
            ice_df["indicator_name"] = "Índice de Confianza Empresarial"
            results.append(ice_df[["date", "value", "indicator", "indicator_name"]])

        # Situación del trimestre anterior
        situacion_mask = df["series_name"].str.contains("Situaci", case=False, na=False)
        situacion_df = df[situacion_mask].copy()
        if not situacion_df.empty:
            situacion_df["indicator"] = "situacion"
            situacion_df["indicator_name"] = "Situación trimestre anterior"
            results.append(situacion_df[["date", "value", "indicator", "indicator_name"]])

        # Expectativas del trimestre entrante
        expectativas_mask = df["series_name"].str.contains("Expectativas", case=False, na=False)
        expectativas_df = df[expectativas_mask].copy()
        if not expectativas_df.empty:
            expectativas_df["indicator"] = "expectativas"
            expectativas_df["indicator_name"] = "Expectativas trimestre entrante"
            results.append(expectativas_df[["date", "value", "indicator", "indicator_name"]])

        if not results:
            print("  WARNING: No Business Confidence data extracted")
            return pd.DataFrame()

        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(["date", "indicator"]).drop_duplicates(subset=["date", "indicator"])

        # YoY % change only makes sense for the ICE index level; the other two are
        # balances (can be negative), so they get NaN. Computed before the 2021
        # cut so that 2021 values have a base period.
        result["yoy_change"] = float("nan")
        ice = result["indicator"] == "ice"
        result.loc[ice, "yoy_change"] = pct_change_by_date(result[ice], "value", 12)

        # Filter from 2021 onwards
        result = result[result["date"] >= "2021-01-01"]

        n_indicators = result["indicator"].nunique()
        print(f"  Found {n_indicators} Business Confidence indicators")

        self._save_processed(result, "business_confidence.csv")
        return result

    # ------------------------------------------------------------------
    # Extended indicators (ext/ine)
    # ------------------------------------------------------------------
    @staticmethod
    def _level_growth(sub: pd.DataFrame, sum_12m: bool = True) -> pd.DataFrame:
        """date, value, yoy_change (by date, relative %) and optionally sum_12m (null unless 12 consecutive months)."""
        out = sub[["date", "value"]].copy()
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out = out.dropna(subset=["value"]).sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
        out["yoy_change"] = pct_change_by_date(out, "value", 12)
        if sum_12m:
            out["sum_12m"] = sum_by_date(out, "value", 12)
        return out

    def _long_level_growth(self, raw: pd.DataFrame, specs: list, sum_12m: bool = True) -> pd.DataFrame:
        """Stack several series (key, pattern, code, label) into one long frame with a `series` column."""
        frames = []
        for key, pattern, code, label in specs:
            sub = select_series(raw, pattern, code, label)
            if sub.empty:
                continue
            f = self._level_growth(sub, sum_12m=sum_12m)
            f.insert(1, "series", key)
            frames.append(f)
        if not frames:
            return pd.DataFrame(columns=["date", "series", "value", "yoy_change", "sum_12m"])
        return pd.concat(frames, ignore_index=True)

    def process_tourist_arrivals(self) -> pd.DataFrame:
        """FRONTUR: international tourists arriving in Spain (persons, monthly, original data)."""
        print("Processing tourist arrivals (FRONTUR)...")
        raw = self._load_raw("tourist_arrivals_raw.csv")
        sub = select_series(raw, r"^Total\. Turista\. Dato base\. (?:Total )?Nacional\.$", "FREG337", "tourist_arrivals")
        result = self._level_growth(sub)
        self._save_processed(result, "tourist_arrivals.csv")
        return result

    def process_tourist_spending(self) -> pd.DataFrame:
        """EGATUR: total spending of international tourists (millions of euros, monthly, original data)."""
        print("Processing tourist spending (EGATUR)...")
        raw = self._load_raw("tourist_spending_raw.csv")
        sub = select_series(raw, r"^Total\. Turista\. Gasto total\. (?:Total )?Nacional\. Dato base\.$", "FREG647", "tourist_spending")
        result = self._level_growth(sub)
        self._save_processed(result, "tourist_spending.csv")
        return result

    def process_hotel_overnight_stays(self) -> pd.DataFrame:
        """Hotel overnight stays: total, residents in Spain, residents abroad (monthly, original data)."""
        print("Processing hotel overnight stays...")
        raw = self._load_raw("hotel_overnight_stays_raw.csv")
        base = r"^(?:Total )?Nacional\. Pernoctaciones\. Total categorías\. "
        result = self._long_level_growth(raw, [
            ("total", base + r"Total\.$", "EOT25", "hotel_overnight_stays total"),
            ("residentes", base + r"Residentes en España\.$", "EOT33", "hotel_overnight_stays residentes"),
            ("no_residentes", base + r"Residentes en el extranjero\.$", "EOT41", "hotel_overnight_stays no_residentes"),
        ])
        self._save_processed(result, "hotel_overnight_stays.csv")
        return result

    def process_housing_transactions(self) -> pd.DataFrame:
        """ETDP: home purchases (compraventas): total, new, second-hand (monthly)."""
        print("Processing housing transactions (ETDP)...")
        raw = self._load_raw("housing_transactions_raw.csv")
        base = r"^(?:Total )?Nacional\. "
        result = self._long_level_growth(raw, [
            ("total", base + r"General\. Compraventa\. Número\.$", "ETDP1826", "housing_transactions total"),
            ("nueva", base + r"Vivienda nueva\. Compraventa\. Número\.$", "ETDP1825", "housing_transactions nueva"),
            ("usada", base + r"Vivienda segunda mano\. Compraventa\. Número\.$", "ETDP1824", "housing_transactions usada"),
        ])
        self._save_processed(result, "housing_transactions.csv")
        return result

    def process_mortgages(self) -> pd.DataFrame:
        """Mortgages on dwellings: number, 12-month sum and average amount in euros (monthly)."""
        print("Processing mortgages on dwellings...")
        raw = self._load_raw("mortgages_raw.csv")
        n = select_series(raw, r"^Viviendas\. Número de hipotecas\. (?:Total )?Nacional\. Base nueva\. Mensual\.$", "HPT34618", "mortgages number")
        amount = select_series(raw, r"^Viviendas\. Importe de hipotecas\. (?:Total )?Nacional\. Base nueva\. Mensual\.$", "HPT34565", "mortgages amount")
        result = self._level_growth(n)
        amt = amount[["date", "value"]].rename(columns={"value": "amount_thousand_eur"})
        result = result.merge(amt, on="date", how="left")
        # importe is in thousands of euros
        result["avg_amount"] = result["amount_thousand_eur"] * 1000 / result["value"]
        result = result.drop(columns=["amount_thousand_eur"])
        self._save_processed(result, "mortgages.csv")
        return result

    def process_companies(self) -> pd.DataFrame:
        """Commercial companies created and dissolved (number, monthly)."""
        print("Processing commercial companies...")
        raw = self._load_raw("companies_raw.csv")
        result = self._long_level_growth(raw, [
            ("created", r"^Sociedades Constitu[ií]das\. Número de Sociedades\. (?:Total )?Nacional\. Mercantiles\.$", "SM21483", "companies created"),
            ("dissolved", r"^Disueltas\. Número de Sociedades\. (?:Total )?Nacional\. Mercantiles\.$", "SM21486", "companies dissolved"),
        ])
        self._save_processed(result, "companies.csv")
        return result

    def process_household_saving_rate(self) -> pd.DataFrame:
        """Household and NPISH saving rate, % of gross disposable income, seasonally and calendar adjusted (quarterly)."""
        print("Processing household saving rate...")
        raw = self._load_raw("household_saving_rate_raw.csv")
        sub = select_series(
            raw,
            r"^Hogares e Instituciones sin fines de lucro al servicio de los hogares\. Tasa de ahorro\. Dato base\. (?:Total )?Nacional\. Datos ajustados de estacionalidad y calendario",
            "CTNFSI11270", "household_saving_rate")
        result = sub[["date", "value"]].copy()
        result["value"] = pd.to_numeric(result["value"], errors="coerce")
        result = result.dropna(subset=["value"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")
        self._save_processed(result, "household_saving_rate.csv")
        return result

    def process_population_nationality(self) -> pd.DataFrame:
        """Resident population by nationality: total, Spanish, foreign (persons, quarterly since 2021, half-yearly before)."""
        print("Processing population by nationality...")
        raw = self._load_raw("population_nationality_raw.csv")
        base = r"^(?:Total )?Nacional\. "
        tail = r"\. Todas las edades\. Total\. Población\. Número\.$"
        result = self._long_level_growth(raw, [
            ("total", base + "Total" + tail, "ECP4961", "population total"),
            ("espanola", base + "Española" + tail, "ECP4901", "population espanola"),
            ("extranjera", base + "Extranjera" + tail, "ECP701", "population extranjera"),
        ], sum_12m=False)
        self._save_processed(result, "population_nationality.csv")
        return result

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
        results["labor_cost_components"] = self.process_labor_cost_components()
        # Prices
        results["cpi"] = self.process_cpi()
        results["cpi_special_groups"] = self.process_cpi_special_groups()
        results["cpi_weights"] = self.process_cpi_weights()
        results["cpi_ecoicop_groups"] = self.process_cpi_ecoicop_groups()
        results["retail_sales"] = self.process_retail_sales()
        results["house_prices"] = self.process_house_prices()
        # Industrial Prices
        results["ipri"] = self.process_ipri()
        # CNTR Employment and Productivity
        results["cntr_employment"] = self.process_cntr_employment()
        results["population"] = self.process_population_age()
        results["gdp_productivity"] = self.process_gdp_productivity()
        results["cpi_ccaa"] = self.process_cpi_ccaa()
        results["business_confidence"] = self.process_business_confidence()
        # Extended indicators (ext/ine)
        results["tourist_arrivals"] = self.process_tourist_arrivals()
        results["tourist_spending"] = self.process_tourist_spending()
        results["hotel_overnight_stays"] = self.process_hotel_overnight_stays()
        results["housing_transactions"] = self.process_housing_transactions()
        results["mortgages"] = self.process_mortgages()
        results["companies"] = self.process_companies()
        results["household_saving_rate"] = self.process_household_saving_rate()
        results["population_nationality"] = self.process_population_nationality()

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

