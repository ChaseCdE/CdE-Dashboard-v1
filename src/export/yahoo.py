"""
Yahoo Finance datasets for site/data/yahoo/. Owned by ws/yahoo.

Phase 1 sample: ibex_35 (daily).
KNOWN ISSUE (see docs/migration-notes.md): European tickers are dated one
day early until yahoo_client.py stops converting to UTC before taking the date.
"""

from .core import Dataset, Field, Series

YAHOO_URL = "https://finance.yahoo.com/quote/{}/"

DATASETS = [
    Dataset(
        source="yahoo",
        indicator="ibex_35",
        csv="yahoo/ibex_35_processed.csv",
        title_es="IBEX 35",
        description_es="Índice de referencia de la Bolsa de Madrid. Cierre diario.",
        source_dataset="^IBEX",
        source_url=YAHOO_URL.format("%5EIBEX"),
        frequency="D",
        fields=[Field("close", "Cierre", "index", 1, column="Close", note_es="Puntos")],
        series=[Series("es", "IBEX 35")],
    ),
]
