"""
Banco de España datasets for site/data/bde/. Owned by ws/bde.

Phase 1 sample: yield_curve (cross-section, x = maturity in years).
"""

from .core import Dataset, Field, Series

BDE_RATES_URL = "https://www.bde.es/webbe/es/estadisticas/temas/tipos-interes.html"

DATASETS = [
    Dataset(
        source="bde",
        indicator="yield_curve",
        csv="bde/yield_curve.csv",
        title_es="Curva de rendimientos de la deuda pública española",
        description_es="Rentabilidad de Letras y Bonos del Tesoro en el mercado secundario, último dato disponible por plazo.",
        source_dataset="Tipos de interés de la deuda del Estado (mercado secundario)",
        source_url=BDE_RATES_URL,
        frequency="X",
        x_column="maturity_years",
        x_type="number",
        fields=[Field("yield", "Rentabilidad", "pct", 2)],
        series=[Series("es", "España", as_of_column="date")],
    ),
]
