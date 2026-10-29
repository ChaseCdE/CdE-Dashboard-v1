"""All datasets exported to site/data/. Each source module owns its own list."""

from . import bde, eurostat, housing, ine, markets_official, yahoo

DATASETS = [*ine.DATASETS, *eurostat.DATASETS, *bde.DATASETS, *yahoo.DATASETS, *housing.DATASETS, *markets_official.DATASETS]
