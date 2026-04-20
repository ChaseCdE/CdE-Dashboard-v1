"""
INE Indicator Fetchers
Functions to fetch specific economic indicators from INE API.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging
from .ine_client import INEClient, parse_ine_data

logger = logging.getLogger(__name__)


# Table IDs for each indicator
# Updated to use CNTR2010 tables with latest data (Q4 2025+)
TABLE_IDS = {
    # GDP
    "gdp": 67822,              # PIB pm Oferta (Índices volumen encadenado) - CNTR2010
    "gdp_demand": 67824,       # PIB pm Demanda (Índices volumen encadenado) - CNTR2010
    # Economic Activity
    "industrial_production": 60280,  # IPI General - corregido estacionalidad y calendario (base 2021)
    "industry_turnover": 61701,      # ICN Índices nacionales por destino económico
    "services_turnover": 60289,      # IAS Cifra de negocios ajustada calendario
    "services_production": 60732,    # IPSS corregido estacionalidad y calendario (base 2015)
    # Labor Market - EPA
    "unemployment": 65349,     # EPA Tasas por provincia y sexo
    "employment_rate": 65305,  # EPA Tasas de empleo por edad, sexo y CCAA
    "activity_rate": 65295,    # EPA Tasas de actividad por edad, sexo y CCAA
    "employed": 65109,         # EPA Ocupados por sexo y grupo de edad
    "temporary_rate": 65194,   # EPA Asalariados por tipo de contrato
    "parttime_rate": 65970,    # EPA Ocupados por tipo de jornada
    "youth_unemployment": 65334,  # EPA Tasas de paro por grupos de edad
    # Labor Market - ETCL (Labor Costs)
    "labor_cost": 6030,        # ETCL Coste laboral por trabajador por sectores (current, 2008+)
    "labor_cost_hour": 6034,   # ETCL Coste laboral por hora efectiva por sectores (current, 2008+)
    # Prices
    "cpi": 50904,              # IPC Índices nacionales por clases
    "cpi_special_groups": 76130,  # IPC Índices nacionales de grupos especiales
    # Consumer
    "retail_sales": 75809,     # ICM Índice nacional
    "house_prices": 25171,     # IPV Índices por CCAA
}

# Series filtering: use seasonally adjusted data where available
SEASONALLY_ADJUSTED_FILTER = "ajustados de estacionalidad"
NOT_ADJUSTED_FILTER = "no ajustados"

# CPI Special Group codes for filtering
CPI_SPECIAL_GROUPS = {
    "core": "IPCA8048",        # General sin alimentos no elaborados ni productos energéticos (subyacente)
    "energy": "IPCA8051",      # Productos energéticos
    "unprocessed_food": "IPCA8052",  # Alimentos sin elaboración
    "processed_food": "IPCA8053",    # Alimentos con elaboración, bebidas y tabaco
    "services": "IPCA8049",    # Servicios
    "non_energy_goods": "IPCA8050",  # Bienes industriales sin productos energéticos
}

# GDP Demand components for filtering
GDP_DEMAND_COMPONENTS = {
    "consumption": "Gasto en consumo final",
    "household_consumption": "Gasto en consumo final de los hogares",
    "government_consumption": "Gasto en consumo final de las AAPP",
    "gfcf": "Formación bruta de capital fijo",
    "exports": "Exportaciones de bienes y servicios",
    "imports": "Importaciones de bienes y servicios",
}


class INEIndicatorFetcher:
    """Fetcher for INE economic indicators."""

    def __init__(self, output_dir: str = "data/raw/ine"):
        """
        Initialize the fetcher.

        Args:
            output_dir: Directory to save CSV files
        """
        self.client = INEClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Save DataFrame to CSV. Skips writing if df is empty to preserve cached data."""
        filepath = self.output_dir / filename
        if df.empty:
            logger.warning(f"Skipping save of empty DataFrame to {filepath} (preserving cached data)")
            return filepath
        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"Saved: {filepath}")
        return filepath

    def fetch_gdp(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch GDP growth data (quarterly).

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with GDP data
        """
        logger.info("Fetching GDP data...")
        raw_data = self.client.get_table_data(TABLE_IDS["gdp"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "gdp_raw.csv")
        return df

    def fetch_gdp_demand(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch GDP demand-side breakdown (quarterly).
        Includes consumption, investment (GFCF), government spending, exports, imports.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with GDP demand components data
        """
        logger.info("Fetching GDP demand-side data...")
        raw_data = self.client.get_table_data(TABLE_IDS["gdp_demand"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "gdp_demand_raw.csv")
        return df

    def fetch_industrial_production(self, nult: int = 72) -> pd.DataFrame:
        """
        Fetch Industrial Production Index (monthly).

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with IPI data
        """
        logger.info("Fetching Industrial Production Index...")
        raw_data = self.client.get_table_data(TABLE_IDS["industrial_production"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "industrial_production_raw.csv")
        return df

    def fetch_unemployment(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch unemployment rate data (quarterly EPA).

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with unemployment data
        """
        logger.info("Fetching Unemployment data (EPA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["unemployment"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "unemployment_raw.csv")
        return df

    def fetch_employment_rate(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch employment rate data (quarterly EPA).
        Tasa de empleo - % of working-age population employed.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with employment rate data
        """
        logger.info("Fetching Employment Rate data (EPA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["employment_rate"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "employment_rate_raw.csv")
        return df

    def fetch_activity_rate(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch labor force participation rate (quarterly EPA).
        Tasa de actividad - % of population in labor force.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with activity rate data
        """
        logger.info("Fetching Activity Rate data (EPA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["activity_rate"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "activity_rate_raw.csv")
        return df

    def fetch_employed(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch total employed persons (quarterly EPA).
        Ocupados - absolute number of employed persons.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with employed persons data
        """
        logger.info("Fetching Employed Persons data (EPA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["employed"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "employed_raw.csv")
        return df

    def fetch_temporary_rate(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch temporary contract rate (quarterly EPA).
        Tasa de temporalidad - % of employees on temporary contracts.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with temporary contract rate data
        """
        logger.info("Fetching Temporary Contract Rate data (EPA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["temporary_rate"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "temporary_rate_raw.csv")
        return df

    def fetch_parttime_rate(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch part-time employment rate (quarterly EPA).
        Tasa de parcialidad - % of workers in part-time employment.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with part-time rate data
        """
        logger.info("Fetching Part-time Rate data (EPA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["parttime_rate"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "parttime_rate_raw.csv")
        return df

    def fetch_youth_unemployment(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch youth unemployment rate (quarterly EPA).
        Paro juvenil - unemployment rate for under-25s.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with youth unemployment data
        """
        logger.info("Fetching Youth Unemployment data (EPA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["youth_unemployment"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "youth_unemployment_raw.csv")
        return df

    def fetch_labor_cost(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch labor cost per worker (quarterly ETCL).
        Coste laboral por trabajador.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with labor cost data
        """
        logger.info("Fetching Labor Cost per Worker data (ETCL)...")
        raw_data = self.client.get_table_data(TABLE_IDS["labor_cost"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "labor_cost_raw.csv")
        return df

    def fetch_labor_cost_hour(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch labor cost per hour worked (quarterly ETCL).
        Coste laboral por hora efectiva.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with labor cost per hour data
        """
        logger.info("Fetching Labor Cost per Hour data (ETCL)...")
        raw_data = self.client.get_table_data(TABLE_IDS["labor_cost_hour"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "labor_cost_hour_raw.csv")
        return df

    def fetch_cpi(self, nult: int = 60) -> pd.DataFrame:
        """
        Fetch Consumer Price Index (monthly).

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with CPI data
        """
        logger.info("Fetching CPI data...")
        raw_data = self.client.get_table_data(TABLE_IDS["cpi"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "cpi_raw.csv")
        return df

    def fetch_cpi_special_groups(self, nult: int = 60) -> pd.DataFrame:
        """
        Fetch CPI special groups (IPCA) including core inflation, energy, food.

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with CPI special groups data
        """
        logger.info("Fetching CPI special groups (IPCA)...")
        raw_data = self.client.get_table_data(TABLE_IDS["cpi_special_groups"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "cpi_special_groups_raw.csv")
        return df

    def fetch_retail_sales(self, nult: int = 60) -> pd.DataFrame:
        """
        Fetch Retail Sales Index (monthly ICM).

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with retail sales data
        """
        logger.info("Fetching Retail Sales Index...")
        raw_data = self.client.get_table_data(TABLE_IDS["retail_sales"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "retail_sales_raw.csv")
        return df

    def fetch_house_prices(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch House Price Index (quarterly IPV).

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with house price data
        """
        logger.info("Fetching House Price Index...")
        raw_data = self.client.get_table_data(TABLE_IDS["house_prices"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "house_prices_raw.csv")
        return df

    def fetch_industry_turnover(self, nult: int = 60) -> pd.DataFrame:
        """
        Fetch Industry Turnover Index (monthly ICN).
        Índice de Cifra de Negocios de la Industria.

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with industry turnover data
        """
        logger.info("Fetching Industry Turnover Index (ICN)...")
        raw_data = self.client.get_table_data(TABLE_IDS["industry_turnover"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "industry_turnover_raw.csv")
        return df

    def fetch_services_turnover(self, nult: int = 60) -> pd.DataFrame:
        """
        Fetch Services Sector Turnover Index (monthly IAS).
        Indicadores de Actividad del Sector Servicios - Cifra de Negocios.

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with services turnover data
        """
        logger.info("Fetching Services Turnover Index (IAS)...")
        raw_data = self.client.get_table_data(TABLE_IDS["services_turnover"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "services_turnover_raw.csv")
        return df

    def fetch_services_production(self, nult: int = 72) -> pd.DataFrame:
        """
        Fetch Services Production Index (monthly IPSS).
        Índice de Producción del Sector Servicios.
        Note: Available from 2021 (base 2015), need 6 years for 2021=100 rebasing.

        Args:
            nult: Number of months to fetch (default: 36 = 3 years)

        Returns:
            DataFrame with services production data
        """
        logger.info("Fetching Services Production Index (IPSS)...")
        raw_data = self.client.get_table_data(TABLE_IDS["services_production"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "services_production_raw.csv")
        return df

    def fetch_all(self) -> dict:
        """
        Fetch all available indicators.

        Returns:
            Dictionary with indicator names as keys and DataFrames as values
        """
        results = {}

        logger.info("=" * 50)
        logger.info("Fetching all INE indicators...")
        logger.info("=" * 50)

        results["gdp"] = self.fetch_gdp()
        results["gdp_demand"] = self.fetch_gdp_demand()
        results["industrial_production"] = self.fetch_industrial_production()
        results["industry_turnover"] = self.fetch_industry_turnover()
        results["services_turnover"] = self.fetch_services_turnover()
        results["services_production"] = self.fetch_services_production()
        results["unemployment"] = self.fetch_unemployment()
        results["employment_rate"] = self.fetch_employment_rate()
        results["activity_rate"] = self.fetch_activity_rate()
        results["employed"] = self.fetch_employed()
        results["temporary_rate"] = self.fetch_temporary_rate()
        results["parttime_rate"] = self.fetch_parttime_rate()
        results["youth_unemployment"] = self.fetch_youth_unemployment()
        results["labor_cost"] = self.fetch_labor_cost()
        results["labor_cost_hour"] = self.fetch_labor_cost_hour()
        results["cpi"] = self.fetch_cpi()
        results["cpi_special_groups"] = self.fetch_cpi_special_groups()
        results["retail_sales"] = self.fetch_retail_sales()
        results["house_prices"] = self.fetch_house_prices()

        logger.info("=" * 50)
        logger.info("All indicators fetched successfully!")
        logger.info("=" * 50)

        return results


def fetch_operation_tables(operation_code: str) -> pd.DataFrame:
    """
    Utility function to explore tables for a given operation.
    Useful for finding table IDs for indicators not yet mapped.

    Args:
        operation_code: Operation code (e.g., 'ICE', 'ETCL', 'IPRI')

    Returns:
        DataFrame with table information
    """
    client = INEClient()
    tables = client.get_operation_tables(operation_code)

    records = []
    for table in tables:
        records.append({
            "id": table.get("Id"),
            "nombre": table.get("Nombre"),
            "periodicidad": table.get("Periodicidad", {}).get("Nombre") if isinstance(table.get("Periodicidad"), dict) else None,
        })

    return pd.DataFrame(records)
