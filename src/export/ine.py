"""
INE datasets for site/data/ine/. Owned by ws/ine.

One Dataset per processed INE CSV in data/processed/ that the former Shiny app loaded (src/app/data.py, removed in Phase 6)
(summary.csv excluded). Dataset id = "ine.<csv stem>".

Not exported on purpose (see docs/notes/ws-ine.md):
- cntr_employment.csv: input to gdp_productivity.csv, which is exported.
- population.csv: input to gdp_productivity.csv, which is exported.

Metadata conventions
- Table ids come from TABLE_IDS in src/fetchers/ine_series.py so a repoint of a
  fetcher table is picked up here automatically.
- Rates of change that INE publishes or that the processor computes are exported as
  fields (yoy / qoq / mom, unit pct_change). Changes of a rate are exported as
  yoy_pp (unit pp): a relative % change of an unemployment rate is not meaningful.
- Index bases come from the INE table code / by checking that the base period
  averages 100 in the data (CPI and house prices: 2025 = 100).
"""

from ..fetchers.ine_series import TABLE_IDS
from .adjustment import ANNUAL, NSA, SCA, note
from .core import Dataset, Field, Series, long_series

INE_TABLE_URL = "https://www.ine.es/jaxiT3/Tabla.htm?t={}"


def _table(key):
    """(source_dataset, source_url) for an entry of TABLE_IDS."""
    tid = TABLE_IDS[key]
    return str(tid), INE_TABLE_URL.format(tid)


def _ine(indicator, key, **kw):
    """Dataset with INE source metadata taken from TABLE_IDS[key]."""
    dataset, url = _table(key)
    kw.setdefault("source_dataset", dataset)
    kw.setdefault("source_url", url)
    return Dataset(source="ine", indicator=indicator, csv=f"{indicator}.csv", **kw)


SPAIN = [Series("es", "España")]


def _epa_rate(indicator, key, column, title, description, label, decimals=2):
    return _ine(
        indicator, key,
        title_es=title,
        description_es=description,
        frequency="Q",
        fields=[
            Field("value", label, "pct", decimals, column=column, note_es=note(NSA, "Encuesta de Población Activa")),
            Field("yoy_pp", "Variación anual (pp)", "pp", decimals, note_es=NSA),
        ],
        series=SPAIN,
    )


DATASETS = [
    # ------------------------------------------------------------------ Actividad
    _ine(
        "gdp", "gdp",
        title_es="Producto Interior Bruto (PIB)",
        description_es="Índice de volumen encadenado del PIB a precios de mercado, corregido de efectos estacionales y de calendario. Variaciones anual y trimestral.",
        frequency="Q",
        fields=[
            Field("value", "Índice de volumen", "index", 1, column="gdp_index",
                  note_es=note(SCA, "Base 2020 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
            Field("qoq", "Variación trimestral", "pct_change", 1, column="qoq_change", note_es=SCA),
        ],
        series=SPAIN,
    ),
    _ine(
        "gdp_demand", "gdp_demand",
        title_es="PIB por componentes de demanda",
        description_es="Aportación de cada componente de la demanda al crecimiento interanual del PIB, en puntos porcentuales. Datos corregidos de estacionalidad y calendario; la suma de las aportaciones coincide con el crecimiento del PIB salvo redondeo.",
        frequency="Q",
        fields=[Field("contribution", "Aportación al crecimiento anual del PIB", "pp", 1, note_es=SCA)],
        series=long_series("component", order=["private_consumption", "public_consumption", "gfcf", "inventories", "external_demand"],
                           labels={
                               "private_consumption": "Consumo de los hogares",
                               "public_consumption": "Consumo de las AAPP",
                               "gfcf": "Formación bruta de capital fijo",
                               "inventories": "Variación de existencias",
                               "external_demand": "Demanda externa",
                           }),
    ),
    _ine(
        "gdp_productivity", "gdp",
        title_es="PIB y productividad (2019T1 = 100)",
        description_es="PIB en volumen y PIB por habitante, por persona en edad de trabajar, por ocupado y por hora trabajada, con base 2019T1 = 100.",
        source_dataset="67822, 67201, 65061",
        frequency="Q",
        fields=[Field("value", "Índice 2019T1 = 100", "index", 1,
                      note_es="Base 2019T1 = 100. PIB de la Contabilidad Nacional Trimestral entre población (EPA), empleo y horas (CNTR). "
                              "PIB, empleo y horas: " + SCA[0].lower() + SCA[1:] + "; población: " + NSA[0].lower() + NSA[1:])],
        series=[
            Series("pib", "PIB", columns={"value": "pib_index"}),
            Series("pib_per_capita", "PIB por habitante", columns={"value": "pib_per_capita_index"}),
            Series("pib_per_working_age", "PIB por persona en edad de trabajar", columns={"value": "pib_per_working_age_index"}),
            Series("pib_per_employed", "PIB por ocupado", columns={"value": "pib_per_employed_index"}),
            Series("pib_per_hour", "PIB por hora trabajada", columns={"value": "pib_per_hour_index"}),
        ],
    ),
    _ine(
        "industrial_production", "industrial_production",
        title_es="Índice de Producción Industrial (IPI)",
        description_es="IPI general, corregido de efectos estacionales y de calendario. Índice, variación anual (publicada por el INE) y variación mensual.",
        frequency="M",
        fields=[
            Field("value", "Índice", "index", 1, column="ipi_index", note_es=note(SCA, "Base 2021 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
            Field("mom", "Variación mensual", "pct_change", 1, column="mom_change", note_es=SCA),
        ],
        series=SPAIN,
    ),
    Dataset(
        source="ine",
        indicator="ipi_sectors",
        csv="ipi_sectors.csv",
        title_es="Producción industrial por destino económico",
        description_es="Índice de Producción Industrial corregido de efectos estacionales y de calendario, por destino económico de los bienes.",
        source_dataset=str(TABLE_IDS["industrial_production"]),
        source_url=INE_TABLE_URL.format(TABLE_IDS["industrial_production"]),
        frequency="M",
        fields=[
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
            Field("ytd", "Variación media en lo que va de año", "pct_change", 1, column="ytd_change", note_es=SCA),
        ],
        series=long_series("sector", label_column="sector_label",
                           order=["total", "consumo", "equipo", "intermedios", "energia"]),
    ),
    _ine(
        "industry_turnover", "industry_turnover",
        title_es="Cifra de negocios de la industria",
        description_es="Tasa de variación anual del índice de cifra de negocios del total de la industria, corregido de efectos estacionales y de calendario.",
        frequency="M",
        fields=[Field("yoy", "Variación anual", "pct_change", 1, column="turnover_yoy", note_es=SCA)],
        series=SPAIN,
    ),
    _ine(
        "services_turnover", "services_turnover",
        title_es="Cifra de negocios del sector servicios (IASS)",
        description_es="Tasa de variación anual del índice general de cifra de negocios del sector servicios, corregido de efectos estacionales y de calendario.",
        frequency="M",
        fields=[Field("yoy", "Variación anual", "pct_change", 1, column="turnover_yoy", note_es=SCA)],
        series=SPAIN,
    ),
    _ine(
        "services_production", "services_production",
        title_es="Indicador de Producción del Sector Servicios (IPSS)",
        description_es="Índice general de cifra de negocios a precios corrientes del sector servicios, corregido de estacionalidad y calendario. Índice y variaciones anual y mensual.",
        frequency="M",
        fields=[
            Field("value", "Índice", "index", 1, column="services_prod_index",
                  note_es=note(SCA, "Base 2021 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
            Field("mom", "Variación mensual", "pct_change", 1, column="mom_change", note_es=SCA),
        ],
        series=SPAIN,
    ),
    _ine(
        "ipss_sectors", "services_production",
        title_es="Servicios por sector de actividad",
        description_es="Cifra de negocios del sector servicios por actividad (IPSS), corregida de estacionalidad y calendario. Variación anual y media en lo que va de año.",
        frequency="M",
        fields=[
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
            Field("ytd", "Variación media en lo que va de año", "pct_change", 1, column="ytd_change", note_es=SCA),
        ],
        series=long_series("sector", label_column="sector_label"),
    ),
    _ine(
        "business_confidence", "business_confidence",
        title_es="Confianza empresarial (ICEA)",
        description_es="Índice de Confianza Empresarial Armonizado y saldos de situación del trimestre anterior y expectativas del trimestre entrante.",
        frequency="Q",
        fields=[
            Field("value", "Valor", "points", 1,
                  note_es=note(NSA, "El índice (ICE) tiene base 2013; situación y expectativas son saldos")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change",
                  note_es=note(NSA, "Solo definida para el índice general (ICE); vacía en los saldos")),
        ],
        series=long_series("indicator", label_column="indicator_name", order=["ice", "situacion", "expectativas"]),
    ),
    # ------------------------------------------------------------------ Mercado laboral
    _epa_rate("unemployment", "unemployment", "unemployment_rate",
              "Tasa de paro (EPA)", "Tasa de paro de la población activa. Total nacional, ambos sexos.", "Tasa de paro"),
    _epa_rate("youth_unemployment", "youth_unemployment", "youth_unemployment_rate",
              "Tasa de paro de menores de 25 años (EPA)", "Tasa de paro de la población activa menor de 25 años. Total nacional, ambos sexos.",
              "Tasa de paro juvenil"),
    _epa_rate("employment_rate", "employment_rate", "employment_rate",
              "Tasa de empleo (EPA)", "Ocupados como porcentaje de la población de 16 y más años. Total nacional, ambos sexos.", "Tasa de empleo"),
    _epa_rate("activity_rate", "activity_rate", "activity_rate",
              "Tasa de actividad (EPA)", "Activos como porcentaje de la población de 16 y más años. Total nacional, ambos sexos.", "Tasa de actividad"),
    _epa_rate("temporary_rate", "temporary_rate", "temporary_rate",
              "Tasa de temporalidad (EPA)", "Asalariados con contrato temporal como porcentaje del total de asalariados. Total nacional, ambos sexos.",
              "Tasa de temporalidad"),
    _ine(
        "parttime_rate", "parttime_rate",
        title_es="Tasa de parcialidad (EPA)",
        description_es="Ocupados a tiempo parcial como porcentaje del total de ocupados. Total nacional, ambos sexos, calculado a partir de la EPA.",
        frequency="Q",
        fields=[
            Field("value", "Tasa de parcialidad", "pct", 1, column="parttime_rate", note_es=note(NSA, "Encuesta de Población Activa")),
            Field("yoy_pp", "Variación anual (pp)", "pp", 1, note_es=NSA),
        ],
        series=SPAIN,
    ),
    _ine(
        "employed", "employed",
        title_es="Ocupados (EPA)",
        description_es="Número de ocupados, total nacional, ambos sexos. Miles de personas.",
        frequency="Q",
        fields=[
            Field("value", "Ocupados", "persons", 1, column="employed", scale=3, note_es=note(NSA, "Miles de personas")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
        ],
        series=SPAIN,
    ),
    _ine(
        "labor_cost", "labor_cost",
        title_es="Coste laboral por trabajador (ETCL)",
        description_es="Coste laboral total por trabajador y mes en la industria, la construcción y los servicios, corregido de efectos estacionales y de calendario.",
        frequency="Q",
        fields=[
            Field("value", "Coste laboral por trabajador y mes", "currency", 0, column="labor_cost", currency="EUR", note_es=SCA),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
        ],
        series=SPAIN,
    ),
    _ine(
        "labor_cost_hour", "labor_cost_hour",
        title_es="Coste laboral por hora efectiva (ETCL)",
        description_es="Coste laboral total por hora efectiva trabajada en la industria, la construcción y los servicios, corregido de efectos estacionales y de calendario.",
        frequency="Q",
        fields=[
            Field("value", "Coste laboral por hora efectiva", "currency", 2, column="labor_cost_hour", currency="EUR", note_es=SCA),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
        ],
        series=SPAIN,
    ),
    _ine(
        "labor_cost_components", "labor_cost",
        title_es="Coste laboral total y coste salarial (ETCL)",
        description_es="Coste laboral total y coste salarial por trabajador y mes, corregidos de efectos estacionales y de calendario: nivel, variaciones anual y trimestral e índice con base 2019T1.",
        frequency="Q",
        fields=[
            Field("value", "Euros por trabajador y mes", "currency", 0, currency="EUR", note_es=SCA),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
            Field("qoq", "Variación trimestral", "pct_change", 1, column="qoq_change", note_es=SCA),
            Field("index_2019q1", "Índice 2019T1 = 100", "index", 1, note_es=note(SCA, "Base 2019T1 = 100")),
        ],
        series=long_series("component", order=["total", "salarial"],
                           labels={"total": "Coste laboral total", "salarial": "Coste salarial total"}),
    ),
    # ------------------------------------------------------------------ Precios
    Dataset(
        source="ine",
        indicator="cpi",
        csv="cpi.csv",
        title_es="Índice de Precios de Consumo (IPC)",
        description_es="IPC general nacional. Índice y tasa de variación anual.",
        source_dataset=str(TABLE_IDS["cpi"]),
        source_url=INE_TABLE_URL.format(TABLE_IDS["cpi"]),
        frequency="M",
        fields=[
            Field("value", "Índice", "index", 1, column="cpi_index", note_es=note(NSA, "Base 2025 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
        ],
        series=SPAIN,
    ),
    _ine(
        "cpi_special_groups", "cpi_special_groups",
        title_es="Inflación general y subyacente",
        description_es="Tasa de variación anual del IPC general y de la inflación subyacente (general sin alimentos no elaborados ni productos energéticos).",
        frequency="M",
        fields=[Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA)],
        series=[Series("headline", "IPC general", where={"group": "headline"}),
                Series("core", "Inflación subyacente", where={"group": "core"})],
    ),
    _ine(
        "cpi_ecoicop_groups", "cpi_ecoicop_groups",
        title_es="Inflación por grupos especiales: aportaciones",
        description_es="Variación anual, peso y aportación a la inflación (en puntos porcentuales) de los grupos especiales del IPC. La aportación usa el peso que el INE publica para cada año.",
        frequency="M",
        fields=[
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            Field("weight", "Peso en la cesta", "pct", 1, column="weight_pct",
                  note_es=note(ANNUAL, "Peso del año de cada observación, según el INE")),
            Field("contribution", "Aportación a la inflación", "pp", 2, note_es=NSA),
        ],
        series=long_series("group_name", order=[
            "Servicios", "Alimentos, bebidas y tabaco", "Bienes industriales sin productos energéticos", "Productos energéticos"]),
    ),
    _ine(
        "cpi_weights", "cpi_weights",
        title_es="Ponderaciones del IPC por grupos",
        description_es="Peso de cada grupo ECOICOP en la cesta del IPC del año en curso.",
        frequency="A",
        fields=[Field("weight", "Peso en la cesta", "pct", 1, column="weight_pct", note_es=ANNUAL)],
        series=long_series("group_name"),
    ),
    _ine(
        "cpi_ccaa", "cpi_ccaa",
        title_es="IPC por comunidades autónomas",
        description_es="Tasa de variación anual y mensual del IPC general en cada comunidad autónoma.",
        frequency="M",
        fields=[
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            # INE publishes no adjusted CPI; the monthly rate on original data is its official headline rate
            Field("mom", "Variación mensual", "pct_change", 1, column="mom_change", note_es=NSA),
        ],
        series=long_series("ccaa_code", label_column="ccaa_name"),
    ),
    _ine(
        "ipri", "ipri",
        title_es="Índice de Precios Industriales (IPRI)",
        description_es="Precios industriales en el mercado interior, total y por destino económico de los bienes. Índice y variaciones anual y mensual.",
        frequency="M",
        fields=[
            Field("value", "Índice", "index", 1, column="ipri_index", note_es=note(NSA, "Base 2021 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            # INE publishes no adjusted IPRI; its press release headlines the monthly rate on original data
            Field("mom", "Variación mensual", "pct_change", 1, column="mom_change", note_es=NSA),
        ],
        series=long_series("category", order=["total", "total_sin_energia", "consumo", "equipo", "intermedios", "energia"],
                           labels={
                               "total": "Total industria",
                               "total_sin_energia": "Total industria sin energía",
                               "consumo": "Bienes de consumo",
                               "equipo": "Bienes de equipo",
                               "intermedios": "Bienes intermedios",
                               "energia": "Energía",
                           }),
    ),
    # ------------------------------------------------------------------ Consumo y vivienda
    _ine(
        "retail_sales", "retail_sales",
        title_es="Comercio minorista (ICM)",
        description_es="Índice general de cifra de negocios del comercio al por menor sin estaciones de servicio, a precios constantes y corregido de estacionalidad y calendario.",
        frequency="M",
        fields=[
            Field("value", "Índice", "index", 1, column="retail_index",
                  note_es=note(SCA, "Base 2021 = 100. Precios constantes")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=SCA),
            Field("mom", "Variación mensual", "pct_change", 1, column="mom_change", note_es=SCA),
        ],
        series=SPAIN,
    ),
    _ine(
        "house_prices", "house_prices",
        title_es="Índice de Precios de Vivienda (IPV)",
        description_es="Índice de precios de vivienda (general, total nacional). Índice y variación anual.",
        frequency="Q",
        fields=[
            Field("value", "Índice", "index", 1, column="hpi_index", note_es=note(NSA, "Base 2025 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
        ],
        series=SPAIN,
    ),
    # ------------------------------------------------------------------ Turismo (ext/ine)
    _ine(
        "tourist_arrivals", "tourist_arrivals",
        title_es="Llegada de turistas internacionales (FRONTUR)",
        description_es="Número de turistas no residentes que llegan a España cada mes, datos originales, con variación anual y suma de los últimos 12 meses.",
        frequency="M",
        fields=[
            Field("value", "Turistas internacionales", "persons", 0, note_es=note(NSA, "Número de personas")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            Field("sum_12m", "Suma de los últimos 12 meses", "persons", 0,
                  note_es=note(NSA, "Suma móvil de 12 meses; vacía si falta algún mes de la ventana")),
        ],
        series=SPAIN,
    ),
    _ine(
        "tourist_spending", "tourist_spending",
        title_es="Gasto de los turistas internacionales (EGATUR)",
        description_es="Gasto total de los turistas no residentes en España cada mes, en millones de euros, datos originales, con variación anual y suma de los últimos 12 meses.",
        frequency="M",
        fields=[
            Field("value", "Gasto total", "currency", 0, currency="EUR", scale=6,
                  note_es=note(NSA, "Millones de euros")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            Field("sum_12m", "Suma de los últimos 12 meses", "currency", 0, currency="EUR", scale=6,
                  note_es=note(NSA, "Millones de euros. Suma móvil de 12 meses; vacía si falta algún mes de la ventana")),
        ],
        series=SPAIN,
    ),
    _ine(
        "hotel_overnight_stays", "hotel_overnight_stays",
        title_es="Pernoctaciones en establecimientos hoteleros",
        description_es="Pernoctaciones hoteleras totales y por residencia del viajero (residentes en España y en el extranjero), datos originales, total nacional.",
        frequency="M",
        fields=[
            Field("value", "Pernoctaciones", "count", 0, note_es=note(NSA, "Encuesta de Ocupación Hotelera")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            Field("sum_12m", "Suma de los últimos 12 meses", "count", 0,
                  note_es=note(NSA, "Suma móvil de 12 meses; vacía si falta algún mes de la ventana")),
        ],
        series=long_series("series", order=["total", "residentes", "no_residentes"],
                           labels={"total": "Total", "residentes": "Residentes en España", "no_residentes": "Residentes en el extranjero"}),
    ),
    # ------------------------------------------------------------------ Vivienda (ext/ine)
    _ine(
        "housing_transactions", "housing_transactions",
        title_es="Compraventa de viviendas (ETDP)",
        description_es="Número de compraventas de viviendas inscritas en los registros de la propiedad: total, vivienda nueva y vivienda de segunda mano. Total nacional.",
        frequency="M",
        fields=[
            Field("value", "Compraventas de viviendas", "count", 0, note_es=NSA),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            Field("sum_12m", "Suma de los últimos 12 meses", "count", 0,
                  note_es=note(NSA, "Suma móvil de 12 meses; vacía si falta algún mes de la ventana")),
        ],
        series=long_series("series", order=["total", "nueva", "usada"],
                           labels={"total": "Total viviendas", "nueva": "Vivienda nueva", "usada": "Vivienda de segunda mano"}),
    ),
    _ine(
        "mortgages", "mortgages",
        title_es="Hipotecas sobre viviendas",
        description_es="Número de hipotecas constituidas sobre viviendas e importe medio por hipoteca. Total nacional.",
        frequency="M",
        fields=[
            Field("value", "Hipotecas sobre viviendas", "count", 0, note_es=note(NSA, "Número de hipotecas constituidas")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            Field("sum_12m", "Suma de los últimos 12 meses", "count", 0,
                  note_es=note(NSA, "Suma móvil de 12 meses; vacía si falta algún mes de la ventana")),
            Field("avg_amount", "Importe medio por hipoteca", "currency", 0, currency="EUR",
                  note_es=note(NSA, "Euros. Importe total de las hipotecas sobre viviendas dividido por su número")),
        ],
        series=SPAIN,
    ),
    # ------------------------------------------------------------------ Empresas (ext/ine)
    _ine(
        "companies", "companies",
        title_es="Sociedades mercantiles creadas y disueltas",
        description_es="Número mensual de sociedades mercantiles constituidas y disueltas, total nacional.",
        frequency="M",
        fields=[
            Field("value", "Sociedades", "count", 0, note_es=note(NSA, "Número de sociedades mercantiles")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
            Field("sum_12m", "Suma de los últimos 12 meses", "count", 0,
                  note_es=note(NSA, "Suma móvil de 12 meses; vacía si falta algún mes de la ventana")),
        ],
        series=long_series("series", order=["created", "dissolved"],
                           labels={"created": "Sociedades creadas", "dissolved": "Sociedades disueltas"}),
    ),
    # ------------------------------------------------------------------ Hogares (ext/ine)
    _ine(
        "household_saving_rate", "household_saving_rate",
        title_es="Tasa de ahorro de los hogares",
        description_es="Ahorro bruto de los hogares e ISFLSH como porcentaje de su renta disponible bruta, Contabilidad Nacional Trimestral por sectores institucionales.",
        frequency="Q",
        fields=[
            Field("value", "Tasa de ahorro", "pct", 1,
                  note_es=note(SCA, "Porcentaje de la renta disponible bruta. Dato trimestral (no es la suma de cuatro trimestres)")),
        ],
        series=SPAIN,
    ),
    _ine(
        "population_nationality", "population_nationality",
        title_es="Población residente por nacionalidad",
        description_es="Población residente en España al inicio de cada trimestre (Estadística Continua de Población): total, de nacionalidad española y de nacionalidad extranjera.",
        frequency="Q",
        fields=[
            Field("value", "Población residente", "persons", 0,
                  note_es=note(NSA, "Número de personas a 1 de enero, abril, julio y octubre; hasta 2020 solo hay datos a 1 de enero y 1 de julio")),
            Field("yoy", "Variación anual", "pct_change", 2, column="yoy_change", note_es=NSA),
        ],
        series=long_series("series", order=["total", "espanola", "extranjera"],
                           labels={"total": "Población total", "espanola": "Nacionalidad española", "extranjera": "Nacionalidad extranjera"}),
    ),
    # ------------------------------------------------------------------ fill/ine (docs/notes/fill-ine.md)
    _ine(
        "gva_sectors", "gva_sectors",
        title_es="Valor añadido bruto por ramas de actividad",
        description_es="Variación anual y trimestral del valor añadido bruto a precios básicos, en volumen, de agricultura, industria, construcción y servicios (Contabilidad Nacional Trimestral). Se incluye el PIB como referencia.",
        frequency="Q",
        start="2016-01-01",
        fields=[
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=note(SCA, "Índice de volumen encadenado")),
            Field("qoq", "Variación trimestral", "pct_change", 1, column="qoq_change", note_es=note(SCA, "Índice de volumen encadenado")),
        ],
        series=long_series("sector", order=["agricultura", "industria", "construccion", "servicios", "pib"],
                           labels={
                               "agricultura": "Agricultura, ganadería, silvicultura y pesca",
                               "industria": "Industria",
                               "construccion": "Construcción",
                               "servicios": "Servicios",
                               "pib": "PIB a precios de mercado",
                           }),
    ),
    _ine(
        "employed_sectors", "employed_sectors",
        title_es="Ocupados por sector económico (EPA)",
        description_es="Número de ocupados en agricultura, industria, construcción y servicios, total nacional, ambos sexos. Miles de personas.",
        source_dataset="65126",
        frequency="Q",
        start="2016-01-01",
        fields=[
            Field("value", "Ocupados", "persons", 1, column="employed", scale=3, note_es=note(NSA, "Miles de personas")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=note(NSA, "Calculada sobre los niveles")),
        ],
        series=long_series("sector", order=["agricultura", "industria", "construccion", "servicios"],
                           labels={"agricultura": "Agricultura", "industria": "Industria",
                                   "construccion": "Construcción", "servicios": "Servicios"}),
    ),
    _ine(
        "cpi_rent", "cpi_rent",
        title_es="IPC: alquiler de vivienda principal",
        description_es="Índice de Precios de Consumo, subclase «Alquiler de vivienda principal» (ECOICOP ver.2), total nacional. Índice y variación anual publicada por el INE.",
        frequency="M",
        start="2016-01-01",
        fields=[
            Field("value", "Índice", "index", 1, column="rent_index", note_es=note(NSA, "Base 2025 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
        ],
        series=SPAIN,
    ),
    _ine(
        "hotel_prices", "hotel_prices",
        title_es="Índice de Precios Hoteleros (IPH)",
        description_es="Precio medio de las habitaciones de los establecimientos hoteleros (Coyuntura Turística Hotelera), total nacional y todas las categorías. Índice y variación anual publicada por el INE.",
        frequency="M",
        start="2016-01-01",
        fields=[
            Field("value", "Índice", "index", 1, column="hotel_price_index", note_es=note(NSA, "Base 2008 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
        ],
        series=SPAIN,
    ),
    _ine(
        "trade_prices", "trade_prices",
        title_es="Precios industriales de exportación e importación",
        description_es="Índices de Precios Industriales de Exportación (IPRIX) y de Importación (IPRIM) del total de la industria, total nacional. Índice y variación anual publicada por el INE.",
        source_dataset="61662, 61672",
        frequency="M",
        start="2016-01-01",
        fields=[
            Field("value", "Índice", "index", 1, column="price_index", note_es=note(NSA, "Base 2021 = 100")),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change", note_es=NSA),
        ],
        series=long_series("flow", order=["exportacion", "importacion"],
                           labels={"exportacion": "Exportación", "importacion": "Importación"}),
    ),
]
