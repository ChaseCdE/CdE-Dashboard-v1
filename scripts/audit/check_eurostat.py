"""
Independent check of every eurostat.* dataset against the Eurostat dissemination
API (JSON-stat 2.0). Every dimension except geo and time is pinned explicitly; a
response with more than one category in any other dimension is an identity FAIL
(an unpinned dimension means the pipeline may have picked an arbitrary slice).

Value fields are compared with the API on the latest ~24 periods; `yoy` / `*_pp`
/ `*_diff` fields that the pipeline computes are recomputed here from the API
levels (date-based: same period one year earlier; null if that period is missing).
"""
from __future__ import annotations

import itertools
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, add_months, http_json, load, series, series_keys  # noqa: E402

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{}"
GEO = {"es": "ES", "eu27": "EU27_2020", "de": "DE", "fr": "FR", "it": "IT", "pt": "PT"}

# dataset -> (eurostat code, pinned filters, mapping field -> how)
#   how = "value"        field equals API value
#   how = "yoy_rel"      field = % change of API value vs one year earlier
#   how = "yoy_diff"     field = API value minus value one year earlier
#   how = "rebase:YYYY-MM-DD" field = 100 * value / value(at date)
SPEC = {
    "eurostat.gdp_growth": ("namq_10_gdp", {"unit": "CLV_PCH_PRE", "s_adj": "SCA", "na_item": "B1GQ"}, {"qoq": "value"}),
    "eurostat.gdp_index": ("namq_10_gdp", {"unit": "CLV10_MNAC", "s_adj": "SCA", "na_item": "B1GQ"}, {"value": "rebase:2019-01-01"}),
    "eurostat.industrial_production": ("sts_inpr_m", {"indic_bt": "PRD", "nace_r2": "B-D", "s_adj": "SCA", "unit": "I21"}, {"value": "value", "yoy": "yoy_rel"}),
    "eurostat.economic_sentiment": ("ei_bssi_m_r2", {"indic": "BS-ESI-I", "s_adj": "SA"}, {"value": "value", "yoy": "yoy_rel"}),
    # Headline harmonised unemployment rate = age TOTAL (15-74). The site title presents it as "Tasa de paro".
    "eurostat.unemployment": ("une_rt_m", {"age": "TOTAL", "unit": "PC_ACT", "s_adj": "SA", "sex": "T"}, {"value": "value", "yoy_pp": "yoy_diff"}),
    "eurostat.employment_growth": ("namq_10_a10_e", {"unit": "PCH_PRE_PER", "s_adj": "SCA", "nace_r2": "TOTAL", "na_item": "EMP_DC"}, {"qoq": "value"}),
    "eurostat.labor_participation": ("lfsi_emp_q", {"unit": "PC_POP", "s_adj": "SA", "sex": "T", "age": "Y15-64", "indic_em": "ACT"}, {"value": "value", "yoy_pp": "yoy_diff"}),
    "eurostat.hicp": ("prc_hicp_minr", {"coicop18": "TOTAL", "unit": "RCH_A"}, {"yoy": "value"}),
    "eurostat.core_inflation": ("prc_hicp_minr", {"coicop18": "TOT_X_NRG_FOOD", "unit": "RCH_A"}, {"yoy": "value"}),
    "eurostat.hicp_energy": ("prc_hicp_minr", {"coicop18": "NRG", "unit": "RCH_A"}, {"yoy": "value"}),
    "eurostat.producer_prices": ("sts_inppd_m", {"indic_bt": "PRC_PRR_DOM", "nace_r2": "B-D", "s_adj": "NSA", "unit": "I21"}, {"value": "value", "yoy": "yoy_rel"}),
    "eurostat.government_debt": ("gov_10q_ggdebt", {"unit": "PC_GDP", "na_item": "GD", "sector": "S13"}, {"value": "value", "yoy_pp": "yoy_diff"}),
    "eurostat.budget_deficit": ("gov_10dd_edpt1", {"unit": "PC_GDP", "na_item": "B9", "sector": "S13"}, {"value": "value"}),
    "eurostat.consumer_confidence": ("ei_bsco_m", {"indic": "BS-CSMCI", "s_adj": "SA", "unit": "BAL"}, {"value": "value", "yoy_diff": "yoy_diff"}),
    "eurostat.retail_trade": ("sts_trtu_m", {"indic_bt": "VOL_SLS", "nace_r2": "G47", "s_adj": "SCA", "unit": "I21"}, {"value": "value", "yoy": "yoy_rel"}),
    "eurostat.house_prices": ("prc_hpi_q", {"purchase": "TOTAL", "unit": "I15_Q"}, {"value": "value", "yoy": "yoy_rel"}),
    "eurostat.gdp_per_capita_pps": ("nama_10_pc", {"unit": "PC_EU27_2020_HAB_MPPS_CP", "na_item": "B1GQ"}, {"value": "value"}),
    "eurostat.labour_productivity_pps": ("tesem160", {"unit": "PC_EU27_2020_MPPS_CP", "na_item": "NLPR_HW"}, {"value": "value"}),
    "eurostat.rd_expenditure": ("rd_e_gerdtot", {"sectperf": "TOTAL", "unit": "PC_GDP"}, {"value": "value"}),
    "eurostat.youth_unemployment": ("une_rt_m", {"age": "Y_LT25", "unit": "PC_ACT", "s_adj": "SA", "sex": "T"}, {"value": "value", "yoy_pp": "yoy_diff"}),
    "eurostat.long_term_unemployment": ("une_ltu_q", {"indic_em": "LTU", "age": "Y15-74", "unit": "PC_ACT", "s_adj": "SA", "sex": "T"}, {"value": "value", "yoy_pp": "yoy_diff"}),
}
# Seasonal-adjustment pass: TRD_VAL (unadjusted) -> TRD_VAL_SCA (seasonally and calendar adjusted).
TRADE = ("ext_st_27_2020msbec", {"partner": "WORLD", "bclas_bec": "TOTAL", "indic_et": "TRD_VAL_SCA"})


def period_to_date(p: str) -> str:
    if "-Q" in p:
        y, q = p.split("-Q")
        return f"{y}-{3 * (int(q) - 1) + 1:02d}-01"
    if len(p) == 7:
        return p + "-01"
    if len(p) == 4:
        return p + "-01-01"
    raise ValueError(p)


def fetch(code: str, filters: dict, geos: list, since: str = "2015"):
    params = [("format", "JSON"), ("lang", "EN"), ("sinceTimePeriod", since)]
    for k, v in filters.items():
        for x in (v if isinstance(v, list) else [v]):
            params.append((k, x))
    for g in geos:
        params.append(("geo", g))
    j = http_json(API.format(code), dict_params(params))
    ids, sizes = j["id"], j["size"]
    cats = {d: j["dimension"][d]["category"] for d in ids}
    order = {d: sorted(cats[d]["index"], key=lambda k: cats[d]["index"][k]) for d in ids}
    labels = {d: {k: cats[d].get("label", {}).get(k, k) for k in order[d]} for d in ids}
    out = {}
    vals = j.get("value", {})
    for flat, combo in enumerate(itertools.product(*[order[d] for d in ids])):
        v = vals.get(str(flat)) if isinstance(vals, dict) else vals[flat]
        if v is None:
            continue
        c = dict(zip(ids, combo))
        key = tuple(c[d] for d in ids if d not in ("geo", "time", "freq"))
        out.setdefault(key, {}).setdefault(c["geo"], {})[period_to_date(c["time"])] = float(v)
    return {"ids": ids, "sizes": dict(zip(ids, sizes)), "labels": labels, "data": out}


def dict_params(pairs):
    # requests accepts a list of tuples for repeated keys
    return pairs


def yoy_rel(d: dict) -> dict:
    return {k: (v / d[add_months(k, -12)] - 1) * 100 for k, v in d.items() if add_months(k, -12) in d and d[add_months(k, -12)]}


def yoy_diff(d: dict) -> dict:
    return {k: v - d[add_months(k, -12)] for k, v in d.items() if add_months(k, -12) in d}


def run(rep: Report):
    jobs = {}
    for ds, (code, flt, _) in SPEC.items():
        geos = [GEO[k] for k in series_keys(ds)]
        jobs[ds] = (code, flt, geos)
    jobs["eurostat.trade_balance"] = (TRADE[0], {**TRADE[1], "stk_flow": ["EXP", "IMP"]}, ["ES"])
    with ThreadPoolExecutor(max_workers=6) as ex:
        got = dict(zip(jobs, ex.map(lambda k: fetch(*jobs[k]), jobs)))

    for ds, (code, flt, fields) in SPEC.items():
        r = got[ds]
        extra = [d for d, s in r["sizes"].items() if d not in ("geo", "time") and s != 1]
        pinned = ", ".join(f"{d}={list(r['labels'][d].values())[0]}" for d in r["ids"] if d not in ("geo", "time", "freq"))
        if extra:
            rep.add(ds, "identity", "FAIL", f"{code}: dimensions not pinned to one category: {extra}")
        else:
            rep.add(ds, "identity", "PASS", f"{code}: {pinned}"[:200])
        (slice_,) = r["data"].keys() if len(r["data"]) == 1 else (None,)
        if slice_ is None:
            rep.add(ds, "values", "FAIL", "no data / ambiguous slice")
            continue
        for skey in series_keys(ds):
            geo = GEO[skey]
            lvl = r["data"][slice_].get(geo, {})
            for fkey, how in fields.items():
                pub = series(ds, skey, fkey)
                if how == "value":
                    off, tol, chk = lvl, 1e-4, "values"
                elif how == "yoy_rel":
                    off, tol, chk = yoy_rel(lvl), 0.01, "transform"
                elif how == "yoy_diff":
                    off, tol, chk = yoy_diff(lvl), 1e-3, "transform"
                elif how.startswith("rebase:"):
                    base = lvl.get(how.split(":")[1])
                    off = {k: 100 * v / base for k, v in lvl.items()} if base else {}
                    tol, chk = 0.006, "transform"
                rep.compare(ds, chk, pub, off, tol=tol, label=f"{skey}.{fkey} ({geo})", last_n=24)

    # Trade: exports, imports, balance = exports - imports (million EUR).
    ds = "eurostat.trade_balance"
    r = got[ds]
    flows = {k[r['ids'].index('stk_flow') - 0] if False else k: v for k, v in r["data"].items()}
    ex_ = next(v for k, v in r["data"].items() if "EXP" in k)["ES"]
    im_ = next(v for k, v in r["data"].items() if "IMP" in k)["ES"]
    pinned = ", ".join(f"{d}={'/'.join(r['labels'][d].values())}" for d in r["ids"] if d not in ("geo", "time", "freq"))
    sca = "seasonally and calendar adjusted" in r["labels"]["indic_et"].get("TRD_VAL_SCA", "").lower()
    rep.add(ds, "identity", "PASS" if sca and r["labels"]["bclas_bec"].get("TOTAL") == "Total" and r["labels"]["partner"].get("WORLD") else "FAIL", pinned[:200])
    rep.compare(ds, "values", series(ds, "es", "exports"), ex_, 1e-4, "exports", last_n=24)
    rep.compare(ds, "values", series(ds, "es", "imports"), im_, 1e-4, "imports", last_n=24)
    rep.compare(ds, "transform", series(ds, "es", "balance"), {k: ex_[k] - im_[k] for k in ex_ if k in im_}, 1e-3, "balance=exp-imp", last_n=24)
    return got


if __name__ == "__main__":
    rep = Report()
    run(rep)
    rep.print()
    sys.exit(1 if rep.failed else 0)
