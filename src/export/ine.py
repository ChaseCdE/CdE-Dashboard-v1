"""
INE datasets for site/data/ine/. Owned by ws/ine.

Phase 1 samples: cpi (single series), ipi_sectors (long format).
"""

from .core import Dataset, Field, Series, long_series

INE_TABLE_URL = "https://www.ine.es/jaxiT3/Tabla.htm?t={}"

DATASETS = [
    Dataset(
        source="ine",
        indicator="cpi",
        csv="cpi.csv",
        title_es="Índice de Precios de Consumo (IPC)",
        description_es="IPC general nacional. Índice y tasa de variación anual.",
        source_dataset="79181",
        source_url=INE_TABLE_URL.format(79181),
        frequency="M",
        fields=[
            Field("value", "Índice", "index", 1, column="cpi_index", note_es="Base 2026 = 100"),
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change"),
        ],
        series=[Series("es", "España")],
    ),
    Dataset(
        source="ine",
        indicator="ipi_sectors",
        csv="ipi_sectors.csv",
        title_es="Producción industrial por destino económico",
        description_es="Índice de Producción Industrial corregido de efectos estacionales y de calendario, por destino económico de los bienes.",
        source_dataset="60280",
        source_url=INE_TABLE_URL.format(60280),
        frequency="M",
        fields=[
            Field("yoy", "Variación anual", "pct_change", 1, column="yoy_change"),
            Field("ytd", "Variación media en lo que va de año", "pct_change", 1, column="ytd_change"),
        ],
        series=long_series("sector", label_column="sector_label",
                           order=["total", "consumo", "equipo", "intermedios", "energia"]),
    ),
]
