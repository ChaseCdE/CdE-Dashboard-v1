"""
Market datasets from official, freely reusable sources (site/data/ecb/, fed/, eia/).

Processed by src/scripts/process_markets_official.py (pipeline source "markets"). Field keys
are the same as in yahoo.py (close, ret_*, chg_*), so pages can mix them with Yahoo series.
"""

from .core import Dataset, Field, Series
from .yahoo import CHANGE_FIELDS, RETURN_FIELDS

ECB_URL = "https://data.ecb.europa.eu/data/datasets/EXR"
FRED_URL = "https://fred.stlouisfed.org/series/{}"
NOTES = {"1w": "5 sesiones", "1m": "21 sesiones", "1y": "1 año natural",
         "ytd": "Frente al último dato del año anterior"}


def _fields(level: Field) -> list:
    fields = [level]
    is_rate = level.unit == "pct"
    for fkey, label, col in (CHANGE_FIELDS if is_rate else RETURN_FIELDS):
        note = NOTES.get(fkey.split("_", 1)[1])
        fields.append(Field(fkey, label, "pp" if is_rate else "pct_change", 2 if is_rate else 1,
                            column=col, note_es=note))
    return fields


def _ds(source, key, title, desc, source_dataset, url, level, series_key, stale=None):
    return Dataset(
        source=source, indicator=key, csv=f"markets_official/{key}.csv", title_es=title,
        description_es=desc, source_dataset=source_dataset, source_url=url, frequency="D",
        fields=_fields(level), series=[Series(series_key, title)], optional=True,
        stale_after_days=stale,
    )


def _fx(key, title, note, code, decimals=4, desc=None):
    level = Field("close", "Tipo de referencia", "rate", decimals, column="Close", note_es=note)
    return _ds("ecb", key, title,
               desc or f"Tipo de cambio de referencia del euro publicado por el BCE ({note}), dato diario hacia las 16:00 CET.",
               code, ECB_URL, level, "global")


def _fred(source, key, code, title, desc, level, series_key, stale):
    return _ds(source, key, title, desc, f"FRED {code}", FRED_URL.format(code), level, series_key, stale)


def _yield(key, code, title, desc):
    level = Field("close", "Rendimiento", "pct", 2, column="Close", note_es="Porcentaje anual")
    return _fred("fed", key, code, title, desc + " Reserva Federal, estadística H.15, dato diario.", level, "us", 7)


def _spot(key, code, title, note, desc):
    level = Field("close", "Precio al contado", "rate", 2, column="Close", note_es=note)
    # EIA spot prices are published weekly with a lag of several days.
    return _fred("eia", key, code, title, desc + " Administración de Información Energética de EE. UU. (EIA), dato diario.",
                 level, "global", 14)


DATASETS = [
    _fx("eur_usd", "Euro / dólar", "USD por EUR", "EXR D.USD.EUR.SP00.A"),
    _fx("eur_gbp", "Euro / libra esterlina", "GBP por EUR", "EXR D.GBP.EUR.SP00.A"),
    _fx("eur_jpy", "Euro / yen", "JPY por EUR", "EXR D.JPY.EUR.SP00.A", decimals=2),
    _fx("eur_chf", "Euro / franco suizo", "CHF por EUR", "EXR D.CHF.EUR.SP00.A"),
    _fx("gbp_usd", "Libra esterlina / dólar", "USD por GBP", "EXR D.USD.EUR.SP00.A / D.GBP.EUR.SP00.A",
        desc="Tipo cruzado calculado a partir de los tipos de referencia del euro frente al dólar y la libra publicados por el BCE."),
    _fx("usd_jpy", "Dólar / yen", "JPY por USD", "EXR D.JPY.EUR.SP00.A / D.USD.EUR.SP00.A", decimals=2,
        desc="Tipo cruzado calculado a partir de los tipos de referencia del euro frente al yen y el dólar publicados por el BCE."),
    _fred("fed", "usd_broad_index", "DTWEXBGS", "Índice amplio del dólar (Reserva Federal)",
          "Valor nominal del dólar frente a una cesta amplia de divisas de sus socios comerciales, ponderada por comercio "
          "(enero 2006 = 100). Reserva Federal, estadística H.10, dato diario publicado semanalmente.",
          Field("close", "Índice", "index", 2, column="Close", note_es="Enero 2006 = 100"), "global", 14),
    _yield("us_tbill_3m", "DGS3MO", "Tesoro de EE. UU. a 3 meses", "Rendimiento a vencimiento constante a 3 meses."),
    _yield("us_treasury_5y", "DGS5", "Bono del Tesoro de EE. UU. a 5 años", "Rendimiento a vencimiento constante a 5 años."),
    _yield("us_treasury_10y", "DGS10", "Bono del Tesoro de EE. UU. a 10 años", "Rendimiento a vencimiento constante a 10 años."),
    _yield("us_treasury_30y", "DGS30", "Bono del Tesoro de EE. UU. a 30 años", "Rendimiento a vencimiento constante a 30 años."),
    _spot("brent_crude", "DCOILBRENTEU", "Petróleo Brent", "USD por barril", "Precio al contado del crudo Brent (Europa)."),
    _spot("wti_crude", "DCOILWTICO", "Petróleo WTI", "USD por barril", "Precio al contado del crudo West Texas Intermediate (Cushing, Oklahoma)."),
    _spot("natural_gas", "DHHNGSP", "Gas natural (Henry Hub)", "USD por millón de BTU", "Precio al contado del gas natural en Henry Hub (Luisiana)."),
]
