"""
Housing price datasets that INE does not provide (site/data/mivau/, site/data/registradores/).

Both are processed by src/scripts/process_housing_data.py (pipeline source "housing").
- mivau.appraised_house_prices: MIVAU "Valor tasado de la vivienda libre", EUR/m2, quarterly,
  downloaded from the Banco de España API (BE si_1_5 republishes it). Full history (1995).
No quarterly rate is exported: both series are original (not seasonally adjusted) data and
the seasonal-adjustment policy (docs/audit/seasonal-adjustment.md) keeps period-on-period
changes for adjusted series only.
- registradores.house_prices: Colegio de Registradores open data, average price per m2 of
  registered residential sales, quarterly.
"""

from .adjustment import NSA
from .core import Dataset, Field, Series

MIVAU_URL = "https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=35000000"
REGISTRADORES_URL = ("https://opendata.registradores.org/dataset/dataset/"
                     "compraventas-de-inmuebles-uso-residencial-por-provincia")

DATASETS = [
    Dataset(
        source="mivau",
        indicator="appraised_house_prices",
        csv="housing/mivau_appraised_prices.csv",
        title_es="Valor tasado de la vivienda libre (MIVAU)",
        description_es=("Valor medio por metro cuadrado de la vivienda libre según las tasaciones hipotecarias, "
                        "Ministerio de Vivienda y Agenda Urbana. Total y por antigüedad (hasta 5 años y más de 5 años). "
                        "Descargado del Banco de España (indicadores del mercado de la vivienda)."),
        source_dataset="Valor tasado de la vivienda (BdE DHIVTNOAPLPMMUVT_RLI.T)",
        source_url=MIVAU_URL,
        frequency="Q",
        optional=True,
        fields=[
            Field("value", "Por metro cuadrado", "currency", 0, currency="EUR", note_es=NSA),
            Field("yoy", "Variación anual", "pct_change", 1, note_es=NSA),
        ],
        series=[
            Series("total", "Total", where={"series": "total"}),
            Series("new", "Hasta 5 años de antigüedad", where={"series": "new"}),
            Series("used", "Más de 5 años de antigüedad", where={"series": "used"}),
        ],
    ),
    Dataset(
        source="registradores",
        indicator="house_prices",
        csv="housing/registradores_house_prices.csv",
        title_es="Precio de la vivienda según los Registradores",
        description_es=("Precio medio por metro cuadrado de las compraventas de vivienda inscritas en los registros de la "
                        "propiedad, total nacional (datos abiertos del Colegio de Registradores). Las tasas coinciden con "
                        "las de la Estadística Registral Inmobiliaria; el nivel puede diferir del publicado en su nota trimestral."),
        source_dataset="Compraventas de inmuebles, uso residencial, por provincia",
        source_url=REGISTRADORES_URL,
        frequency="Q",
        optional=True,
        fields=[
            Field("value", "Por metro cuadrado", "currency", 0, currency="EUR", note_es=NSA),
            Field("yoy", "Variación anual", "pct_change", 1, note_es=NSA),
            Field("price_dwelling", "Precio medio por vivienda (euros)", "currency", 0, currency="EUR", note_es=NSA),
        ],
        series=[Series("es", "Registradores", where={"series": "es"})],
    ),
]
