"""
Data loading utilities for the dashboard.
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# COLUMN NAMING CONVENTION
# =============================================================================
# Each indicator has a unique value_col name defined in its INDICATORS entry
# (e.g., "gdp_index", "ipi_index", "unemployment_rate"). This is intentional
# for disambiguation when multiple indicators are merged into comparison
# datasets. The value_col name is the authoritative mapping between the
# processed CSV columns and the dashboard rendering code.
# =============================================================================

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
EUROSTAT_DIR = DATA_DIR / "eurostat"
YAHOO_DIR = DATA_DIR / "yahoo"
BDE_DIR = DATA_DIR / "bde"


def load_indicator(filename: str, subdir: str = None, date_col: str = "date") -> pd.DataFrame:
    """Load a processed indicator CSV file."""
    if subdir:
        filepath = DATA_DIR / subdir / filename
    else:
        filepath = DATA_DIR / filename
    if filepath.exists():
        df = pd.read_csv(filepath)
        # Parse date column if it exists
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            # Remove rows with NaT dates to prevent corrupted data from reaching the dashboard
            df = df[df[date_col].notna()].copy()
            return df.sort_values(date_col)
        return df
    return pd.DataFrame()


def load_all_indicators() -> dict:
    """Load all INE indicator data (Spain)."""
    return {
        "gdp": load_indicator("gdp.csv"),
        "gdp_demand": load_indicator("gdp_demand.csv"),
        "industrial_production": load_indicator("industrial_production.csv"),
        "ipi_sectors": load_indicator("ipi_sectors.csv"),
        "industry_turnover": load_indicator("industry_turnover.csv"),
        "services_turnover": load_indicator("services_turnover.csv"),
        "services_production": load_indicator("services_production.csv"),
        "ipss_sectors": load_indicator("ipss_sectors.csv"),
        # Labor Market - EPA
        "unemployment": load_indicator("unemployment.csv"),
        "employment_rate": load_indicator("employment_rate.csv"),
        "activity_rate": load_indicator("activity_rate.csv"),
        "employed": load_indicator("employed.csv"),
        "temporary_rate": load_indicator("temporary_rate.csv"),
        "parttime_rate": load_indicator("parttime_rate.csv"),
        "youth_unemployment": load_indicator("youth_unemployment.csv"),
        # Labor Market - Labor Costs
        "labor_cost": load_indicator("labor_cost.csv"),
        "labor_cost_hour": load_indicator("labor_cost_hour.csv"),
        "labor_cost_components": load_indicator("labor_cost_components.csv"),
        # Prices
        "cpi": load_indicator("cpi.csv"),
        "cpi_special_groups": load_indicator("cpi_special_groups.csv"),
        "cpi_weights": load_indicator("cpi_weights.csv", date_col=None),
        "cpi_ecoicop_groups": load_indicator("cpi_ecoicop_groups.csv"),
        "retail_sales": load_indicator("retail_sales.csv"),
        "house_prices": load_indicator("house_prices.csv"),
        # Industrial Prices
        "ipri": load_indicator("ipri.csv"),
        # Productivity
        "gdp_productivity": load_indicator("gdp_productivity.csv"),
        # CPI by CCAA
        "cpi_ccaa": load_indicator("cpi_ccaa.csv"),
        # Business Confidence
        "business_confidence": load_indicator("business_confidence.csv"),
    }


def load_eurostat_indicators() -> dict:
    """Load all Eurostat indicator data (Spain + EU27 comparison)."""
    return {
        # Economic Activity
        "gdp_growth_spain": load_indicator("gdp_growth_spain.csv", "eurostat"),
        "gdp_growth_eu27": load_indicator("gdp_growth_eu27.csv", "eurostat"),
        "gdp_growth_comparison": load_indicator("gdp_growth_comparison.csv", "eurostat"),
        "gdp_index_comparison": load_indicator("gdp_index_comparison.csv", "eurostat"),
        "ipi_spain": load_indicator("industrial_production_spain.csv", "eurostat"),
        "ipi_eu27": load_indicator("industrial_production_eu27.csv", "eurostat"),
        "ipi_comparison": load_indicator("industrial_production_comparison.csv", "eurostat"),
        "esi_spain": load_indicator("economic_sentiment_spain.csv", "eurostat"),
        "esi_eu27": load_indicator("economic_sentiment_eu27.csv", "eurostat"),
        "esi_comparison": load_indicator("economic_sentiment_comparison.csv", "eurostat"),

        # Labor Market
        "unemployment_spain_eu": load_indicator("unemployment_spain.csv", "eurostat"),
        "unemployment_eu27": load_indicator("unemployment_eu27.csv", "eurostat"),
        "unemployment_comparison": load_indicator("unemployment_comparison.csv", "eurostat"),
        "employment_growth_spain": load_indicator("employment_growth_spain.csv", "eurostat"),
        "employment_growth_eu27": load_indicator("employment_growth_eu27.csv", "eurostat"),

        # Prices & Inflation
        "hicp_spain": load_indicator("hicp_spain.csv", "eurostat"),
        "hicp_eu27": load_indicator("hicp_eu27.csv", "eurostat"),
        "hicp_comparison": load_indicator("hicp_comparison.csv", "eurostat"),
        "core_inflation_spain": load_indicator("core_inflation_spain.csv", "eurostat"),
        "core_inflation_eu27": load_indicator("core_inflation_eu27.csv", "eurostat"),
        "ppi_spain": load_indicator("producer_prices_spain.csv", "eurostat"),
        "ppi_eu27": load_indicator("producer_prices_eu27.csv", "eurostat"),

        # External Sector
        "trade_balance": load_indicator("trade_balance_spain.csv", "eurostat"),

        # Public Finances
        "debt_spain": load_indicator("government_debt_spain.csv", "eurostat"),
        "debt_eu27": load_indicator("government_debt_eu27.csv", "eurostat"),
        "debt_comparison": load_indicator("government_debt_comparison.csv", "eurostat"),
        "deficit_spain": load_indicator("budget_deficit_spain.csv", "eurostat"),
        "deficit_eu27": load_indicator("budget_deficit_eu27.csv", "eurostat"),

        # Consumer & Household
        "consumer_confidence_spain": load_indicator("consumer_confidence_spain.csv", "eurostat"),
        "consumer_confidence_eu27": load_indicator("consumer_confidence_eu27.csv", "eurostat"),
        "retail_spain_eu": load_indicator("retail_trade_spain.csv", "eurostat"),
        "retail_eu27": load_indicator("retail_trade_eu27.csv", "eurostat"),
        "hpi_spain_eu": load_indicator("house_prices_spain.csv", "eurostat"),
        "hpi_eu27": load_indicator("house_prices_eu27.csv", "eurostat"),
        "hpi_comparison": load_indicator("house_prices_comparison.csv", "eurostat"),
    }


def load_eurostat_summary() -> pd.DataFrame:
    """Load the Eurostat summary dataset."""
    return load_indicator("summary.csv", "eurostat")


def load_yahoo_indicators() -> dict:
    """Load all Yahoo Finance indicator data (Financial Markets)."""
    return {
        # Stock Indices
        "ibex_35": load_indicator("ibex_35_processed.csv", "yahoo"),
        "euro_stoxx_50": load_indicator("euro_stoxx_50_processed.csv", "yahoo"),
        "sp_500": load_indicator("sp_500_processed.csv", "yahoo"),
        "nasdaq_composite": load_indicator("nasdaq_composite_processed.csv", "yahoo"),
        "dax": load_indicator("dax_processed.csv", "yahoo"),
        "ftse_100": load_indicator("ftse_100_processed.csv", "yahoo"),

        # Currencies
        "eur_usd": load_indicator("eur_usd_processed.csv", "yahoo"),
        "eur_gbp": load_indicator("eur_gbp_processed.csv", "yahoo"),
        "dxy": load_indicator("dxy_processed.csv", "yahoo"),

        # Commodities
        "gold": load_indicator("gold_processed.csv", "yahoo"),
        "brent_crude": load_indicator("brent_crude_processed.csv", "yahoo"),
        "wti_crude": load_indicator("wti_crude_processed.csv", "yahoo"),
        "natural_gas": load_indicator("natural_gas_processed.csv", "yahoo"),

        # Volatility
        "vix": load_indicator("vix_processed.csv", "yahoo"),
        "vstoxx": load_indicator("vstoxx_processed.csv", "yahoo"),

        # Bonds (ETFs)
        "spain_govt_bond_etf": load_indicator("spain_govt_bond_etf_processed.csv", "yahoo"),
        "us_treasury_20y_etf": load_indicator("us_treasury_20y_etf_processed.csv", "yahoo"),

        # US Treasury Yields
        "us_treasury_5y": load_indicator("us_treasury_5y_processed.csv", "yahoo"),
        "us_treasury_10y": load_indicator("us_treasury_10y_processed.csv", "yahoo"),
        "us_treasury_30y": load_indicator("us_treasury_30y_processed.csv", "yahoo"),

        # Sector ETFs
        "spanish_banks_etf": load_indicator("spanish_banks_etf_processed.csv", "yahoo"),
        "european_banks_etf": load_indicator("european_banks_etf_processed.csv", "yahoo"),

        # Comparison datasets
        "stock_indices_comparison": load_indicator("stock_indices_comparison.csv", "yahoo"),
        "commodities_comparison": load_indicator("commodities_comparison.csv", "yahoo"),
        "market_summary": load_indicator("market_summary.csv", "yahoo"),
    }


def load_summary() -> pd.DataFrame:
    """Load the summary dataset."""
    return load_indicator("summary.csv")


# =============================================================================
# BANCO DE ESPANA DATA LOADING FUNCTIONS
# =============================================================================

def load_bde_indicator(filename: str, date_col: str = "date") -> pd.DataFrame:
    """
    Load a processed BdE indicator CSV file.

    Args:
        filename: Name of the CSV file
        date_col: Name of the date column

    Returns:
        DataFrame with the indicator data
    """
    return load_indicator(filename, subdir="bde", date_col=date_col)


def load_bde_interest_rates() -> dict:
    """
    Load BdE interest rate data including EURIBOR rates and bond yields.

    Returns:
        Dictionary mapping indicator keys to DataFrames
    """
    return {
        # EURIBOR rates
        "euribor_12m_monthly": load_bde_indicator("euribor_12m_monthly_processed.csv"),
        "euribor_3m_daily": load_bde_indicator("euribor_3m_daily_processed.csv"),
        "euribor_12m_daily": load_bde_indicator("euribor_12m_daily_processed.csv"),
        "ester_daily": load_bde_indicator("ester_daily_processed.csv"),
        "euribor_1w_daily": load_bde_indicator("euribor_1w_daily_processed.csv"),
        "euribor_1m_daily": load_bde_indicator("euribor_1m_daily_processed.csv"),
        "euribor_6m_daily": load_bde_indicator("euribor_6m_daily_processed.csv"),
        # Government bond yields - Spain
        "spain_10y_bond": load_bde_indicator("spain_10y_bond_processed.csv"),
        "spain_2y_bond": load_bde_indicator("spain_2y_bond_processed.csv"),
        "spain_3y_bond": load_bde_indicator("spain_3y_bond_processed.csv"),
        "spain_5y_bond": load_bde_indicator("spain_5y_bond_processed.csv"),
        "spain_15y_bond": load_bde_indicator("spain_15y_bond_processed.csv"),
        "spain_tbill_3m": load_bde_indicator("spain_tbill_3m_processed.csv"),
        "spain_tbill_6m": load_bde_indicator("spain_tbill_6m_processed.csv"),
        "spain_tbill_1y": load_bde_indicator("spain_tbill_1y_processed.csv"),
        # Government bond yields - European (10Y) - Monthly
        "spain_10y_bond_monthly": load_bde_indicator("spain_10y_bond_monthly_processed.csv"),
        "germany_10y_bond": load_bde_indicator("germany_10y_bond_processed.csv"),
        "france_10y_bond": load_bde_indicator("france_10y_bond_processed.csv"),
        "italy_10y_bond": load_bde_indicator("italy_10y_bond_processed.csv"),
        # Comparison datasets
        "euribor_comparison": load_bde_indicator("euribor_comparison.csv"),
        "yield_curve": load_bde_indicator("yield_curve.csv"),
    }


def load_bde_credit_data() -> dict:
    """
    Load BdE credit and banking data including lending rates and credit volumes.

    Returns:
        Dictionary mapping indicator keys to DataFrames
    """
    return {
        # Bank lending rates
        "mortgage_rate": load_bde_indicator("mortgage_rate_processed.csv"),
        "consumer_credit_rate": load_bde_indicator("consumer_credit_rate_processed.csv"),
        "corporate_lending_rate": load_bde_indicator("corporate_lending_rate_processed.csv"),
        "household_deposit_rate": load_bde_indicator("household_deposit_rate_processed.csv"),
        "household_overnight_deposit_rate": load_bde_indicator("household_overnight_deposit_rate_processed.csv"),
        # Credit volumes
        "credit_households_total": load_bde_indicator("credit_households_total_processed.csv"),
        "credit_nfc_total": load_bde_indicator("credit_nfc_total_processed.csv"),
        # Comparison dataset
        "lending_rates_comparison": load_bde_indicator("lending_rates_comparison.csv"),
    }


def load_bde_debt_ratios() -> dict:
    """
    Load BdE debt-to-GDP ratio data.

    Returns:
        Dictionary mapping indicator keys to DataFrames
    """
    return {
        "household_debt_gdp": load_bde_indicator("household_debt_gdp_processed.csv"),
        "nfc_debt_gdp": load_bde_indicator("nfc_debt_gdp_processed.csv"),
        "debt_ratios_comparison": load_bde_indicator("debt_ratios_comparison.csv"),
    }


def load_bde_external_sector() -> dict:
    """
    Load BdE external sector data (current account, tourism).

    Returns:
        Dictionary mapping indicator keys to DataFrames
    """
    return {
        "current_account_balance": load_bde_indicator("current_account_balance_processed.csv"),
        "tourism_receipts": load_bde_indicator("tourism_receipts_processed.csv"),
    }


def load_bde_summary() -> pd.DataFrame:
    """
    Load the BdE summary table with latest values for all indicators.

    Returns:
        DataFrame with summary data
    """
    return load_bde_indicator("bde_summary.csv")


def load_all_bde_indicators() -> dict:
    """
    Load all BdE indicators into a single dictionary.

    Returns:
        Dictionary with all BdE indicator data
    """
    data = {}
    data.update(load_bde_interest_rates())
    data.update(load_bde_credit_data())
    data.update(load_bde_debt_ratios())
    data.update(load_bde_external_sector())
    return data


def load_data_store() -> dict:
    """Load all data sources into a single dict with error isolation.

    Each source is loaded independently so that a failure in one
    (e.g. missing files, corrupt CSV) does not prevent the rest
    of the dashboard from rendering.
    """
    sources = [
        ("ine", load_all_indicators),
        ("eurostat", load_eurostat_indicators),
        ("yahoo", load_yahoo_indicators),
        ("bde_rates", load_bde_interest_rates),
        ("bde_credit", load_bde_credit_data),
        ("bde_debt", load_bde_debt_ratios),
        ("bde_external", load_bde_external_sector),
    ]
    store = {}
    for key, loader in sources:
        try:
            store[key] = loader()
            n = sum(1 for v in store[key].values()
                    if isinstance(v, pd.DataFrame) and not v.empty)
            logger.info("Loaded %s: %d indicators with data", key, n)
        except Exception as e:
            logger.warning("Failed to load %s: %s", key, e)
            store[key] = {}
    return store


def get_latest_value(df: pd.DataFrame, value_col: str) -> dict:
    """Get the latest value and metadata from a dataframe."""
    if df.empty:
        return {"value": None, "date": None, "yoy_change": None}

    latest = df.iloc[-1]
    return {
        "value": latest[value_col],
        "date": latest["date"],
        "yoy_change": latest.get("yoy_change"),
    }


def get_last_update_time() -> str:
    """Get the timestamp of the last data update."""
    summary_file = DATA_DIR / "summary.csv"
    if summary_file.exists():
        mtime = datetime.fromtimestamp(summary_file.stat().st_mtime)
        return mtime.strftime("%Y-%m-%d %H:%M")
    return "Unknown"


# Indicator metadata
INDICATORS = {
    "gdp": {
        "name": "PIB",
        "full_name": "Producto Interior Bruto",
        "value_col": "gdp_index",
        "unit": "Índice",
        "frequency": "Trimestral",
        "description": "Índice de volumen encadenado de la producción económica.",
        "positive_is_good": True,
    },
    "industrial_production": {
        "name": "Producción Industrial",
        "full_name": "Índice de Producción Industrial",
        "value_col": "ipi_index",
        "unit": "Índice",
        "frequency": "Mensual",
        "description": "Mide la producción del sector industrial.",
        "positive_is_good": True,
    },
    "industry_turnover": {
        "name": "Cifra Negocios Industria",
        "full_name": "Índice de Cifra de Negocios de la Industria",
        "value_col": "turnover_yoy",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Variación interanual de la cifra de negocios del sector industrial.",
        "positive_is_good": True,
    },
    "services_turnover": {
        "name": "Cifra Negocios Servicios",
        "full_name": "Índice de Actividad del Sector Servicios (Cifra de Negocios)",
        "value_col": "turnover_yoy",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Variación interanual de la cifra de negocios del sector servicios.",
        "positive_is_good": True,
    },
    "services_production": {
        "name": "Producción Servicios",
        "full_name": "Índice de Producción del Sector Servicios",
        "value_col": "services_prod_index",
        "unit": "Índice",
        "frequency": "Mensual",
        "description": "Índice de producción del sector servicios (base 2021).",
        "positive_is_good": True,
    },
    "unemployment": {
        "name": "Desempleo",
        "full_name": "Tasa de Paro",
        "value_col": "unemployment_rate",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Porcentaje de la población activa sin empleo.",
        "positive_is_good": False,  # Lower is better
    },
    "employment_rate": {
        "name": "Tasa de Empleo",
        "full_name": "Tasa de Empleo",
        "value_col": "employment_rate",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Porcentaje de la población en edad de trabajar que está empleada.",
        "positive_is_good": True,
    },
    "activity_rate": {
        "name": "Tasa de Actividad",
        "full_name": "Tasa de Actividad",
        "value_col": "activity_rate",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Porcentaje de la población que participa en el mercado laboral.",
        "positive_is_good": True,
    },
    "employed": {
        "name": "Ocupados",
        "full_name": "Número de Ocupados",
        "value_col": "employed",
        "unit": "Miles",
        "frequency": "Trimestral",
        "description": "Número total de personas empleadas (en miles).",
        "positive_is_good": True,
    },
    "temporary_rate": {
        "name": "Temporalidad",
        "full_name": "Tasa de Temporalidad",
        "value_col": "temporary_rate",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Porcentaje de asalariados con contrato temporal.",
        "positive_is_good": False,  # Lower is generally better (more job stability)
    },
    "parttime_rate": {
        "name": "Parcialidad",
        "full_name": "Tasa de Empleo a Tiempo Parcial",
        "value_col": "parttime_rate",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Porcentaje de ocupados con jornada a tiempo parcial.",
        "positive_is_good": None,  # Neutral - depends on context
    },
    "youth_unemployment": {
        "name": "Paro Juvenil",
        "full_name": "Tasa de Paro Juvenil",
        "value_col": "youth_unemployment_rate",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Tasa de paro de menores de 25 años.",
        "positive_is_good": False,
    },
    "labor_cost": {
        "name": "Coste Laboral",
        "full_name": "Coste Laboral por Trabajador",
        "value_col": "labor_cost",
        "unit": "€",
        "frequency": "Trimestral",
        "description": "Coste laboral total por trabajador y mes.",
        "positive_is_good": None,  # Depends on perspective
    },
    "labor_cost_hour": {
        "name": "Coste/Hora",
        "full_name": "Coste Laboral por Hora",
        "value_col": "labor_cost_hour",
        "unit": "€",
        "frequency": "Trimestral",
        "description": "Coste laboral por hora efectiva trabajada.",
        "positive_is_good": None,
    },
    "cpi": {
        "name": "Inflación",
        "full_name": "Índice de Precios al Consumo",
        "value_col": "cpi_index",
        "change_col": "inflation_rate",
        "unit": "Índice",
        "frequency": "Mensual",
        "description": "Mide los cambios en los precios al consumidor.",
        "positive_is_good": None,  # Neutral - depends on level
    },
    "retail_sales": {
        "name": "Comercio Minorista",
        "full_name": "Índice de Comercio al por Menor",
        "value_col": "retail_index",
        "unit": "Índice",
        "frequency": "Mensual",
        "description": "Mide la actividad del comercio minorista.",
        "positive_is_good": True,
    },
    "house_prices": {
        "name": "Precio Vivienda",
        "full_name": "Índice de Precios de Vivienda",
        "value_col": "hpi_index",
        "unit": "Índice",
        "frequency": "Trimestral",
        "description": "Mide los cambios en los precios de la vivienda residencial.",
        "positive_is_good": None,  # Depends on perspective
    },
    "gdp_demand": {
        "name": "PIB por Demanda",
        "full_name": "Desglose del PIB por Demanda",
        "value_col": "contribution",
        "unit": "Índice",
        "frequency": "Trimestral",
        "description": "Desglose del PIB por componentes de demanda (consumo, inversión, sector exterior).",
        "positive_is_good": True,
    },
    "cpi_special_groups": {
        "name": "Desglose Inflación",
        "full_name": "Grupos Especiales del IPC",
        "value_col": "value",
        "unit": "Índice",
        "frequency": "Mensual",
        "description": "Desglose del IPC por grupos especiales (subyacente, energía, alimentos).",
        "positive_is_good": None,
    },
}


# Labels for GDP demand components
GDP_DEMAND_LABELS = {
    "private_consumption": "Consumo Privado",
    "public_consumption": "Consumo Público",
    "gfcf": "FBCF",
    "external_demand": "Demanda Externa",
    "household_consumption": "Consumo de Hogares",
    "government_consumption": "Gasto Público",
    "exports": "Exportaciones",
    "imports": "Importaciones",
}

# Labels for CPI special groups
CPI_GROUP_LABELS = {
    "headline": "IPC General",
    "core": "Inflación Subyacente",
    "energy": "Energía",
    "unprocessed_food": "Alimentos No Elaborados",
    "processed_food": "Alimentos Elaborados",
    "services": "Servicios",
    "non_energy_goods": "Bienes Industriales",
}


# Eurostat indicator metadata for EU comparison
EUROSTAT_INDICATORS = {
    "gdp_growth": {
        "name": "Crecimiento PIB",
        "value_col": "gdp_growth_qoq",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Tasa de crecimiento trimestral del PIB.",
        "positive_is_good": True,
    },
    "industrial_production": {
        "name": "Producción Industrial",
        "value_col": "ipi_index",
        "unit": "Índice",
        "frequency": "Mensual",
        "description": "Índice de producción industrial (2021=100).",
        "positive_is_good": True,
    },
    "economic_sentiment": {
        "name": "Sentimiento Económico",
        "value_col": "esi",
        "unit": "Índice",
        "frequency": "Mensual",
        "description": "Indicador de Sentimiento Económico (100=media largo plazo).",
        "positive_is_good": True,
    },
    "unemployment_eu": {
        "name": "Tasa de Paro",
        "value_col": "unemployment_rate",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Tasa de paro armonizada (25-74 años).",
        "positive_is_good": False,
    },
    "hicp": {
        "name": "Inflación IPCA",
        "value_col": "hicp_inflation",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Índice de Precios al Consumo Armonizado (tasa anual).",
        "positive_is_good": None,
    },
    "core_inflation": {
        "name": "Inflación Subyacente",
        "value_col": "core_inflation",
        "unit": "%",
        "frequency": "Mensual",
        "description": "IPCA excluyendo energía y alimentos.",
        "positive_is_good": None,
    },
    "government_debt": {
        "name": "Deuda Pública",
        "value_col": "debt_to_gdp",
        "unit": "% PIB",
        "frequency": "Trimestral",
        "description": "Deuda bruta consolidada de las administraciones públicas.",
        "positive_is_good": False,
    },
    "consumer_confidence": {
        "name": "Confianza del Consumidor",
        "value_col": "consumer_confidence",
        "unit": "Saldo",
        "frequency": "Mensual",
        "description": "Indicador de confianza del consumidor.",
        "positive_is_good": True,
    },
    "house_prices_eu": {
        "name": "Precios Vivienda",
        "value_col": "hpi_index",
        "unit": "Índice",
        "frequency": "Trimestral",
        "description": "Índice de precios de vivienda (2015=100).",
        "positive_is_good": None,
    },
}


# Yahoo Finance indicator metadata
YAHOO_INDICATORS = {
    # Stock Indices
    "ibex_35": {
        "name": "IBEX 35",
        "full_name": "Índice IBEX 35",
        "value_col": "Close",
        "unit": "Puntos",
        "currency": "EUR",
        "frequency": "Diario",
        "description": "Principal índice bursátil de la bolsa española.",
        "positive_is_good": True,
        "category": "stock_indices",
    },
    "euro_stoxx_50": {
        "name": "Euro Stoxx 50",
        "full_name": "Índice Euro Stoxx 50",
        "value_col": "Close",
        "unit": "Puntos",
        "currency": "EUR",
        "frequency": "Diario",
        "description": "Índice de referencia de la Eurozona.",
        "positive_is_good": True,
        "category": "stock_indices",
    },
    "sp_500": {
        "name": "S&P 500",
        "full_name": "Índice S&P 500",
        "value_col": "Close",
        "unit": "Puntos",
        "currency": "USD",
        "frequency": "Diario",
        "description": "Principal índice bursátil de EE.UU.",
        "positive_is_good": True,
        "category": "stock_indices",
    },
    "dax": {
        "name": "DAX",
        "full_name": "Índice DAX",
        "value_col": "Close",
        "unit": "Puntos",
        "currency": "EUR",
        "frequency": "Diario",
        "description": "Índice de referencia de la bolsa alemana.",
        "positive_is_good": True,
        "category": "stock_indices",
    },
    "ftse_100": {
        "name": "FTSE 100",
        "full_name": "Índice FTSE 100",
        "value_col": "Close",
        "unit": "Puntos",
        "currency": "GBP",
        "frequency": "Diario",
        "description": "Índice de referencia de la bolsa británica.",
        "positive_is_good": True,
        "category": "stock_indices",
    },
    # Currencies
    "eur_usd": {
        "name": "EUR/USD",
        "full_name": "Euro a Dólar",
        "value_col": "Close",
        "unit": "Tipo",
        "currency": "USD",
        "frequency": "Diario",
        "description": "Tipo de cambio euro/dólar estadounidense.",
        "positive_is_good": None,
        "category": "currencies",
    },
    "eur_gbp": {
        "name": "EUR/GBP",
        "full_name": "Euro a Libra",
        "value_col": "Close",
        "unit": "Tipo",
        "currency": "GBP",
        "frequency": "Diario",
        "description": "Tipo de cambio euro/libra esterlina.",
        "positive_is_good": None,
        "category": "currencies",
    },
    "dxy": {
        "name": "DXY",
        "full_name": "Índice Dólar",
        "value_col": "Close",
        "unit": "Índice",
        "currency": "Índice",
        "frequency": "Diario",
        "description": "Valor del dólar frente a principales divisas.",
        "positive_is_good": None,
        "category": "currencies",
    },
    # Commodities
    "gold": {
        "name": "Oro",
        "full_name": "Futuros Oro",
        "value_col": "Close",
        "unit": "USD/oz",
        "currency": "USD",
        "frequency": "Diario",
        "description": "Precio de futuros del oro por onza troy.",
        "positive_is_good": None,
        "category": "commodities",
    },
    "brent_crude": {
        "name": "Petróleo Brent",
        "full_name": "Futuros Brent",
        "value_col": "Close",
        "unit": "USD/barril",
        "currency": "USD",
        "frequency": "Diario",
        "description": "Precio de referencia europeo del petróleo.",
        "positive_is_good": None,
        "category": "commodities",
    },
    "wti_crude": {
        "name": "Petróleo WTI",
        "full_name": "Futuros WTI",
        "value_col": "Close",
        "unit": "USD/barril",
        "currency": "USD",
        "frequency": "Diario",
        "description": "Precio de referencia estadounidense del petróleo.",
        "positive_is_good": None,
        "category": "commodities",
    },
    "natural_gas": {
        "name": "Gas Natural",
        "full_name": "Futuros Gas Natural",
        "value_col": "Close",
        "unit": "USD/MMBtu",
        "currency": "USD",
        "frequency": "Diario",
        "description": "Precio de futuros del gas natural Henry Hub.",
        "positive_is_good": None,
        "category": "commodities",
    },
    # Volatility
    "vix": {
        "name": "VIX",
        "full_name": "Índice de Volatilidad CBOE",
        "value_col": "Close",
        "unit": "Puntos",
        "currency": "Índice",
        "frequency": "Diario",
        "description": "Volatilidad esperada del S&P 500 (índice del miedo).",
        "positive_is_good": False,  # Lower is better (less fear)
        "category": "volatility",
    },
    "vstoxx": {
        "name": "VSTOXX",
        "full_name": "Índice de Volatilidad Euro Stoxx 50",
        "value_col": "Close",
        "unit": "Puntos",
        "currency": "Índice",
        "frequency": "Diario",
        "description": "Volatilidad esperada del Euro Stoxx 50.",
        "positive_is_good": False,
        "category": "volatility",
    },
    # Bonds (ETFs)
    "spain_govt_bond_etf": {
        "name": "Bonos España",
        "full_name": "ETF Deuda Pública España",
        "value_col": "Close",
        "unit": "Precio",
        "currency": "EUR",
        "frequency": "Diario",
        "description": "iShares Spain Government Bond ETF.",
        "positive_is_good": None,
        "category": "bonds",
    },
    "us_treasury_20y_etf": {
        "name": "Bonos EEUU",
        "full_name": "ETF Treasuries +20 años",
        "value_col": "Close",
        "unit": "Precio",
        "currency": "USD",
        "frequency": "Diario",
        "description": "iShares 20+ Year Treasury Bond ETF.",
        "positive_is_good": None,
        "category": "bonds",
    },
    # Sector ETFs
    "spanish_banks_etf": {
        "name": "ETF España",
        "full_name": "iShares MSCI Spain ETF",
        "value_col": "Close",
        "unit": "Precio",
        "currency": "USD",
        "frequency": "Diario",
        "description": "ETF de renta variable española.",
        "positive_is_good": True,
        "category": "sector",
    },
    "european_banks_etf": {
        "name": "Financieras UE",
        "full_name": "iShares MSCI Europe Financials ETF",
        "value_col": "Close",
        "unit": "Precio",
        "currency": "USD",
        "frequency": "Diario",
        "description": "ETF del sector financiero europeo.",
        "positive_is_good": True,
        "category": "sector",
    },
}


# Banco de Espana indicator metadata
BDE_INDICATORS = {
    # EURIBOR rates
    "euribor_12m_monthly": {
        "name": "EURIBOR 12M",
        "full_name": "EURIBOR 12 Meses (Media Mensual)",
        "value_col": "value",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Tipo de referencia Euribor a 12 meses.",
        "positive_is_good": None,
        "category": "interest_rates",
    },
    "euribor_3m_daily": {
        "name": "EURIBOR 3M",
        "full_name": "EURIBOR 3 Meses (Diario)",
        "value_col": "value",
        "unit": "%",
        "frequency": "Diario",
        "description": "Tipo de referencia Euribor a 3 meses.",
        "positive_is_good": None,
        "category": "interest_rates",
    },
    "euribor_12m_daily": {
        "name": "EURIBOR 12M Diario",
        "full_name": "EURIBOR 12 Meses (Diario)",
        "value_col": "value",
        "unit": "%",
        "frequency": "Diario",
        "description": "Tipo de referencia Euribor a 12 meses (diario).",
        "positive_is_good": None,
        "category": "interest_rates",
    },
    # Government bond yields
    "spain_10y_bond": {
        "name": "Bono 10A",
        "full_name": "Rendimiento Bono Espana 10 Anos",
        "value_col": "value",
        "unit": "%",
        "frequency": "Diario",
        "description": "Rendimiento del bono del Estado espanol a 10 anos.",
        "positive_is_good": None,
        "category": "interest_rates",
    },
    "spain_5y_bond": {
        "name": "Bono 5A",
        "full_name": "Rendimiento Bono Espana 5 Anos",
        "value_col": "value",
        "unit": "%",
        "frequency": "Diario",
        "description": "Rendimiento del bono del Estado espanol a 5 anos.",
        "positive_is_good": None,
        "category": "interest_rates",
    },
    "spain_2y_bond": {
        "name": "Bono 2A+",
        "full_name": "Rendimiento Bono Espana 2+ Anos",
        "value_col": "value",
        "unit": "%",
        "frequency": "Diario",
        "description": "Rendimiento del bono del Estado espanol a 2+ anos.",
        "positive_is_good": None,
        "category": "interest_rates",
    },
    # Bank lending rates
    "mortgage_rate": {
        "name": "Tipo Hipotecas",
        "full_name": "Tipo de Interes Hipotecas (Nuevas Op.)",
        "value_col": "value",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Tipo de interes aplicado a nuevas hipotecas.",
        "positive_is_good": False,
        "category": "credit_banking",
    },
    "consumer_credit_rate": {
        "name": "Tipo Consumo",
        "full_name": "Tipo de Interes Credito Consumo (Nuevas Op.)",
        "value_col": "value",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Tipo de interes aplicado a nuevos creditos al consumo.",
        "positive_is_good": False,
        "category": "credit_banking",
    },
    "corporate_lending_rate": {
        "name": "Tipo Empresas",
        "full_name": "Tipo de Interes Credito Empresarial (Nuevas Op.)",
        "value_col": "value",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Tipo de interes aplicado a nuevos creditos a empresas.",
        "positive_is_good": False,
        "category": "credit_banking",
    },
    "household_deposit_rate": {
        "name": "Tipo Depositos",
        "full_name": "Tipo de Interes Depositos Hogares",
        "value_col": "value",
        "unit": "%",
        "frequency": "Mensual",
        "description": "Tipo de interes de depositos a plazo de hogares.",
        "positive_is_good": True,
        "category": "credit_banking",
    },
    # Credit volumes
    "credit_households_total": {
        "name": "Credito Hogares",
        "full_name": "Credito Total a Hogares",
        "value_col": "value",
        "unit": "M EUR",
        "frequency": "Mensual",
        "description": "Saldo vivo de credito a hogares (millones de euros).",
        "positive_is_good": None,
        "category": "credit_banking",
    },
    "credit_nfc_total": {
        "name": "Credito Empresas",
        "full_name": "Credito Total a Empresas (SNF)",
        "value_col": "value",
        "unit": "M EUR",
        "frequency": "Mensual",
        "description": "Saldo vivo de credito a sociedades no financieras.",
        "positive_is_good": None,
        "category": "credit_banking",
    },
    # Debt ratios
    "household_debt_gdp": {
        "name": "Deuda Hogares/PIB",
        "full_name": "Ratio Deuda Hogares sobre PIB",
        "value_col": "value",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Deuda de los hogares como porcentaje del PIB.",
        "positive_is_good": False,
        "category": "debt_ratios",
    },
    "nfc_debt_gdp": {
        "name": "Deuda Empresas/PIB",
        "full_name": "Ratio Deuda Empresas (SNF) sobre PIB",
        "value_col": "value",
        "unit": "%",
        "frequency": "Trimestral",
        "description": "Deuda de las empresas no financieras como porcentaje del PIB.",
        "positive_is_good": False,
        "category": "debt_ratios",
    },
    # External sector
    "current_account_balance": {
        "name": "Cuenta Corriente",
        "full_name": "Saldo Cuenta Corriente",
        "value_col": "value",
        "unit": "M EUR",
        "frequency": "Mensual",
        "description": "Saldo de la balanza por cuenta corriente (millones de euros).",
        "positive_is_good": True,
        "category": "external_sector",
    },
    "tourism_receipts": {
        "name": "Ingresos Turismo",
        "full_name": "Ingresos por Turismo",
        "value_col": "value",
        "unit": "M EUR",
        "frequency": "Mensual",
        "description": "Ingresos por turismo en balanza de pagos.",
        "positive_is_good": True,
        "category": "external_sector",
    },
}
