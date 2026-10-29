"""
Eurostat Indicator Fetcher

Every indicator is one server-filtered request (see eurostat_client.py), defined in
EUROSTAT_INDICATORS: dataset, one value per non-geo dimension, geographies, first year.
The requests run a few at a time; a failed one keeps the previous raw file and logs an error
(run_pipeline.py reports it and exits 3, audit H1). A raw file is rewritten only when its
content changed.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging
from .http_session import CircuitBreaker, map_bounded
from .eurostat_client import (
    EurostatClient,
    parse_eurostat_data,
    convert_period_to_date,
    melt_eurostat_data,
)

logger = logging.getLogger(__name__)


# Dataset codes for each indicator
DATASET_CODES = {
    # Economic Activity
    "gdp_growth": "namq_10_gdp",
    "industrial_production": "sts_inpr_m",
    "economic_sentiment": "ei_bssi_m_r2",

    # Labor Market
    "unemployment": "une_rt_m",
    "employment_growth": "namq_10_a10_e",
    "labor_participation": "lfsi_emp_q",

    # Prices & Inflation
    # prc_hicp_manr (ECOICOP ver. 1) was frozen at 2025-12 when Eurostat moved
    # the HICP to ECOICOP ver. 2 (2026). Its successor prc_hicp_minr carries the
    # whole history back to 1996 on the new classification, so no splicing is
    # needed (see docs/notes/ws-eurostat.md). Note the dimension is `coicop18`.
    "hicp": "prc_hicp_minr",
    "core_inflation": "prc_hicp_minr",  # Same dataset, different coicop18 filter
    "producer_prices": "sts_inppd_m",

    # External Sector
    # Monthly, by Member State (EU27 from 2020). Replaces the annual
    # ext_lt_intratrd, which ends in 2025 and was also mis-aggregated (see notes).
    "trade_balance": "ext_st_27_2020msbec",

    # Public Finances
    "government_debt": "gov_10q_ggdebt",
    "budget_deficit": "gov_10dd_edpt1",

    # Consumer & Household
    "consumer_confidence": "ei_bsco_m",
    "retail_trade": "sts_trtu_m",
    "house_prices": "prc_hpi_q",

    # Extension (ext/eurostat): structural and labour-market indicators
    "gdp_per_capita_pps": "nama_10_pc",        # GDP per head in PPS, EU27_2020 = 100 (tec00114 is the same series rounded to integers)
    "labour_productivity_pps": "tesem160",     # Productivity per hour worked, PPS, EU27_2020 = 100
    "rd_expenditure": "rd_e_gerdtot",          # GERD, % of GDP
    "youth_unemployment": "une_rt_m",          # Same table as `unemployment`, age Y_LT25
    "long_term_unemployment": "une_ltu_q",     # LTU, % of active population, quarterly
    "hicp_energy": "prc_hicp_minr",            # Same table as `hicp`, coicop18 = NRG
}

# Geographies of the extension datasets (Eurostat codes)
GEO_EXT_PEERS = ['ES', 'DE', 'FR', 'IT', 'PT']
GEO_EXT_RD = ['ES', 'EU27_2020', 'DE', 'FR', 'IT']
# Annual extension series start earlier than the pipeline default (2015)
EXT_ANNUAL_START = 2005



MAX_WORKERS = 4  # concurrent requests to ec.europa.eu

_COMPARISON_GEOS = ['ES', 'FR', 'IT', 'DE', 'EU27_2020']


def _ind(dataset_key, filters, geos=None, start=None, geo_filter=None):
    """geos: geographies requested (default ES, EU27_2020); geo_filter: geographies kept (default = geos)."""
    return {"dataset": DATASET_CODES[dataset_key], "filters": filters, "geos": geos, "start": start, "geo_filter": geo_filter}


# name -> request. The raw file is data/raw/eurostat/<name>_raw.csv.
EUROSTAT_INDICATORS = {
    "gdp_growth": _ind("gdp_growth", {'unit': ['CLV_PCH_PRE'], 's_adj': ['SCA'], 'na_item': ['B1GQ']}),
    # Levels (chain-linked volumes 2010) for the European comparison
    "gdp_index_comparison": _ind("gdp_growth", {'unit': ['CLV10_MNAC'], 's_adj': ['SCA'], 'na_item': ['B1GQ']},
                                 geos=_COMPARISON_GEOS),
    "industrial_production": _ind("industrial_production", {'unit': ['I21'], 's_adj': ['SCA'], 'nace_r2': ['B-D']}),
    "economic_sentiment": _ind("economic_sentiment", {'indic': ['BS-ESI-I'], 's_adj': ['SA']}),
    # age TOTAL = 15-74, the headline rate (audit C1; Y25-74 understated it by ~1 pp)
    "unemployment": _ind("unemployment", {'unit': ['PC_ACT'], 's_adj': ['SA'], 'sex': ['T'], 'age': ['TOTAL']}),
    "employment_growth": _ind("employment_growth", {'unit': ['PCH_PRE_PER'], 's_adj': ['SCA'], 'nace_r2': ['TOTAL'], 'na_item': ['EMP_DC']}),
    "labor_participation": _ind("labor_participation", {'unit': ['PC_POP'], 's_adj': ['SA'], 'sex': ['T'], 'age': ['Y15-64'], 'indic_em': ['ACT']}),
    "hicp": _ind("hicp", {'coicop18': ['TOTAL'], 'unit': ['RCH_A']}),
    "core_inflation": _ind("core_inflation", {'coicop18': ['TOT_X_NRG_FOOD'], 'unit': ['RCH_A']}),
    "producer_prices": _ind("producer_prices", {'unit': ['I21'], 'nace_r2': ['B-D']}),
    # Spain only; exports and imports with the whole world, million EUR, seasonally and calendar
    # adjusted (TRD_VAL_SCA; TRD_VAL, used before, is the unadjusted value)
    "trade_balance": _ind("trade_balance", {'partner': ['WORLD'], 'bclas_bec': ['TOTAL'], 'indic_et': ['TRD_VAL_SCA'], 'stk_flow': ['EXP', 'IMP']},
                          geos=['ES'], geo_filter=['ES', 'EU27_2020']),
    "government_debt": _ind("government_debt", {'unit': ['PC_GDP'], 'na_item': ['GD'], 'sector': ['S13']}),
    "budget_deficit": _ind("budget_deficit", {'unit': ['PC_GDP'], 'na_item': ['B9'], 'sector': ['S13']}),
    "consumer_confidence": _ind("consumer_confidence", {'indic': ['BS-CSMCI'], 's_adj': ['SA']}),
    "retail_trade": _ind("retail_trade", {'unit': ['I21'], 's_adj': ['SCA'], 'nace_r2': ['G47'], 'indic_bt': ['VOL_SLS']}),
    "house_prices": _ind("house_prices", {'unit': ['I15_Q'], 'purchase': ['TOTAL']}),
    # Extension indicators
    "gdp_per_capita_pps": _ind("gdp_per_capita_pps", {'unit': ['PC_EU27_2020_HAB_MPPS_CP'], 'na_item': ['B1GQ']},
                               geos=GEO_EXT_PEERS, start=EXT_ANNUAL_START),
    "labour_productivity_pps": _ind("labour_productivity_pps", {'unit': ['PC_EU27_2020_MPPS_CP'], 'na_item': ['NLPR_HW']},
                                    geos=GEO_EXT_PEERS, start=EXT_ANNUAL_START),
    "rd_expenditure": _ind("rd_expenditure", {'sectperf': ['TOTAL'], 'unit': ['PC_GDP']},
                           geos=GEO_EXT_RD, start=EXT_ANNUAL_START),
    "youth_unemployment": _ind("youth_unemployment", {'unit': ['PC_ACT'], 's_adj': ['SA'], 'sex': ['T'], 'age': ['Y_LT25']}),
    "long_term_unemployment": _ind("long_term_unemployment", {'indic_em': ['LTU'], 'age': ['Y15-74'], 'unit': ['PC_ACT'], 's_adj': ['SA'], 'sex': ['T']}),
    "hicp_energy": _ind("hicp_energy", {'coicop18': ['NRG'], 'unit': ['RCH_A']}),
}


class EurostatIndicatorFetcher:
    """Fetcher for Eurostat economic indicators."""

    def __init__(
        self,
        output_dir: str = "data/raw/eurostat",
        start_period: int = 2015,
        geo_codes: List[str] = None
    ):
        """
        Args:
            output_dir: Directory to save CSV files
            start_period: Start year for data fetching
            geo_codes: Geographic codes to fetch (default: ES, EU27_2020)
        """
        self.client = EurostatClient(start_period=start_period)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.geo_codes = geo_codes or [EurostatClient.GEO_SPAIN, EurostatClient.GEO_EU27]
        self.breaker = CircuitBreaker()

    def _save_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Write the raw CSV if its content changed. Never overwrite cached data with an empty frame."""
        filepath = self.output_dir / filename
        if df.empty:
            logger.warning(f"Skipping save of empty DataFrame to {filepath} (preserving cached data)")
            return filepath
        text = df.to_csv(index=False)
        if filepath.exists() and filepath.read_bytes() == text.encode("utf-8"):
            logger.info(f"Unchanged: {filepath}")
            return filepath
        filepath.write_text(text, encoding="utf-8", newline="")
        logger.info(f"Saved: {filepath}")
        return filepath

    def _fetch_one(self, name: str) -> pd.DataFrame:
        spec = EUROSTAT_INDICATORS[name]
        geos = spec["geos"] or self.geo_codes
        filter_pars = {'geo': geos, **spec["filters"]}
        if spec["start"] is not None:
            filter_pars['startPeriod'] = spec["start"]
        logger.info(f"Fetching Eurostat {name} ({spec['dataset']})...")
        try:
            self.breaker.check()
        except ConnectionError as exc:
            logger.error(f"Error fetching {spec['dataset']}: {exc}")
            return pd.DataFrame()
        df = self.client.get_data(spec["dataset"], filter_pars)
        (self.breaker.failure if df.empty else self.breaker.success)()
        if df.empty:
            return df
        df = melt_eurostat_data(df)
        return parse_eurostat_data(df, spec["geo_filter"] or geos)

    def fetch_indicators(self, names: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """Fetch the given indicators (default: all), a few requests at a time, and save their raw files."""
        names = list(names or EUROSTAT_INDICATORS)
        outcomes = map_bounded(self._fetch_one, names, MAX_WORKERS)
        results = {}
        for name, (df, exc) in zip(names, outcomes):
            if exc is not None:
                logger.error(f"Eurostat {name}: fetch failed: {exc}")
                df = pd.DataFrame()
            self._save_csv(df, f"{name}_raw.csv")
            results[name] = df
        for name, df in results.items():
            logger.info(f"{name}: {len(df)} rows")
        return results

    def fetch_all(self) -> dict:
        """Fetch all indicators. Returns indicator name -> DataFrame (empty if it failed)."""
        return self.fetch_indicators()
