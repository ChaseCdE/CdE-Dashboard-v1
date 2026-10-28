"""All datasets exported to site/data/. Each source module owns its own list."""

from . import bde, eurostat, ine, yahoo

DATASETS = [*ine.DATASETS, *eurostat.DATASETS, *bde.DATASETS, *yahoo.DATASETS]
