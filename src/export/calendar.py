"""
Release calendar for the site (site/data/calendar.json): the "Calendario" page and the
"Próximas publicaciones" box of the Portada.

Input: data/raw/calendar/<source>.json, written by src/fetchers/calendars.py.
build_events() normalises every event (Spanish title and reference period, the period as a date
for monthly and quarterly data) and marks the statistics the site shows (`tracked`, with the page
that shows them). To show or hide a statistic, edit RULES: no JS changes are needed.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw" / "calendar"
PROCESSED = ROOT / "data" / "processed" / "calendar" / "events.json"
PAST_DAYS, FUTURE_DAYS = 31, 190

SOURCES = {
    "INE": "https://www.ine.es/daco/daco41/calen.htm",
    "Eurostat": "https://ec.europa.eu/eurostat/news/euro-indicators/release-calendar",
    "Banco de España": "https://www.bde.es/wbe/es/estadisticas/",
    "Ministerios de Trabajo e Inclusión": "https://www.mites.gob.es/es/estadisticas/calendario/index.htm",
}

# (source, regex on the source title, Spanish label, page, value shown for a past release)
# value: (dataset, series, field) read at the release's reference period, or None.
R = lambda src, rx, label, page, value=None: {"source": src, "rx": re.compile(rx), "label": label, "page": page, "value": value}
RULES = [
    # INE
    R("INE", r"^Índice de Precios de Consumo$", "Índice de Precios de Consumo (IPC)", "pages/precios.html", ("ine.cpi", "es", "yoy")),
    R("INE", r"^Índices de Precios de Consumo Armonizado$", "Índice de Precios de Consumo Armonizado (IPCA)", "pages/precios.html"),
    R("INE", r"^Contabilidad Nacional Trimestral de España", "PIB trimestral (Contabilidad Nacional)", "pages/actividad.html", ("ine.gdp", "es", "qoq")),
    R("INE", r"^Encuesta de Población Activa$", "Encuesta de Población Activa (EPA)", "pages/laboral.html", ("ine.unemployment", "es", "value")),
    R("INE", r"^Índice de Producción Industrial$", "Producción industrial (IPI)", "pages/sectores.html#industria", ("ine.industrial_production", "es", "yoy")),
    R("INE", r"^Índice de Cifras de Negocios en la Industria$", "Cifra de negocios de la industria", "pages/sectores.html#industria"),
    R("INE", r"^Índice de Producción del Sector Servicios$", "Producción del sector servicios", "pages/sectores.html#servicios", ("ine.services_production", "es", "yoy")),
    R("INE", r"^Indicadores de actividad del sector servicios$", "Cifra de negocios de los servicios (IASS)", "pages/sectores.html#servicios"),
    R("INE", r"^Índices de Comercio al por menor$", "Comercio minorista", "pages/actividad.html", ("ine.retail_sales", "es", "yoy")),
    R("INE", r"^Índice de Precios Industriales$", "Precios industriales (IPRI)", "pages/precios.html", ("ine.ipri", "total", "yoy")),
    R("INE", r"^Índices de Precios de Exportación", "Precios de exportación e importación", "pages/sector-exterior.html"),
    R("INE", r"^Índice de Producción de la Construcción$", "Producción de la construcción", "pages/sectores.html#construccion-vivienda", ("ine.construction_ipco", "total", "yoy")),
    R("INE", r"^Índice de Precios de Vivienda$", "Precio de la vivienda (IPV)", "pages/sectores.html#construccion-vivienda", ("ine.house_prices", "es", "yoy")),
    R("INE", r"^Hipotecas Mensual$", "Hipotecas sobre viviendas", "pages/sectores.html#construccion-vivienda"),
    R("INE", r"^Estadística de Transmisiones de Derechos de la Propiedad$", "Compraventa de viviendas", "pages/sectores.html#construccion-vivienda", ("ine.housing_transactions", "total", "yoy")),
    R("INE", r"^Sociedades Mercantiles Mensual$", "Sociedades mercantiles", "pages/empresas.html"),
    R("INE", r"^Indicadores de Confianza Empresarial$", "Confianza empresarial", "pages/empresas.html", ("ine.business_confidence", "ice", "value")),
    R("INE", r"^Movimientos Turísticos en Fronteras$", "Turistas internacionales (FRONTUR)", "pages/sectores.html#turismo", ("ine.tourist_arrivals", "es", "yoy")),
    R("INE", r"^Encuesta de Gasto Turístico Mensual$", "Gasto de los turistas internacionales (EGATUR)", "pages/sectores.html#turismo"),
    R("INE", r"^Coyuntura Turística Hotelera", "Pernoctaciones y precios hoteleros", "pages/sectores.html#turismo"),
    R("INE", r"^Encuesta Trimestral de Coste Laboral$", "Coste laboral (ETCL)", "pages/laboral.html"),
    R("INE", r"^Cuentas Trimestrales no Financieras de los Sectores Institucionales$", "Cuentas de los sectores institucionales (ahorro de los hogares)", "pages/actividad.html"),
    R("INE", r"^Estadística Continua de Población", "Población residente", "pages/laboral.html"),
    # Banco de España
    R("Banco de España", r"^Euribor", "Euríbor y otros tipos de referencia (mensual)", "pages/credito.html"),
    R("Banco de España", r"^Tipos de interés aplicados por las Instituciones Financieras", "Tipos de interés de préstamos y depósitos", "pages/credito.html"),
    R("Banco de España", r"^Indicadores de liquidez y financiación", "Financiación de hogares y empresas", "pages/credito.html"),
    R("Banco de España", r"^Cuentas Financieras de la Economía Española", "Cuentas financieras: endeudamiento", "pages/credito.html"),
    R("Banco de España", r"\(PDE\) \(Avance mensual\)", "Deuda de las Administraciones Públicas (avance mensual)", "pages/sector-publico.html"),
    R("Banco de España", r"^Balanza de Pagos \(Datos mensuales\)", "Balanza de pagos", "pages/sector-exterior.html", ("bde.current_account_balance", "es", "value")),
    # Trabajo e Inclusión
    R("Ministerios de Trabajo e Inclusión", r"^Afiliación", "Afiliación a la Seguridad Social", "pages/laboral.html", ("bde.social_security_affiliates", "es", "value")),
    R("Ministerios de Trabajo e Inclusión", r"^Paro registrado", "Paro registrado", "pages/laboral.html", ("bde.registered_unemployment", "es", "value")),
    # Eurostat (euro indicators)
    R("Eurostat", r"^Flash estimate inflation euro area", "Inflación de la zona del euro (avance)", "pages/ue.html"),
    R("Eurostat", r"^Inflation \(HICP\)", "Inflación armonizada en la UE (IPCA)", "pages/ue.html", ("eurostat.hicp", "es", "yoy")),
    R("Eurostat", r"^Unemployment", "Paro en la UE", "pages/ue.html", ("eurostat.unemployment", "es", "value")),
    R("Eurostat", r"^(Preliminary flash|Flash) estimate GDP", "PIB de la UE y de la zona del euro (avance)", "pages/ue.html"),
    R("Eurostat", r"^GDP main aggregates and employment", "PIB y empleo en la UE", "pages/ue.html", ("eurostat.gdp_growth", "es", "qoq")),
    R("Eurostat", r"^Quarterly government (debt|deficit)", "Deuda y déficit públicos trimestrales (UE)", "pages/sector-publico.html"),
    R("Eurostat", r"^General government deficit and debt", "Deuda y déficit públicos anuales (UE)", "pages/sector-publico.html"),
    R("Eurostat", r"^Economic Sentiment Indicator", "Sentimiento económico (Comisión Europea)", "pages/ue.html", ("eurostat.economic_sentiment", "es", "value")),
    R("Eurostat", r"^Industrial production", "Producción industrial en la UE", "pages/ue.html"),
    R("Eurostat", r"^Retail trade", "Comercio minorista en la UE", "pages/ue.html"),
    R("Eurostat", r"^International trade in goods", "Comercio exterior de bienes (UE)", "pages/sector-exterior.html"),
    R("Eurostat", r"^Production in construction", "Producción de la construcción en la UE", "pages/ue.html"),
    R("Eurostat", r"^House price index", "Precios de la vivienda en la UE", "pages/sectores.html#construccion-vivienda"),
    R("Eurostat", r"^Job vacancy", "Vacantes en la UE", "pages/laboral.html"),
    R("Eurostat", r"^Labour cost index", "Coste laboral en la UE", "pages/laboral.html"),
]
# Spanish titles of the Eurostat releases not tracked by the site.
EUROSTAT_ES = {
    "Building permits": "Permisos de construcción (UE)", "Services production": "Producción de servicios (UE)",
    "Industrial producer prices, domestic market": "Precios industriales, mercado interior (UE)",
    "Industrial import prices": "Precios de importación de productos industriales (UE)",
    "Interest rates (3 months)": "Tipos de interés a tres meses (UE)", "Long term gvt bond yield": "Rentabilidad de la deuda pública a largo plazo (UE)",
    "Long-term government bond yield": "Rentabilidad de la deuda pública a largo plazo (UE)",
    "Long term government bond yield": "Rentabilidad de la deuda pública a largo plazo (UE)",
    "Balance of payments": "Balanza de pagos (UE)", "Services producer prices": "Precios de producción de los servicios (UE)",
    "First release sector accounts (households and businesses)": "Cuentas de los sectores: hogares y empresas (UE, primera estimación)",
    "Second release sector accounts (households)": "Cuentas de los sectores: hogares (UE, segunda estimación)",
}

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
          "noviembre", "diciembre"]
MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
             "november", "december"]
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}


def normalise_period(period: str | None, release: date) -> tuple[str | None, str | None]:
    """(Spanish label, ISO date of the period start for monthly/quarterly data)."""
    if not period:
        return None, None
    p = period.strip()
    low = p.lower()
    m = re.match(r"^([a-záéíóú]+)\.?\s+(\d{4})$", low)                      # Octubre 2026 / October 2026
    if m:
        name = m.group(1)
        idx = MONTHS.index(name) if name in MONTHS else (MONTHS_EN.index(name) if name in MONTHS_EN else None)
        if idx is not None:
            return f"{MONTHS[idx]} {m.group(2)}", f"{m.group(2)}-{idx + 1:02d}-01"
    m = re.match(r"^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)/(\d{2})$", low)   # Nov/25 (BdE)
    if m:
        idx = [x[:3] for x in MONTHS].index(m.group(1))
        year = 2000 + int(m.group(2))
        return f"{MONTHS[idx]} {year}", f"{year}-{idx + 1:02d}-01"
    if re.match(r"^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)$", low):           # dic (MITES)
        idx = [x[:3] for x in MONTHS].index(low)
        year = release.year - (1 if idx + 1 > release.month else 0)
        return f"{MONTHS[idx]} {year}", f"{year}-{idx + 1:02d}-01"
    m = (re.match(r"^trimestre\s+([1-4])/(\d{4})$", low) or re.match(r"^q([1-4])[\s/](\d{4})$", low)
         or re.match(r"^(\d{4})[-\s]?q([1-4])$", low))
    if m:
        q, y = (m.group(1), m.group(2)) if len(m.group(1)) == 1 else (m.group(2), m.group(1))
        return f"T{q} {y}", f"{y}-{(int(q) - 1) * 3 + 1:02d}-01"
    m = re.match(r"^(I{1,3}|IV)-(\d{4})$", p)                                             # III-2025 (BdE)
    if m:
        q = ROMAN[m.group(1)]
        return f"T{q} {m.group(2)}", f"{m.group(2)}-{(q - 1) * 3 + 1:02d}-01"
    p = p.replace("2nd notification", "segunda notificación").replace("1st notification", "primera notificación")
    if re.match(r"^(año\s+)?\d{4}$", low):
        return p.replace("Año", "año"), None
    return p, None


def classify(ev: dict) -> dict:
    for r in RULES:
        if r["source"] == ev["source"] and r["rx"].search(ev["title"]):
            return r
    return {}


def build_events(raw_dir: Path = RAW_DIR) -> list:
    out = []
    for f in sorted(raw_dir.glob("*.json")):
        for ev in json.loads(f.read_text(encoding="utf-8")).get("events", []):
            d = date.fromisoformat(ev["date"])
            rule = classify(ev)
            period_es, period_iso = normalise_period(ev.get("period"), d)
            title = rule.get("label") or (EUROSTAT_ES.get(ev["title"], ev["title"]) if ev["source"] == "Eurostat" else ev["title"])
            row = {
                "date": ev["date"], "time": ev.get("time"), "source": ev["source"], "title_es": title,
                "period_es": period_es, "period_iso": period_iso, "flash": bool(ev.get("flash")),
                "tracked": bool(rule),
            }
            if rule:
                row["page"] = rule["page"]
                if rule.get("value"):
                    row["value"] = dict(zip(("dataset", "series", "field"), rule["value"]))
            out.append(row)
    seen, uniq = set(), []
    for e in sorted(out, key=lambda e: (e["date"], e["time"] or "99", not e["tracked"], e["title_es"])):
        k = (e["date"], e["source"], e["title_es"], e["period_es"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    return uniq


def for_site(events: list, today: date, generated_at: str) -> dict:
    lo, hi = (today - timedelta(days=PAST_DAYS)).isoformat(), (today + timedelta(days=FUTURE_DAYS)).isoformat()
    sel = [e for e in events if lo <= e["date"] <= hi]
    return {
        "generated_at": generated_at,
        "sources": [{"name": k, "url": v} for k, v in SOURCES.items()],
        "coverage": {s: max((e["date"] for e in events if e["source"] == s), default=None) for s in SOURCES},
        "events": sel,
    }
