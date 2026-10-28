"""
Shared helpers for the independent audit checks (scripts/audit/).

These checks deliberately do NOT import anything from src/: every number is
fetched again from the official APIs (or recomputed from the published JSON)
with minimal code, so that a bug in the pipeline cannot hide itself.

Dependencies: requests, pandas (only).
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site" / "data"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CdE-audit/1.0", "Accept": "application/json"})


def http_json(url: str, params: dict | None = None, tries: int = 3, timeout: int = 60):
    last = None
    for i in range(tries):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"GET {url} {params} failed: {last}")


# ---------------------------------------------------------------- site data
_cache: dict = {}


def manifest() -> dict:
    return json.loads((SITE / "manifest.json").read_text(encoding="utf-8"))


def load(ds_id: str) -> dict:
    if ds_id not in _cache:
        src, ind = ds_id.split(".", 1)
        _cache[ds_id] = json.loads((SITE / src / f"{ind}.json").read_text(encoding="utf-8"))
    return _cache[ds_id]


def field_index(ds: dict, key: str) -> int:
    keys = [f["key"] for f in ds["fields"]]
    return keys.index(key) + 1


def series(ds_id: str, skey: str, fkey: str) -> dict:
    """{x: value} for one series/field of a published dataset (nulls dropped)."""
    ds = load(ds_id)
    i = field_index(ds, fkey)
    for s in ds["series"]:
        if s["key"] == skey:
            return {r[0]: r[i] for r in s["data"] if r[i] is not None}
    raise KeyError(f"{ds_id}: series {skey} not found")


def series_keys(ds_id: str) -> list:
    return [s["key"] for s in load(ds_id)["series"]]


# ---------------------------------------------------------------- results
@dataclass
class Result:
    ds: str
    check: str          # identity | values | transform | dating | meta
    status: str         # PASS | FAIL | WARN | SKIP
    detail: str = ""
    maxdiff: float | None = None
    n: int = 0


@dataclass
class Report:
    rows: list = field(default_factory=list)

    def add(self, *a, **k):
        r = Result(*a, **k)
        self.rows.append(r)
        return r

    def compare(self, ds: str, check: str, published: dict, official: dict, tol: float,
                label: str = "", last_n: int | None = None, warn_only: bool = False,
                require_latest: bool = True):
        """Compare two {date: value} dicts on common dates (last_n most recent official dates)."""
        keys = sorted(official)
        if last_n:
            keys = keys[-last_n:]
        common = [k for k in keys if k in published]
        missing = [k for k in keys if k not in published]
        diffs = [(k, published[k], official[k], abs(published[k] - official[k])) for k in common
                 if official[k] is not None and published[k] is not None]
        md = max((d[3] for d in diffs), default=0.0)
        bad = [d for d in diffs if d[3] > tol]
        status = "PASS"
        detail = f"{label} n={len(common)} maxdiff={md:.4g}"
        if bad:
            status = "WARN" if warn_only else "FAIL"
            k, p, o, d = max(bad, key=lambda t: t[3])
            detail += f" ({len(bad)} > tol {tol}; worst {k}: published {p} vs official {o})"
        # A missing most-recent official period means the site is behind the source.
        if require_latest and keys and keys[-1] not in published:
            status = "FAIL" if status != "FAIL" and not warn_only else status
            detail += f" latest official {keys[-1]} not published"
        elif missing:
            detail += f" ({len(missing)} official dates absent from site: {missing[:3]})"
        if not common:
            status = "FAIL"
            detail += " NO OVERLAP"
        return self.add(ds, check, status, detail.strip(), md, len(common))

    def print(self):
        w = max((len(r.ds) for r in self.rows), default=10)
        for r in self.rows:
            print(f"{r.status:<5} {r.ds:<{w}} {r.check:<10} {r.detail}")
        c = {}
        for r in self.rows:
            c[r.status] = c.get(r.status, 0) + 1
        print("\nSummary:", ", ".join(f"{k}={v}" for k, v in sorted(c.items())))

    @property
    def failed(self) -> bool:
        return any(r.status == "FAIL" for r in self.rows)


# ---------------------------------------------------------------- date helpers
def first_of_month(y: int, m: int) -> str:
    return f"{y:04d}-{m:02d}-01"


def quarter_start(y: int, q: int) -> str:
    return first_of_month(y, 3 * (q - 1) + 1)


def add_months(x: str, months: int) -> str:
    y, m = int(x[:4]), int(x[5:7])
    t = y * 12 + (m - 1) + months
    return first_of_month(t // 12, t % 12 + 1)


def rel(a, b):
    if a is None or b is None or b == 0:
        return None
    return (a / b - 1.0) * 100.0


def isclose(a, b, tol):
    return a is not None and b is not None and math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol
