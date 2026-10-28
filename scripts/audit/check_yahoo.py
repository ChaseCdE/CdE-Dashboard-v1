"""
Independent check of every yahoo.* dataset against Yahoo Finance's chart API
(query1.finance.yahoo.com/v8/finance/chart), without yfinance.

identity: ticker metadata (longName/shortName, currency, instrument type) must be
          consistent with the published title and unit/currency.
values:   last ~24 sessions. Each session is dated on the exchange's local calendar
          date (timestamp converted with exchangeTimezoneName). The published close
          is compared with Yahoo's raw close and, for ETFs, with the dividend-adjusted
          close (yfinance's default auto_adjust=True publishes the adjusted series).
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, SESSION, http_json, load, manifest  # noqa: E402

API = "https://query1.finance.yahoo.com/v8/finance/chart/{}"

# id -> tokens expected in Yahoo longName/shortName (case-insensitive), expected currency or None
EXPECT = {
    "ibex_35": (["IBEX"], "EUR"), "euro_stoxx_50": (["STOXX 50"], "EUR"), "stoxx_600": (["600"], "EUR"),
    "sp_500": (["S&P 500"], "USD"), "nasdaq_composite": (["NASDAQ"], "USD"), "dax": (["DAX"], "EUR"),
    "cac_40": (["CAC 40"], "EUR"), "ftse_100": (["FTSE 100"], "GBP"), "vix": (["VOLATILITY"], "USD"),
    "eur_usd": (["EUR/USD"], "USD"), "eur_gbp": (["EUR/GBP"], "GBP"), "eur_jpy": (["EUR/JPY"], "JPY"),
    "eur_chf": (["EUR/CHF"], "CHF"), "gbp_usd": (["GBP/USD"], "USD"), "usd_jpy": (["USD/JPY"], "JPY"),
    "dxy": (["DOLLAR"], "USD"), "brent_crude": (["BRENT"], "USD"), "wti_crude": (["CRUDE"], "USD"),
    "natural_gas": (["NATURAL GAS"], "USD"), "gold": (["GOLD"], "USD"), "silver": (["SILVER"], "USD"),
    "us_tbill_3m": (["13 WEEK"], "USD"), "us_treasury_5y": (["5 YEAR"], "USD"),
    "us_treasury_10y": (["10 YEAR"], "USD"), "us_treasury_30y": (["30 YEAR"], "USD"),
    "euro_govt_bond_etf": (["GOVT BOND"], "EUR"), "us_treasury_20y_etf": (["20+"], "USD"),
    "us_treasury_7_10y_etf": (["7-10"], "USD"), "msci_spain_etf": (["MSCI SPAIN"], "USD"),
    "european_banks_etf": (["EUROPE FINANCIALS"], "USD"),
}


def fetch(ticker: str):
    j = http_json(API.format(ticker), {"range": "2y", "interval": "1d", "events": "div,split"})
    r = j["chart"]["result"][0]
    meta = r["meta"]
    tz = ZoneInfo(meta["exchangeTimezoneName"])
    q = r["indicators"]["quote"][0]
    adj = (r["indicators"].get("adjclose") or [{}])[0].get("adjclose")
    close, aclose = {}, {}
    today_local = datetime.now(tz).date().isoformat()
    for i, ts in enumerate(r.get("timestamp") or []):
        d = datetime.fromtimestamp(ts, timezone.utc).astimezone(tz).date().isoformat()
        if d >= today_local:
            continue  # session of today may still be open; the pipeline excludes it too
        if q["close"][i] is not None:
            close[d] = float(q["close"][i])
        if adj and adj[i] is not None:
            aclose[d] = float(adj[i])
    divs = sorted((r.get("events") or {}).get("dividends", {}).values(), key=lambda e: e["date"])
    return meta, close, aclose, divs


def run(rep: Report):
    ids = [e["id"] for e in manifest()["datasets"] if e["id"].startswith("yahoo.")]
    tick = {i: load(i)["source"]["dataset"] for i in ids}
    with ThreadPoolExecutor(max_workers=6) as ex:
        got = dict(zip(ids, ex.map(lambda i: fetch(tick[i]), ids)))
    for i in ids:
        ds = load(i)
        meta, close, aclose, divs = got[i]
        key = i.split(".", 1)[1]
        toks, cur = EXPECT.get(key, ([], None))
        name = f"{meta.get('longName', '')} / {meta.get('shortName', '')}"
        f0 = ds["fields"][0]
        probs = [t for t in toks if t.lower() not in name.lower()]
        if cur and meta.get("currency") != cur:
            probs.append(f"currency {meta.get('currency')} != {cur}")
        if f0["unit"] == "currency" and f0.get("currency") != meta.get("currency"):
            probs.append(f"field currency {f0.get('currency')} != Yahoo {meta.get('currency')}")
        rep.add(i, "identity", "FAIL" if probs else "PASS",
                f"{tick[i]}: {name} [{meta.get('currency')}, {meta.get('instrumentType')}, {meta.get('exchangeTimezoneName')}]"
                + (f" problems: {probs}" if probs else ""))
        pub = {r[0]: r[1] for r in ds["series"][0]["data"] if r[1] is not None}
        last = sorted(close)[-24:]
        raw = {k: close[k] for k in last}
        adjd = {k: aclose[k] for k in last if k in aclose}
        dec = 4
        r_raw = rep.compare(i, "values", pub, raw, tol=10 ** -dec * 1.01 + 1e-9 * max(raw.values()), label="close vs raw close")
        if r_raw.status == "FAIL" and adjd:
            r_adj = rep.compare(i, "values", pub, adjd, tol=10 ** -dec * 1.01 + 1e-9 * max(adjd.values()),
                                label="close vs dividend-adjusted close")
            if r_adj.status == "PASS":
                r_raw.status = "WARN"
                r_raw.detail += " -> published 'Cierre' is the dividend-adjusted close, not the traded price"
        if meta.get("instrumentType") == "ETF":
            # Over the whole 2-year window: is the published history the traded price or the adjusted one?
            full_raw = {k: v for k, v in close.items() if k in pub}
            full_adj = {k: v for k, v in aclose.items() if k in pub}
            off_raw = max((abs(pub[k] - v) for k, v in full_raw.items()), default=0)
            off_adj = max((abs(pub[k] - v) for k, v in full_adj.items()), default=0)
            st = "PASS" if off_raw < 1e-3 else "WARN"
            rep.add(i, "values", st, f"2y history: max |published - traded close| = {off_raw:.4f}, "
                    f"max |published - adjusted close| = {off_adj:.4f}; dividends in window: {len(divs)}"
                    + ("" if st == "PASS" else " -> 'Cierre' history is dividend-adjusted, not the traded price"))
        # Dating: no published date may fall on a weekend (UTC-shift symptom) and the
        # set of published dates in the window must equal Yahoo's local sessions.
        wk = [d for d in pub if datetime.fromisoformat(d).weekday() >= 5]
        missing = [d for d in last if d not in pub]
        extra = [d for d in pub if last and last[0] <= d <= last[-1] and d not in close]
        st = "FAIL" if (wk or missing or extra) else "PASS"
        rep.add(i, "dating", st, f"weekend dates={len(wk)} {wk[:2]} missing={missing[:3]} extra={extra[:3]}")
    return got


if __name__ == "__main__":
    rep = Report()
    run(rep)
    rep.print()
    sys.exit(1 if rep.failed else 0)
