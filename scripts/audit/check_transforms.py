"""
Offline checks on site/data (no network): every derived field is recomputed from
the published levels of the same dataset and compared; dating, ordering and unit
sanity rules of docs/data-contract.md are checked for all 125 datasets.

Window definitions recomputed here (independently of src/):
  yoy / qoq / mom        relative % change vs the same x 12 / 3 / 1 calendar months
                         earlier (date-based: null if that period is absent)
  yoy_pp / yoy_diff      difference vs 12 months earlier; qoq_pp 3 months; mom_pp 1
  sum_12m                sum of the 12 consecutive months ending at x; null unless all 12 exist
  BdE daily chg_1m       value - last value on or before x - 30 days
  BdE daily chg_ytd      value - last value on or before 31 Dec of the previous year
  BdE daily chg_1y       value - last value on or before x - 1 calendar year
  Yahoo ret_1d/1w/1m  % change vs 1 / 5 / 21 published sessions earlier; ret_1y/chg_1y vs the last close on or before x - 1 calendar year
  Yahoo chg_*            same windows, difference (pp) for yields
  Yahoo ret_ytd/chg_ytd  vs last published close of the previous calendar year
  sma_200                mean of the last 200 published closes
"""
from __future__ import annotations

import bisect
import math
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, add_months, load, manifest  # noqa: E402

LAG = {"yoy": 12, "qoq": 3, "mom": 1, "yoy_pp": 12, "yoy_diff": 12, "qoq_pp": 3, "mom_pp": 1}
# Fields that are the source's own published rate (checked against the source in check_<src>.py)
OFFICIAL = {
    ("ine.industrial_production", "yoy"), ("ine.services_production", "yoy"),
    ("ine.business_confidence", "yoy"),  # computed, but only for the ICE index: handled below
    ("ine.ipri", "yoy"), ("ine.ipri", "mom"),  # INE's published rates (1 decimal), checked in check_ine.py
    # Audit M4: INE's published rates replace the rates recomputed from rounded indices (check_ine.py compares them)
    ("ine.industrial_production", "mom"), ("ine.services_production", "mom"),
    ("ine.cpi", "yoy"), ("ine.retail_sales", "yoy"), ("ine.retail_sales", "mom"), ("ine.house_prices", "yoy"),
    ("ine.tourist_arrivals", "yoy"), ("ine.tourist_spending", "yoy"),
    # Audit M3: BdE's published transaction-based growth rates (check_bde.py compares them with the API)
    ("bde.credit_households_total", "yoy"), ("bde.credit_nfc_total", "yoy"),
}
LEVEL_FIELD = {"yahoo": "close"}


def rows(ds, fkey):
    i = [f["key"] for f in ds["fields"]].index(fkey) + 1
    return i


def recompute_period(ds, s, fkey, base_key="value"):
    keys = [f["key"] for f in ds["fields"]]
    if base_key not in keys:
        return None
    bi, fi = keys.index(base_key) + 1, keys.index(fkey) + 1
    lvl = {r[0]: r[bi] for r in s["data"] if r[bi] is not None}
    pub = {r[0]: r[fi] for r in s["data"]}
    lag = LAG[fkey]
    exp = {}
    for x in pub:
        cur, prev = lvl.get(x), lvl.get(add_months(x, -lag))
        if cur is None or prev is None:
            exp[x] = None
        elif fkey in ("yoy", "qoq", "mom"):
            exp[x] = (cur / prev - 1) * 100 if prev else None
        else:
            exp[x] = cur - prev
    return pub, exp


def compare_maps(rep, ds_id, label, pub, exp, tol):
    bad, nulls, n, md = [], [], 0, 0.0
    for x, p in pub.items():
        e = exp.get(x)
        if p is None and e is None:
            continue
        if (p is None) != (e is None):
            nulls.append((x, p, e))
            continue
        n += 1
        d = abs(p - e)
        md = max(md, d)
        if d > tol:
            bad.append((x, p, e))
    st = "FAIL" if bad or nulls else "PASS"
    det = f"{label} n={n} maxdiff={md:.3g}"
    if bad:
        x, p, e = max(bad, key=lambda t: abs(t[1] - t[2]))
        det += f"; {len(bad)} > tol {tol} (worst {x}: published {p} vs recomputed {e:.4f})"
    if nulls:
        det += f"; {len(nulls)} null mismatches (e.g. {nulls[0]})"
    rep.add(ds_id, "transform", st, det, md, n)


def asof(sorted_x, vals, target):
    i = bisect.bisect_right(sorted_x, target) - 1
    return vals[sorted_x[i]] if i >= 0 else None


def check_dating(rep, ds_id, ds):
    freq = ds["frequency"]
    probs = []
    for s in ds["series"]:
        xs = [r[0] for r in s["data"]]
        if xs != sorted(xs) or len(set(xs)) != len(xs):
            probs.append(f"{s['key']}: not sorted/unique")
        if freq == "X":
            continue
        for x in xs:
            d = date.fromisoformat(x)
            if freq == "M" and d.day != 1:
                probs.append(f"{s['key']} {x} not 1st of month"); break
            if freq == "Q" and (d.day != 1 or d.month not in (1, 4, 7, 10)):
                probs.append(f"{s['key']} {x} not quarter start"); break
            if freq == "A" and (d.day != 1 or d.month != 1):
                probs.append(f"{s['key']} {x} not 1 Jan"); break
            if freq == "D" and d.weekday() >= 5 and ds_id.split(".")[0] in ("yahoo", "bde"):
                probs.append(f"{s['key']} {x} weekend"); break
        for r in s["data"]:
            if len(r) != 1 + len(ds["fields"]):
                probs.append(f"{s['key']} bad row length"); break
    rep.add(ds_id, "dating", "FAIL" if probs else "PASS", "; ".join(probs[:3]) or f"{freq}: period-start dates, sorted, unique")


def check_units(rep, ds_id, ds):
    probs = []
    for fi, f in enumerate(ds["fields"], start=1):
        vals = [r[fi] for s in ds["series"] for r in s["data"] if r[fi] is not None]
        if not vals:
            continue
        mx = max(abs(v) for v in vals)
        k, u = f["key"], f["unit"]
        if k in ("yoy", "qoq", "mom") or k.startswith("ret_"):
            if u != "pct_change":
                probs.append(f"{k} unit {u}")
        if k.endswith("_pp") or k.startswith("chg_") or k == "contribution":
            if u != "pp":
                probs.append(f"{k} unit {u}")
        if u == "pct" and k in ("value", "yield", "weight") and mx > 300:
            probs.append(f"{k} pct max {mx} (x100?)")
        if u == "pct_change" and 0 < mx < 0.05 and len(vals) > 12 and not ds_id.startswith("yahoo"):
            probs.append(f"{k} max |{mx}| suspiciously small (/100?)")
    rep.add(ds_id, "meta", "FAIL" if probs else "PASS", "; ".join(probs) or "field units consistent with key naming and magnitudes")


def run(rep: Report):
    for e in manifest()["datasets"]:
        ds_id = e["id"]
        ds = load(ds_id)
        src = ds_id.split(".")[0]
        check_dating(rep, ds_id, ds)
        check_units(rep, ds_id, ds)
        keys = [f["key"] for f in ds["fields"]]
        # manifest latest == file
        for ms in e["series"]:
            s = next(x for x in ds["series"] if x["key"] == ms["key"])
            for i, k in enumerate(keys, start=1):
                last = next(([r[0], r[i]] for r in reversed(s["data"]) if r[i] is not None), None)
                if ms["latest"].get(k) != last:
                    rep.add(ds_id, "meta", "FAIL", f"manifest latest {ms['key']}.{k} {ms['latest'].get(k)} != file {last}")
        if src == "yahoo":
            check_yahoo(rep, ds_id, ds)
            continue
        if ds["frequency"] == "D":
            check_daily_bde(rep, ds_id, ds)
            continue
        for s in ds["series"]:
            for k in keys:
                if k in LAG and (ds_id, k) not in OFFICIAL:
                    r = recompute_period(ds, s, k)
                    if r is None:
                        continue
                    pub, exp = r
                    if ds_id == "ine.business_confidence" and s["key"] != "ice":
                        continue
                    tol = 0.002 if k in ("yoy", "qoq", "mom") else 0.0002
                    if ds_id.startswith("bde.spread"):
                        tol = 0.0051
                    compare_maps(rep, ds_id, f"{s['key']}.{k}", pub, exp, tol)
                if k == "sum_12m":
                    vi, si = keys.index("value") + 1, keys.index("sum_12m") + 1
                    lvl = {r[0]: r[vi] for r in s["data"] if r[vi] is not None}
                    pub = {r[0]: r[si] for r in s["data"]}
                    exp = {}
                    for x in pub:
                        win = [lvl.get(add_months(x, -j)) for j in range(12)]
                        exp[x] = None if any(w is None for w in win) else sum(win)
                    compare_maps(rep, ds_id, f"{s['key']}.sum_12m", pub, exp, 0.01)
                if k == "index_2019q1":
                    vi, ii = keys.index("value") + 1, keys.index("index_2019q1") + 1
                    lvl = {r[0]: r[vi] for r in s["data"] if r[vi] is not None}
                    b = lvl.get("2019-01-01")
                    pub = {r[0]: r[ii] for r in s["data"]}
                    exp = {x: (lvl[x] / b * 100 if b and x in lvl else None) for x in pub}
                    compare_maps(rep, ds_id, f"{s['key']}.index_2019q1", pub, exp, 0.001)
                if k == "contribution" and "weight" in keys and "yoy" in keys:
                    yi, wi, ci = keys.index("yoy") + 1, keys.index("weight") + 1, keys.index("contribution") + 1
                    pub = {r[0]: r[ci] for r in s["data"]}
                    exp = {r[0]: (r[yi] * r[wi] / 100 if r[yi] is not None and r[wi] is not None else None) for r in s["data"]}
                    compare_maps(rep, ds_id, f"{s['key']}.contribution=yoy*weight", pub, exp, 0.0002)
    additivity(rep)
    bases(rep)


def bases(rep):
    """An index field whose note says 'Base YYYY = 100' must average ~100 over YYYY (where published)."""
    import re
    for e in manifest()["datasets"]:
        ds = load(e["id"])
        for fi, f in enumerate(ds["fields"], start=1):
            m = re.search(r"Base (\d{4}) = 100", f.get("note_es") or "")
            if not m or f["unit"] != "index":
                continue
            y = m.group(1)
            for s in ds["series"]:
                vals = [r[fi] for r in s["data"] if r[0].startswith(y) and r[fi] is not None]
                need = {"M": 12, "Q": 4, "A": 1}.get(ds["frequency"], 0)
                if len(vals) < need or not need:
                    rep.add(e["id"], "meta", "SKIP", f"{s['key']}: base year {y} not in published range")
                    continue
                avg = sum(vals) / len(vals)
                rep.add(e["id"], "meta", "PASS" if abs(avg - 100) < 0.5 else "FAIL",
                        f"{s['key']}.{f['key']}: mean over {y} = {avg:.2f} (note says Base {y} = 100)")


def check_daily_bde(rep, ds_id, ds):
    keys = [f["key"] for f in ds["fields"]]
    for s in ds["series"]:
        xs = [r[0] for r in s["data"] if r[1] is not None]
        vals = {r[0]: r[1] for r in s["data"] if r[1] is not None}
        for k in keys[1:]:
            fi = keys.index(k) + 1
            pub = {r[0]: r[fi] for r in s["data"]}
            exp = {}
            for x in pub:
                d = date.fromisoformat(x)
                if k == "chg_1m":
                    t = d - timedelta(days=30)
                elif k == "chg_ytd":
                    t = date(d.year - 1, 12, 31)
                elif k == "chg_1y":
                    try:
                        t = d.replace(year=d.year - 1)
                    except ValueError:
                        t = d.replace(year=d.year - 1, day=28)
                else:
                    continue
                p = asof(xs, vals, t.isoformat())
                exp[x] = None if p is None or vals.get(x) is None else vals[x] - p
            compare_maps(rep, ds_id, f"{s['key']}.{k}", pub, exp, 0.0002)


SESS = {"1d": 1, "1w": 5, "1m": 21}  # 1y is a calendar year (audit L3), handled below


def check_yahoo(rep, ds_id, ds):
    keys = [f["key"] for f in ds["fields"]]
    s = ds["series"][0]
    data = [r for r in s["data"] if r[1] is not None]
    xs = [r[0] for r in data]
    cl = [r[1] for r in data]
    for k in keys[1:]:
        fi = keys.index(k) + 1
        pub = {r[0]: r[fi] for r in data}
        exp = {}
        kind, win = k.split("_", 1)
        for j, x in enumerate(xs):
            if win in SESS:
                n = SESS[win]
                base = cl[j - n] if j - n >= 0 else None
            elif win == "1y":
                d = date.fromisoformat(x)
                try:
                    t = d.replace(year=d.year - 1)
                except ValueError:
                    t = d.replace(year=d.year - 1, day=28)
                base = asof(xs, dict(zip(xs, cl)), t.isoformat())
            elif win == "ytd":
                y = int(x[:4])
                prev = [i for i in range(j) if int(xs[i][:4]) == y - 1]
                base = cl[prev[-1]] if prev else None
            elif k == "sma_200":
                exp[x] = sum(cl[j - 199:j + 1]) / 200 if j >= 199 else None
                continue
            else:
                continue
            if base is None:
                exp[x] = None
            elif kind == "ret":
                exp[x] = (cl[j] / base - 1) * 100
            else:
                exp[x] = cl[j] - base
        # closes are stored with 4 decimals: allow the rounding error of the level
        tol = (0.002 + 100 * 1.0e-4 / min(abs(c) for c in cl)) if kind == "ret" else 0.0002
        if k == "sma_200":
            tol = 0.01
        compare_maps(rep, ds_id, f"{s['key']}.{k}", pub, exp, tol)


def additivity(rep):
    """CPI special-group contributions should add up to headline CPI inflation."""
    ds = load("ine.cpi_ecoicop_groups")
    ci = [f["key"] for f in ds["fields"]].index("contribution") + 1
    tot = {}
    for s in ds["series"]:
        for r in s["data"]:
            if r[ci] is not None:
                tot[r[0]] = tot.get(r[0], 0) + r[ci]
    head = {r[0]: r[1] for r in next(s for s in load("ine.cpi_special_groups")["series"] if s["key"] == "headline")["data"]}
    gaps = sorted(((abs(tot[x] - head[x]), x, tot[x], head[x]) for x in tot if x in head), reverse=True)
    if gaps:
        g, x, t, h = gaps[0]
        recent = [abs(tot[x] - head[x]) for x in sorted(tot)[-12:] if x in head]
        st = "FAIL" if max(recent) > 0.3 else ("WARN" if g > 0.15 else "PASS")
        rep.add("ine.cpi_ecoicop_groups", "transform", st,
                f"sum of contributions vs headline CPI yoy: max gap {g:.2f} pp at {x} ({t:.2f} vs {h}); last-12m max gap {max(recent):.2f} pp")
    # GDP demand contributions vs GDP yoy (same page)
    dd = load("ine.gdp_demand")
    s4 = {}
    for s in dd["series"]:
        for r in s["data"]:
            if r[1] is not None:
                s4[r[0]] = s4.get(r[0], 0) + r[1]
    gy = {r[0]: r[2] for r in load("ine.gdp")["series"][0]["data"] if r[2] is not None}
    gaps = [(abs(s4[x] - gy[x]), x, s4[x], gy[x]) for x in sorted(s4)[-8:] if x in gy]
    g, x, t, h = max(gaps)
    rep.add("ine.gdp_demand", "transform", "FAIL" if g > 0.3 else "PASS",
            f"sum of the 4 published contributions vs published GDP yoy, last 8 quarters: max gap {g:.2f} pp at {x} ({t:.2f} vs {h:.2f})")


if __name__ == "__main__":
    rep = Report()
    run(rep)
    rep.print()
    sys.exit(1 if rep.failed else 0)
