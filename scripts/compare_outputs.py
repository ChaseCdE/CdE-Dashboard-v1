#!/usr/bin/env python3
"""
Compare a pipeline output with a reference ("golden") output, per dataset.

    python scripts/compare_outputs.py [--golden-site DIR] [--site DIR]
                                      [--golden-processed DIR] [--processed DIR]
                                      [--only PREFIX ...] [--strict-rows] [--verbose]

site/data JSON: everything except `generated_at` must match. Series rows are matched by
x value (first element of each row); rows present on only one side are reported as
`+new` (only in the new output) / `-gone` (only in the reference). Without --strict-rows
a dataset whose common rows are identical and that only has `+new` rows (the source
published new data since the reference run) is reported as "identical (overlap)".

processed CSV (--golden-processed): files are compared on the columns they have in
common, rows matched by the first column; columns present on one side only are listed.

Exit code 1 if any dataset differs.
"""
import argparse
import json
import math
import sys
from pathlib import Path

IGNORE_KEYS = {"generated_at"}


def num(a):
    return isinstance(a, (int, float)) and not isinstance(a, bool)


def diff_scalar(a, b):
    """Return (differs, absdiff or None)."""
    if num(a) and num(b):
        if (isinstance(a, float) and math.isnan(a)) and (isinstance(b, float) and math.isnan(b)):
            return False, None
        return (a != b), abs(a - b)
    return (a != b), None


class Result:
    def __init__(self):
        self.n_diff = 0
        self.max_abs = 0.0
        self.new_rows = 0
        self.gone_rows = 0
        self.notes = []
        self.compared = 0

    def add(self, a, b, where=None):
        self.compared += 1
        d, ad = diff_scalar(a, b)
        if d:
            self.n_diff += 1
            if ad is not None:
                self.max_abs = max(self.max_abs, ad)
            if where and len(self.notes) < 3:
                self.notes.append(f"{where}: {a!r} -> {b!r}")


def deep(a, b, res, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in IGNORE_KEYS:
                continue
            if k not in a or k not in b:
                res.n_diff += 1
                res.notes.append(f"{path}/{k}: key only in {'new' if k in b else 'reference'}")
                continue
            deep(a[k], b[k], res, f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            res.n_diff += 1
            res.notes.append(f"{path}: length {len(a)} -> {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            deep(x, y, res, f"{path}[{i}]")
    else:
        res.add(a, b, path)


def compare_series(sa, sb, res, path):
    ra = {tuple(r[:1])[0]: r for r in sa}
    rb = {tuple(r[:1])[0]: r for r in sb}
    for x in ra.keys() & rb.keys():
        a, b = ra[x], rb[x]
        if len(a) != len(b):
            res.n_diff += 1
            res.notes.append(f"{path}@{x}: row width {len(a)} -> {len(b)}")
            continue
        for j in range(1, len(a)):
            res.add(a[j], b[j], f"{path}@{x}[{j}]")
    res.new_rows += len(rb.keys() - ra.keys())
    res.gone_rows += len(ra.keys() - rb.keys())


def compare_json(pa, pb):
    a, b = json.loads(pa.read_text("utf-8")), json.loads(pb.read_text("utf-8"))
    res = Result()
    if isinstance(a, dict) and "series" in a and isinstance(b, dict) and "series" in b:
        deep({k: v for k, v in a.items() if k not in ("series", "last_observation")},
             {k: v for k, v in b.items() if k not in ("series", "last_observation")}, res)
        ka = {s["key"]: s for s in a["series"]}
        kb = {s["key"]: s for s in b["series"]}
        if list(ka) != list(kb):
            res.n_diff += 1
            res.notes.append(f"series keys {list(ka)} -> {list(kb)}")
        for k in ka.keys() & kb.keys():
            deep({x: y for x, y in ka[k].items() if x != "data"},
                 {x: y for x, y in kb[k].items() if x != "data"}, res, f"series[{k}]")
            compare_series(ka[k]["data"], kb[k]["data"], res, f"series[{k}]")
    else:
        deep(a, b, res)
    return res


def compare_csv(pa, pb):
    import pandas as pd
    res = Result()
    a, b = pd.read_csv(pa), pd.read_csv(pb)
    common = [c for c in a.columns if c in b.columns]
    only_a = [c for c in a.columns if c not in b.columns]
    only_b = [c for c in b.columns if c not in a.columns]
    if only_a or only_b:
        res.notes.append(f"columns only in reference: {only_a}; only in new: {only_b}")
    if not common:
        res.n_diff += 1
        return res
    key = common[0]
    a, b = a[common].drop_duplicates(subset=[key], keep="last").set_index(key), \
        b[common].drop_duplicates(subset=[key], keep="last").set_index(key)
    idx = a.index.intersection(b.index)
    res.new_rows = len(b.index.difference(a.index))
    res.gone_rows = len(a.index.difference(b.index))
    aa, bb = a.loc[idx], b.loc[idx]
    for c in aa.columns:
        x, y = aa[c], bb[c]
        both_nan = x.isna() & y.isna()
        if x.dtype.kind in "fi" and y.dtype.kind in "fi":
            d = (x != y) & ~both_nan
            res.compared += int(len(x))
            if d.any():
                res.n_diff += int(d.sum())
                res.max_abs = max(res.max_abs, float((x - y).abs()[d].max()))
                if len(res.notes) < 3:
                    i = d.idxmax()
                    res.notes.append(f"{c}@{i}: {x[i]} -> {y[i]}")
        else:
            d = (x.astype(str) != y.astype(str)) & ~both_nan
            res.compared += int(len(x))
            if d.any():
                res.n_diff += int(d.sum())
                if len(res.notes) < 3:
                    i = d.idxmax()
                    res.notes.append(f"{c}@{i}: {x[i]!r} -> {y[i]!r}")
    return res


def status(res, strict_rows):
    if res.n_diff or res.gone_rows or (strict_rows and res.new_rows):
        return "DIFFERS"
    return "identical (overlap)" if res.new_rows else "identical"


def run(ref_dir, new_dir, pattern, only, strict_rows, verbose, comparer, label):
    ref_dir, new_dir = Path(ref_dir), Path(new_dir)
    bad = 0
    counts = {}
    for p in sorted(ref_dir.rglob(pattern)):
        rel = p.relative_to(ref_dir)
        name = str(rel.with_suffix("")).replace("/", ".")
        if only and not any(name.startswith(o) for o in only):
            continue
        q = new_dir / rel
        if not q.exists():
            print(f"{label} {name:55s} DIFFERS  (missing in new output)")
            bad += 1
            continue
        res = comparer(p, q)
        st = status(res, strict_rows)
        counts[st] = counts.get(st, 0) + 1
        if st == "DIFFERS":
            bad += 1
        if st == "DIFFERS" or verbose or res.new_rows:
            extra = f" n_diff={res.n_diff} max_abs={res.max_abs:.6g} +new={res.new_rows} -gone={res.gone_rows}"
            print(f"{label} {name:55s} {st}{extra}")
            for n in res.notes:
                print(f"      {n}")
    extra_new = [str(q.relative_to(new_dir)) for q in sorted(new_dir.rglob(pattern))
                 if not (ref_dir / q.relative_to(new_dir)).exists()]
    if extra_new and not only:
        print(f"{label} files only in new output (not compared): {extra_new}")
    print(f"{label} summary: {counts}")
    return bad


def main():
    home = Path.home()
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden-site", default=str(home / "golden" / "site_data"))
    ap.add_argument("--site", default=str(root / "site" / "data"))
    ap.add_argument("--golden-processed", default=None)
    ap.add_argument("--processed", default=str(root / "data" / "processed"))
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--strict-rows", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    bad = run(a.golden_site, a.site, "*.json", a.only, a.strict_rows, a.verbose, compare_json, "site")
    if a.golden_processed:
        bad += run(a.golden_processed, a.processed, "*.csv", a.only, a.strict_rows, a.verbose, compare_csv, "csv ")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
