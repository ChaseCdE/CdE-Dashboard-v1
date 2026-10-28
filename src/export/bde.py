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


def _fields(key: str, meta: dict, decimals: int) -> list:
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
        fields.append(Field("mom_pp", "Variación mensual", "pp", decimals, column="change_abs"))
    elif kind == "credit_stock":
        fields += [
            Field("mom", "Variación mensual del saldo", "pct_change", 1, column="change_pct",
                  note_es="Variación del saldo: incluye reclasificaciones, fallidos y titulizaciones"),
            Field("yoy", "Variación interanual", "pct_change", 1, column="yoy_change_pct",
                  note_es="Tasa de crecimiento interanual basada en operaciones, publicada por el Banco de España"),
        ]
    elif kind == "ratio":
        fields.append(Field("qoq_pp", "Variación trimestral", "pp", 1, column="change_abs"))
    elif kind == "balance":
        fields.append(Field("sum_12m", "Acumulado 12 meses", "currency", 0, column="rolling_12m_sum", **money))
    elif kind == "npl":
        fields.append(Field("yoy_pp", "Variación interanual", "pp", decimals, column="yoy_change_abs"))
    elif kind in ("receipts", "persons", "debt_stock"):
        fields.append(Field("yoy", "Variación interanual", "pct_change", 1, column="yoy_change_pct"))
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
            source_dataset=cfg["series_code"],
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
