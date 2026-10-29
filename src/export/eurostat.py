"""
Eurostat datasets for site/data/eurostat/. Owned by ws/eurostat.

Dataset ids follow `eurostat.<indicator>`, where <indicator> is the processed CSV
stem without the `_spain`, `_eu27` and `_comparison` suffixes. One series per
geography, built from the `_comparison` CSV (wide: one column per geography)
where it exists. Dataset codes are taken from the fetcher so the two cannot
drift apart.

Conventions for the `yoy` field:
- indices / levels (IPI, PPI, retail, house prices, ESI): % change on the same
  period a year earlier, unit `pct_change`;
- rates and balances (unemployment, participation, debt/GDP, consumer
  confidence): difference with the same period a year earlier, unit `pp`
  (`points` for the confidence balance);
- HICP and core inflation: the main value already is an annual rate, so the
  only field is `yoy`.
"""

from ..fetchers.eurostat_indicators import DATASET_CODES
from .adjustment import ANNUAL, NSA, SA, SCA, note
from .core import Dataset, Field, Series

EUROSTAT_URL = "https://ec.europa.eu/eurostat/databrowser/view/{}/default/table"

ES = "España"
EU = "UE-27"


def _url(code: str) -> str:
    return EUROSTAT_URL.format(code)


def _es_eu(col_es: str, col_eu: str, field: str = "value", extra: dict | None = None) -> list:
    """Spain + EU27 series where each field maps to `<column>_es` / `<column>_eu27`."""
    def cols(suffix):
        c = {field: f"{col_es}_{suffix}"}
        for k, base in (extra or {}).items():
            c[k] = f"{base}_{suffix}"
        return c
    return [Series("es", ES, columns=cols("es")), Series("eu27", EU, columns=cols("eu27"))]


def _comparison(indicator: str, code_key: str, title: str, desc: str, freq: str, value_col: str,
                value_field: Field | None, yoy_field: Field | None, csv: str | None = None,
                code: str | None = None) -> Dataset:
    fields = []
    extra = {}
    if value_field:
        fields.append(value_field)
    if yoy_field:
        fields.append(yoy_field)
        extra = {yoy_field.key: "yoy_change"}
    main = value_field.key if value_field else yoy_field.key
    series = _es_eu(value_col, value_col, field=main, extra=extra if value_field else None)
    if not value_field:
        series = [Series(s.key, s.label_es, columns={main: s.columns[main]}) for s in series]
    code = code or DATASET_CODES[code_key]
    return Dataset(
        source="eurostat",
        indicator=indicator,
        csv=csv or f"eurostat/{indicator}_comparison.csv",
        title_es=title,
        description_es=desc,
        source_dataset=code,
        source_url=_url(code),
        frequency=freq,
        fields=fields,
        series=series,
    )


DATASETS = [
    # ---- Actividad -------------------------------------------------------
    _comparison(
        "gdp_growth", "gdp_growth",
        "Crecimiento del PIB (trimestral)",
        "Variación trimestral del PIB real, corregida de estacionalidad y calendario. España frente a UE-27.",
        "Q", "gdp_growth_qoq",
        Field("qoq", "Variación trimestral", "pct_change", 1, column="gdp_growth_qoq",
              note_es=note(SCA, "Volúmenes encadenados")),
        None,
    ),
    Dataset(
        source="eurostat",
        indicator="gdp_index",
        csv="eurostat/gdp_index_comparison.csv",
        title_es="PIB real, comparación entre países",
        description_es="Nivel del PIB real en volumen, con base 100 en el primer trimestre de 2019. España, UE-27, Alemania, Francia e Italia.",
        source_dataset=DATASET_CODES["gdp_growth"],
        source_url=_url(DATASET_CODES["gdp_growth"]),
        frequency="Q",
        fields=[Field("value", "Índice (1T 2019 = 100)", "index", 1,
                      note_es=note(SCA, "Base 1T 2019 = 100. Volúmenes encadenados"))],
        series=[
            Series("es", ES, columns={"value": "gdp_index_spain"}),
            Series("eu27", EU, columns={"value": "gdp_index_eu27"}),
            Series("de", "Alemania", columns={"value": "gdp_index_germany"}),
            Series("fr", "Francia", columns={"value": "gdp_index_france"}),
            Series("it", "Italia", columns={"value": "gdp_index_italy"}),
        ],
    ),
    _comparison(
        "industrial_production", "industrial_production",
        "Producción industrial",
        "Índice de producción industrial (industria sin construcción). España frente a UE-27.",
        "M", "ipi_index",
        Field("value", "Índice (2021 = 100)", "index", 1,
              note_es=note(SCA, "Base 2021 = 100")),
        Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
    ),
    _comparison(
        "economic_sentiment", "economic_sentiment",
        "Indicador de sentimiento económico",
        "Indicador de Sentimiento Económico de la Comisión Europea (media de largo plazo = 100). España frente a UE-27.",
        "M", "esi",
        Field("value", "Índice (media largo plazo = 100)", "index", 1,
              note_es=note(SA, "Media de largo plazo = 100")),
        Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SA),
    ),
    # ---- Mercado laboral -------------------------------------------------
    _comparison(
        "unemployment", "unemployment",
        "Tasa de paro (Eurostat)",
        "Tasa de paro armonizada de la población de 15 a 74 años. España frente a UE-27.",
        "M", "unemployment_rate",
        Field("value", "Tasa de paro", "pct", 1,
              note_es=note(SA, "Población activa de 15 a 74 años")),
        Field("yoy_pp", "Variación anual (puntos porcentuales)", "pp", 1, column="yoy_change", note_es=SA),
    ),
    _comparison(
        "employment_growth", "employment_growth",
        "Crecimiento del empleo (trimestral)",
        "Variación trimestral del empleo total (concepto de cuentas nacionales). España frente a UE-27.",
        "Q", "employment_growth",
        Field("qoq", "Variación trimestral", "pct_change", 1, column="employment_growth",
              note_es=SCA),
        None,
    ),
    _comparison(
        "labor_participation", "labor_participation",
        "Tasa de actividad",
        "Población activa de 15 a 64 años como porcentaje de la población de esa edad. España frente a UE-27.",
        "Q", "participation_rate",
        Field("value", "Tasa de actividad", "pct", 1,
              note_es=note(SA, "Población de 15 a 64 años")),
        Field("yoy_pp", "Variación anual (puntos porcentuales)", "pp", 1, column="yoy_change", note_es=SA),
    ),
    # ---- Precios ---------------------------------------------------------
    _comparison(
        "hicp", "hicp",
        "Inflación armonizada (IPCA)",
        "Tasa de variación anual del Índice de Precios de Consumo Armonizado. España frente a UE-27.",
        "M", "hicp_inflation",
        None,
        Field("yoy", "Variación anual", "pct_change", 1, column="hicp_inflation",
              note_es=note(NSA, "Clasificación ECOICOP 2. Serie histórica reconstruida por Eurostat con la nueva clasificación")),
    ),
    _comparison(
        "core_inflation", "core_inflation",
        "Inflación subyacente (IPCA sin energía ni alimentos)",
        "Tasa de variación anual del IPCA general sin energía ni alimentos. España frente a UE-27.",
        "M", "core_inflation",
        None,
        Field("yoy", "Variación anual", "pct_change", 1, column="core_inflation",
              note_es=note(NSA, "IPCA excluidos energía, alimentos, alcohol y tabaco (TOT_X_NRG_FOOD). Clasificación ECOICOP 2")),
    ),
    _comparison(
        "producer_prices", "producer_prices",
        "Precios industriales (mercado interior)",
        "Índice de precios de producción industrial para el mercado interior (industria sin construcción). España frente a UE-27.",
        "M", "ppi_index",
        Field("value", "Índice (2021 = 100)", "index", 1,
              note_es=note(NSA, "Base 2021 = 100")),
        Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
    ),
    # ---- Sector exterior -------------------------------------------------
    Dataset(
        source="eurostat",
        indicator="trade_balance",
        csv="eurostat/trade_balance_spain.csv",
        title_es="Comercio exterior de bienes de España",
        description_es="Exportaciones, importaciones y saldo comercial de bienes de España con el resto del mundo (millones de euros), corregidos de efectos estacionales y de calendario.",
        source_dataset=DATASET_CODES["trade_balance"],
        source_url=_url(DATASET_CODES["trade_balance"]),
        frequency="M",
        fields=[
            Field("balance", "Saldo comercial", "currency", 0, column="trade_balance", currency="EUR", scale=6,
                  note_es=note(SCA, "Exportaciones menos importaciones")),
            Field("exports", "Exportaciones", "currency", 0, currency="EUR", scale=6, note_es=SCA),
            Field("imports", "Importaciones", "currency", 0, currency="EUR", scale=6, note_es=SCA),
        ],
        series=[Series("es", ES)],
    ),
    # ---- Finanzas públicas -----------------------------------------------
    _comparison(
        "government_debt", "government_debt",
        "Deuda pública (% del PIB)",
        "Deuda bruta de las Administraciones Públicas en porcentaje del PIB. España frente a UE-27.",
        "Q", "debt_to_gdp",
        Field("value", "Deuda pública (% del PIB)", "pct", 1, note_es=note(NSA, "Deuda bruta consolidada de las Administraciones Públicas (S13)")),
        Field("yoy_pp", "Variación anual (puntos porcentuales)", "pp", 1, column="yoy_change", note_es=NSA),
    ),
    _comparison(
        "budget_deficit", "budget_deficit",
        "Déficit público (% del PIB)",
        "Capacidad (+) o necesidad (-) de financiación de las Administraciones Públicas, en porcentaje del PIB. Dato anual. España frente a UE-27.",
        "A", "deficit_gdp",
        Field("value", "Saldo de las AAPP (% del PIB)", "pct", 1,
              note_es=note(ANNUAL, "Capacidad o necesidad de financiación de las Administraciones Públicas (S13)")),
        None,
    ),
    # ---- Consumo y hogares -----------------------------------------------
    _comparison(
        "consumer_confidence", "consumer_confidence",
        "Confianza del consumidor",
        "Indicador de confianza del consumidor de la Comisión Europea (saldo de respuestas). España frente a UE-27.",
        "M", "consumer_confidence",
        Field("value", "Saldo de respuestas", "points", 1, note_es=note(SA, "Saldo de respuestas")),
        Field("yoy_diff", "Variación anual (puntos)", "points", 1, column="yoy_change", note_es=SA),
    ),
    _comparison(
        "retail_trade", "retail_trade",
        "Comercio minorista",
        "Índice de volumen de ventas del comercio al por menor, excluido el de vehículos. España frente a UE-27.",
        "M", "retail_index",
        Field("value", "Índice (2021 = 100)", "index", 1,
              note_es=note(SCA, "Base 2021 = 100. Volumen de ventas (deflactado)")),
        Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
    ),
    _comparison(
        "house_prices", "house_prices",
        "Precios de la vivienda",
        "Índice de precios de la vivienda (todas las viviendas). España frente a UE-27.",
        "Q", "hpi_index",
        Field("value", "Índice (2015 = 100)", "index", 1, note_es=note(NSA, "Base 2015 = 100")),
        Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
    ),
]


# ---- Extension (ext/eurostat) ---------------------------------------------
def _multi(indicator: str, col: str, title: str, desc: str, freq: str, code: str, fields: list,
           geos: list, yoy_col: str | None = None) -> Dataset:
    """Dataset with several geographies read from `<indicator>_comparison.csv`.

    `col` is the value column stem (`<col>_<geo>`); `yoy_col` the yoy stem if any.
    """
    series = []
    for key, label in geos:
        cols = {fields[0].key: f"{col}_{key}"}
        if yoy_col:
            cols[fields[1].key] = f"{yoy_col}_{key}"
        series.append(Series(key, label, columns=cols))
    return Dataset(
        source="eurostat",
        indicator=indicator,
        csv=f"eurostat/{indicator}_comparison.csv",
        title_es=title,
        description_es=desc,
        source_dataset=code,
        source_url=_url(code),
        frequency=freq,
        fields=fields,
        series=series,
    )


_PEERS = [("es", ES), ("de", "Alemania"), ("fr", "Francia"), ("it", "Italia"), ("pt", "Portugal")]

DATASETS += [
    _multi(
        "gdp_per_capita_pps", "gdp_pc_pps",
        "PIB per cápita en paridad de poder adquisitivo",
        "PIB por habitante en estándares de poder adquisitivo (PPS), índice UE-27 = 100. España, Alemania, Francia, Italia y Portugal.",
        "A", DATASET_CODES["gdp_per_capita_pps"],
        [Field("value", "Índice (UE-27 = 100)", "index", 1, note_es=note(ANNUAL, "UE-27 = 100"))],
        _PEERS,
    ),
    _multi(
        "labour_productivity_pps", "productivity_pps",
        "Productividad por hora trabajada en paridad de poder adquisitivo",
        "Productividad nominal del trabajo por hora trabajada, en PPS, índice UE-27 = 100. España, Alemania, Francia, Italia y Portugal.",
        "A", DATASET_CODES["labour_productivity_pps"],
        [Field("value", "Índice (UE-27 = 100)", "index", 1,
               note_es=note(ANNUAL, "UE-27 = 100. PIB por hora trabajada en PPS (concepto de cuentas nacionales)"))],
        _PEERS,
    ),
    _multi(
        "rd_expenditure", "rd_pct_gdp",
        "Gasto en I+D (% del PIB)",
        "Gasto interno bruto en investigación y desarrollo, todos los sectores, en porcentaje del PIB. España, UE-27, Alemania, Francia e Italia.",
        "A", DATASET_CODES["rd_expenditure"],
        [Field("value", "Gasto en I+D (% del PIB)", "pct", 1,
               note_es=note(ANNUAL, "Gasto interno bruto en I+D, todos los sectores. Los últimos años pueden ser provisionales o estimados"))],
        [("es", ES), ("eu27", EU), ("de", "Alemania"), ("fr", "Francia"), ("it", "Italia")],
    ),
    _multi(
        "youth_unemployment", "youth_unemployment_rate",
        "Paro juvenil (menores de 25 años)",
        "Tasa de paro de los menores de 25 años. España frente a UE-27.",
        "M", DATASET_CODES["youth_unemployment"],
        [Field("value", "Tasa de paro juvenil", "pct", 1,
               note_es=note(SA, "Población activa menor de 25 años")),
         Field("yoy_pp", "Variación anual (puntos porcentuales)", "pp", 1, column="yoy_change", note_es=SA)],
        [("es", ES), ("eu27", EU)], yoy_col="yoy_change",
    ),
    _multi(
        "long_term_unemployment", "ltu_rate",
        "Paro de larga duración",
        "Parados de 12 meses o más como porcentaje de la población activa de 15 a 74 años. España frente a UE-27.",
        "Q", DATASET_CODES["long_term_unemployment"],
        [Field("value", "Paro de larga duración (% de la población activa)", "pct", 1,
               note_es=note(SA, "Parados desde hace 12 meses o más, población de 15 a 74 años")),
         Field("yoy_pp", "Variación anual (puntos porcentuales)", "pp", 1, column="yoy_change", note_es=SA)],
        [("es", ES), ("eu27", EU)], yoy_col="yoy_change",
    ),
    _multi(
        "hicp_energy", "hicp_energy",
        "Inflación de la energía (IPCA)",
        "Tasa de variación anual del componente de energía del IPCA. España frente a UE-27.",
        "M", DATASET_CODES["hicp_energy"],
        [Field("yoy", "Variación anual", "pct_change", 1, note_es=note(NSA, "Componente energía (ECOICOP 2) del IPCA"))],
        [("es", ES), ("eu27", EU)],
    ),
]


# Eurostat publishes R&D expenditure for year t around November of t+1, so the latest year
# is legitimately ~22 months past its end just before each release (contract v1.2).
for _ds in DATASETS:
    if _ds.indicator == "rd_expenditure":
        _ds.stale_after_days = 760
