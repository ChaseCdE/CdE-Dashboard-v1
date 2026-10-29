"""
Observatorio de Márgenes Empresariales (AEAT) datasets (site/data/aeat/).

Processed by src/scripts/process_aeat_data.py (pipeline source "aeat"). Quarterly series built by
the Agencia Tributaria from the VAT (modelos 303/322) and withholding (modelo 111) returns of
private non-financial companies, population "homogénea corriente", all company sizes. CVEC data
(seasonally and calendar adjusted by the AEAT).
- aeat.ome_totals: sales, purchases, wage bill and gross operating result indicator (total
  economy): level (millions of euros), year-on-year rate and index 2019 = 100.
- aeat.ome_divisions: sales by CNAE-2009 division, level and year-on-year rate.
"""

from .adjustment import SCA, note
from .core import Dataset, Field, Series, long_series

OME_URL = ("https://sede.agenciatributaria.gob.es/Sede/estadisticas/observatorio-margenes-empresariales/"
           "observatorio-margenes-empresariales.html")
OME_DATASET = "Observatorio de Márgenes Empresariales, 2.1 Datos trimestrales (población homogénea corriente)"
EUR_M = "Millones de euros"

DATASETS = [
    Dataset(
        source="aeat",
        indicator="ome_totals",
        csv="aeat/ome_totals.csv",
        title_es="Ventas, compras y masa salarial de las sociedades no financieras",
        description_es=(
            "Observatorio de Márgenes Empresariales (Agencia Tributaria): ventas totales, compras totales y masa "
            "salarial declaradas en los modelos periódicos de IVA y retenciones por las sociedades no financieras, "
            "y el indicador de resultado bruto de explotación (ventas menos compras menos masa salarial). Las compras "
            "incluyen bienes corrientes y de inversión; la masa salarial son las retribuciones del trabajo sujetas a "
            "retención, sin cotizaciones sociales a cargo de la empresa. Población homogénea corriente, todas las "
            "empresas. Datos corregidos de efectos estacionales y de calendario (CVEC) de la AEAT."),
        source_dataset=OME_DATASET,
        source_url=OME_URL,
        frequency="Q",
        optional=True,
        fields=[
            Field("value", "Nivel", "currency", 0, currency="EUR", scale=6, note_es=note(SCA, EUR_M)),
            Field("yoy", "Variación anual", "pct_change", 1, note_es=SCA),
            Field("index_2019", "Índice (2019 = 100)", "index", 1, note_es=note(SCA, "Media de 2019 = 100")),
        ],
        series=[
            Series("sales", "Ventas totales", where={"series": "sales"}),
            Series("purchases", "Compras totales (aprovisionamientos)", where={"series": "purchases"}),
            Series("wages", "Masa salarial (costes de personal)", where={"series": "wages"}),
            Series("gross_result", "Resultado bruto de explotación (indicador)", where={"series": "gross_result"}),
        ],
    ),
    Dataset(
        source="aeat",
        indicator="ome_divisions",
        csv="aeat/ome_divisions.csv",
        title_es="Ventas de las sociedades no financieras por divisiones de actividad",
        description_es=(
            "Observatorio de Márgenes Empresariales (Agencia Tributaria): ventas totales declaradas en los modelos "
            "periódicos de IVA por las sociedades no financieras de cada división de la CNAE-2009, datos corregidos "
            "de efectos estacionales y de calendario (CVEC). El comercio (divisiones 45, 46 y 47) se publica por "
            "grupos de tres dígitos y aquí se agrega sumando sus grupos, como hace la AEAT con sus totales."),
        source_dataset=OME_DATASET,
        source_url=OME_URL,
        frequency="Q",
        optional=True,
        fields=[
            Field("value", "Ventas", "currency", 0, currency="EUR", scale=6, note_es=note(SCA, EUR_M)),
            Field("yoy", "Variación anual de las ventas", "pct_change", 1, note_es=SCA),
        ],
        series=long_series("sector", label_column="sector_label"),
    ),
]
