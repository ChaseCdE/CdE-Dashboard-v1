"""
Independent check of every ine.* dataset against the INE Tempus API.

For each published series/field we name the INE series code that SHOULD feed it,
assert (identity) that the series name returned by the API contains the tokens
that define it (geography, concept, adjustment, unit), and compare values on the
latest observations. Periods are dated independently from Anyo + FK_Periodo.

Modes:
  level     published value must equal the INE value (after 4-decimal rounding).
  official  published field is computed by the pipeline; compare with the rate INE
            publishes. FAIL if |diff| > 0.1, WARN if it differs once rounded to the
            field's display decimals (the site would show a figure INE did not publish).
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, add_months, http_json, load, quarter_start, first_of_month, series  # noqa: E402

API = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{}"
NULT = 36

# (dataset, series, field, INE code, mode, tokens that must appear in the INE series name)
SA = "Datos ajustados de estacionalidad y calendario"
SPEC = [
    ("ine.gdp", "es", "value", "CNTR6652", "level", ["Total Nacional", SA, "Producto interior bruto a precios de mercado", "Dato base", "volumen encadenados"]),
    # Seasonal-adjustment pass: yoy/qoq are INE's published rates of the SA series (were recomputed from CNTR6652).
    ("ine.gdp", "es", "yoy", "CNTR6654", "level", ["Total Nacional", SA, "Producto interior bruto", "Variación anual"]),
    ("ine.gdp", "es", "qoq", "CNTR6653", "level", ["Total Nacional", SA, "Producto interior bruto", "Variación trimestral"]),
    # Demand contributions: INE's headline contributions are computed on SA data, like ine.gdp.
    ("ine.gdp_demand", "private_consumption", "contribution", "CNTR7160", "level", [SA, "consumo final de los hogares y las ISFLSH", "Aportación anual"]),
    ("ine.gdp_demand", "public_consumption", "contribution", "CNTR7190", "level", [SA, "consumo final de las AAPP", "Aportación anual"]),
    ("ine.gdp_demand", "gfcf", "contribution", "CNTR7215", "level", [SA, "Formación bruta de capital fijo (FBCF)", "Aportación anual"]),
    ("ine.gdp_demand", "external_demand", "contribution", "CNTR7264", "level", [SA, "Demanda externa", "Aportación anual"]),
    ("ine.industrial_production", "es", "value", "IPI15360", "level", ["Total Nacional", "Índice", SA, "Total industria"]),
    ("ine.industrial_production", "es", "yoy", "IPI15374", "level", ["Total Nacional", "Variación anual", SA, "Total industria"]),
    ("ine.industrial_production", "es", "mom", "IPI15381", "official", ["Total Nacional", "Variación mensual", SA, "Total industria"]),
    # Seasonal-adjustment pass: ICN2412 (original) -> ICN2920 (SA+calendar); IAS3856 (calendar only) -> IAS4004 (SA+calendar).
    ("ine.industry_turnover", "es", "yoy", "ICN2920", "level", ["Nacional", "Total industria", "Variación anual", SA]),
    ("ine.services_turnover", "es", "yoy", "IAS4004", "level", ["Cifra de negocio", SA, "Índice General", "Nacional", "Variación anual"]),
    ("ine.services_production", "es", "value", "IPSS380", "level", ["precios corrientes", SA, "Índice General", "Total Nacional", "Índice"]),
    ("ine.services_production", "es", "yoy", "IPSS490", "level", [SA, "Índice General", "Variación anual"]),
    ("ine.services_production", "es", "mom", "IPSS491", "official", [SA, "Índice General", "Variación mensual"]),
    ("ine.business_confidence", "ice", "value", "ICE1", "level", ["Total Nacional", "Índice", "Base 2013"]),
    ("ine.business_confidence", "situacion", "value", "ICE54", "level", ["Total Nacional", "Situación del trimestre anterior"]),
    ("ine.business_confidence", "expectativas", "value", "ICE53", "level", ["Total Nacional", "Expectativas del trimestre entrante"]),
    ("ine.unemployment", "es", "value", "EPA453100", "level", ["Tasa de paro", "Ambos sexos", "Total Nacional", "Total."]),
    ("ine.youth_unemployment", "es", "value", "EPA452436", "level", ["Tasa de paro", "Ambos sexos", "Total Nacional", "Menores de 25"]),
    ("ine.employment_rate", "es", "value", "EPA441060", "level", ["Total Nacional", "Tasa de empleo", "Ambos sexos", "Total."]),
    ("ine.activity_rate", "es", "value", "EPA388079", "level", ["Total Nacional", "Tasa de actividad", "Ambos sexos", "Total."]),
    ("ine.temporary_rate", "es", "value", "EPA416256", "level", ["Asalariados", "Total Nacional", "Ambos sexos", "Temporal", "Porcentaje"]),
    # ine.employed stays on original data: INE's adjusted EPA level exists only in a workbook (treated as unavailable).
    ("ine.employed", "es", "value", "EPA387796", "level", ["Total Nacional", "Ambos sexos", "Ocupados", "Valor absoluto"]),
    ("ine.parttime_rate", "es", "value", "EPA404363", "official", ["Ocupados", "Total Nacional", "Ambos sexos", "Total.", "tiempo parcial", "Porcentaje"]),
    # Seasonal-adjustment pass: ETCL68/67/925 (original) -> SA+calendar ETCL13714/13712/13732, with INE's own yoy.
    ("ine.labor_cost", "es", "value", "ETCL13714", "level", ["Total Nacional", SA, "Coste total por trabajador", "Euros"]),
    ("ine.labor_cost", "es", "yoy", "ETCL13713", "level", ["Total Nacional", SA, "Coste total por trabajador", "Tasa de variación anual"]),
    ("ine.labor_cost_hour", "es", "value", "ETCL13732", "level", [SA, "Coste laboral total por hora", "Total Nacional", "Euros"]),
    ("ine.labor_cost_hour", "es", "yoy", "ETCL13731", "level", [SA, "Coste laboral total por hora", "Total Nacional", "Tasa de variación anual"]),
    ("ine.labor_cost_components", "total", "value", "ETCL13714", "level", [SA, "Coste total por trabajador", "Euros", "Total Nacional"]),
    ("ine.labor_cost_components", "salarial", "value", "ETCL13712", "level", [SA, "Coste salarial total por trabajador", "Euros", "Total Nacional"]),
    ("ine.labor_cost_components", "total", "yoy", "ETCL13713", "level", [SA, "Coste total por trabajador", "Tasa de variación anual"]),
    ("ine.labor_cost_components", "salarial", "yoy", "ETCL13711", "level", [SA, "Coste salarial total por trabajador", "Tasa de variación anual"]),
    ("ine.cpi", "es", "value", "IPC290751", "level", ["Nacional", "Índice general", "Índice"]),
    ("ine.cpi", "es", "yoy", "IPC290750", "official", ["Nacional", "Índice general", "Variación anual"]),
    ("ine.cpi_special_groups", "headline", "yoy", "IPC290750", "level", ["Nacional", "Índice general", "Variación anual"]),
    ("ine.cpi_special_groups", "core", "yoy", "IPC292510", "level", ["Nacional", "Subyacente", "Variación anual"]),
    ("ine.cpi_ecoicop_groups", "alimentos_bebidas_y_tabaco", "yoy", "IPC292534", "level", ["Nacional", "Alimentos, bebidas y tabaco", "Variación anual"]),
    ("ine.cpi_ecoicop_groups", "bienes_industriales_sin_productos_energeticos", "yoy", "IPC292538", "level", ["Nacional", "Bienes industriales sin productos energéticos", "Variación anual"]),
    ("ine.cpi_ecoicop_groups", "productos_energeticos", "yoy", "IPC292458", "level", ["Nacional", "Productos energéticos", "Variación anual"]),
    ("ine.cpi_ecoicop_groups", "servicios", "yoy", "IPC292494", "level", ["Nacional", "Servicios", "Variación anual"]),
    ("ine.retail_sales", "es", "value", "ICM4062", "level", ["Total Nacional", "precios constantes", "47 sin 473", "General", "Índice", SA]),
    ("ine.retail_sales", "es", "yoy", "ICM4079", "official", ["precios constantes", "47 sin 473", "General", "Variación anual", SA]),
    ("ine.retail_sales", "es", "mom", "ICM4080", "official", ["precios constantes", "47 sin 473", "General", "Variación mensual", SA]),
    ("ine.house_prices", "es", "value", "IPV1209", "level", ["Nacional", "General", "Índice"]),
    ("ine.house_prices", "es", "yoy", "IPV1376", "official", ["Nacional", "General", "Variación anual"]),
    ("ine.tourist_arrivals", "es", "value", "FREG337", "level", ["Total", "Turista", "Dato base", "Total Nacional"]),
    ("ine.tourist_arrivals", "es", "yoy", "FREG321", "official", ["Total", "Turista", "Tasa de variación anual", "Total Nacional"]),
    ("ine.tourist_spending", "es", "value", "FREG647", "level", ["Total", "Turista", "Gasto total", "Total Nacional", "Dato base"]),
    ("ine.tourist_spending", "es", "yoy", "FREG623", "official", ["Total", "Turista", "Gasto total", "Tasa de variación anual"]),
    ("ine.hotel_overnight_stays", "total", "value", "EOT25", "level", ["Nacional", "Pernoctaciones", "Total categorías", "Total"]),
    ("ine.hotel_overnight_stays", "residentes", "value", "EOT33", "level", ["Nacional", "Pernoctaciones", "Total categorías", "Residentes en España"]),
    ("ine.hotel_overnight_stays", "no_residentes", "value", "EOT41", "level", ["Nacional", "Pernoctaciones", "Total categorías", "Residentes en el extranjero"]),
    ("ine.housing_transactions", "total", "value", "ETDP1826", "level", ["Total Nacional", "General", "Compraventa", "Número"]),
    ("ine.housing_transactions", "nueva", "value", "ETDP1825", "level", ["Total Nacional", "Vivienda nueva", "Compraventa", "Número"]),
    ("ine.housing_transactions", "usada", "value", "ETDP1824", "level", ["Total Nacional", "Vivienda segunda mano", "Compraventa", "Número"]),
    ("ine.mortgages", "es", "value", "HPT34618", "level", ["Viviendas", "Número de hipotecas", "Total Nacional"]),
    ("ine.companies", "created", "value", "SM21483", "level", ["Sociedades Constitu", "Número de Sociedades", "Total Nacional", "Mercantiles"]),
    ("ine.companies", "dissolved", "value", "SM21486", "level", ["Disueltas", "Número de Sociedades", "Total Nacional", "Mercantiles"]),
    ("ine.household_saving_rate", "es", "value", "CTNFSI11270", "level", ["Hogares e Instituciones sin fines de lucro", "Tasa de ahorro", "Total Nacional", SA]),
    ("ine.population_nationality", "total", "value", "ECP4961", "level", ["Total Nacional", "Total", "Todas las edades", "Población"]),
    ("ine.population_nationality", "espanola", "value", "ECP4901", "level", ["Total Nacional", "Española", "Todas las edades"]),
    ("ine.population_nationality", "extranjera", "value", "ECP701", "level", ["Total Nacional", "Extranjera", "Todas las edades"]),
]

# fill/ine: datasets added to complete page sections. Codes are written again here, independently of src/.
_GVA = {"agricultura": ("CNTR6659", "CNTR6658", "VABpb Agricultura, ganadería, silvicultura y pesca (A, CNAE 2009)"),
        "industria": ("CNTR6664", "CNTR6663", "VABpb Industria (B-E, CNAE 2009)"),
        "construccion": ("CNTR6674", "CNTR6673", "VABpb Construcción (F, CNAE 2009)"),
        "servicios": ("CNTR6679", "CNTR6678", "VABpb Servicios (G-T, CNAE 2009)"),
        "pib": ("CNTR6654", "CNTR6653", "Producto interior bruto a precios de mercado")}
for k, (yoy, qoq, name) in _GVA.items():
    SPEC.append(("ine.gva_sectors", k, "yoy", yoy, "level", ["Total Nacional", SA, name, "Variación anual", "Índices de volumen encadenados"]))
    SPEC.append(("ine.gva_sectors", k, "qoq", qoq, "level", ["Total Nacional", SA, name, "Variación trimestral", "Índices de volumen encadenados"]))
for k, c, name in (("agricultura", "EPA399207", "Agricultura"), ("industria", "EPA399208", "Industria"),
                   ("construccion", "EPA399209", "Construcción"), ("servicios", "EPA399210", "Servicios")):
    SPEC.append(("ine.employed_sectors", k, "value", c, "level", ["Total Nacional", "Ocupados", "Ambos sexos", "Total", name, "Valor absoluto"]))
SPEC += [
    ("ine.cpi_rent", "es", "value", "IPC291807", "level", ["Nacional", "Alquiler de vivienda principal", "Índice"]),
    ("ine.cpi_rent", "es", "yoy", "IPC291806", "level", ["Nacional", "Alquiler de vivienda principal", "Variación anual"]),
    ("ine.hotel_prices", "es", "value", "EOT14624", "level", ["Indice de precios hoteleros", "Base 2008", "Nacional", "Dato base"]),
    ("ine.hotel_prices", "es", "yoy", "EOT14625", "level", ["Indice de precios hoteleros", "Base 2008", "Nacional", "Tasa de variación interanual"]),
    ("ine.trade_prices", "exportacion", "value", "IPR30874", "level", ["Nacional", "IPRIX", "Total industria", "Índice"]),
    ("ine.trade_prices", "exportacion", "yoy", "IPR30945", "level", ["Nacional", "IPRIX", "Total industria", "Variación anual"]),
    ("ine.trade_prices", "importacion", "value", "IPR34018", "level", ["Nacional", "IPRIM", "Total industria", "Índice"]),
    ("ine.trade_prices", "importacion", "yoy", "IPR34016", "level", ["Nacional", "IPRIM", "Total industria", "Variación anual"]),
]

# fill/ine expectations on the published files (identity of the dataset, not only of the numbers).
# adj: SCA = seasonally and calendar adjusted, NSA = original data. Phrases are the ones the contract/notes use.
_PHRASE = {"SCA": "datos corregidos de efectos estacionales y de calendario",
           "NSA": "datos originales (sin corregir de estacionalidad)"}
_URL = "https://www.ine.es/jaxiT3/Tabla.htm?t={}"
FILL = {
    "ine.gva_sectors": dict(table="67822", freq="Q", adj="SCA", series=["agricultura", "industria", "construccion", "servicios", "pib"],
                            fields={"yoy": ("pct_change", 0), "qoq": ("pct_change", 0)}),
    "ine.employed_sectors": dict(table="65126", freq="Q", adj="NSA", series=["agricultura", "industria", "construccion", "servicios"],
                                 fields={"value": ("persons", 3), "yoy": ("pct_change", 0)}),
    "ine.cpi_rent": dict(table="76128", freq="M", adj="NSA", series=["es"], fields={"value": ("index", 0), "yoy": ("pct_change", 0)}),
    "ine.hotel_prices": dict(table="12157", freq="M", adj="NSA", series=["es"], fields={"value": ("index", 0), "yoy": ("pct_change", 0)}),
    "ine.trade_prices": dict(table="61662, 61672", freq="M", adj="NSA", series=["exportacion", "importacion"],
                             fields={"value": ("index", 0), "yoy": ("pct_change", 0)}),
}

_IPI = {"total": ("15374", "15367", "Total industria"), "consumo": ("15373", "15366", "Bienes de consumo"),
        "equipo": ("15370", "15363", "Bienes de equipo"), "intermedios": ("15369", "15362", "Bienes intermedios"),
        "energia": ("15368", "15361", "Energía")}
for k, (yoy, ytd, name) in _IPI.items():
    SPEC.append(("ine.ipi_sectors", k, "yoy", f"IPI{yoy}", "level", ["Total Nacional", "Variación anual", SA, name]))
    SPEC.append(("ine.ipi_sectors", k, "ytd", f"IPI{ytd}", "level", ["Total Nacional", "media en lo que va de año", SA, name]))

_IPSS = {"hosteleria": (481, 480, "Hostelería"), "inmobiliarias": (475, 474, "Actividades inmobiliarias"),
         # "Comercio mayorista" = CNAE 46 (IPSS469/468). The pipeline publishes section G
         # (IPSS487/486: wholesale + retail + motor vehicles) under this label.
         "mayoristas": (469, 468, "Comercio al por mayor e intermediarios del comercio"),
         "minoristas": (466, 465, "Comercio al por menor, excepto de vehículos"),
         "profesionales": (388, 387, "Actividades profesionales, científicas y técnicas"),
         "tic": (478, 477, "Información y comunicaciones"), "transporte": (484, 483, "Transporte y almacenamiento"),
         "vehiculos": (472, 471, "Venta y reparación de vehículos de motor")}
for k, (yoy, ytd, name) in _IPSS.items():
    SPEC.append(("ine.ipss_sectors", k, "yoy", f"IPSS{yoy}", "level", [SA, name, "Total Nacional", "Variación anual"]))
    SPEC.append(("ine.ipss_sectors", k, "ytd", f"IPSS{ytd}", "level", [SA, name, "Total Nacional", "media en lo que va de año"]))

_IPRI = {"total": (34522, 34953, 34954, "Total industria."), "total_sin_energia": (34515, 34932, 34933, "Total industria sin energía"),
         "consumo": (34521, 34950, 34951, "Bienes de consumo."), "equipo": (34518, 34941, 34942, "Bienes de equipo"),
         "intermedios": (34517, 34938, 34939, "Bienes intermedios"), "energia": (34516, 34935, 34936, "Energía")}
for k, (idx, yoy, mom, name) in _IPRI.items():
    SPEC.append(("ine.ipri", k, "value", f"IPR{idx}", "level", ["Nacional", "Mercado interior", name, "Índice"]))
    SPEC.append(("ine.ipri", k, "yoy", f"IPR{yoy}", "level", ["Nacional", "Mercado interior", name, "Variación anual"]))
    SPEC.append(("ine.ipri", k, "mom", f"IPR{mom}", "level", ["Nacional", "Mercado interior", name, "Variación mensual"]))

_CCAA = {"an": (293659, "Andalucía"), "ar": (293715, "Aragón"), "as": (293771, "Asturias"), "ib": (293827, "Balears"),
         "cn": (293883, "Canarias"), "cb": (293939, "Cantabria"), "cl": (293995, "Castilla y León"),
         "cm": (294051, "Castilla - La Mancha"), "ct": (294107, "Cataluña"), "vc": (294163, "Comunitat Valenciana"),
         "ex": (294219, "Extremadura"), "ga": (294275, "Galicia"), "md": (294331, "Madrid"), "mc": (294387, "Murcia"),
         "nc": (294443, "Navarra"), "pv": (294499, "País Vasco"), "ri": (294555, "Rioja"), "ce": (294611, "Ceuta"),
         "ml": (293603, "Melilla")}
for k, (yoy, name) in _CCAA.items():
    SPEC.append(("ine.cpi_ccaa", k, "yoy", f"IPC{yoy}", "level", [name, "Índice general", "Variación anual"]))
    SPEC.append(("ine.cpi_ccaa", k, "mom", f"IPC{yoy + 2}", "level", [name, "Índice general", "Variación mensual"]))

# Series used only for recomputations (gdp_productivity, mortgages.avg_amount, cpi contributions).
AUX = {
    "CNTR7659": ["Ocupado", "Personas", SA, "Total CNAE"],
    "CNTR7896": ["Ocupado", "Horas trabajadas", SA, "Total CNAE"],
    "EPA384355": ["Total Nacional", "Ambos sexos", "Total", "Valor absoluto"],
    "HPT34565": ["Viviendas", "Importe de hipotecas", "Total Nacional"],
    "IPC332382": ["Alimentos, bebidas y tabaco", "Ponderación"],
    "IPC332383": ["Bienes industriales sin productos energéticos", "Ponderación"],
    "IPC332363": ["Productos energéticos", "Ponderación"],
    "IPC332372": ["Servicios", "Ponderación"],
    # previous-base weights of the same four groups (table 50951), used for the years before 2026
    "IPC233251": ["Alimentos, bebidas y tabaco", "Ponderación"],
    "IPC233249": ["Bienes industriales sin productos energéticos", "Ponderación"],
    "IPC233270": ["Productos energéticos", "Ponderación"],
    "IPC233252": ["Servicios", "Ponderación"],
}
WA_CODES = [f"EPA{c}" for c in range(384363, 384382, 2)]  # 16-19 ... 60-64, ambos sexos
for c in WA_CODES:
    AUX[c] = ["Total Nacional", "Ambos sexos", "años", "Valor absoluto"]
CPI_WEIGHTS = {f"IPC{c}": None for c in range(331937, 331950)}
for c in CPI_WEIGHTS:
    AUX[c] = ["Nacional", "Ponderación"]


def ine_date(d: dict) -> str | None:
    y, p = d["Anyo"], d["FK_Periodo"]
    if 1 <= p <= 12:
        return first_of_month(y, p)
    if 19 <= p <= 22:
        return quarter_start(y, p - 18)
    if p == 28:
        return f"{y:04d}-01-01"
    return None


def fetch(code: str, nult: int = NULT):
    j = http_json(API.format(code), {"nult": nult})
    data = {}
    for d in j.get("Data", []):
        x = ine_date(d)
        if x and d.get("Valor") is not None:
            data[x] = float(d["Valor"])
    return j.get("Nombre", "").strip(), data


def fetch_all(codes, nult=NULT):
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = dict(zip(codes, ex.map(lambda c: fetch(c, nult), codes)))
    return res


def identity(rep: Report, ds: str, code: str, name: str, tokens: list) -> bool:
    low = name.lower()
    miss = [t for t in tokens if t.lower() not in low]
    if miss:
        rep.add(ds, "identity", "FAIL", f"{code} '{name}' lacks {miss}")
        return False
    return True


def run(rep: Report) -> dict:
    codes = sorted({s[3] for s in SPEC} | set(AUX))
    got = fetch_all(codes)
    ids_ok = {}
    for ds, skey, fkey, code, mode, tokens in SPEC:
        name, data = got[code]
        ok = identity(rep, ds, code, name, tokens)
        ids_ok.setdefault(ds, True)
        ids_ok[ds] &= ok
        try:
            pub = series(ds, skey, fkey)
        except KeyError as e:
            rep.add(ds, "values", "FAIL", str(e))
            continue
        lab = f"{skey}.{fkey}<-{code}"
        if mode == "level":
            rep.compare(ds, "values", pub, data, tol=1e-4, label=lab, last_n=24)
        else:
            dec = next(f["decimals"] for f in load(ds)["fields"] if f["key"] == fkey)
            r = rep.compare(ds, "transform", pub, data, tol=0.1, label=lab + " (computed vs official)", last_n=None)
            disp = [k for k in sorted(data) if k in pub and round(pub[k] + 1e-9, dec) != round(data[k], dec)]
            if disp and r.status == "PASS":
                r.status = "WARN"
                r.detail += f"; {len(disp)} periods display a different rounded figure than INE (e.g. {disp[-1]}: {pub[disp[-1]]} vs {data[disp[-1]]})"
    for c, toks in AUX.items():
        identity(rep, "ine.aux", c, got[c][0], toks)
    for ds, ok in ids_ok.items():
        if ok:
            rep.add(ds, "identity", "PASS", "INE series names match the definition")
    derived(rep, got)
    labels(rep)
    fill_meta(rep, got)
    return got


def fill_meta(rep: Report, got: dict):
    """fill/ine datasets: identity of the file (source table, url, frequency, series, fields, units, scale),
    adjustment statement of every field, history depth and last observation against the API."""
    for ds_id, e in FILL.items():
        d = load(ds_id)
        bad = []
        first_table = e["table"].split(",")[0].strip()
        if d["source"]["name"] != "INE" or d["source"]["dataset"] != e["table"]:
            bad.append(f"source.dataset {d['source']['dataset']!r} != {e['table']!r}")
        if d["source"]["url"] != _URL.format(first_table):
            bad.append(f"source.url {d['source']['url']!r}")
        if d["frequency"] != e["freq"]:
            bad.append(f"frequency {d['frequency']} != {e['freq']}")
        if [s["key"] for s in d["series"]] != e["series"]:
            bad.append(f"series {[s['key'] for s in d['series']]}")
        if [f["key"] for f in d["fields"]] != list(e["fields"]):
            bad.append(f"fields {[f['key'] for f in d['fields']]}")
        if not d.get("title_es") or not d.get("description_es"):
            bad.append("missing Spanish title/description")
        for f in d["fields"]:
            unit, scale = e["fields"].get(f["key"], (None, None))
            if f["unit"] != unit or f.get("scale", 0) != scale:
                bad.append(f"{f['key']}: unit/scale {f['unit']}/{f.get('scale', 0)} != {unit}/{scale}")
            n = (f.get("note_es") or "").lower()
            want = _PHRASE[e["adj"]]
            if want not in n or (e["adj"] == "NSA" and "corregidos" in n):
                bad.append(f"{f['key']}: note must state '{want}' (got {f.get('note_es')!r})")
            if e["adj"] == "NSA" and f["key"] in ("mom", "qoq"):
                bad.append(f"{f['key']}: period-on-period change of original data")
        # history from ~2016 and last observation equal to the API's latest period of the same series
        codes = {s[1]: s[3] for s in SPEC if s[0] == ds_id}
        for s in d["series"]:
            xs = [r[0] for r in s["data"]]
            if not xs or not ("2016-01-01" <= xs[0] <= "2016-04-01"):
                bad.append(f"{s['key']}: history starts {xs[:1]}, expected 2016")
            api = got[codes[s["key"]]][1]
            if api and max(api) != xs[-1]:
                bad.append(f"{s['key']}: last published {xs[-1]} != INE latest {max(api)}")
        rep.add(ds_id, "identity", "FAIL" if bad else "PASS",
                "fill/ine file identity: " + ("; ".join(bad) if bad else f"table {e['table']}, {e['freq']}, series {e['series']}, fields {list(e['fields'])}, {e['adj']} notes, history from 2016, last period = INE latest"))

    # EPA employed by sector: the four sectors add up to INE's national total EPA387796
    tot = got["EPA387796"][1]
    pub = {}
    for k in FILL["ine.employed_sectors"]["series"]:
        for x, v in series("ine.employed_sectors", k, "value").items():
            pub[x] = pub.get(x, 0) + v
    rep.compare("ine.employed_sectors", "transform", pub, tot, tol=0.25,
                label="sum of 4 sectors = EPA387796 total (thousand, rounding)", last_n=24)

    # EPA employed by sector: yoy recomputed from the API levels (INE publishes no rate for this table), 4 years of levels
    codes_by_key = {s[1]: s[3] for s in SPEC if s[0] == "ine.employed_sectors"}
    long_levels = fetch_all(list(codes_by_key.values()), nult=48)
    for k, c in codes_by_key.items():
        lv = long_levels[c][1]
        off = {x: (v / lv[add_months(x, -12)] - 1) * 100 for x, v in lv.items() if add_months(x, -12) in lv}
        rep.compare("ine.employed_sectors", "transform", series("ine.employed_sectors", k, "yoy"), off, tol=0.0002,
                    label=f"{k}.yoy = % change of {c} vs 12 months earlier (recomputed from the API)", last_n=40)


# Published labels that must describe the series actually fetched.
LABEL_RULES = [
    ("ine.ipss_sectors", "mayoristas", lambda lab: "mayorista" in lab.lower() or "por mayor" in lab.lower(),
     "must be wholesale trade (CNAE 46)"),
]


def labels(rep: Report):
    for ds, skey, ok, why in LABEL_RULES:
        lab = next(s["label_es"] for s in load(ds)["series"] if s["key"] == skey)
        rep.add(ds, "meta", "PASS" if ok(lab) else "FAIL", f"label of {skey} = '{lab}': {why}")


def derived(rep: Report, got: dict):
    """Fields the pipeline builds from several INE series, recomputed from the API."""
    # mortgages.avg_amount = importe (miles de euros) * 1000 / número
    imp, num = got["HPT34565"][1], got["HPT34618"][1]
    off = {k: imp[k] * 1000 / num[k] for k in imp if k in num and num[k]}
    rep.compare("ine.mortgages", "transform", series("ine.mortgages", "es", "avg_amount"), off, tol=0.01,
                label="avg_amount = HPT34565*1000/HPT34618", last_n=24)

    # gdp_productivity: GDP volume index per head / per working-age person / per employed / per hour, 2019Q1 = 100
    full = fetch_all(["CNTR6652", "CNTR7659", "CNTR7896", "EPA384355"] + WA_CODES, nult=60)
    gdp, emp, hrs, pop = (full[c][1] for c in ("CNTR6652", "CNTR7659", "CNTR7896", "EPA384355"))
    wa = {}
    for c in WA_CODES:
        for k, v in full[c][1].items():
            wa[k] = wa.get(k, 0) + v
    b = "2019-01-01"
    comps = {"pib": None, "pib_per_capita": pop, "pib_per_working_age": wa, "pib_per_employed": emp, "pib_per_hour": hrs}
    for key, den in comps.items():
        if den is None:
            off = {k: gdp[k] / gdp[b] * 100 for k in gdp}
        else:
            off = {k: (gdp[k] / den[k]) / (gdp[b] / den[b]) * 100 for k in gdp if k in den}
        rep.compare("ine.gdp_productivity", "transform", series("ine.gdp_productivity", key, "value"), off, tol=0.006,
                    label=f"{key} (recomputed from CNTR6652, CNTR7659, CNTR7896, EPA pop.)", last_n=24)
    rep.add("ine.gdp_productivity", "identity", "PASS", "components CNTR6652 (GDP SA), CNTR7659 (employed persons SA), CNTR7896 (hours SA), EPA384355 (population), EPA 16-64 groups")

    # CPI weights (per mille -> %) for the 13 ECOICOP v2 groups and for the 4 special groups
    pubw = {}
    for s in load("ine.cpi_weights")["series"]:
        pubw[s["label_es"]] = s["data"][-1][1]
    year = max(load("ine.cpi_weights")["series"][0]["data"])[0]
    bad = []
    for c in CPI_WEIGHTS:
        name, data = got[c]
        v = data.get(year)
        label = name.replace("Total Nacional. ", "").replace("Nacional. ", "").replace(". Ponderación.", "").strip()
        match = [k for k in pubw if abs(pubw[k] - (v or 0) / 10) < 1e-3]
        if v is None or not match:
            bad.append(f"{c} {label} {v}")
    rep.add("ine.cpi_weights", "values", "FAIL" if bad else "PASS",
            f"13 group weights {year} equal INE IPC33193x/10" if not bad else f"unmatched: {bad[:3]}")
    rep.add("ine.cpi_weights", "identity", "PASS" if not bad else "FAIL", "ECOICOP v2 group weights, Total Nacional")
    w = {"alimentos_bebidas_y_tabaco": ("IPC332382", "IPC233251"), "bienes_industriales_sin_productos_energeticos": ("IPC332383", "IPC233249"),
         "productos_energeticos": ("IPC332363", "IPC233270"), "servicios": ("IPC332372", "IPC233252")}
    bad = []
    for k, (cur, prev) in w.items():
        by_year = {int(x[:4]): v for x, v in got[prev][1].items()}
        by_year.update({int(x[:4]): v for x, v in got[cur][1].items()})  # current base wins where both exist
        pub = series("ine.cpi_ecoicop_groups", k, "weight")
        # M2: each month carries INE's weight of its own year (per mille / 10 = %)
        if any(int(x[:4]) not in by_year or abs(v - by_year[int(x[:4])] / 10) > 0.01 for x, v in pub.items()):
            bad.append(k)
    rep.add("ine.cpi_ecoicop_groups", "values", "FAIL" if bad else "PASS",
            "weights equal INE special-group weights /10 of each observation's own year" + (f" mismatch {bad}" if bad else ""))


if __name__ == "__main__":
    rep = Report()
    run(rep)
    rep.print()
    sys.exit(1 if rep.failed else 0)
