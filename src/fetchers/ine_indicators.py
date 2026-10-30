"""
INE Indicator Fetcher

Downloads exactly the INE series the dashboard uses, by series code, from the registry in
`src/fetchers/ine_series.py`:  GET DATOS_SERIE/{code}?nult=N, one small request per series, a few at
a time. (Before, 33 whole tables were downloaded, 48 MB, and filtered later by series name.)

Failure semantics:
- A series that cannot be fetched, is empty, comes back under another code, or whose name no
  longer contains the registry's tokens makes its indicator fail: the previous raw file is
  kept and an ERROR is logged ("... failed ..."), which run_pipeline.py reports and turns
  into exit code 3 (audit H1).
- One failing indicator does not stop the others.
- A raw file is rewritten only when its content changed.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .ine_series import INDICATORS, TABLE_IDS
from .http_session import CircuitBreaker, map_bounded
from .ine_client import INEClient, flash_dates, parse_ine_data

logger = logging.getLogger(__name__)

MAX_WORKERS = 4  # concurrent requests to servicios.ine.es

__all__ = ["INEIndicatorFetcher", "fetch_operation_tables", "TABLE_IDS", "INDICATORS"]


class SeriesError(Exception):
    """A requested INE series is missing, empty or not what the registry says it is."""


def _norm(text: str) -> str:
    return " ".join(str(text).replace("Total Nacional", "Nacional").lower().split())


def validate_series(code: str, tokens: Iterable[str], item) -> None:
    """Raise SeriesError unless `item` is a non-empty INE series `code` whose name has all tokens."""
    if not isinstance(item, dict) or item.get("COD") != code:
        got = item.get("COD") if isinstance(item, dict) else type(item).__name__
        raise SeriesError(f"{code}: INE returned {got!r}")
    if not item.get("Data"):
        raise SeriesError(f"{code}: no observations")
    name = _norm(item.get("Nombre", ""))
    missing = [t for t in tokens if _norm(t) not in name]
    if missing:
        raise SeriesError(f"{code}: name {item.get('Nombre')!r} lacks {missing} (INE redefined the series?)")
    # "ajustados de estacionalidad" is also a substring of "no ajustados de estacionalidad":
    # a series declared adjusted must not be the unadjusted variant.
    if any("ajustados de estacionalidad" in _norm(t) for t in tokens) and "no ajustados" in name:
        raise SeriesError(f"{code}: declared seasonally adjusted but INE names it {item.get('Nombre')!r}")


FLASH_FILE = "flash.json"  # read by src/export/core.py


class INEIndicatorFetcher:
    """Fetcher for INE economic indicators."""

    def __init__(self, output_dir: str = "data/raw/ine"):
        self.client = INEClient()
        self.breaker = CircuitBreaker()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ io
    def _save_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Write the raw CSV if its content changed. Never overwrite cached data with an empty frame."""
        filepath = self.output_dir / filename
        if df.empty:
            logger.warning(f"Skipping save of empty DataFrame to {filepath} (preserving cached data)")
            return filepath
        text = df.to_csv(index=False)
        if filepath.exists() and filepath.read_bytes() == text.encode("utf-8"):
            logger.info(f"Unchanged: {filepath}")
            return filepath
        filepath.write_text(text, encoding="utf-8", newline="")
        logger.info(f"Saved: {filepath}")
        return filepath

    def _save_flash(self, by_code: Dict[str, List[str]]) -> None:
        """Record which observations are INE flash estimates ("avance") in flash.json, by series
        code. Codes fetched in this run replace their previous entry; the others are kept."""
        path = self.output_dir / FLASH_FILE
        try:
            current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except ValueError:
            current = {}
        current.update(by_code)
        current = {k: v for k, v in sorted(current.items()) if v}
        path.write_text(json.dumps(current, indent=1) + "\n", encoding="utf-8")
        if any(by_code.values()):
            logger.info("INE flash estimates: " + ", ".join(f"{k} {v[-1]}" for k, v in by_code.items() if v))

    # ------------------------------------------------------------------ fetch
    def _fetch_series(self, job: Tuple[str, int, tuple]):
        code, nult, tokens = job
        self.breaker.check()
        try:
            item = self.client.get_series_data(code, nult=nult)
        except Exception:
            self.breaker.failure()
            raise
        self.breaker.success()
        validate_series(code, tokens, item)
        return item

    def fetch_indicators(self, names: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch the given indicators (default: all) and save their raw files.
        Returns indicator -> DataFrame (empty if that indicator failed and its cached file was kept).
        """
        names = list(names or INDICATORS)
        unknown = [n for n in names if n not in INDICATORS]
        if unknown:
            raise KeyError(f"unknown INE indicators: {unknown}")

        # One request per distinct (code, nult); a series shared by two indicators is fetched once.
        jobs: Dict[Tuple[str, int], tuple] = {}
        for n in names:
            spec = INDICATORS[n]
            for code, tokens in spec["series"].values():
                jobs.setdefault((code, spec["nult"]), tokens)
        keys = list(jobs)
        logger.info(f"Fetching {len(keys)} INE series for {len(names)} indicators ({MAX_WORKERS} at a time)...")
        outcomes = map_bounded(lambda k: self._fetch_series((k[0], k[1], jobs[k])), keys, MAX_WORKERS)
        fetched = {k: out for k, out in zip(keys, outcomes)}
        self._save_flash({code: flash_dates(item) for (code, _), (item, exc) in fetched.items() if exc is None})

        results = {}
        for n in names:
            spec = INDICATORS[n]
            items, errors = [], []
            for role, (code, _) in spec["series"].items():
                item, exc = fetched[(code, spec["nult"])]
                if exc is not None:
                    errors.append(f"{code} ({role}): {exc}")
                else:
                    items.append(item)
            if errors:
                logger.error(f"INE {n}: fetch failed for {len(errors)} of {len(spec['series'])} series, "
                             f"keeping the previous {spec['file']}: " + "; ".join(errors[:3]))
                results[n] = pd.DataFrame()
                continue
            df = parse_ine_data(items)
            if spec.get("since"):
                df = df[df["date"] >= pd.Timestamp(spec["since"])]
            self._save_csv(df, spec["file"])
            results[n] = df
        return results

    def fetch_all(self) -> Dict[str, pd.DataFrame]:
        """Fetch every indicator."""
        return self.fetch_indicators()


def fetch_operation_tables(operation_code: str) -> pd.DataFrame:
    """
    Utility function to explore tables for a given operation.
    Useful for finding table IDs for indicators not yet mapped.

    Args:
        operation_code: Operation code (e.g., 'ICE', 'ETCL', 'IPRI')
    """
    client = INEClient()
    tables = client.get_operation_tables(operation_code)

    records = []
    for table in tables:
        records.append({
            "id": table.get("Id"),
            "nombre": table.get("Nombre"),
            "periodicidad": table.get("Periodicidad", {}).get("Nombre") if isinstance(table.get("Periodicidad"), dict) else None,
        })

    return pd.DataFrame(records)
