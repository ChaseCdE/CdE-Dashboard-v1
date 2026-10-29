"""
Banco de España datasets for site/data/bde/. Owned by ws/bde.

One dataset per processed series in data/processed/bde/<key>_processed.csv,
with id `bde.<key>` (key = CSV stem without `_processed`), plus the yield
curve cross-section. Titles, labels, URLs and money units live in
BDE_EXPORT_META (src/fetchers/bde_indicators.py); this module only maps each
kind of series to its contract fields.

The wide `*_comparison.csv` files and `bde_summary.csv` are not exported: the
frontend combines datasets itself and the manifest replaces the summary.
"""

from .adjustment import NSA, note
from .core import Dataset, Field, Series
from ..fetchers.bde_indicators import BDE_INDICATORS, BDE_EXPORT_META, BDE_DERIVED, BDE_DERIVED_META

BDE_RATES_URL = "https://www.bde.es/webbe/es/estadisticas/temas/tipos-interes.html"

# Series key: ISO-like geography. Euro-area money-market rates use "ea".
_SERIES_KEY = {
    "germany_10y_bond": "de",
    "france_10y_bond": "fr",
    "italy_10y_bond": "it",
}
_EURO_AREA = {k for k in BDE_INDICATORS if k.startswith("euribor") or k == "ester_daily"}


def _value_label(key: str, kind: str) -> str:
    if "bond" in key or "tbill" in key:
        return "Rentabilidad"
    if kind == "credit_stock":
        return "Saldo"
    if kind == "ratio":
        return "Ratio sobre PIB"
    if kind == "npl":
        return "Ratio de dudosos"
    if kind == "persons":
        return "Personas"
    if kind == "debt_stock":
        return "Saldo de deuda"
    if kind in ("balance", "receipts"):
        return "Importe mensual"
    return "Tipo de interés"


# The yoy of the credit stocks is BdE's transaction-based growth rate (audit M3). It does not
# measure exactly the same aggregate as the stock shown as the level, so the note says which.
_CREDIT_GROWTH_NOTE = {
    "credit_households_total": "Tasa interanual de la financiación total a hogares e ISFLSH (préstamos y valores), "
                               "basada en operaciones (Banco de España, Boletín Estadístico 3.21). Agregado más amplio "
                               "que el saldo de préstamos mostrado como nivel",
    "credit_nfc_total": "Tasa interanual de los préstamos de entidades de crédito a sociedades no financieras, basada "
                        "en operaciones (Banco de España, Boletín Estadístico 3.20). No coincide exactamente con el "
                        "saldo mostrado como nivel",
}
_CREDIT_GROWTH_CODE = {
    "credit_households_total": "credit_households_growth",
    "credit_nfc_total": "credit_nfc_growth",
}


# Seasonal adjustment (docs/audit/seasonal-adjustment.md). The Banco de España publishes none of
# these series seasonally adjusted (the SDMX keys carry adjustment "N"; e.g. "Ajuste: Sin ajuste de
# estacionalidad"), so every statistical series is original data and period-on-period changes are
# not published: the monthly change of the credit stocks is dropped, and the bank interest rates
# and debt ratios show the change on a year earlier instead of the previous month / quarter.
# Market prices (Euribor, €STR, government bond yields) have no adjustment concept: no note.
_MARKET_KINDS = {"rate_daily", "rate_daily_chg", "rate_monthly"}
# Being changed in parallel by the lead: their fields are left exactly as they were.
_NOT_IN_SCOPE = {"social_security_affiliates", "registered_unemployment"}


def _fields(key: str, meta: dict, decimals: int) -> list:
    fields = _base_fields(key, meta, decimals)
    if meta["kind"] in _MARKET_KINDS or key in _NOT_IN_SCOPE:
        return fields
    for f in fields:
        f.note_es = note(NSA, f.note_es)
    return fields


def _base_fields(key: str, meta: dict, decimals: int) -> list:
    kind = meta["kind"]
    money = {"currency": meta.get("currency"), "scale": meta.get("scale", 0)}
    value_unit = ("currency" if kind in ("credit_stock", "balance", "receipts", "debt_stock")
                  else "persons" if kind == "persons" else "pct")
    value_decimals = {"credit_stock": 1 if meta.get("scale") == 9 else 0, "balance": 0, "receipts": 0,
                      "debt_stock": 0, "persons": 0, "ratio": 1}.get(kind, decimals)
    fields = [Field("value", _value_label(key, kind), value_unit, value_decimals,
                    **(money if value_unit == "currency" else {}))]

    if kind == "rate_daily_chg":
        fields += [
            Field("chg_1m", "Variación en 30 días", "pp", decimals, column="change_30d_abs"),
            Field("chg_ytd", "Variación en el año", "pp", decimals, column="change_ytd_abs"),
            Field("chg_1y", "Variación en 1 año", "pp", decimals, column="yoy_change_abs"),
        ]
    elif kind == "rate_monthly_chg":
        fields.append(Field("yoy_pp", "Variación interanual", "pp", decimals, column="yoy_change_abs"))
    elif kind == "credit_stock":
        fields.append(Field("yoy", "Variación interanual", "pct_change", 1, column="yoy_change_pct",
                            note_es=_CREDIT_GROWTH_NOTE[key]))
    elif kind == "ratio":
        fields.append(Field("yoy_pp", "Variación interanual", "pp", 1, column="yoy_change_abs"))
    elif kind == "balance":
        fields.append(Field("sum_12m", "Acumulado 12 meses", "currency", 0, column="rolling_12m_sum", **money))
    elif kind == "npl":
        fields.append(Field("yoy_pp", "Variación interanual", "pp", decimals, column="yoy_change_abs"))
    elif kind in ("receipts", "persons", "debt_stock"):
        fields.append(Field("yoy", "Variación interanual", "pct_change", 1, column="yoy_change_pct"))
        if kind == "persons":
            # Monthly change of an unadjusted end-of-month count: it includes seasonal swings
            # (no seasonally adjusted series is available from the BdE API).
            nsa = "Datos originales a fin de mes, sin corregir de estacionalidad: incluye efectos estacionales"
            fields += [
                Field("mom", "Variación mensual", "pct_change", 2, column="change_pct", note_es=nsa),
                Field("mom_diff", "Variación mensual (miles de personas)", "persons", 1,
                      column="change_abs_k", scale=3, note_es=nsa),
            ]
    return fields


def _build() -> list:
    out = []
    for key, meta in BDE_EXPORT_META.items():
        cfg = BDE_INDICATORS[key]
        freq = cfg["frequency"]
        # BdE publishes 3 decimals for Euribor/€STR and 2 for the rest
        decimals = 3 if key in _EURO_AREA else 2
        series_key = "ea" if key in _EURO_AREA else _SERIES_KEY.get(key, "es")
        out.append(Dataset(
            source="bde",
            indicator=key,
            csv=f"bde/{key}_processed.csv",
            title_es=meta["title_es"],
            description_es=meta.get("description_es"),
            source_dataset=(cfg["series_code"] if key not in _CREDIT_GROWTH_CODE else
                            f'{cfg["series_code"]} (saldo); {BDE_INDICATORS[_CREDIT_GROWTH_CODE[key]]["series_code"]} (tasa interanual)'),
            source_url=meta["url"],
            frequency=freq,
            fields=_fields(key, meta, decimals),
            series=[Series(series_key, meta["label_es"])],
        ))
    return out


def _build_spreads() -> list:
    out = []
    for key, cfg in BDE_DERIVED.items():
        meta = BDE_DERIVED_META[key]
        out.append(Dataset(
            source="bde",
            indicator=key,
            csv=f"bde/{key}_processed.csv",
            title_es=meta["title_es"],
            description_es=meta["description_es"],
            source_dataset=cfg["series_code"],
            source_url=meta["url"],
            frequency=cfg["frequency"],
            fields=[
                Field("value", meta["value_label"], "pp", 2, note_es=meta["note_es"]),
                Field("chg_1m", "Variación mensual", "pp", 2, column="change_abs"),
                Field("chg_1y", "Variación en 1 año", "pp", 2, column="yoy_change_abs"),
            ],
            series=[Series("es", meta["label_es"])],
        ))
    return out


DATASETS = _build() + _build_spreads() + [
    Dataset(
        source="bde",
        indicator="yield_curve",
        csv="bde/yield_curve.csv",
        title_es="Curva de rendimientos de la deuda pública española",
        description_es="Rentabilidad de Letras y Bonos del Tesoro en el mercado secundario, última fecha con dato en todos los plazos. El punto de 3 meses recoge Letras a 1-3 meses. No hay un punto a 2 años: la serie del Banco de España «a más de 2 años» es un promedio de todos los plazos largos.",
        source_dataset="D_DTES00B7, D_DTES00S7, D_DTES00U7, D_G0B1F0ZN, D_G0B1F0ZO, D_G0B1F0ZP, D_G0B1F0ZQ",
        source_url=BDE_RATES_URL,
        frequency="X",
        x_column="maturity_years",
        x_type="number",
        fields=[Field("yield", "Rentabilidad", "pct", 2)],
        series=[Series("es", "España", as_of_column="date")],
    ),
]
