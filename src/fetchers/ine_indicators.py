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
    "parttime_rate": 65148,    # EPA Ocupados por tipo de jornada, sexo y grupo de edad (trimestral; 65970 es la versión anual y se quedó en 2025)
    "youth_unemployment": 65334,  # EPA Tasas de paro por grupos de edad
    # Labor Market - ETCL (Labor Costs)
    "labor_cost": 6030,        # ETCL Coste laboral por trabajador por sectores (current, 2008+)
    "labor_cost_hour": 6034,   # ETCL Coste laboral por hora efectiva por sectores (current, 2008+)
    # Prices
    "cpi": 79181,              # IPC Índices nacionales: general y grupos ECOICOP ver.2 (base 2025 = 100; replaces frozen 50904, base 2021)
    "cpi_special_groups": 76130,  # IPC Índices nacionales de grupos especiales
    "cpi_ecoicop_groups": 76125,  # IPC Índices nacionales de grupos ECOICOP ver.2
    "cpi_weights": 76156,      # IPC Ponderaciones de grupos ECOICOP ver.2
    "cpi_special_weights": 76161,  # IPC Ponderaciones de grupos especiales
    # Consumer
    "retail_sales": 67178,     # ICM Índices de especiales agregados (incluye "General"; 75809 solo tiene modos de distribución, sin total)
    "house_prices": 80270,     # IPV Índices por CCAA trimestrales (replaces frozen 25171)
    # Industrial Prices
    "ipri": 76655,             # IPRI Índices nacionales: general y por destino económico
    # CNTR Employment and Productivity
    "cntr_employment": 67201,  # CNTR Empleo por ramas de actividad (includes hours worked, FTE)
    # Population by age (EPA)
    "population_age": 65061,   # EPA Población por sexo y grupo de edad
    # IPC by CCAA
    "cpi_ccaa": 76136,         # IPC por CCAA y grupos ECOICOP
    # Business Confidence
    "business_confidence": 8027,  # Índice de Confianza Empresarial Armonizado (ICEA)
    # Extended indicators (ext/ine). Verified against the API on 2026-10-28.
    "tourist_arrivals": 10822,     # FRONTUR Número de turistas según país de residencia (serie "Total. Turista. Dato base"); 75719 es una copia que va un mes por detrás
    "tourist_spending": 10838,     # EGATUR Gasto de los turistas internacionales según país de residencia (serie "Total. Turista. Gasto total", millones de euros)
    "hotel_overnight_stays": 2009,  # Encuesta de Ocupación Hotelera: viajeros y pernoctaciones por categorías (Nacional, total categorías, residentes / no residentes)
    "housing_transactions": 6150,   # ETDP Compraventa de viviendas según régimen y estado (general, nueva, segunda mano)
    "mortgages": 13896,             # Hipotecas constituidas sobre el total de fincas por naturaleza de la finca (serie Viviendas: número e importe en miles de euros)
    "companies": 13912,             # Sociedades Mercantiles: resumen (constituidas y disueltas, número)
    "household_saving_rate": 62275,  # CTNFSI Hogares e ISFLSH: tasa de ahorro (SA y NSA), saldos contables
    "population_nationality": 59587,  # ECP Población residente por fecha, sexo, grupo de edad y nacionalidad (española/extranjera)
}

# Estadística del Procedimiento Concursal (operación 13, tablas 3181/3182/2992...): el INE dejó de elaborarla
# (último dato 2020; pasó al Colegio de Registradores). No se exporta ningún dataset de concursos.

# Series codes for the population-by-nationality table (59587 has 3600 series, too big to download whole).
POPULATION_NATIONALITY_CODES = {
    "total": "ECP4961",      # Total Nacional. Total. Todas las edades. Total. Población. Número.
    "espanola": "ECP4901",   # Total Nacional. Española. ...
    "extranjera": "ECP701",  # Total Nacional. Extranjera. ...
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

    def fetch_cpi_ecoicop_groups(self, nult: int = 60) -> pd.DataFrame:
        """
        Fetch CPI ECOICOP groups data (monthly).
        Includes 12 main product groups with indices and variations.

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with CPI ECOICOP groups data
        """
        logger.info("Fetching CPI ECOICOP groups...")
        raw_data = self.client.get_table_data(TABLE_IDS["cpi_ecoicop_groups"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "cpi_ecoicop_groups_raw.csv")
        return df

    def fetch_cpi_weights(self, nult: int = 12) -> pd.DataFrame:
        """
        Fetch CPI weights for ECOICOP groups (annual).
        Weights show the importance of each group in the CPI basket.

        Args:
            nult: Number of periods to fetch (default: 12)

        Returns:
            DataFrame with CPI weights data
        """
        logger.info("Fetching CPI weights...")
        raw_data = self.client.get_table_data(TABLE_IDS["cpi_weights"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "cpi_weights_raw.csv")
        return df

    def fetch_cpi_special_weights(self, nult: int = 12) -> pd.DataFrame:
        """
        Fetch CPI weights for special groups (annual).
        Used for inflation decomposition (Alimentos, Energía, Servicios, Bienes industriales).

        Args:
            nult: Number of periods to fetch (default: 12)

        Returns:
            DataFrame with CPI special weights data
        """
        logger.info("Fetching CPI special weights...")
        raw_data = self.client.get_table_data(TABLE_IDS["cpi_special_weights"], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, "cpi_special_weights_raw.csv")
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

    def fetch_ipri(self, nult: int = 60) -> pd.DataFrame:
        """
        Fetch Industrial Price Index (IPRI) - Índice de Precios Industriales.
        National data only, by economic destination of goods.

        Categories:
        - Total industria (General)
        - Total industria sin energía (General without energy)
        - Bienes de consumo (Consumer goods)
        - Bienes de equipo (Capital goods)
        - Bienes intermedios (Intermediate goods)
        - Energía (Energy)

        Args:
            nult: Number of months to fetch (default: 60 = 5 years)

        Returns:
            DataFrame with IPRI data (index, yoy_change, mom_change)
        """
        logger.info("Fetching Industrial Price Index (IPRI)...")
        raw_data = self.client.get_table_data(TABLE_IDS["ipri"], nult=nult)
        df = parse_ine_data(raw_data)

        # Filter only national data. After the 2026 rebase INE names these series
        # "Nacional. Mercado interior. ..." (before: "Total Nacional. ..."); accept both.
        df = df[df["series_name"].str.contains(r"^(?:Total )?Nacional\.", case=False, na=False, regex=True)]

        self._save_csv(df, "ipri_raw.csv")
        return df

    def fetch_cntr_employment(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch CNTR employment data (quarterly).
        Includes: Ocupados (persons), Puestos de trabajo equivalentes a tiempo completo (FTE),
        and Horas trabajadas (hours worked).

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with employment data
        """
        logger.info("Fetching CNTR Employment data...")
        raw_data = self.client.get_table_data(TABLE_IDS["cntr_employment"], nult=nult)
        df = parse_ine_data(raw_data)

        # Filter only the key series we need (seasonally adjusted, Total CNAE)
        key_series = [
            "CNTR7659",  # Ocupados - Personas - Ajustados - Total CNAE
            "CNTR7818",  # Ocupados - Puestos FTE - Ajustados - Total CNAE
            "CNTR7896",  # Ocupados - Horas trabajadas - Ajustados - Total CNAE
        ]
        df = df[df["series_code"].isin(key_series)]

        self._save_csv(df, "cntr_employment_raw.csv")
        return df

    def fetch_population_age(self, nult: int = 40) -> pd.DataFrame:
        """
        Fetch EPA population by age (quarterly).
        Used for calculating GDP per capita and per working-age population.

        Args:
            nult: Number of quarters to fetch (default: 40 = 10 years)

        Returns:
            DataFrame with population data by age groups
        """
        logger.info("Fetching EPA Population by age...")
        raw_data = self.client.get_table_data(TABLE_IDS["population_age"], nult=nult)
        df = parse_ine_data(raw_data)

        # Filter national totals (Ambos sexos, absolute persons - not percentages).
        # INE renamed the series in 2026: "... Personas." became "... Valor absoluto.";
        # accept both (the old filter only knew "Personas" and returned an empty frame).
        df = df[
            (df["series_name"].str.contains("Ambos sexos", case=False, na=False)) &
            (df["series_name"].str.contains(r"Personas|Valor absoluto", case=False, na=False, regex=True)) &
            (~df["series_name"].str.contains("Porcentaje", case=False, na=False))
        ]

        self._save_csv(df, "population_age_raw.csv")
        return df

    def fetch_cpi_ccaa(self, nult: int = 24) -> pd.DataFrame:
        """
        Fetch CPI data by Autonomous Community (CCAA).
        Table 76136: IPC por CCAA y grupos ECOICOP.

        Args:
            nult: Number of months to fetch (default: 24 = 2 years)

        Returns:
            DataFrame with CPI data by CCAA
        """
        logger.info("Fetching CPI by CCAA...")
        raw_data = self.client.get_table_data(TABLE_IDS["cpi_ccaa"], nult=nult)
        df = parse_ine_data(raw_data)

        # Filter for "Índice general" only (not individual product categories)
        df = df[df["series_name"].str.contains("ndice general", case=False, na=False)]

        self._save_csv(df, "cpi_ccaa_raw.csv")
        return df

    def fetch_business_confidence(self, nult: int = 24) -> pd.DataFrame:
        """
        Fetch Business Confidence Index (Índice de Confianza Empresarial Armonizado).
        Table 8027: ICEA - Índice de Confianza Empresarial Armonizado.

        Args:
            nult: Number of quarters to fetch (default: 24 = 6 years)

        Returns:
            DataFrame with business confidence data
        """
        logger.info("Fetching Business Confidence Index...")
        raw_data = self.client.get_table_data(TABLE_IDS["business_confidence"], nult=nult)
        df = parse_ine_data(raw_data)

        self._save_csv(df, "business_confidence_raw.csv")
        return df

    # ------------------------------------------------------------------
    # Extended indicators (ext/ine)
    # ------------------------------------------------------------------
    def _fetch_table_to_csv(self, key: str, filename: str, nult: int, label: str) -> pd.DataFrame:
        logger.info(f"Fetching {label}...")
        raw_data = self.client.get_table_data(TABLE_IDS[key], nult=nult)
        df = parse_ine_data(raw_data)
        self._save_csv(df, filename)
        return df

    def fetch_tourist_arrivals(self, nult: int = 132) -> pd.DataFrame:
        """FRONTUR: international tourist arrivals (monthly), table 10822."""
        return self._fetch_table_to_csv("tourist_arrivals", "tourist_arrivals_raw.csv", nult, "FRONTUR tourist arrivals")

    def fetch_tourist_spending(self, nult: int = 132) -> pd.DataFrame:
        """EGATUR: spending of international tourists (monthly, millions of euros), table 10838."""
        return self._fetch_table_to_csv("tourist_spending", "tourist_spending_raw.csv", nult, "EGATUR tourist spending")

    def fetch_hotel_overnight_stays(self, nult: int = 192) -> pd.DataFrame:
        """Encuesta de Ocupación Hotelera: overnight stays (monthly), table 2009."""
        return self._fetch_table_to_csv("hotel_overnight_stays", "hotel_overnight_stays_raw.csv", nult, "hotel overnight stays")

    def fetch_housing_transactions(self, nult: int = 192) -> pd.DataFrame:
        """ETDP: home purchases (monthly), table 6150."""
        return self._fetch_table_to_csv("housing_transactions", "housing_transactions_raw.csv", nult, "housing transactions (ETDP)")

    def fetch_mortgages(self, nult: int = 192) -> pd.DataFrame:
        """Hipotecas sobre viviendas (monthly), table 13896."""
        return self._fetch_table_to_csv("mortgages", "mortgages_raw.csv", nult, "mortgages on dwellings")

    def fetch_companies(self, nult: int = 192) -> pd.DataFrame:
        """Sociedades Mercantiles: created and dissolved (monthly), table 13912."""
        return self._fetch_table_to_csv("companies", "companies_raw.csv", nult, "commercial companies created / dissolved")

    def fetch_household_saving_rate(self, nult: int = 80) -> pd.DataFrame:
        """CTNFSI: household and NPISH saving rate (quarterly), table 62275."""
        return self._fetch_table_to_csv("household_saving_rate", "household_saving_rate_raw.csv", nult, "household saving rate")

    def fetch_population_nationality(self, nult: int = 70) -> pd.DataFrame:
        """
        ECP: resident population by nationality (Spanish / foreign), table 59587.

        The table has 3600 series, so the three national series are requested by code.
        """
        logger.info("Fetching population by nationality (ECP)...")
        raw = []
        for key, code in POPULATION_NATIONALITY_CODES.items():
            item = self.client.get_series_data(code, nult=nult)
            if isinstance(item, dict):
                raw.append(item)
        df = parse_ine_data(raw)
        self._save_csv(df, "population_nationality_raw.csv")
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
        results["cpi_ecoicop_groups"] = self.fetch_cpi_ecoicop_groups()
        results["cpi_weights"] = self.fetch_cpi_weights()
        results["cpi_special_weights"] = self.fetch_cpi_special_weights()
        results["retail_sales"] = self.fetch_retail_sales()
        results["house_prices"] = self.fetch_house_prices()
        results["ipri"] = self.fetch_ipri()
        results["cntr_employment"] = self.fetch_cntr_employment()
        results["population_age"] = self.fetch_population_age()
        results["cpi_ccaa"] = self.fetch_cpi_ccaa()
        results["business_confidence"] = self.fetch_business_confidence()
        results["tourist_arrivals"] = self.fetch_tourist_arrivals()
        results["tourist_spending"] = self.fetch_tourist_spending()
        results["hotel_overnight_stays"] = self.fetch_hotel_overnight_stays()
        results["housing_transactions"] = self.fetch_housing_transactions()
        results["mortgages"] = self.fetch_mortgages()
        results["companies"] = self.fetch_companies()
        results["household_saving_rate"] = self.fetch_household_saving_rate()
        results["population_nationality"] = self.fetch_population_nationality()

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
