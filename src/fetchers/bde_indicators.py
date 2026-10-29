"""
Banco de Espana (BdE) Indicators Configuration
Defines all economic indicators to fetch from the BdE statistics API.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from .bde_client import BdeClient, get_appropriate_range
from .http_session import map_bounded

BATCH_SIZE = 20   # series per request (the API takes many; one time range per request)
MAX_WORKERS = 2   # concurrent requests to app.bde.es
# Years of history kept for every BdE series. The API only offers fixed ranges: monthly and
# quarterly series are fetched with MAX and trimmed; daily series allow at most 36M, so the
# earlier years are requested one calendar year at a time (rango=YYYY) and merged.
HISTORY_YEARS = 10
DAILY_RECENT = "36M"

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary of all BdE indicators
# Structure: indicator_key -> { series_code, name, category, description, unit, frequency }

BDE_INDICATORS: Dict[str, Dict[str, Any]] = {
    # ==========================================================================
    # INTEREST RATES - EURIBOR
    # ==========================================================================

    "euribor_12m_monthly": {
        "series_code": "D_1NBAF472",
        "name": "EURIBOR 12M (Monthly Average)",
        "category": "interest_rates",
        "description": "One-year Euribor - Monthly average",
        "unit": "%",
        "frequency": "M",
        "source": "European Banking Federation / ECB",
        "priority": "high"
    },

    "euribor_3m_daily": {
        "series_code": "D_DNBAD172",
        "name": "EURIBOR 3M (Daily)",
        "category": "interest_rates",
        "description": "3-month Euribor - Daily",
        "unit": "%",
        "frequency": "D",
        "source": "European Banking Federation / ECB",
        "priority": "high"
    },

    "euribor_12m_daily": {
        "series_code": "D_DNBAF172",
        "name": "EURIBOR 12M (Daily)",
        "category": "interest_rates",
        "description": "12-month Euribor - Daily",
        "unit": "%",
        "frequency": "D",
        "source": "European Banking Federation / ECB",
        "priority": "high"
    },

    "ester_daily": {
        "series_code": "D_DNBAA572",
        "name": "ESTER (Overnight)",
        "category": "interest_rates",
        "description": "Euro Short-Term Rate - Daily",
        "unit": "%",
        "frequency": "D",
        "source": "ECB",
        "priority": "medium"
    },

    "euribor_1w_daily": {
        "series_code": "D_DNBAS172",
        "name": "EURIBOR 1 Week (Daily)",
        "category": "interest_rates",
        "description": "1-week Euribor - Daily",
        "unit": "%",
        "frequency": "D",
        "source": "European Banking Federation / ECB",
        "priority": "medium"
    },

    "euribor_1m_daily": {
        "series_code": "D_DNBAC172",
        "name": "EURIBOR 1 Month (Daily)",
        "category": "interest_rates",
        "description": "1-month Euribor - Daily",
        "unit": "%",
        "frequency": "D",
        "source": "European Banking Federation / ECB",
        "priority": "medium"
    },

    "euribor_6m_daily": {
        "series_code": "D_DNBAE172",
        "name": "EURIBOR 6 Month (Daily)",
        "category": "interest_rates",
        "description": "6-month Euribor - Daily",
        "unit": "%",
        "frequency": "D",
        "source": "European Banking Federation / ECB",
        "priority": "medium"
    },

    # ==========================================================================
    # INTEREST RATES - GOVERNMENT BONDS
    # ==========================================================================

    "spain_10y_bond": {
        "series_code": "D_G0B1F0ZP",
        "name": "Spain 10Y Government Bond Yield",
        "category": "interest_rates",
        "description": "10-year government bond yield - Secondary market",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "spain_2y_bond": {
        "series_code": "D_G0B1F0ZE",
        "name": "Spain 2Y+ Government Bond Yield",
        "category": "interest_rates",
        "description": "Government bonds 2+ years - Secondary market",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    "spain_3y_bond": {
        "series_code": "D_G0B1F0ZN",
        "name": "Spain 3Y Government Bond Yield",
        "category": "interest_rates",
        "description": "3-year government bond yield - Secondary market",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    "spain_5y_bond": {
        "series_code": "D_G0B1F0ZO",
        "name": "Spain 5Y Government Bond Yield",
        "category": "interest_rates",
        "description": "5-year government bond yield - Secondary market",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    "spain_15y_bond": {
        "series_code": "D_G0B1F0ZQ",
        "name": "Spain 15Y Government Bond Yield",
        "category": "interest_rates",
        "description": "15-year government bond yield - Secondary market",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    "spain_tbill_3m": {
        "series_code": "D_DTES00B7",
        "name": "Spain Treasury Bills 1-3 Months",
        "category": "interest_rates",
        "description": "Treasury bills 1-3 months yield",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    "spain_tbill_6m": {
        "series_code": "D_DTES00S7",
        "name": "Spain Treasury Bills 6 Months",
        "category": "interest_rates",
        "description": "Treasury bills 6 months yield",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    "spain_tbill_1y": {
        "series_code": "D_DTES00U7",
        "name": "Spain Treasury Bills 1 Year",
        "category": "interest_rates",
        "description": "Treasury bills 1 year yield",
        "unit": "%",
        "frequency": "D",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    # ==========================================================================
    # INTERNATIONAL GOVERNMENT BONDS (10Y) - MONTHLY
    # ==========================================================================

    "spain_10y_bond_monthly": {
        "series_code": "D_1NBBO320",
        "name": "Spain 10Y Government Bond Yield (Monthly)",
        "category": "interest_rates",
        "description": "10-year government bond yield - Spain (Monthly average)",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "germany_10y_bond": {
        "series_code": "D_1NBBO308",
        "name": "Germany 10Y Government Bond Yield",
        "category": "interest_rates",
        "description": "10-year government bond yield - Germany (Bund)",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana / ECB",
        "priority": "high"
    },

    "france_10y_bond": {
        "series_code": "D_1NBBO303",
        "name": "France 10Y Government Bond Yield",
        "category": "interest_rates",
        "description": "10-year government bond yield - France (OAT)",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana / ECB",
        "priority": "high"
    },

    "italy_10y_bond": {
        "series_code": "D_1NBBO309",
        "name": "Italy 10Y Government Bond Yield",
        "category": "interest_rates",
        "description": "10-year government bond yield - Italy (BTP)",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana / ECB",
        "priority": "high"
    },

    # ==========================================================================
    # CREDIT AND BANKING
    # ==========================================================================

    "mortgage_rate": {
        "series_code": "DN_1TI2T0135",
        "name": "Bank Mortgage Rate (New Business)",
        "category": "credit_banking",
        "description": "NEDR. Loans to households & NPISHs. House purchase. New business",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "consumer_credit_rate": {
        "series_code": "DN_1TI2T0138",
        "name": "Consumer Credit Rate (New Business)",
        "category": "credit_banking",
        "description": "NEDR. Loans to households & NPISHs. Consumption. New business",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "corporate_lending_rate": {
        "series_code": "DN_1TI2T0144",
        "name": "Corporate Lending Rate (New Business)",
        "category": "credit_banking",
        "description": "NEDR. Loans to NFCs. New business",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "household_deposit_rate": {
        "series_code": "DN_1TI2T0024",
        "name": "Household Term Deposit Rate",
        "category": "credit_banking",
        "description": "NEDR. Deposits from households & NPISHs. Term deposits. Weighted average rate",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "household_overnight_deposit_rate": {
        "series_code": "DN_1TI1T0010",
        "name": "Household Overnight Deposit Rate",
        "category": "credit_banking",
        "description": "Overnight deposits rate for households",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "medium"
    },

    "credit_households_total": {
        "series_code": "DF_MESNAA20A1U62250Z01E",
        "name": "Credit to Households - Total",
        "category": "credit_banking",
        "description": "OIFM. Loans and credits. To households and NPISHs",
        "growth_key": "credit_households_growth",
        "unit": "Millions EUR",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "credit_nfc_total": {
        "series_code": "DF_MESNAA20A1U62240Z01E",
        "name": "Credit to Non-Financial Corporations - Total",
        "category": "credit_banking",
        "description": "Total lending to NFCs",
        "growth_key": "credit_nfc_growth",
        "unit": "Billions EUR",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    # Transaction-based year-on-year growth rates published by BdE (Boletin Estadistico 3.19-3.21,
    # "Indicadores de liquidez y financiacion"). They exclude reclassifications, write-offs and
    # securitisations, which move the stock series above. Used as the "yoy" of the credit stocks
    # (audit M3); not exported on their own.
    "credit_households_growth": {
        "series_code": "DCF_M.N.ES.W0.S1M.S1.N.L.LE.FD.T._Z.XDC._T.M.V.TVA._T",
        "name": "Household financing, year-on-year growth (transaction-based)",
        "category": "credit_growth",
        "description": "Financing of households and NPISHs: balance, year-on-year growth rate (BE 3.21)",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "credit_nfc_growth": {
        "series_code": "DCF_M.N.ES.W0.S11.S1.N.L.LE.F4.T._Z.XDC._T.M.V.TVA._T",
        "name": "NFC loans from credit institutions, year-on-year growth (transaction-based)",
        "category": "credit_growth",
        "description": "Loans from credit institutions to non-financial corporations: balance, year-on-year growth rate (BE 3.20)",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    # ==========================================================================
    # DEBT RATIOS
    # ==========================================================================

    "household_debt_gdp": {
        "series_code": "DMZ10S80ZH0_TPRPIB.Q",
        "name": "Household Debt-to-GDP Ratio",
        "category": "debt_ratios",
        "description": "Debt households & NPISH. % of GDP (4 quarters)",
        "unit": "%",
        "frequency": "Q",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "nfc_debt_gdp": {
        "series_code": "DMZ10S80ZN0_TPRPIB.Q",
        "name": "Corporate (NFC) Debt-to-GDP Ratio",
        "category": "debt_ratios",
        "description": "Debt NFCs. % of GDP (4 quarters)",
        "unit": "%",
        "frequency": "Q",
        "source": "Banco de Espana",
        "priority": "high"
    },

    # ==========================================================================
    # EXTERNAL SECTOR
    # ==========================================================================

    "current_account_balance": {
        "series_code": "DEEM.N.ES.W1.S1.S1.T.B.CA._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "Current Account Balance",
        "category": "external_sector",
        "description": "Balance of Payments. Current Account. Total Current Account. Balance",
        "unit": "Millions EUR",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "tourism_receipts": {
        "series_code": "DEEM.N.ES.W1.S1.S1.T.C.SD._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "Tourism Receipts",
        "category": "external_sector",
        "description": "Balance of Payments. Current Account. Services. Tourism. Income",
        "unit": "Millions EUR",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "medium"
    },
    # ==========================================================================
    # FINANCIAL STABILITY, LABOUR MARKET, PUBLIC FINANCES (ext/bde)
    # ==========================================================================

    "npl_ratio": {
        "series_code": "D_BEEA2020",
        "name": "NPL Ratio (Credit Institutions)",
        "category": "financial_stability",
        "description": "Credit institutions and EFC. Doubtful loans to other resident sectors as a share of total loans (Boletin Estadistico 4.3)",
        "unit": "%",
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },

    "social_security_affiliates": {
        "series_code": "DEPSEGS1AF_XRTODS.M",
        "name": "Social Security Affiliates (End of Month)",
        "category": "labour_market",
        "description": "Affiliates to Social Security at end of month, all regimes, not seasonally adjusted (Boletin Estadistico 24.19)",
        "unit": "Persons",
        "frequency": "M",
        "source": "Banco de Espana / Seguridad Social",
        "priority": "high"
    },

    "registered_unemployment": {
        "series_code": "D_1JA0D000",
        "name": "Registered Unemployment",
        "category": "labour_market",
        "description": "Registered unemployed (paro registrado, SEPE), end of month, not seasonally adjusted (Boletin Estadistico 24.15)",
        "unit": "Persons",
        "frequency": "M",
        "source": "Banco de Espana / SEPE",
        "priority": "high"
    },

    "government_debt_pde": {
        "series_code": "DMNPDE2010_P00000_PS_APU",
        "name": "General Government Debt (EDP)",
        "category": "public_finances",
        "description": "General government debt under the Excessive Deficit Procedure (PDE, ESA 2010), stock. Source unit: thousands of EUR; processed in millions of EUR (Boletin Estadistico 3.22)",
        "unit": "Millions EUR",
        "value_divisor": 1000,
        "frequency": "M",
        "source": "Banco de Espana",
        "priority": "high"
    },
}


# Indicator groupings for different dashboard views
INDICATOR_GROUPS = {
    "interest_rates": [
        "euribor_12m_monthly", "euribor_3m_daily", "euribor_12m_daily",
        "ester_daily", "euribor_1w_daily", "euribor_1m_daily", "euribor_6m_daily",
        "spain_10y_bond", "spain_2y_bond", "spain_3y_bond", "spain_5y_bond",
        "spain_15y_bond", "spain_tbill_3m", "spain_tbill_6m", "spain_tbill_1y",
        "germany_10y_bond", "france_10y_bond", "italy_10y_bond"
    ],
    "credit_banking": [
        "mortgage_rate", "consumer_credit_rate", "corporate_lending_rate",
        "household_deposit_rate", "household_overnight_deposit_rate",
        "credit_households_total", "credit_nfc_total"
    ],
    "credit_growth": ["credit_households_growth", "credit_nfc_growth"],
    "debt_ratios": [
        "household_debt_gdp", "nfc_debt_gdp"
    ],
    "financial_stability": ["npl_ratio"],
    "labour_market": ["social_security_affiliates", "registered_unemployment"],
    "public_finances": ["government_debt_pde"],
    "external_sector": [
        "current_account_balance", "tourism_receipts"
    ],
    # Key indicators for dashboard overview
    "dashboard_summary": [
        "euribor_12m_monthly", "spain_10y_bond", "mortgage_rate",
        "household_debt_gdp", "current_account_balance"
    ],
    # High priority indicators only
    "high_priority": [
        "euribor_12m_monthly", "euribor_3m_daily", "euribor_12m_daily",
        "spain_10y_bond", "mortgage_rate", "consumer_credit_rate",
        "corporate_lending_rate", "household_deposit_rate",
        "credit_households_total", "credit_nfc_total",
        "household_debt_gdp", "nfc_debt_gdp", "current_account_balance"
    ],
    # EURIBOR rates only
    "euribor": [
        "euribor_12m_monthly", "euribor_3m_daily", "euribor_12m_daily",
        "ester_daily", "euribor_1w_daily", "euribor_1m_daily", "euribor_6m_daily"
    ],
    # Government bond yields
    "bond_yields": [
        "spain_10y_bond", "spain_2y_bond", "spain_3y_bond", "spain_5y_bond",
        "spain_15y_bond", "spain_tbill_3m", "spain_tbill_6m", "spain_tbill_1y",
        "germany_10y_bond", "france_10y_bond", "italy_10y_bond"
    ],
    # Bank lending rates
    "lending_rates": [
        "mortgage_rate", "consumer_credit_rate", "corporate_lending_rate",
        "household_deposit_rate"
    ]
}


def get_indicator(key: str) -> Dict[str, Any]:
    """
    Get indicator configuration by key.

    Args:
        key: Indicator key (e.g., 'euribor_12m_monthly')

    Returns:
        Dictionary with indicator configuration
    """
    return BDE_INDICATORS.get(key, {})


def get_all_series_codes() -> Dict[str, str]:
    """
    Get mapping of all indicator keys to their BdE series codes.

    Returns:
        Dictionary mapping indicator keys to series codes
    """
    return {key: info["series_code"] for key, info in BDE_INDICATORS.items()}


def get_indicators_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all indicators for a specific category.

    Args:
        category: Category name (e.g., 'interest_rates', 'credit_banking')

    Returns:
        Dictionary of indicators in that category
    """
    return {
        key: info
        for key, info in BDE_INDICATORS.items()
        if info.get("category") == category
    }


def get_indicators_by_frequency(frequency: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all indicators with a specific frequency.

    Args:
        frequency: Frequency code ('D', 'M', 'Q', 'A')

    Returns:
        Dictionary of indicators with that frequency
    """
    return {
        key: info
        for key, info in BDE_INDICATORS.items()
        if info.get("frequency") == frequency
    }


def get_indicators_by_priority(priority: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all indicators with a specific priority level.

    Args:
        priority: Priority level ('high', 'medium', 'low')

    Returns:
        Dictionary of indicators with that priority
    """
    return {
        key: info
        for key, info in BDE_INDICATORS.items()
        if info.get("priority") == priority
    }


def get_indicator_group(group_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Get indicators for a predefined group.

    Args:
        group_name: Name of the indicator group

    Returns:
        Dictionary of indicators in that group
    """
    if group_name not in INDICATOR_GROUPS:
        return {}

    keys = INDICATOR_GROUPS[group_name]
    return {key: BDE_INDICATORS[key] for key in keys if key in BDE_INDICATORS}


def list_groups() -> List[str]:
    """
    List all available indicator groups.

    Returns:
        List of group names
    """
    return list(INDICATOR_GROUPS.keys())


def list_categories() -> List[str]:
    """
    List all available categories.

    Returns:
        List of category names
    """
    categories = set(info.get("category", "") for info in BDE_INDICATORS.values())
    return sorted(list(categories))


class BdeIndicatorFetcher:
    """Fetcher for Banco de Espana economic indicators."""

    def __init__(
        self,
        output_dir: str = "data/raw/bde",
        language: str = "EN",
    ):
        """
        Initialize the fetcher.

        Args:
            output_dir: Directory to save CSV files
            language: Language for API responses ('EN' or 'ES')
        """
        self.client = BdeClient(language=language)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

    def _get_time_range(self, frequency: str) -> str:
        """Get appropriate time range for frequency."""
        return get_appropriate_range(frequency, years=5)

    def fetch_keys(self, keys: List[str], time_range: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch several indicators with as few requests as possible.

        The BdE API accepts many series in one request (one time range per request). Every
        series keeps HISTORY_YEARS of history: monthly/quarterly with MAX (trimmed); daily with
        36M plus earlier calendar years (rango=YYYY) from the series' first date, merged. A series missing from the response, or a failed
        request, keeps the previous raw file and logs an error (audit H1).
        """
        results: Dict[str, pd.DataFrame] = {}
        valid = []
        for key in keys:
            if key not in BDE_INDICATORS:
                logger.warning(f"Unknown indicator key: {key}")
                results[key] = pd.DataFrame()
            else:
                valid.append(key)

        today = pd.Timestamp.today().normalize()
        cutoff = today - pd.DateOffset(years=HISTORY_YEARS)
        first_recent_year = (today - pd.DateOffset(months=36)).year

        def is_daily(key):
            return BDE_INDICATORS[key].get("frequency", "M") == "D"

        def fetch(groups):
            """groups: {range: [keys]} -> ({key: [df]}, {key: reason}, {key: first date})"""
            batches = [(rng, ks[i:i + BATCH_SIZE]) for rng, ks in groups.items()
                       for i in range(0, len(ks), BATCH_SIZE)]

            def run(batch):
                rng, ks = batch
                return self.client.get_series([BDE_INDICATORS[k]["series_code"] for k in ks], rng)

            got, bad, start = {}, {}, {}
            for (rng, ks), (data, exc) in zip(batches, map_bounded(run, batches, MAX_WORKERS)):
                by_code = {item.get("serie"): item for item in (data or []) if isinstance(item, dict)}
                for key in ks:
                    item = by_code.get(BDE_INDICATORS[key]["series_code"])
                    df = self.client.series_to_dataframe(item) if item else pd.DataFrame()
                    if df.empty:
                        bad[key] = f"range {rng}" + (f" ({exc})" if exc else "")
                        continue
                    got.setdefault(key, []).append(df.assign(_recent=(rng == DAILY_RECENT)))
                    if item.get("fechaInicio"):
                        start[key] = pd.Timestamp(item["fechaInicio"]).tz_localize(None)
            return got, bad, start

        # Phase 1: the recent range for every series (36M daily; MAX otherwise, trimmed below).
        groups = {}
        for key in valid:
            rng = time_range or (DAILY_RECENT if is_daily(key) else "MAX")
            groups.setdefault(rng, []).append(key)
        parts, failed, inception = fetch(groups)
        logger.info(f"BdE phase 1: {len(valid)} series")

        # Phase 2: earlier calendar years for daily series (the API caps daily ranges at 36M),
        # only for years in which the series exists (asking for a year before a series starts
        # makes the API reject the whole batch with 412).
        if not time_range:
            groups = {}
            for key in valid:
                if not is_daily(key) or key in failed:
                    continue
                first_year = max(cutoff.year, inception.get(key, cutoff).year)
                for y in range(first_year, first_recent_year + 1):
                    groups.setdefault(str(y), []).append(key)
            if groups:
                more, more_failed, _ = fetch(groups)
                for key, dfs in more.items():
                    parts.setdefault(key, []).extend(dfs)
                failed.update(more_failed)
                logger.info(f"BdE phase 2: {sum(len(v) for v in groups.values())} series-years")

        for key in valid:
            config = BDE_INDICATORS[key]
            if key in failed or key not in parts:
                # Any missing piece keeps the whole previous file: a partial history is not published.
                logger.error(f"BdE {key} ({config['series_code']}): fetch failed or no data "
                             f"({failed.get(key, 'no response')}); keeping the previous {key}_raw.csv")
                results[key] = pd.DataFrame()
                continue
            # On overlapping dates the most recent request (36M) wins.
            df = (pd.concat(parts[key], ignore_index=True)
                  .sort_values(["date", "_recent"])
                  .drop_duplicates(subset=["date"], keep="last")
                  .drop(columns="_recent"))
            if not time_range:
                df = df[df["date"] >= cutoff]
            df = df.sort_values("date").reset_index(drop=True)
            df["indicator"] = key
            df["name"] = config["name"]
            df["category"] = config.get("category", "")
            self._save_csv(df, f"{key}_raw.csv")
            logger.info(f"Fetched {key}: {len(df)} rows")
            results[key] = df
        return results

    def fetch_indicator(self, key: str, time_range: Optional[str] = None) -> pd.DataFrame:
        """Fetch a single indicator by its key (e.g. 'euribor_12m_monthly')."""
        return self.fetch_keys([key], time_range)[key]

    def fetch_group(self, group_name: str, time_range: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Fetch all indicators in a group."""
        if group_name not in INDICATOR_GROUPS:
            logger.warning(f"Unknown group: {group_name}")
            return {}
        return self.fetch_keys(list(INDICATOR_GROUPS[group_name]), time_range)

    def fetch_category(self, category: str, time_range: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Fetch all indicators in a category (e.g., 'interest_rates', 'credit_banking')."""
        return self.fetch_keys(list(get_indicators_by_category(category)), time_range)

    def fetch_all(self, time_range: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Fetch all configured indicators."""
        results = self.fetch_keys(list(BDE_INDICATORS), time_range)
        success = sum(1 for df in results.values() if not df.empty)
        logger.info(f"BdE fetch: {success} of {len(results)} indicators fetched")
        return results

    def fetch_selected(self, keys: List[str], time_range: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Fetch selected indicators by key."""
        return self.fetch_keys(list(keys), time_range)

    def fetch_latest(self, keys: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fetch latest values for all or selected indicators.

        Args:
            keys: Optional list of indicator keys (defaults to all)

        Returns:
            DataFrame with latest values
        """
        if keys is None:
            keys = list(BDE_INDICATORS.keys())

        series_codes = [BDE_INDICATORS[k]["series_code"] for k in keys if k in BDE_INDICATORS]

        logger.info(f"Fetching latest values for {len(series_codes)} indicators...")

        df = self.client.get_latest_as_dataframe(series_codes)

        if not df.empty:
            # Add indicator keys
            code_to_key = {v["series_code"]: k for k, v in BDE_INDICATORS.items()}
            df["indicator"] = df["series_code"].map(code_to_key)

            filename = "latest_values.csv"
            self._save_csv(df, filename)

        return df

    def close(self) -> None:
        """Close the client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# =============================================================================
# SITE EXPORT METADATA (consumed by src/export/bde.py)
# =============================================================================
# Spanish titles, descriptions, series labels and public BdE pages for every
# indicator in BDE_INDICATORS. `kind` selects the field set exported to
# site/data/bde/<key>.json (see src/export/bde.py):
#   rate_daily_chg   daily rate: value + changes over 30 days / YTD / 1 year (pp)
#   rate_daily       daily rate: value
#   rate_monthly     monthly rate: value
#   rate_monthly_chg monthly rate: value + monthly change (pp)
#   credit_stock     stock of credit: value + monthly and annual growth
#   ratio            quarterly ratio to GDP: value + quarterly change (pp)
#   balance          balance of payments flow: value + rolling 12m sum
#   receipts         balance of payments flow: value + annual growth
# `currency`/`scale` apply to money amounts only (scale 6 = millions, 9 = billions).

BDE_URL_RATES = "https://www.bde.es/webbe/es/estadisticas/temas/tipos-interes.html"
BDE_URL_MARKETS = "https://www.bde.es/webbe/es/estadisticas/temas/mercados-financieros.html"
BDE_URL_INSTITUTIONS = "https://www.bde.es/webbe/es/estadisticas/temas/instituciones-financieras.html"
BDE_URL_ACCOUNTS = "https://www.bde.es/webbe/es/estadisticas/temas/cuentas-financieras.html"
BDE_URL_EXTERNAL = "https://www.bde.es/webbe/es/estadisticas/temas/estadisticas-exteriores.html"
BDE_URL_LABOUR = "https://www.bde.es/webbe/es/estadisticas/temas/estadisticas-economicas-generales.html"
BDE_URL_PUBLIC = "https://www.bde.es/webbe/es/estadisticas/temas/administraciones-publicas.html"

# Derived datasets computed in the processor from two processed BdE series
# (no API call of their own). value = `minuend` - `subtrahend`, in pp, on the
# dates both series share. Both inputs are BdE "Economia internacional"
# monthly series (Maastricht long-term yield, monthly average), so the
# definitions are homogeneous; the frequency is that of the German/Italian
# series (monthly).
BDE_DERIVED: Dict[str, Dict[str, Any]] = {
    "spread_10y_de": {
        "minuend": "spain_10y_bond_monthly",
        "subtrahend": "germany_10y_bond",
        "frequency": "M",
        "series_code": "D_1NBBO320 - D_1NBBO308",
    },
    "spread_10y_it": {
        "minuend": "spain_10y_bond_monthly",
        "subtrahend": "italy_10y_bond",
        "frequency": "M",
        "series_code": "D_1NBBO320 - D_1NBBO309",
    },
}

BDE_EXPORT_META: Dict[str, Dict[str, Any]] = {
    "euribor_12m_monthly": dict(kind="rate_monthly", url=BDE_URL_RATES, label_es="Euríbor 12 meses",
        title_es="Euríbor a 12 meses (media mensual)",
        description_es="Media mensual del Euríbor a un año."),
    "euribor_12m_daily": dict(kind="rate_daily_chg", url=BDE_URL_RATES, label_es="Euríbor 12 meses",
        title_es="Euríbor a 12 meses (diario)", description_es="Euríbor a un año, dato diario."),
    "euribor_6m_daily": dict(kind="rate_daily", url=BDE_URL_RATES, label_es="Euríbor 6 meses",
        title_es="Euríbor a 6 meses (diario)", description_es="Euríbor a seis meses, dato diario."),
    "euribor_3m_daily": dict(kind="rate_daily_chg", url=BDE_URL_RATES, label_es="Euríbor 3 meses",
        title_es="Euríbor a 3 meses (diario)", description_es="Euríbor a tres meses, dato diario."),
    "euribor_1m_daily": dict(kind="rate_daily", url=BDE_URL_RATES, label_es="Euríbor 1 mes",
        title_es="Euríbor a 1 mes (diario)", description_es="Euríbor a un mes, dato diario."),
    "euribor_1w_daily": dict(kind="rate_daily", url=BDE_URL_RATES, label_es="Euríbor 1 semana",
        title_es="Euríbor a 1 semana (diario)", description_es="Euríbor a una semana, dato diario."),
    "ester_daily": dict(kind="rate_daily_chg", url=BDE_URL_RATES, label_es="€STR",
        title_es="Tipo a corto plazo del euro (€STR)",
        description_es="Euro short-term rate (€STR), tipo de interés a un día publicado por el BCE."),
    "spain_10y_bond": dict(kind="rate_daily_chg", url=BDE_URL_MARKETS, label_es="España 10 años",
        title_es="Rentabilidad del bono español a 10 años",
        description_es="Rentabilidad de la deuda pública española a 10 años en el mercado secundario, dato diario."),
    "spain_5y_bond": dict(kind="rate_daily_chg", url=BDE_URL_MARKETS, label_es="España 5 años",
        title_es="Rentabilidad del bono español a 5 años",
        description_es="Rentabilidad de la deuda pública española a 5 años en el mercado secundario, dato diario."),
    "spain_3y_bond": dict(kind="rate_daily", url=BDE_URL_MARKETS, label_es="España 3 años",
        title_es="Rentabilidad del bono español a 3 años",
        description_es="Rentabilidad de la deuda pública española a 3 años en el mercado secundario, dato diario."),
    "spain_2y_bond": dict(kind="rate_daily", url=BDE_URL_MARKETS, label_es="España más de 2 años",
        title_es="Rentabilidad de la deuda española a más de 2 años",
        description_es="Rentabilidad de bonos y obligaciones del Estado a más de 2 años en el mercado secundario, dato diario."),
    "spain_15y_bond": dict(kind="rate_daily", url=BDE_URL_MARKETS, label_es="España 15 años",
        title_es="Rentabilidad del bono español a 15 años",
        description_es="Rentabilidad de la deuda pública española a 15 años en el mercado secundario, dato diario."),
    "spain_tbill_3m": dict(kind="rate_daily", url=BDE_URL_MARKETS, label_es="Letras 1 a 3 meses",
        title_es="Rentabilidad de las Letras del Tesoro a 1-3 meses",
        description_es="Rentabilidad de las Letras del Tesoro a plazo de 1 a 3 meses en el mercado secundario, dato diario."),
    "spain_tbill_6m": dict(kind="rate_daily", url=BDE_URL_MARKETS, label_es="Letras 6 meses",
        title_es="Rentabilidad de las Letras del Tesoro a 6 meses",
        description_es="Rentabilidad de las Letras del Tesoro a 6 meses en el mercado secundario, dato diario."),
    "spain_tbill_1y": dict(kind="rate_daily", url=BDE_URL_MARKETS, label_es="Letras 1 año",
        title_es="Rentabilidad de las Letras del Tesoro a 1 año",
        description_es="Rentabilidad de las Letras del Tesoro a 1 año en el mercado secundario, dato diario."),
    "spain_10y_bond_monthly": dict(kind="rate_monthly", url=BDE_URL_MARKETS, label_es="España",
        title_es="Rentabilidad de la deuda pública a 10 años: España (mensual)",
        description_es="Rendimiento de la deuda pública a largo plazo (criterio de Maastricht), media mensual."),
    "germany_10y_bond": dict(kind="rate_monthly", url=BDE_URL_MARKETS, label_es="Alemania",
        title_es="Rentabilidad de la deuda pública a 10 años: Alemania (mensual)",
        description_es="Rendimiento de la deuda pública a largo plazo (criterio de Maastricht), media mensual."),
    "france_10y_bond": dict(kind="rate_monthly", url=BDE_URL_MARKETS, label_es="Francia",
        title_es="Rentabilidad de la deuda pública a 10 años: Francia (mensual)",
        description_es="Rendimiento de la deuda pública a largo plazo (criterio de Maastricht), media mensual."),
    "italy_10y_bond": dict(kind="rate_monthly", url=BDE_URL_MARKETS, label_es="Italia",
        title_es="Rentabilidad de la deuda pública a 10 años: Italia (mensual)",
        description_es="Rendimiento de la deuda pública a largo plazo (criterio de Maastricht), media mensual."),
    "mortgage_rate": dict(kind="rate_monthly_chg", url=BDE_URL_RATES, label_es="Hipotecas",
        title_es="Tipo de interés de los préstamos para vivienda",
        description_es="Tipo de interés de las nuevas operaciones de crédito a hogares para adquisición de vivienda."),
    "consumer_credit_rate": dict(kind="rate_monthly_chg", url=BDE_URL_RATES, label_es="Crédito al consumo",
        title_es="Tipo de interés del crédito al consumo",
        description_es="Tipo de interés de las nuevas operaciones de crédito a hogares para consumo."),
    "corporate_lending_rate": dict(kind="rate_monthly_chg", url=BDE_URL_RATES, label_es="Crédito a sociedades no financieras",
        title_es="Tipo de interés de los préstamos a sociedades no financieras",
        description_es="Tipo de interés de las nuevas operaciones de crédito a sociedades no financieras."),
    "household_deposit_rate": dict(kind="rate_monthly_chg", url=BDE_URL_RATES, label_es="Depósitos a plazo",
        title_es="Tipo de interés de los depósitos a plazo de los hogares",
        description_es="Tipo medio ponderado de las nuevas operaciones de depósitos a plazo de hogares."),
    "household_overnight_deposit_rate": dict(kind="rate_monthly_chg", url=BDE_URL_RATES, label_es="Depósitos a la vista",
        title_es="Tipo de interés de los depósitos a la vista de los hogares",
        description_es="Tipo de interés de los depósitos a la vista de hogares."),
    "credit_households_total": dict(kind="credit_stock", url=BDE_URL_INSTITUTIONS, label_es="Hogares",
        currency="EUR", scale=6, title_es="Crédito a hogares",
        description_es="Saldo del crédito a hogares e ISFLSH (préstamos y créditos, criterio de estadísticas monetarias de la UEM)."),
    "credit_nfc_total": dict(kind="credit_stock", url=BDE_URL_INSTITUTIONS, label_es="Sociedades no financieras",
        currency="EUR", scale=9, title_es="Crédito a sociedades no financieras",
        description_es="Saldo del crédito total a sociedades no financieras (SNF)."),
    "household_debt_gdp": dict(kind="ratio", url=BDE_URL_ACCOUNTS, label_es="Hogares",
        title_es="Deuda de los hogares sobre el PIB",
        description_es="Deuda de los hogares e ISFLSH en porcentaje del PIB a precios de mercado."),
    "nfc_debt_gdp": dict(kind="ratio", url=BDE_URL_ACCOUNTS, label_es="Sociedades no financieras",
        title_es="Deuda de las sociedades no financieras sobre el PIB",
        description_es="Deuda de las sociedades no financieras en porcentaje del PIB a precios de mercado."),
    "current_account_balance": dict(kind="balance", url=BDE_URL_EXTERNAL, label_es="España",
        currency="EUR", scale=6, title_es="Saldo por cuenta corriente",
        description_es="Saldo mensual de la cuenta corriente de la balanza de pagos, sin ajustar."),
    "tourism_receipts": dict(kind="receipts", url=BDE_URL_EXTERNAL, label_es="España",
        currency="EUR", scale=6, title_es="Ingresos por turismo",
        description_es="Ingresos mensuales por turismo en la cuenta corriente de la balanza de pagos."),
    "npl_ratio": dict(kind="npl", url=BDE_URL_INSTITUTIONS, label_es="España",
        title_es="Ratio de créditos dudosos",
        description_es="Créditos dudosos a otros sectores residentes en porcentaje del crédito total, entidades de crédito y establecimientos financieros de crédito (tasa de morosidad)."),
    "social_security_affiliates": dict(kind="persons", url=BDE_URL_LABOUR, label_es="España",
        title_es="Afiliados a la Seguridad Social (último día del mes)",
        description_es="Afiliados a fin de mes, total de regímenes, sin desestacionalizar."),
    "registered_unemployment": dict(kind="persons", url=BDE_URL_LABOUR, label_es="España",
        title_es="Paro registrado",
        description_es="Demandantes de empleo no ocupados inscritos en los servicios públicos de empleo (SEPE), a fin de mes, sin desestacionalizar."),
    "government_debt_pde": dict(kind="debt_stock", url=BDE_URL_PUBLIC, label_es="Administraciones Públicas",
        currency="EUR", scale=6, title_es="Deuda de las Administraciones Públicas (PDE)",
        description_es="Deuda de las Administraciones Públicas según el Protocolo de Déficit Excesivo (SEC 2010), saldo a fin de mes."),
}


# Export metadata of the derived spreads (see BDE_DERIVED).
BDE_DERIVED_META: Dict[str, Dict[str, Any]] = {
    "spread_10y_de": dict(url=BDE_URL_MARKETS, label_es="España frente a Alemania",
        title_es="Diferencial de rentabilidad a 10 años: España frente a Alemania",
        description_es="Rentabilidad de la deuda pública española a 10 años menos la alemana (media mensual, criterio de Maastricht). Prima de riesgo.",
        value_label="Diferencial frente a Alemania",
        note_es="Diferencia entre las rentabilidades de la deuda pública a 10 años de España y Alemania, en puntos porcentuales (1 p. p. = 100 p. b.). Media mensual."),
    "spread_10y_it": dict(url=BDE_URL_MARKETS, label_es="España frente a Italia",
        title_es="Diferencial de rentabilidad a 10 años: España frente a Italia",
        description_es="Rentabilidad de la deuda pública española a 10 años menos la italiana (media mensual, criterio de Maastricht).",
        value_label="Diferencial frente a Italia",
        note_es="Diferencia entre las rentabilidades de la deuda pública a 10 años de España e Italia, en puntos porcentuales (1 p. p. = 100 p. b.). Un valor negativo significa que España paga menos que Italia. Media mensual."),
}
