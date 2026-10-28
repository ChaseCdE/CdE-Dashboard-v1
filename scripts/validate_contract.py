#!/usr/bin/env python3
"""
Validate site/data/ against docs/data-contract.md (v1.2).

Errors: anything that breaks the contract. Exit code 1.
Warnings: stale data (see staleness thresholds in the contract). Exit code 0,
unless --strict, which turns warnings into errors.

Usage:
    python scripts/validate_contract.py
    python scripts/validate_contract.py --strict
    python scripts/validate_contract.py --dir path/to/site/data
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / "site" / "data"

CONTRACT_VERSION = "1.2"
UNITS = {"pct", "pct_change", "pp", "index", "points", "currency", "rate", "persons", "hours", "years", "count"}
FREQUENCIES = {"D", "W", "M", "Q", "A", "X"}
X_TYPES = {"date", "number", "category"}
SOURCES = {"ine": "INE", "eurostat": "Eurostat", "bde": "Banco de España", "yahoo": "Yahoo Finance"}
# Staleness: days between the END of the last observed period and generated_at.
STALE_DAYS = {"D": 7, "W": 21, "M": 100, "Q": 200, "A": 550}
PERIOD_MONTHS = {"M": 1, "Q": 3, "A": 12}

# Field-key naming rules (contract v1.1, "Field keys and units").
PCT_CHANGE_KEYS = {"yoy", "qoq", "mom"}


def required_unit(key: str):
    """Unit a field key forces, or None if the key carries no unit rule."""
    if key in PCT_CHANGE_KEYS or key.startswith("ret_"):
        return "pct_change"
    if key.endswith("_pp") or key.startswith("chg_"):
        return "pp"
    return None


def period_end(d: date, freq: str) -> date:
    """First day after the period that starts on d."""
    from datetime import timedelta
    if freq in PERIOD_MONTHS:
        m = d.month - 1 + PERIOD_MONTHS[freq]
        return date(d.year + m // 12, m % 12 + 1, 1)
    return d + timedelta(days=7 if freq == "W" else 1)

SNAKE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CURRENCY = re.compile(r"^[A-Z]{3}$")


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, where: str, msg: str):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str):
        self.warnings.append(f"{where}: {msg}")


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def too_many_decimals(v: float) -> bool:
    return isinstance(v, float) and round(v, 4) != v


def parse_date(s) -> date | None:
    if not isinstance(s, str) or not ISO_DATE.match(s):
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def period_start_ok(d: date, freq: str) -> bool:
    if freq == "M":
        return d.day == 1
    if freq == "Q":
        return d.day == 1 and d.month in (1, 4, 7, 10)
    if freq == "A":
        return d.day == 1 and d.month == 1
    return True


def validate_dataset(path: Path, rel: str, obj: dict, r: Report) -> dict | None:
    w = rel
    required = ["contract_version", "id", "title_es", "source", "frequency", "x", "fields", "series",
                "last_observation", "generated_at"]
    missing = [k for k in required if k not in obj]
    if missing:
        r.err(w, f"missing keys {missing}")
        return None
    allowed = set(required) | {"description_es", "stale_after_days"}
    sad = obj.get("stale_after_days")
    if sad is not None and (not isinstance(sad, int) or isinstance(sad, bool) or sad <= 0):
        r.err(w, "stale_after_days must be a positive integer")
    extra = set(obj) - allowed
    if extra:
        r.err(w, f"unknown keys {sorted(extra)}")

    if obj["contract_version"] != CONTRACT_VERSION:
        r.err(w, f"contract_version {obj['contract_version']!r} != {CONTRACT_VERSION!r}")

    # id <-> path
    src_dir, _, fname = rel.partition("/")
    expected_id = f"{src_dir}.{fname[:-5]}" if fname.endswith(".json") else None
    if obj["id"] != expected_id:
        r.err(w, f"id {obj['id']!r} does not match path (expected {expected_id!r})")
    if src_dir not in SOURCES:
        r.err(w, f"unknown source directory {src_dir!r}")
    if expected_id and not SNAKE.match(fname[:-5]):
        r.err(w, f"indicator {fname[:-5]!r} is not snake_case")

    if not isinstance(obj["title_es"], str) or not obj["title_es"].strip() or obj["title_es"].rstrip().endswith("."):
        r.err(w, "title_es must be non-empty with no trailing period")

    src = obj["source"]
    if not isinstance(src, dict) or set(src) != {"name", "dataset", "url"}:
        r.err(w, "source must have exactly name, dataset, url")
    else:
        if src_dir in SOURCES and src["name"] != SOURCES[src_dir]:
            r.err(w, f"source.name {src['name']!r} != {SOURCES[src_dir]!r}")
        if not str(src["dataset"]).strip():
            r.err(w, "source.dataset empty")
        if not str(src["url"]).startswith("https://"):
            r.err(w, "source.url must be https")

    freq = obj["frequency"]
    if freq not in FREQUENCIES:
        r.err(w, f"frequency {freq!r} not in {sorted(FREQUENCIES)}")
    x = obj["x"]
    xtype = x.get("type") if isinstance(x, dict) else None
    if xtype not in X_TYPES or not isinstance(x.get("key"), str):
        r.err(w, f"x must be {{key, type}} with type in {sorted(X_TYPES)}")
    if (xtype == "date") != (freq != "X"):
        r.err(w, f"x.type {xtype!r} inconsistent with frequency {freq!r} (date iff not X)")
    if xtype == "date" and x.get("key") != "date":
        r.err(w, "x.key must be 'date' when x.type is date")

    if not ISO_TS.match(str(obj["generated_at"])):
        r.err(w, f"generated_at {obj['generated_at']!r} not UTC ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)")

    # fields
    fields = obj["fields"]
    if not isinstance(fields, list) or not fields:
        r.err(w, "fields must be a non-empty list")
        return None
    fkeys = []
    for i, f in enumerate(fields):
        fw = f"{w} fields[{i}]"
        if not isinstance(f, dict):
            r.err(fw, "not an object"); continue
        for k in ("key", "label_es", "unit", "decimals"):
            if k not in f:
                r.err(fw, f"missing {k}")
        extra = set(f) - {"key", "label_es", "unit", "decimals", "currency", "scale", "note_es"}
        if extra:
            r.err(fw, f"unknown keys {sorted(extra)}")
        key = f.get("key")
        fkeys.append(key)
        if not isinstance(key, str) or not SNAKE.match(key):
            r.err(fw, f"key {key!r} not snake_case")
        if f.get("unit") not in UNITS:
            r.err(fw, f"unit {f.get('unit')!r} not in {sorted(UNITS)}")
        need = required_unit(str(key))
        if need and f.get("unit") != need:
            r.err(fw, f"key {key!r} requires unit {need!r} (got {f.get('unit')!r}); "
                      "use a '_pp' or '_diff' key for differences")
        if f.get("unit") == "currency" and not CURRENCY.match(str(f.get("currency", ""))):
            r.err(fw, "unit currency requires an ISO 4217 'currency'")
        if not isinstance(f.get("decimals"), int) or not 0 <= f.get("decimals", -1) <= 4:
            r.err(fw, "decimals must be an int 0..4")
        if "scale" in f and not isinstance(f["scale"], int):
            r.err(fw, "scale must be an int (power of ten)")
    if len(set(fkeys)) != len(fkeys):
        r.err(w, f"duplicate field keys {fkeys}")
    nf = len(fields)

    # series
    series = obj["series"]
    if not isinstance(series, list) or not series:
        r.err(w, "series must be a non-empty list")
        return None
    skeys, max_x = [], None
    for si, s in enumerate(series):
        sw = f"{w} series[{s.get('key', si)}]"
        if not isinstance(s, dict) or not {"key", "label_es", "data"} <= set(s):
            r.err(sw, "series needs key, label_es, data"); continue
        extra = set(s) - {"key", "label_es", "data", "as_of"}
        if extra:
            r.err(sw, f"unknown keys {sorted(extra)}")
        skeys.append(s["key"])
        if not isinstance(s["key"], str) or not SNAKE.match(s["key"]):
            r.err(sw, f"key {s['key']!r} not snake_case")
        if "as_of" in s and parse_date(s["as_of"]) is None:
            r.err(sw, f"as_of {s['as_of']!r} not YYYY-MM-DD")
        data = s["data"]
        if not isinstance(data, list) or not data:
            r.err(sw, "data must be a non-empty list"); continue
        prev, bad = None, 0
        for ri, row in enumerate(data):
            if bad >= 5:
                r.err(sw, "... further row errors suppressed"); break
            rw = f"{sw} row {ri}"
            if not isinstance(row, list) or len(row) != nf + 1:
                r.err(rw, f"expected {nf + 1} items, got {row!r}"[:200]); bad += 1; continue
            xv, vals = row[0], row[1:]
            if xtype == "date":
                d = parse_date(xv)
                if d is None:
                    r.err(rw, f"x {xv!r} not a valid YYYY-MM-DD"); bad += 1; continue
                if not period_start_ok(d, freq):
                    r.err(rw, f"x {xv} is not the first day of the period for frequency {freq}"); bad += 1
                key = d
            elif xtype == "number":
                if not is_number(xv):
                    r.err(rw, f"x {xv!r} not a finite number"); bad += 1; continue
                key = xv
            else:
                if not isinstance(xv, str):
                    r.err(rw, f"x {xv!r} not a string"); bad += 1; continue
                key = None
            if key is not None and prev is not None and key <= prev:
                r.err(rw, f"x {xv} not strictly ascending (previous {prev})"); bad += 1
            prev = key if key is not None else prev
            if all(v is None for v in vals):
                r.err(rw, "all values null (row should be dropped)"); bad += 1
            for v in vals:
                if v is not None and not is_number(v):
                    r.err(rw, f"value {v!r} not a finite number or null"); bad += 1
                elif v is not None and too_many_decimals(v):
                    r.err(rw, f"value {v!r} has more than 4 decimals"); bad += 1
        if xtype == "date" and isinstance(prev, date):
            max_x = prev if max_x is None or prev > max_x else max_x
    if len(set(skeys)) != len(skeys):
        r.err(w, f"duplicate series keys {skeys}")

    lo = obj["last_observation"]
    if xtype == "date":
        expected = max_x.isoformat() if max_x else None
        if lo != expected:
            r.err(w, f"last_observation {lo!r} != max x {expected!r}")
        gen = obj["generated_at"]
        if expected and freq in STALE_DAYS and ISO_TS.match(str(gen)):
            age = (datetime.fromisoformat(gen.replace("Z", "+00:00")).date() - period_end(max_x, freq)).days
            limit = obj.get("stale_after_days") if isinstance(obj.get("stale_after_days"), int) else STALE_DAYS[freq]
            if age > limit:
                r.warn(w, f"stale: period starting {expected} ended {age} days before generation "
                          f"(limit {limit} for {freq})")
    elif lo is not None:
        r.err(w, "last_observation must be null for non-date datasets")
    return obj


def expected_latest(obj: dict) -> list:
    keys = [f["key"] for f in obj["fields"]]
    out = []
    for s in obj["series"]:
        latest = {}
        for i, k in enumerate(keys, start=1):
            latest[k] = None
            for row in reversed(s["data"]):
                if row[i] is not None:
                    latest[k] = [row[0], row[i]]
                    break
        out.append({"key": s["key"], "label_es": s["label_es"], "latest": latest})
    return out


def validate(data_dir: Path) -> Report:
    r = Report()
    if not data_dir.is_dir():
        r.err(str(data_dir), "directory not found")
        return r

    files = {}
    for p in sorted(data_dir.rglob("*.json")):
        rel = p.relative_to(data_dir).as_posix()
        if rel == "manifest.json":
            continue
        if rel.count("/") != 1:
            r.err(rel, "dataset files must be exactly site/data/<source>/<indicator>.json")
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            r.err(rel, f"invalid JSON: {e}")
            continue
        if validate_dataset(p, rel, obj, r) is not None:
            files[rel] = obj

    mpath = data_dir / "manifest.json"
    if not mpath.exists():
        r.err("manifest.json", "missing")
        return r
    try:
        m = json.loads(mpath.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        r.err("manifest.json", f"invalid JSON: {e}")
        return r
    if m.get("contract_version") != CONTRACT_VERSION:
        r.err("manifest.json", f"contract_version {m.get('contract_version')!r} != {CONTRACT_VERSION!r}")
    if not ISO_TS.match(str(m.get("generated_at"))):
        r.err("manifest.json", "generated_at not UTC ISO 8601")
    entries = m.get("datasets")
    if not isinstance(entries, list):
        r.err("manifest.json", "datasets must be a list")
        return r

    seen = set()
    for e in entries:
        ew = f"manifest.json [{e.get('id')}]"
        path = e.get("path")
        if path in seen:
            r.err(ew, f"duplicate path {path}")
        seen.add(path)
        obj = files.get(path)
        if obj is None:
            if not (data_dir / str(path)).exists():
                r.err(ew, f"path {path!r} does not exist")
            continue
        for k in ("id", "title_es", "frequency", "last_observation"):
            if e.get(k) != obj.get(k):
                r.err(ew, f"{k} {e.get(k)!r} != file {obj.get(k)!r}")
        if e.get("source") != obj["source"]["name"]:
            r.err(ew, f"source {e.get('source')!r} != file {obj['source']['name']!r}")
        if e.get("fields") != [f["key"] for f in obj["fields"]]:
            r.err(ew, "fields do not match file")
        if e.get("series") != expected_latest(obj):
            r.err(ew, "series/latest do not match file")
    for rel in files:
        if rel not in seen:
            r.err(rel, "file not listed in manifest.json")
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate site/data against the data contract.")
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    r = validate(args.dir)
    for wmsg in r.warnings:
        print(f"[WARN] {wmsg}")
    for emsg in r.errors:
        print(f"[ERROR] {emsg}")
    n_files = len(list(args.dir.rglob("*.json"))) - 1 if args.dir.exists() else 0
    failed = bool(r.errors) or (args.strict and bool(r.warnings))
    print(f"\n{'FAIL' if failed else 'OK'}: {n_files} dataset file(s), {len(r.errors)} error(s), {len(r.warnings)} warning(s)"
          + (" [strict]" if args.strict else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
