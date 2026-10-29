"""
Yahoo Finance datasets for site/data/yahoo/. Owned by ws/yahoo.

One dataset per data/processed/yahoo/<key>_processed.csv, id `yahoo.<key>`.
Daily data on the exchange's local trading date (see yahoo_client.py).

Fields exported (only what markets/overview display):
  close       closing level/price
  ret_1d      daily change (%)
  ret_1w/1m/1y  change over 5 / 21 trading sessions and 1 calendar year (%)
  ret_ytd     change vs last close of the previous calendar year (%)
  sma_200     200-session simple moving average (equity indices only; drawn on
              the single-index chart of the Markets page)
Not exported: OHLC, volume, 20/50-day SMAs, 3-month return, volatility (no page
displays them), correlation matrix / comparison / summary CSVs.
"""

from urllib.parse import quote

from .core import Dataset, Field, Series

RETURN_FIELDS = [
    ("ret_1d", "Variación diaria", "daily_return_pct"),
    ("ret_1w", "Variación 1 semana", "return_1w_pct"),
    ("ret_1m", "Variación 1 mes", "return_1m_pct"),
    ("ret_1y", "Variación 1 año", "return_1y_pct"),
    ("ret_ytd", "Variación en el año", "ytd_return_pct"),
]


def _url(ticker: str) -> str:
    return f"https://finance.yahoo.com/quote/{quote(ticker, safe='')}/"


# Yields: changes are differences in percentage points, not relative returns.
CHANGE_FIELDS = [
    ("chg_1d", "Variación diaria", "daily_change_abs"),
    ("chg_1w", "Variación 1 semana", "change_1w_abs"),
    ("chg_1m", "Variación 1 mes", "change_1m_abs"),
    ("chg_1y", "Variación 1 año", "change_1y_abs"),
    ("chg_ytd", "Variación en el año", "ytd_change_abs"),
]


def _make(key, ticker, title, desc, close_field, series_key, series_label, sma=False):
    fields = [close_field]
    if close_field.unit == "pct":
        for fkey, label, col in CHANGE_FIELDS:
            note = {
                "chg_1w": "5 sesiones",
                "chg_1m": "21 sesiones",
                "chg_1y": "1 año natural",
                "chg_ytd": "Frente al último cierre del año anterior",
            }.get(fkey)
            fields.append(Field(fkey, label, "pp", 2, column=col, note_es=note))
        return Dataset(
            source="yahoo", indicator=key, csv=f"yahoo/{key}_processed.csv", title_es=title,
            description_es=desc, source_dataset=ticker, source_url=_url(ticker), frequency="D",
            fields=fields, series=[Series(series_key, series_label)],
        )
    for fkey, label, col in RETURN_FIELDS:
        note = {
            "ret_1w": "5 sesiones",
            "ret_1m": "21 sesiones",
            "ret_1y": "1 año natural",
            "ret_ytd": "Frente al último cierre del año anterior",
        }.get(fkey)
        fields.append(Field(fkey, label, "pct_change", 1, column=col, note_es=note))
    if sma:
        fields.append(Field("sma_200", "Media móvil 200 sesiones", "index", 1, column="sma_200", note_es="Puntos"))
    return Dataset(
        source="yahoo",
        indicator=key,
        csv=f"yahoo/{key}_processed.csv",
        title_es=title,
        description_es=desc,
        source_dataset=ticker,
        source_url=_url(ticker),
        frequency="D",
        fields=fields,
        series=[Series(series_key, series_label)],
    )


def _index(key, ticker, title, series_key, desc):
    f = Field("close", "Cierre", "index", 1, column="Close", note_es="Puntos")
    return _make(key, ticker, title, f"{desc} Cierre diario.", f, series_key, title, sma=True)


def _rate(key, ticker, title, note, series_key="global", desc=None, decimals=4):
    f = Field("close", "Cierre", "rate", decimals, column="Close", note_es=note)
    return _make(key, ticker, title, desc or f"Tipo de cambio {note.lower()}. Cierre diario.", f, series_key, title)


def _commodity(key, ticker, title, note, desc):
    f = Field("close", "Cierre", "rate", 2, column="Close", note_es=note)
    return _make(key, ticker, title, f"{desc} Cierre diario del contrato de futuros de referencia.", f, "global", title)


def _yield(key, ticker, title, desc):
    f = Field("close", "Rendimiento", "pct", 2, column="Close", note_es="Porcentaje anual")
    return _make(key, ticker, title, f"{desc} Cierre diario.", f, "us", title)


def _etf(key, ticker, title, currency, series_key, desc):
    f = Field("close", "Cierre", "currency", 2, column="Close", currency=currency, note_es="Precio de la participación")
    return _make(key, ticker, title, f"{desc} Cierre diario.", f, series_key, title)


DATASETS = [
    # Equity indices
    _index("ibex_35", "^IBEX", "IBEX 35", "es", "Índice de referencia de la Bolsa de Madrid."),
    _index("euro_stoxx_50", "^STOXX50E", "Euro Stoxx 50", "ez", "Cincuenta mayores empresas de la zona euro."),
    _index("stoxx_600", "^STOXX", "STOXX Europe 600", "eu", "Seiscientas empresas europeas de 17 países."),
    _index("sp_500", "^GSPC", "S&P 500", "us", "Quinientas mayores empresas cotizadas de EE. UU."),
    _index("nasdaq_composite", "^IXIC", "NASDAQ Composite", "us", "Todas las acciones cotizadas en NASDAQ."),
    _index("dax", "^GDAXI", "DAX 40", "de", "Cuarenta grandes empresas alemanas."),
    _index("cac_40", "^FCHI", "CAC 40", "fr", "Cuarenta mayores empresas de Euronext París."),
    _index("ftse_100", "^FTSE", "FTSE 100", "uk", "Cien mayores empresas de la Bolsa de Londres."),
    _index("vix", "^VIX", "VIX (volatilidad implícita del S&P 500)", "us", "Volatilidad esperada a 30 días del S&P 500."),
    # Commodities
    _commodity("gold", "GC=F", "Oro", "USD por onza troy", "Precio del oro (COMEX)."),
    _commodity("silver", "SI=F", "Plata", "USD por onza troy", "Precio de la plata (COMEX)."),
    # ETFs
    _etf("msci_spain_etf", "EWP", "ETF iShares MSCI España", "USD", "es", "Renta variable española (alto peso financiero), cotizada en dólares."),
    _etf("european_banks_etf", "EUFN", "ETF iShares MSCI Europa Financiero", "USD", "eu", "Sector financiero europeo, cotizado en dólares."),
]
