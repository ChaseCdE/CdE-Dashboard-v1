"""
INE Data Processor
Clean and transform raw INE data for dashboard use.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging

from .series_ops import diff_by_date, pct_change_by_date, sum_by_date
from ..fetchers.ine_series import CPI_GROUP_LABELS, INDICATORS, code as ine_code, codes

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


class SeriesNotFound(ValueError):
    """An INE series the processor needs is not in the raw data (fail loudly instead of publishing less)."""


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
        self._raw_cache = {}

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

    # ------------------------------------------------------------------ helpers
    def _pick(self, ind: str, role: str) -> pd.DataFrame:
        """
        Rows of one INE series, selected by its registry code (src/fetchers/ine_series.py).
        Raises SeriesNotFound if the code is absent from the raw file (audit M1: no name
        matching, no "first match", no silent empty result).
        """
        code = ine_code(ind, role)
        raw = self._raw(ind)
        sub = raw[raw["series_code"] == code]
        if sub.empty:
            raise SeriesNotFound(f"{ind}.{role}: INE series {code} not found in {INDICATORS[ind]['file']}")
        return sub.copy()

    def _raw(self, ind: str) -> pd.DataFrame:
        """Raw file of an indicator, loaded once per processor."""
        if ind not in self._raw_cache:
            self._raw_cache[ind] = self._load_raw(INDICATORS[ind]["file"])
        return self._raw_cache[ind]

    def _official(self, ind: str, role: str, dates: pd.Series) -> pd.Series:
        """INE's published rate (series `role`) at each of `dates`; NaN where INE has none (audit M4)."""
        return dates.map(self._published(ind, role))

    def _published(self, ind: str, role: str) -> pd.Series:
        """INE's published series `role`, as a Series indexed by date."""
        return self._pick(ind, role).drop_duplicates("date", keep="last").set_index("date")["value"]

    def _level(self, ind: str, role: str, name: str, gaps: str = None, pp: bool = False,
               yoy_role: str = None) -> pd.DataFrame:
        """
        date, year, <name>, yoy_change (+ yoy_pp) for one level series.
        yoy_change is computed from the levels unless `yoy_role` names the rate INE publishes.
        """
        filtered = self._pick(ind, role)
        if gaps:
            _check_time_gaps(filtered, gaps, ind)
        filtered = self._calculate_yoy_change(filtered)
        if yoy_role:
            filtered["yoy_change"] = self._official(ind, yoy_role, filtered["date"])
        result = filtered[["date", "year", "value", "yoy_change"]].copy()
        result = result.rename(columns={"value": name})
        result = result.sort_values("date").drop_duplicates(subset=["date"])
        if pp:
            result = self._add_yoy_pp(result, name)
        return result

    def process_gdp(self) -> pd.DataFrame:
        """GDP, volume index, seasonally and calendar adjusted (CNTR6652), with yoy and qoq."""
        print("Processing GDP...")
        result = self._level("gdp", "value", "gdp_index", gaps="Q")
        result["qoq_change"] = pct_change_by_date(result, "gdp_index", 3)
        self._save_processed(result, "gdp.csv")
        return result

    def process_industrial_production(self) -> pd.DataFrame:
        """IPI total industry, seasonally and calendar adjusted: index and INE's published yoy."""
        print("Processing Industrial Production...")
        index_df = self._pick("industrial_production", "index")[["date", "year", "value"]].rename(columns={"value": "ipi_index"})
        variation_df = self._pick("industrial_production", "yoy")[["date", "value"]].rename(columns={"value": "yoy_change"})
        result = index_df.merge(variation_df, on="date", how="left")
        result = result.sort_values("date").drop_duplicates(subset=["date"])
        result["mom_change"] = self._official("industrial_production", "mom", result["date"])
        self._save_processed(result, "industrial_production.csv")
        return result

    def process_unemployment(self) -> pd.DataFrame:
        """EPA unemployment rate, total, both sexes (EPA453100)."""
        print("Processing Unemployment...")
        result = self._level("unemployment", "rate", "unemployment_rate", gaps="Q", pp=True)
        self._save_processed(result, "unemployment.csv")
        return result

    def process_employment_rate(self) -> pd.DataFrame:
        """EPA employment rate (EPA441060)."""
        print("Processing Employment Rate...")
        result = self._level("employment_rate", "rate", "employment_rate", pp=True)
        self._save_processed(result, "employment_rate.csv")
        return result

    def process_activity_rate(self) -> pd.DataFrame:
        """EPA activity rate (EPA388079)."""
        print("Processing Activity Rate...")
        result = self._level("activity_rate", "rate", "activity_rate", pp=True)
        self._save_processed(result, "activity_rate.csv")
        return result

    def process_employed(self) -> pd.DataFrame:
        """EPA employed persons, thousands (EPA387796)."""
        print("Processing Employed Persons...")
        result = self._level("employed", "level", "employed")
        self._save_processed(result, "employed.csv")
        return result

    def process_temporary_rate(self) -> pd.DataFrame:
        """EPA temporary-contract rate, % of employees (EPA416256)."""
        print("Processing Temporary Contract Rate...")
        result = self._level("temporary_rate", "rate", "temporary_rate", pp=True)
        self._save_processed(result, "temporary_rate.csv")
        return result

    def process_parttime_rate(self) -> pd.DataFrame:
        """EPA part-time rate = part-time employed / total employed * 100 (EPA404362 / EPA404358)."""
        print("Processing Part-time Rate...")
        total_df = self._pick("parttime_rate", "total")
        parttime_df = self._pick("parttime_rate", "parttime")
        merged = pd.merge(
            total_df[["date", "year", "value"]],
            parttime_df[["date", "value"]],
            on="date",
            suffixes=("_total", "_parttime"),
            how="inner"
        )
        merged = merged[merged["value_total"] != 0].copy()
        if merged.empty:
            raise SeriesNotFound("parttime_rate: no period with both total and part-time employment")
        merged["parttime_rate"] = (merged["value_parttime"] / merged["value_total"]) * 100
        merged = merged.sort_values("date")
        merged["yoy_change"] = pct_change_by_date(merged, "parttime_rate", 12)
        result = merged[["date", "year", "parttime_rate", "yoy_change"]].copy()
        result = result.sort_values("date").drop_duplicates(subset=["date"])
        result = self._add_yoy_pp(result, "parttime_rate")
        self._save_processed(result, "parttime_rate.csv")
        return result

    def process_youth_unemployment(self) -> pd.DataFrame:
        """EPA unemployment rate, under 25, both sexes (EPA452436)."""
        print("Processing Youth Unemployment...")
        result = self._level("youth_unemployment", "rate", "youth_unemployment_rate", pp=True)
        self._save_processed(result, "youth_unemployment.csv")
        return result

    def process_labor_cost(self) -> pd.DataFrame:
        """ETCL labor cost per worker, total (ETCL68)."""
        print("Processing Labor Cost per Worker...")
        result = self._level("labor_cost", "total", "labor_cost")
        self._save_processed(result, "labor_cost.csv")
        return result

    def process_labor_cost_components(self) -> pd.DataFrame:
        """
        ETCL labor cost per worker split into total (ETCL68) and wages (ETCL67), long format,
        with QoQ, YoY and an index rebased to 2019Q1=100.
        """
        print("Processing Labor Cost Components (Total + Coste Salarial)...")
        frames = []
        for component_key in ("total", "salarial"):
            sub = self._pick("labor_cost", component_key)
            sub = sub.sort_values("date").drop_duplicates(subset=["date"])
            sub["yoy_change"] = pct_change_by_date(sub, "value", 12)
            sub["qoq_change"] = pct_change_by_date(sub, "value", 3)
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
        result = pd.concat(frames, ignore_index=True)
        result = result.sort_values(["component", "date"]).reset_index(drop=True)
        self._save_processed(result, "labor_cost_components.csv")
        return result

    def process_labor_cost_hour(self) -> pd.DataFrame:
        """ETCL labor cost per hour worked, total (ETCL925)."""
        print("Processing Labor Cost per Hour...")
        result = self._level("labor_cost_hour", "total", "labor_cost_hour")
        self._save_processed(result, "labor_cost_hour.csv")
        return result

    def process_cpi(self) -> pd.DataFrame:
        """CPI, national general index (IPC290751), with yoy."""
        print("Processing CPI...")
        result = self._level("cpi", "index", "cpi_index", gaps="M", yoy_role="yoy")
        result = result.rename(columns={"yoy_change": "inflation_rate"})
        result["yoy_change"] = result["inflation_rate"]
        self._save_processed(result, "cpi.csv")
        return result

    def process_retail_sales(self) -> pd.DataFrame:
        """Retail trade index at constant prices, excluding service stations, SA (ICM4062)."""
        print("Processing Retail Sales...")
        result = self._level("retail_sales", "index", "retail_index", yoy_role="yoy")
        result["mom_change"] = self._official("retail_sales", "mom", result["date"])
        self._save_processed(result, "retail_sales.csv")
        return result

    def process_house_prices(self) -> pd.DataFrame:
        """House price index, national general (IPV1209)."""
        print("Processing House Prices...")
        result = self._level("house_prices", "index", "hpi_index", yoy_role="yoy")
        self._save_processed(result, "house_prices.csv")
        return result

    def _published_rate(self, ind: str, role: str, name: str) -> pd.DataFrame:
        """date, year, <name> for a series that already is a rate published by INE."""
        result = self._pick(ind, role)[["date", "year", "value"]].rename(columns={"value": name})
        return result.sort_values("date").drop_duplicates(subset=["date"])

    def process_industry_turnover(self) -> pd.DataFrame:
        """Industrial turnover index, total industry, INE's yoy (ICN2412)."""
        print("Processing Industry Turnover...")
        result = self._published_rate("industry_turnover", "yoy", "turnover_yoy")
        self._save_processed(result, "industry_turnover.csv")
        return result

    def process_services_turnover(self) -> pd.DataFrame:
        """Services turnover, calendar adjusted, general index, INE's yoy (IAS3856)."""
        print("Processing Services Turnover...")
        result = self._published_rate("services_turnover", "yoy", "turnover_yoy")
        self._save_processed(result, "services_turnover.csv")
        return result

    def process_services_production(self) -> pd.DataFrame:
        """IPSS general index, seasonally and calendar adjusted: index (IPSS380) and INE's yoy (IPSS490)."""
        print("Processing Services Production...")
        index_df = self._pick("services_production", "index")[["date", "year", "value"]].rename(columns={"value": "services_prod_index"})
        variation_df = self._pick("services_production", "yoy")[["date", "value"]].rename(columns={"value": "yoy_change"})
        result = index_df.merge(variation_df, on="date", how="left")
        print(f"  Found services production: {len(result)} records")
        result = result.sort_values("date").drop_duplicates(subset=["date"])
        result["mom_change"] = self._official("services_production", "mom", result["date"])
        self._save_processed(result, "services_production.csv")
        return result

    def process_gdp_demand(self) -> pd.DataFrame:
        """
        GDP demand-side breakdown using INE's seasonally adjusted annual contributions
        ("Aportación anual"): private and public consumption, GFCF, inventories, external demand.
        """
        print("Processing GDP Demand-Side (Annual Contributions)...")
        results = []
        for component_key in INDICATORS["gdp_demand"]["series"]:
            filtered = self._pick("gdp_demand", component_key)[["date", "year", "value"]]
            filtered = filtered.sort_values("date").drop_duplicates(subset=["date"])
            filtered = filtered.rename(columns={"value": "contribution"})
            filtered["component"] = component_key
            results.append(filtered)
            print(f"  Found {component_key}: {len(filtered)} records")
        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(["date", "component"]).drop_duplicates()
        self._save_processed(result, "gdp_demand.csv")
        return result

    def _sectors(self, ind: str, labels: dict) -> pd.DataFrame:
        """Long frame of ytd (average so far this year) and yoy variation per sector, from INE's published rates."""
        results = []
        for sector_key, label in labels.items():
            yoy_role = "yoy" if sector_key == "total" else f"yoy_{sector_key}"
            ytd_df = self._pick(ind, f"ytd_{sector_key}")[["date", "year", "value"]].rename(columns={"value": "ytd_change"})
            yoy_df = self._pick(ind, yoy_role)[["date", "value"]].rename(columns={"value": "yoy_change"})
            merged = ytd_df.merge(yoy_df, on="date", how="outer").sort_values("date")
            merged["sector"] = sector_key
            merged["sector_label"] = label
            results.append(merged)
            print(f"  Found {sector_key}: {len(merged)} records")
        result = pd.concat(results, ignore_index=True)
        return result.sort_values(["date", "sector"]).drop_duplicates(subset=["date", "sector"])

    def process_ipi_sectors(self) -> pd.DataFrame:
        """IPI by sector (SA): ytd and yoy variation."""
        print("Processing IPI Sectors...")
        result = self._sectors("industrial_production", {
            "total": "Total", "consumo": "Bienes de consumo", "equipo": "Bienes de equipo",
            "intermedios": "Bienes intermedios", "energia": "Energía",
        })
        self._save_processed(result, "ipi_sectors.csv")
        return result

    def process_ipss_sectors(self) -> pd.DataFrame:
        """IPSS by activity (SA): ytd and yoy variation. (The services total is published as services_production.)"""
        print("Processing IPSS Sectors...")
        result = self._sectors("services_production", {
            "vehiculos": "Venta vehículos", "mayoristas": "Comercio mayorista", "minoristas": "Comercio minorista",
            "transporte": "Transporte", "hosteleria": "Hostelería", "tic": "TIC",
            "inmobiliarias": "Inmobiliarias", "profesionales": "Profesionales",
        })
        self._save_processed(result, "ipss_sectors.csv")
        return result

    def process_cpi_special_groups(self) -> pd.DataFrame:
        """Headline and core CPI, INE's published yoy (IPC290750, IPC292510)."""
        print("Processing CPI Special Groups...")
        results = []
        for group_key in ("headline", "core"):
            filtered = self._pick("cpi_special_groups", group_key).sort_values("date")
            filtered["group"] = group_key
            filtered["yoy_change"] = filtered["value"]  # Value IS the YoY change
            filtered = filtered[["date", "year", "value", "yoy_change", "group"]]
            results.append(filtered)
            print(f"  Found {group_key}: {len(filtered)} records")
        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(["date", "group"]).drop_duplicates(subset=["date", "group"])
        self._save_processed(result, "cpi_special_groups.csv")
        return result

    def process_cpi_weights(self) -> pd.DataFrame:
        """Latest CPI weights of the ECOICOP groups (table 76156), per mille."""
        print("Processing CPI Weights...")
        filtered = self._raw("cpi_weights").copy()
        missing = set(codes("cpi_weights").values()) - set(filtered["series_code"])
        if missing:
            raise SeriesNotFound(f"cpi_weights: INE series {sorted(missing)} not found in cpi_weights_raw.csv")

        filtered["group_name"] = filtered["series_code"].map(CPI_GROUP_LABELS)

        latest_year = filtered["year"].max()
        latest_weights = filtered[filtered["year"] == latest_year].copy()
        latest_weights = latest_weights[~latest_weights["group_name"].str.contains("ndice general", case=False, na=False)]
        result = latest_weights[["year", "group_name", "value"]].copy()
        result = result.rename(columns={"value": "weight"})
        result = result.sort_values("weight", ascending=False)
        print(f"  Found {len(result)} groups for year {latest_year}")
        result["weight_pct"] = result["weight"] / 10
        result["date"] = pd.to_datetime(result["year"].astype(int).astype(str) + "-01-01")
        self._save_processed(result, "cpi_weights.csv")
        return result

    def _special_group_weights(self, role: str) -> pd.Series:
        """Weight (per mille) of one special group by year, from INE's current and previous-base series."""
        parts = [self._pick("cpi_special_weights", r)[["year", "value"]] for r in (role, f"prev_{role}")]
        w = pd.concat(parts).drop_duplicates("year", keep="first").set_index("year")["value"]
        return w.sort_index()

    def process_cpi_ecoicop_groups(self) -> pd.DataFrame:
        """
        CPI contributions of the four special groups: contribution = weight / 1000 * yoy.

        yoy is INE's published annual variation. The weight is INE's weight of the year of each
        observation (audit M2). Observations from years before the first available weight (2021)
        are not published. A later year without a weight raises: no other year's weight is reused.
        """
        print("Processing CPI Special Groups Contributions...")
        names = {
            "alimentos_bebidas_y_tabaco": "Alimentos, bebidas y tabaco",
            "productos_energeticos": "Productos energéticos",
            "servicios": "Servicios",
            "bienes_industriales_sin_productos_energeticos": "Bienes industriales sin productos energéticos",
        }
        results = []
        for role, short_name in names.items():
            weights = self._special_group_weights(role)
            group_data = self._pick("cpi_special_groups", role).sort_values("date")
            years = group_data["year"].astype(int)
            covered = years >= int(weights.index.min())
            if (~covered).any():
                print(f"  {short_name}: {int((~covered).sum())} observations before {int(weights.index.min())} have no INE weight and are not published")
            group_data = group_data[covered].copy()
            group_data["weight"] = group_data["year"].astype(int).map(weights)
            missing = group_data.loc[group_data["weight"].isna(), "year"].unique()
            if len(missing):
                raise SeriesNotFound(f"cpi_ecoicop_groups: no INE weight for {short_name} in {sorted(int(y) for y in missing)}")
            group_data["group_name"] = short_name
            group_data["yoy_change"] = group_data["value"]
            group_data["contribution"] = (group_data["weight"] / 1000) * group_data["yoy_change"]
            group_data = group_data[["date", "year", "group_name", "yoy_change", "weight", "contribution"]]
            results.append(group_data)
            print(f"  Found {short_name}: {len(group_data)} records, weights by year {weights.to_dict()}")
        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(["date", "group_name"]).drop_duplicates(subset=["date", "group_name"])
        print(f"  Processed {len(result['group_name'].unique())} groups")
        result["weight_pct"] = result["weight"] / 10
        self._save_processed(result, "cpi_ecoicop_groups.csv")
        return result

    def process_ipri(self) -> pd.DataFrame:
        """Industrial price index (national, domestic market) by destination: index, yoy and mom as published by INE."""
        print("Processing Industrial Price Index (IPRI)...")
        frames = []
        for cat_key in ("total", "total_sin_energia", "consumo", "equipo", "intermedios", "energia"):
            index_df = self._pick("ipri", f"index_{cat_key}")[["date", "year", "value"]].rename(columns={"value": "ipri_index"})
            yoy_df = self._pick("ipri", f"yoy_{cat_key}")[["date", "value"]].rename(columns={"value": "yoy_change"})
            mom_df = self._pick("ipri", f"mom_{cat_key}")[["date", "value"]].rename(columns={"value": "mom_change"})
            f = index_df.merge(yoy_df.drop_duplicates("date"), on="date", how="left") \
                        .merge(mom_df.drop_duplicates("date"), on="date", how="left")
            f.insert(2, "category", cat_key)
            frames.append(f)
        result = pd.concat(frames, ignore_index=True)
        result = result.sort_values(["category", "date"]).drop_duplicates(subset=["category", "date"])
        _check_time_gaps(result[result["category"] == "total"], "M", "IPRI")
        self._save_processed(result, "ipri.csv")
        return result

    def process_cntr_employment(self) -> pd.DataFrame:
        """CNTR employment (SA, total CNAE): persons, full-time equivalents, hours worked."""
        print("Processing CNTR Employment...")
        results = []
        for role in ("employed_persons", "employed_fte", "hours_worked"):
            series_df = self._pick("cntr_employment", role)[["date", "value"]].rename(columns={"value": role})
            series_df = series_df.sort_values("date").drop_duplicates(subset=["date"])
            results.append(series_df)
            print(f"  Found {role}: {len(series_df)} records")
        result = results[0]
        for r in results[1:]:
            result = result.merge(r, on="date", how="outer")
        result = result.sort_values("date")
        self._save_processed(result, "cntr_employment.csv")
        return result

    def process_population_age(self) -> pd.DataFrame:
        """EPA population: total and working-age (16-64, sum of the ten five-year groups)."""
        print("Processing Population by Age...")
        total_df = self._pick("population_age", "total")[["date", "value"]].rename(columns={"value": "total_population"})
        total_df = total_df.sort_values("date").drop_duplicates(subset=["date"])
        print(f"  Found total population: {len(total_df)} records")
        dates = pd.Index(total_df["date"].unique())
        acc = pd.Series(0, index=dates)
        for role in INDICATORS["population_age"]["series"]:
            if role == "total":
                continue
            s = self._pick("population_age", role).drop_duplicates("date").set_index("date")["value"]
            acc = acc + s.reindex(dates).fillna(0)  # same order of additions as the age groups
        working_age_df = pd.DataFrame({"date": dates, "working_age_population": acc.values})
        print(f"  Calculated working-age population (16-64): {len(working_age_df)} records")
        result = total_df.merge(working_age_df, on="date", how="left")
        result = result.sort_values("date")
        self._save_processed(result, "population.csv")
        return result

    def process_gdp_productivity(self) -> pd.DataFrame:
        """
        GDP productivity indices, rebased to 2019Q1 = 100: GDP, per inhabitant, per person of working
        age (16-64), per employed person and per hour worked.

        Inputs are the processed gdp.csv, cntr_employment.csv and population.csv. Every input must
        be present (audit M5): a missing file, column or base-period value raises instead of
        silently dropping a line from the chart.
        """
        print("Processing GDP Productivity Indices...")
        need = {
            "gdp.csv": ["gdp_index"],
            "cntr_employment.csv": ["employed_persons", "hours_worked"],
            "population.csv": ["total_population", "working_age_population"],
        }
        frames = {}
        for fname, cols in need.items():
            path = self.output_dir / fname
            if not path.exists():
                raise SeriesNotFound(f"gdp_productivity: {fname} not found; process its source first")
            f = pd.read_csv(path, parse_dates=["date"])
            absent = [c for c in cols if c not in f.columns]
            if absent:
                raise SeriesNotFound(f"gdp_productivity: {fname} lacks {absent}")
            frames[fname] = f[["date"] + cols]

        result = frames["gdp.csv"].merge(frames["cntr_employment.csv"], on="date", how="left") \
                                  .merge(frames["population.csv"], on="date", how="left").sort_values("date")
        inputs = ["gdp_index", "employed_persons", "hours_worked", "total_population", "working_age_population"]
        base_mask = result["date"] == pd.Timestamp("2019-01-01")
        if base_mask.sum() != 1 or result.loc[base_mask, inputs].isna().any(axis=None):
            raise SeriesNotFound("gdp_productivity: 2019Q1 base period missing or incomplete in the inputs")
        base_row = result[base_mask].iloc[0]
        for c in inputs:
            # Latest quarters may lag by a release or two, but a column must not be (nearly) empty.
            if result[c].notna().sum() < len(result) - 2:
                raise SeriesNotFound(f"gdp_productivity: input {c} has only {int(result[c].notna().sum())} of {len(result)} quarters")

        result["pib_index"] = (result["gdp_index"] / base_row["gdp_index"] * 100).round(2)
        for col, out in (("total_population", "pib_per_capita_index"),
                         ("working_age_population", "pib_per_working_age_index"),
                         ("employed_persons", "pib_per_employed_index"),
                         ("hours_worked", "pib_per_hour_index")):
            base = base_row["gdp_index"] / base_row[col]
            result[out] = ((result["gdp_index"] / result[col]) / base * 100).round(2)

        result = result[result["date"] >= "2019-01-01"]
        result = result[["date", "pib_index", "pib_per_capita_index", "pib_per_working_age_index",
                         "pib_per_employed_index", "pib_per_hour_index"]]
        self._save_processed(result, "gdp_productivity.csv")
        return result

    def process_cpi_ccaa(self) -> pd.DataFrame:
        """CPI general index by autonomous community: INE's published yoy and mom."""
        print("Processing CPI by CCAA...")
        ccaa_names = {
            "an": "Andalucía", "ar": "Aragón", "as": "Asturias, Principado de", "ib": "Balears, Illes",
            "cn": "Canarias", "cb": "Cantabria", "cl": "Castilla y León", "cm": "Castilla - La Mancha",
            "ct": "Cataluña", "vc": "Comunitat Valenciana", "ex": "Extremadura", "ga": "Galicia",
            "md": "Madrid, Comunidad de", "mc": "Murcia, Región de", "nc": "Navarra, Comunidad Foral de",
            "pv": "País Vasco", "ri": "Rioja, La", "ce": "Ceuta", "ml": "Melilla",
        }
        results = []
        for key, ccaa_name in ccaa_names.items():
            yoy_df = self._pick("cpi_ccaa", f"yoy_{key}")[["date", "value"]].rename(columns={"value": "yoy_change"})
            mom_df = self._pick("cpi_ccaa", f"mom_{key}")[["date", "value"]].rename(columns={"value": "mom_change"})
            merged = yoy_df.merge(mom_df, on="date", how="left")
            merged["ccaa_code"] = key.upper()
            merged["ccaa_name"] = ccaa_name
            results.append(merged)
        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(["date", "ccaa_code"]).drop_duplicates(subset=["date", "ccaa_code"])
        print(f"  Found CPI data for {result['ccaa_code'].nunique()} CCAA")
        self._save_processed(result, "cpi_ccaa.csv")
        return result

    def process_business_confidence(self) -> pd.DataFrame:
        """Business confidence (ICEA, quarterly): index (ICE1), situation (ICE54) and expectations (ICE53)."""
        print("Processing Business Confidence Index...")
        names = {
            "ice": "Índice de Confianza Empresarial",
            "situacion": "Situación trimestre anterior",
            "expectativas": "Expectativas trimestre entrante",
        }
        results = []
        for indicator, indicator_name in names.items():
            sub = self._pick("business_confidence", indicator)
            sub["indicator"] = indicator
            sub["indicator_name"] = indicator_name
            results.append(sub[["date", "value", "indicator", "indicator_name"]])
        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(["date", "indicator"]).drop_duplicates(subset=["date", "indicator"])
        result["yoy_change"] = float("nan")
        ice = result["indicator"] == "ice"
        result.loc[ice, "yoy_change"] = pct_change_by_date(result[ice], "value", 12)
        result = result[result["date"] >= "2021-01-01"]
        print(f"  Found {result['indicator'].nunique()} Business Confidence indicators")
        self._save_processed(result, "business_confidence.csv")
        return result

    @staticmethod
    def _level_growth(sub: pd.DataFrame, sum_12m: bool = True, yoy: pd.Series = None) -> pd.DataFrame:
        """
        date, value, yoy_change and optionally sum_12m (null unless 12 consecutive months).
        yoy_change is computed by date (relative %) unless `yoy`, INE's published rate indexed by date, is given.
        """
        out = sub[["date", "value"]].copy()
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out = out.dropna(subset=["value"]).sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
        out["yoy_change"] = pct_change_by_date(out, "value", 12) if yoy is None else out["date"].map(yoy)
        if sum_12m:
            out["sum_12m"] = sum_by_date(out, "value", 12)
        return out

    def _long_level_growth(self, ind: str, roles: list, sum_12m: bool = True) -> pd.DataFrame:
        """Stack several series of an indicator into one long frame with a `series` column."""
        frames = []
        for role in roles:
            f = self._level_growth(self._pick(ind, role), sum_12m=sum_12m)
            f.insert(1, "series", role)
            frames.append(f)
        return pd.concat(frames, ignore_index=True)

    def process_tourist_arrivals(self) -> pd.DataFrame:
        """FRONTUR: international tourists arriving in Spain (persons, monthly, original data; FREG337)."""
        print("Processing tourist arrivals (FRONTUR)...")
        result = self._level_growth(self._pick("tourist_arrivals", "level"), yoy=self._published("tourist_arrivals", "yoy"))
        self._save_processed(result, "tourist_arrivals.csv")
        return result

    def process_tourist_spending(self) -> pd.DataFrame:
        """EGATUR: total spending of international tourists (millions of euros, monthly, original data; FREG647)."""
        print("Processing tourist spending (EGATUR)...")
        result = self._level_growth(self._pick("tourist_spending", "level"), yoy=self._published("tourist_spending", "yoy"))
        self._save_processed(result, "tourist_spending.csv")
        return result

    def process_hotel_overnight_stays(self) -> pd.DataFrame:
        """Hotel overnight stays: total, residents in Spain, residents abroad (monthly, original data)."""
        print("Processing hotel overnight stays...")
        result = self._long_level_growth("hotel_overnight_stays", ["total", "residentes", "no_residentes"])
        self._save_processed(result, "hotel_overnight_stays.csv")
        return result

    def process_housing_transactions(self) -> pd.DataFrame:
        """ETDP: home purchases (compraventas): total, new, second-hand (monthly)."""
        print("Processing housing transactions (ETDP)...")
        result = self._long_level_growth("housing_transactions", ["total", "nueva", "usada"])
        self._save_processed(result, "housing_transactions.csv")
        return result

    def process_mortgages(self) -> pd.DataFrame:
        """Mortgages on dwellings: number (HPT34618), 12-month sum and average amount in euros (HPT34565, monthly)."""
        print("Processing mortgages on dwellings...")
        n = self._pick("mortgages", "number")
        amount = self._pick("mortgages", "amount")
        result = self._level_growth(n)
        amt = amount[["date", "value"]].rename(columns={"value": "amount_thousand_eur"})
        result = result.merge(amt, on="date", how="left")
        result["avg_amount"] = result["amount_thousand_eur"] * 1000 / result["value"]
        result = result.drop(columns=["amount_thousand_eur"])
        self._save_processed(result, "mortgages.csv")
        return result

    def process_companies(self) -> pd.DataFrame:
        """Commercial companies created and dissolved (number, monthly)."""
        print("Processing commercial companies...")
        result = self._long_level_growth("companies", ["created", "dissolved"])
        self._save_processed(result, "companies.csv")
        return result

    def process_household_saving_rate(self) -> pd.DataFrame:
        """Household and NPISH saving rate, % of gross disposable income, seasonally and calendar adjusted (quarterly)."""
        print("Processing household saving rate...")
        result = self._pick("household_saving_rate", "rate")[["date", "value"]].copy()
        result["value"] = pd.to_numeric(result["value"], errors="coerce")
        result = result.dropna(subset=["value"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")
        self._save_processed(result, "household_saving_rate.csv")
        return result

    def process_population_nationality(self) -> pd.DataFrame:
        """Resident population by nationality: total, Spanish, foreign (persons, quarterly since 2021, half-yearly before)."""
        print("Processing population by nationality...")
        result = self._long_level_growth("population_nationality", ["total", "espanola", "extranjera"], sum_12m=False)
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

