"""
Eurostat datasets for site/data/eurostat/. Owned by ws/eurostat.

Phase 1 sample: hicp (wide format, Spain vs EU27).
"""

from .core import Dataset, Field, Series

EUROSTAT_URL = "https://ec.europa.eu/eurostat/databrowser/view/{}/default/table"

DATASETS = [
    Dataset(
        source="eurostat",
        indicator="hicp",
        csv="eurostat/hicp_comparison.csv",
        title_es="Inflación armonizada (IPCA)",
        description_es="Tasa de variación anual del Índice de Precios de Consumo Armonizado. España frente a UE-27.",
        source_dataset="prc_hicp_manr",
        source_url=EUROSTAT_URL.format("prc_hicp_manr"),
        frequency="M",
        fields=[Field("yoy", "Variación anual", "pct_change", 1)],
        series=[
            Series("es", "España", columns={"yoy": "hicp_inflation_es"}),
            Series("eu27", "UE-27", columns={"yoy": "hicp_inflation_eu27"}),
        ],
    ),
]
