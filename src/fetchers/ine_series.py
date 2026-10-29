"""
INE series registry: every INE series the pipeline uses, by stable identifier.

The pipeline used to download whole INE tables (39 MB of CSV) and then pick series by
regular expressions on their names, taking "the first match" (audit M1: it broke twice
when INE renamed series and caused C2/C3). Now each indicator is defined here by the INE
series codes (`COD`, e.g. "IPC290751") and the fetcher requests exactly those series
(`DATOS_SERIE/{code}?nult=N`). The processors select by code too.

Each series also carries a few tokens that must appear in the name INE returns for that
code. If INE ever reuses or redefines a code, the fetch fails loudly instead of silently
publishing another concept. A code that INE no longer serves fails the fetch as well.

Structure: INDICATORS[indicator] = {
    "table": INE table id (documentation, used for source links and provenance),
    "nult":  number of last observations requested per series (same as the old table call),
    "file":  raw file written to data/raw/ine/,
    "since": optional first date kept (ISO), to keep a window narrower than the series' history,
    "series": {role: (code, (name tokens, all must appear, case-insensitive))},
}
"""

SA = "ajustados de estacionalidad"
# Seasonal-adjustment rule (docs/audit/seasonal-adjustment.md): every series uses INE's
# "Datos ajustados de estacionalidad y calendario" variant whenever INE publishes one; the
# SA token in a series' name tokens makes the fetch fail if INE ever serves another variant.


def _s(code, *tokens):
    return (code, tuple(tokens))


# key -> (yoy code number, ytd code number, INE name of the activity)
_IPSS = {
    "hosteleria": (481, 480, "Hostelería"), "inmobiliarias": (475, 474, "Actividades inmobiliarias"),
    "mayoristas": (469, 468, "Comercio al por mayor e intermediarios del comercio"),
    "minoristas": (466, 465, "Comercio al por menor, excepto de vehículos"),
    "profesionales": (388, 387, "Actividades profesionales, científicas y técnicas"),
    "tic": (478, 477, "Información y comunicaciones"), "transporte": (484, 483, "Transporte y almacenamiento"),
    "vehiculos": (472, 471, "Venta y reparación de vehículos de motor"),
}
# key -> (yoy code number (mom = +2), INE name of the region)
_CCAA = {
    "an": (293659, "Andalucía"), "ar": (293715, "Aragón"), "as": (293771, "Asturias"), "ib": (293827, "Balears"),
    "cn": (293883, "Canarias"), "cb": (293939, "Cantabria"), "cl": (293995, "Castilla y León"),
    "cm": (294051, "Castilla - La Mancha"), "ct": (294107, "Cataluña"), "vc": (294163, "Comunitat Valenciana"),
    "ex": (294219, "Extremadura"), "ga": (294275, "Galicia"), "md": (294331, "Madrid"), "mc": (294387, "Murcia"),
    "nc": (294443, "Navarra"), "pv": (294499, "País Vasco"), "ri": (294555, "Rioja"), "ce": (294611, "Ceuta"),
    "ml": (293603, "Melilla"),
}


INDICATORS = {
    "gdp": dict(table=67822, nult=40, file="gdp_raw.csv", series={
        "value": _s("CNTR6652", "Total Nacional", SA, "Producto interior bruto a precios de mercado", "Dato base", "volumen encadenados"),
        # INE's published rates of the same SA series (audit M4 principle)
        "yoy": _s("CNTR6654", "Total Nacional", SA, "Producto interior bruto a precios de mercado", "Variación anual"),
        "qoq": _s("CNTR6653", "Total Nacional", SA, "Producto interior bruto a precios de mercado", "Variación trimestral"),
    }),
    "gdp_demand": dict(table=67824, nult=40, file="gdp_demand_raw.csv", series={
        "private_consumption": _s("CNTR7160", SA, "consumo final de los hogares y las ISFLSH", "Aportación anual"),
        "public_consumption": _s("CNTR7190", SA, "consumo final de las AAPP", "Aportación anual"),
        "gfcf": _s("CNTR7215", SA, "Formación bruta de capital fijo (FBCF)", "Aportación anual"),
        "inventories": _s("CNTR7262", SA, "existencias", "Aportación anual"),
        "external_demand": _s("CNTR7264", SA, "Demanda externa", "Aportación anual"),
    }),
    "industrial_production": dict(table=60280, nult=132, file="industrial_production_raw.csv", series={
        "index": _s("IPI15360", "Total Nacional", "Índice", SA, "Total industria"),
        "yoy": _s("IPI15374", "Total Nacional", "Variación anual", SA, "Total industria"),
        "mom": _s("IPI15381", "Total Nacional", "Variación mensual", SA, "Total industria"),
        "yoy_consumo": _s("IPI15373", "Total Nacional", "Variación anual", SA, "Bienes de consumo"),
        "yoy_equipo": _s("IPI15370", "Total Nacional", "Variación anual", SA, "Bienes de equipo"),
        "yoy_intermedios": _s("IPI15369", "Total Nacional", "Variación anual", SA, "Bienes intermedios"),
        "yoy_energia": _s("IPI15368", "Total Nacional", "Variación anual", SA, "Energía"),
        "ytd_total": _s("IPI15367", "Total Nacional", "media en lo que va de año", SA, "Total industria"),
        "ytd_consumo": _s("IPI15366", "Total Nacional", "media en lo que va de año", SA, "Bienes de consumo"),
        "ytd_equipo": _s("IPI15363", "Total Nacional", "media en lo que va de año", SA, "Bienes de equipo"),
        "ytd_intermedios": _s("IPI15362", "Total Nacional", "media en lo que va de año", SA, "Bienes intermedios"),
        "ytd_energia": _s("IPI15361", "Total Nacional", "media en lo que va de año", SA, "Energía"),
    }),
    # Table 61709 = seasonally and calendar adjusted ICN (61701, used before, is the original series)
    "industry_turnover": dict(table=61709, nult=120, file="industry_turnover_raw.csv", series={
        "yoy": _s("ICN2920", "Nacional", "Total industria", "Variación anual", SA),
    }),
    # Table 60290 = IASS seasonally and calendar adjusted (60289, used before, is calendar adjusted only)
    "services_turnover": dict(table=60290, nult=120, file="services_turnover_raw.csv", series={
        "yoy": _s("IAS4004", "Cifra de negocio", SA, "Índice General", "Nacional", "Variación anual"),
    }),
    # The series endpoint returns history before the table's own 2021-01 start; it is published.
    "services_production": dict(table=60732, nult=132, file="services_production_raw.csv", series={
        "index": _s("IPSS380", "precios corrientes", SA, "Índice General", "Total Nacional", "Índice"),
        "yoy": _s("IPSS490", SA, "Índice General", "Variación anual"),
        "mom": _s("IPSS491", SA, "Índice general", "Variación mensual"),
        **{f"yoy_{k}": _s(f"IPSS{y}", SA, n, "Total Nacional", "Variación anual") for k, (y, _, n) in _IPSS.items()},
        **{f"ytd_{k}": _s(f"IPSS{y}", SA, n, "Total Nacional", "media en lo que va de año") for k, (_, y, n) in _IPSS.items()},
    }),
    # Labour market (EPA, quarterly)
    "unemployment": dict(table=65349, nult=40, file="unemployment_raw.csv", series={
        "rate": _s("EPA453100", "Tasa de paro", "Ambos sexos", "Total Nacional", "Total."),
    }),
    "employment_rate": dict(table=65305, nult=40, file="employment_rate_raw.csv", series={
        "rate": _s("EPA441060", "Total Nacional", "Tasa de empleo", "Ambos sexos", "Total."),
    }),
    "activity_rate": dict(table=65295, nult=40, file="activity_rate_raw.csv", series={
        "rate": _s("EPA388079", "Total Nacional", "Tasa de actividad", "Ambos sexos", "Total."),
    }),
    # Original data: INE publishes the seasonally adjusted EPA level only in a workbook outside its API,
    # which the project treats as unavailable (docs/audit/seasonal-adjustment.md).
    "employed": dict(table=65109, nult=40, file="employed_raw.csv", series={
        "level": _s("EPA387796", "Total Nacional", "Ambos sexos", "Ocupados", "Valor absoluto"),
    }),
    "temporary_rate": dict(table=65194, nult=40, file="temporary_rate_raw.csv", series={
        "rate": _s("EPA416256", "Asalariados", "Total Nacional", "Ambos sexos", "Temporal", "Porcentaje"),
    }),
    "parttime_rate": dict(table=65148, nult=40, file="parttime_rate_raw.csv", series={
        "total": _s("EPA404358", "Ocupados", "Total Nacional", "Ambos sexos", "Total.", "Valor absoluto"),
        "parttime": _s("EPA404362", "Ocupados", "Total Nacional", "Ambos sexos", "tiempo parcial", "Valor absoluto"),
    }),
    "youth_unemployment": dict(table=65334, nult=40, file="youth_unemployment_raw.csv", series={
        "rate": _s("EPA452436", "Tasa de paro", "Ambos sexos", "Total Nacional", "Menores de 25"),
    }),
    # Labour costs (ETCL), seasonally and calendar adjusted (tables 11221/11222). Their original
    # variants (ETCL13726/13724/13744) equal the series used before (ETCL68/67/925, tables 6030/6034).
    "labor_cost": dict(table=11221, nult=40, file="labor_cost_raw.csv", series={
        "total": _s("ETCL13714", "Total Nacional", SA, "Coste total por trabajador", "Euros"),
        "salarial": _s("ETCL13712", "Total Nacional", SA, "Coste salarial total por trabajador", "Euros"),
        "yoy_total": _s("ETCL13713", "Total Nacional", SA, "Coste total por trabajador", "Tasa de variación anual"),
        "yoy_salarial": _s("ETCL13711", "Total Nacional", SA, "Coste salarial total por trabajador", "Tasa de variación anual"),
    }),
    "labor_cost_hour": dict(table=11222, nult=40, file="labor_cost_hour_raw.csv", series={
        "total": _s("ETCL13732", "Total Nacional", SA, "Coste laboral total por hora", "Euros"),
        "yoy": _s("ETCL13731", "Total Nacional", SA, "Coste laboral total por hora", "Tasa de variación anual"),
    }),
    # Prices
    "cpi": dict(table=79181, nult=120, file="cpi_raw.csv", series={
        "index": _s("IPC290751", "Nacional", "Índice general", "Índice"),
        "yoy": _s("IPC290750", "Nacional", "Índice general", "Variación anual"),
    }),
    "cpi_special_groups": dict(table=76130, nult=120, file="cpi_special_groups_raw.csv", series={
        "headline": _s("IPC290750", "Nacional", "Índice general", "Variación anual"),
        "core": _s("IPC292510", "Nacional", "Subyacente", "Variación anual"),
        "alimentos_bebidas_y_tabaco": _s("IPC292534", "Nacional", "Alimentos, bebidas y tabaco", "Variación anual"),
        "bienes_industriales_sin_productos_energeticos": _s("IPC292538", "Nacional", "Bienes industriales sin productos energéticos", "Variación anual"),
        "productos_energeticos": _s("IPC292458", "Nacional", "Productos energéticos", "Variación anual"),
        "servicios": _s("IPC292494", "Nacional", "Servicios", "Variación anual"),
    }),
    "cpi_weights": dict(table=76156, nult=12, file="cpi_weights_raw.csv", series={
        f"w{c}": _s(f"IPC{c}", "Nacional", "Ponderación") for c in range(331936, 331950)
    }),
    # Weights (per mille) of the four special groups, one observation per year. INE publishes them in
    # two series families: ECOICOP ver.2 (base 2025; table 76161, from 2026) and the previous base
    # (table 50951, 2022-2025). Both are fetched so every year has its own weights (audit M2).
    "cpi_special_weights": dict(table=76161, nult=12, file="cpi_special_weights_raw.csv", series={
        "alimentos_bebidas_y_tabaco": _s("IPC332382", "Nacional", "Alimentos, bebidas y tabaco", "Ponderación"),
        "productos_energeticos": _s("IPC332363", "Nacional", "Productos energéticos", "Ponderación"),
        "servicios": _s("IPC332372", "Nacional", "Servicios", "Ponderación"),
        "bienes_industriales_sin_productos_energeticos": _s("IPC332383", "Nacional", "Bienes industriales sin productos energéticos", "Ponderación"),
        "prev_alimentos_bebidas_y_tabaco": _s("IPC233251", "Nacional", "Alimentos, bebidas y tabaco", "Ponderación"),
        "prev_productos_energeticos": _s("IPC233270", "Nacional", "Productos energéticos", "Ponderación"),
        "prev_servicios": _s("IPC233252", "Nacional", "Servicios", "Ponderación"),
        "prev_bienes_industriales_sin_productos_energeticos": _s("IPC233249", "Nacional", "Bienes industriales sin productos energéticos", "Ponderación"),
    }),
    "retail_sales": dict(table=67178, nult=120, file="retail_sales_raw.csv", series={
        "index": _s("ICM4062", "Total Nacional", "precios constantes", "47 sin 473", "General", "Índice", SA),
        "yoy": _s("ICM4079", "precios constantes", "47 sin 473", "General", "Variación anual", SA),
        "mom": _s("ICM4080", "precios constantes", "47 sin 473", "General", "Variación mensual", SA),
    }),
    "house_prices": dict(table=80270, nult=40, file="house_prices_raw.csv", series={
        "index": _s("IPV1209", "Nacional", "General", "Índice"),
        "yoy": _s("IPV1376", "Nacional", "General", "Variación anual"),
    }),
    "ipri": dict(table=76655, nult=120, file="ipri_raw.csv", series={
        f"{part}_{k}": _s(f"IPR{code}", "Nacional", "Mercado interior", n, what)
        for k, (idx, yoy, mom, n) in {
            "total": (34522, 34953, 34954, "Total industria."), "total_sin_energia": (34515, 34932, 34933, "Total industria sin energía"),
            "consumo": (34521, 34950, 34951, "Bienes de consumo."), "equipo": (34518, 34941, 34942, "Bienes de equipo"),
            "intermedios": (34517, 34938, 34939, "Bienes intermedios"), "energia": (34516, 34935, 34936, "Energía")}.items()
        for part, code, what in (("index", idx, "Índice"), ("yoy", yoy, "Variación anual"), ("mom", mom, "Variación mensual"))
    }),
    "cntr_employment": dict(table=67201, nult=40, file="cntr_employment_raw.csv", series={
        "employed_persons": _s("CNTR7659", "Ocupado", "Personas", SA, "Total CNAE"),
        "employed_fte": _s("CNTR7818", "Ocupado", "equivalentes a tiempo completo", SA, "Total CNAE"),
        "hours_worked": _s("CNTR7896", "Ocupado", "Horas trabajadas", SA, "Total CNAE"),
    }),
    "population_age": dict(table=65061, nult=40, file="population_age_raw.csv", series={
        "total": _s("EPA384355", "Total Nacional", "Ambos sexos", "Total", "Valor absoluto"),
        **{f"age_{a}_{b}": _s(f"EPA{c}", "Total Nacional", "Ambos sexos", f"De {a} a {b} años", "Valor absoluto")
           for c, a, b in zip(range(384363, 384382, 2), (16, 20, 25, 30, 35, 40, 45, 50, 55, 60), (19, 24, 29, 34, 39, 44, 49, 54, 59, 64))},
    }),
    "cpi_ccaa": dict(table=76136, nult=84, file="cpi_ccaa_raw.csv", series={
        **{f"yoy_{k}": _s(f"IPC{c}", n, "Índice general", "Variación anual") for k, (c, n) in _CCAA.items()},
        **{f"mom_{k}": _s(f"IPC{c + 2}", n, "Índice general", "Variación mensual") for k, (c, n) in _CCAA.items()},
    }),
    "business_confidence": dict(table=8027, nult=44, file="business_confidence_raw.csv", series={
        "ice": _s("ICE1", "Total Nacional", "Índice", "Base 2013"),
        "situacion": _s("ICE54", "Total Nacional", "Situación del trimestre anterior"),
        "expectativas": _s("ICE53", "Total Nacional", "Expectativas del trimestre entrante"),
    }),
    # Extended indicators
    "tourist_arrivals": dict(table=10822, nult=132, file="tourist_arrivals_raw.csv", series={
        "level": _s("FREG337", "Total", "Turista", "Dato base", "Total Nacional"),
        "yoy": _s("FREG321", "Total", "Turista", "Tasa de variación anual", "Total Nacional"),
    }),
    "tourist_spending": dict(table=10838, nult=132, file="tourist_spending_raw.csv", series={
        "level": _s("FREG647", "Total", "Turista", "Gasto total", "Total Nacional", "Dato base"),
        "yoy": _s("FREG623", "Total", "Turista", "Gasto total", "Tasa de variación anual"),
    }),
    "hotel_overnight_stays": dict(table=2009, nult=192, file="hotel_overnight_stays_raw.csv", series={
        "total": _s("EOT25", "Nacional", "Pernoctaciones", "Total categorías", "Total"),
        "residentes": _s("EOT33", "Nacional", "Pernoctaciones", "Total categorías", "Residentes en España"),
        "no_residentes": _s("EOT41", "Nacional", "Pernoctaciones", "Total categorías", "Residentes en el extranjero"),
    }),
    "housing_transactions": dict(table=6150, nult=192, file="housing_transactions_raw.csv", series={
        "total": _s("ETDP1826", "Total Nacional", "General", "Compraventa", "Número"),
        "nueva": _s("ETDP1825", "Total Nacional", "Vivienda nueva", "Compraventa", "Número"),
        "usada": _s("ETDP1824", "Total Nacional", "Vivienda segunda mano", "Compraventa", "Número"),
    }),
    "mortgages": dict(table=13896, nult=192, file="mortgages_raw.csv", series={
        "number": _s("HPT34618", "Viviendas", "Número de hipotecas", "Total Nacional"),
        "amount": _s("HPT34565", "Viviendas", "Importe de hipotecas", "Total Nacional"),
    }),
    "companies": dict(table=13912, nult=192, file="companies_raw.csv", series={
        "created": _s("SM21483", "Sociedades Constitu", "Número de Sociedades", "Total Nacional", "Mercantiles"),
        "dissolved": _s("SM21486", "Disueltas", "Número de Sociedades", "Total Nacional", "Mercantiles"),
    }),
    "household_saving_rate": dict(table=62275, nult=80, file="household_saving_rate_raw.csv", series={
        "rate": _s("CTNFSI11270", "Hogares e Instituciones sin fines de lucro", "Tasa de ahorro", "Total Nacional", SA),
    }),
    "population_nationality": dict(table=59587, nult=70, file="population_nationality_raw.csv", series={
        "total": _s("ECP4961", "Total Nacional", "Total", "Todas las edades", "Población"),
        "espanola": _s("ECP4901", "Total Nacional", "Española", "Todas las edades"),
        "extranjera": _s("ECP701", "Total Nacional", "Extranjera", "Todas las edades"),
    }),
}


def code(indicator: str, role: str) -> str:
    """INE series code of one role of an indicator. KeyError if it is not defined."""
    return INDICATORS[indicator]["series"][role][0]


def codes(indicator: str) -> dict:
    """role -> code for an indicator."""
    return {role: c for role, (c, _) in INDICATORS[indicator]["series"].items()}


# Table ids, for the published provenance (`source.dataset` / `source.url`, src/export/ine.py).
# Keys are the old indicator names, kept so published metadata do not change.
TABLE_IDS = {name: spec["table"] for name, spec in INDICATORS.items()}
TABLE_IDS.update({
    "cpi_ecoicop_groups": 76125,   # IPC Índices nacionales de grupos ECOICOP ver.2 (published as the source of the contributions chart)
    "cpi_special_weights": 76161,  # IPC Ponderaciones de grupos especiales
})


# Stable labels of the CPI weight groups (published as series keys/labels by src/export/ine.py).
# INE names the same code differently in its table and series endpoints and renames groups
# between releases, so the label is fixed here, by code, instead of read from the INE name.
CPI_GROUP_LABELS = {
    "IPC331936": "Índice general",
    "IPC331937": "Alimentos y bebidas no alcohólicas",
    "IPC331943": "Bebidas alcohólicas, tabaco y estupefacientes",
    "IPC331938": "Vestido y calzado",
    "IPC331939": "Vivienda, agua, electricidad, gas y otros combustibles",
    "IPC331940": "Muebles, artículos del hogar y artículos para el mantenimiento corriente del hogar",
    "IPC331941": "Sanidad",
    "IPC331942": "Transporte",
    "IPC331944": "Información y comunicaciones",
    "IPC331945": "Actividades recreativas, deporte y cultura",
    "IPC331946": "Servicios de educación",
    "IPC331947": "Restaurantes y servicios de alojamiento",
    "IPC331948": "Seguros y servicios financieros",
    "IPC331949": "Cuidado personal, protección social, y bienes y servicios diversos",
}
