"""
Independent check of every bde.* dataset against the Banco de España API
(https://app.bde.es/bierest/resources/srdatosapp/listaSeries).

identity: the BdE description (Spanish, long and short) must contain the tokens
          that define the series; the unit symbol must match the published scale.
values:   latest ~24 observations, published value * 10**scale == API value * unit factor.
Spreads and the yield curve are recomputed from the official component series.
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, add_months, http_json, load, series, series_keys  # noqa: E402

API = "https://app.bde.es/bierest/resources/srdatosapp/listaSeries"

# dataset -> (code, tokens in description, API unit symbol, factor so that API*factor = euros/persons/%)
SPEC = {
    "bde.euribor_12m_monthly": ("D_1NBAF472", ["Euribor a un año"], "%", 1, "M"),
    "bde.euribor_12m_daily": ("D_DNBAF172", ["Euribor a 12 meses"], "%", 1, "D"),
    "bde.euribor_6m_daily": ("D_DNBAE172", ["Euribor a 6 meses"], "%", 1, "D"),
    "bde.euribor_3m_daily": ("D_DNBAD172", ["Euribor a 3 meses"], "%", 1, "D"),
    "bde.euribor_1m_daily": ("D_DNBAC172", ["Euribor a 1 mes"], "%", 1, "D"),
    "bde.euribor_1w_daily": ("D_DNBAS172", ["1 semana", "Euríbor"], "%", 1, "D"),
    "bde.ester_daily": ("D_DNBAA572", ["STR", "1 día"], "%", 1, "D"),
    "bde.spain_10y_bond": ("D_G0B1F0ZP", ["obligaciones a 10 años"], "%", 1, "D"),
    "bde.spain_5y_bond": ("D_G0B1F0ZO", ["bonos a 5 años"], "%", 1, "D"),
    "bde.spain_3y_bond": ("D_G0B1F0ZN", ["bonos a 3 años"], "%", 1, "D"),
    "bde.spain_2y_bond": ("D_G0B1F0ZE", ["Más de 2 años"], "%", 1, "D"),
    "bde.spain_15y_bond": ("D_G0B1F0ZQ", ["obligaciones a 15 años"], "%", 1, "D"),
    "bde.spain_tbill_3m": ("D_DTES00B7", ["Letras del tesoro", "De 1 a 3 meses"], "%", 1, "D"),
    "bde.spain_tbill_6m": ("D_DTES00S7", ["letras a 6 meses"], "%", 1, "D"),
    "bde.spain_tbill_1y": ("D_DTES00U7", ["letras a 1 año"], "%", 1, "D"),
    "bde.spain_10y_bond_monthly": ("D_1NBBO320", ["España", "Rendimiento de la deuda pública", "Largo plazo"], "%", 1, "M"),
    "bde.germany_10y_bond": ("D_1NBBO308", ["Alemania", "Rendimiento de la deuda pública"], "%", 1, "M"),
    "bde.france_10y_bond": ("D_1NBBO303", ["Francia", "Rendimiento de la deuda pública"], "%", 1, "M"),
    "bde.italy_10y_bond": ("D_1NBBO309", ["Italia", "Rendimiento de la deuda pública"], "%", 1, "M"),
    "bde.mortgage_rate": ("DN_1TI2T0135", ["TEDR", "hogares e ISFLSH", "Vivienda", "Nuevas operaciones"], "%", 1, "M"),
    "bde.consumer_credit_rate": ("DN_1TI2T0138", ["TEDR", "hogares e ISFLSH", "Consumo", "Nuevas operaciones"], "%", 1, "M"),
    "bde.corporate_lending_rate": ("DN_1TI2T0144", ["TEDR", "SNF", "Nuevas operaciones"], "%", 1, "M"),
    "bde.household_deposit_rate": ("DN_1TI2T0024", ["Nuevas operaciones", "Hogares e ISFLSH", "Depósitos a plazo"], "%", 1, "M"),
    "bde.household_overnight_deposit_rate": ("DN_1TI1T0010", ["TEDR", "hogares e ISFLSH", "A la vista"], "%", 1, "M"),
    "bde.credit_households_total": ("DF_MESNAA20A1U62250Z01E", ["Préstamos y créditos", "hogares e ISFLSH"], "M  EUR", 1e6, "M"),
    "bde.credit_nfc_total": ("DF_MESNAA20A1U62240Z01E", ["créditos a SNF"], "mM &euro;", 1e9, "M"),
    "bde.household_debt_gdp": ("DMZ10S80ZH0_TPRPIB.Q", ["Deuda Hogares e ISFLSH", "PIB"], "%", 1, "Q"),
    "bde.nfc_debt_gdp": ("DMZ10S80ZN0_TPRPIB.Q", ["Deuda SNF", "PIB"], "%", 1, "Q"),
    "bde.current_account_balance": ("DEEM.N.ES.W1.S1.S1.T.B.CA._Z._Z._Z.EUR._T._X.N.ALL", ["Cuenta corriente", "Saldo", "Sin ajuste de estacionalidad"], "M  EUR", 1e6, "M"),
    "bde.tourism_receipts": ("DEEM.N.ES.W1.S1.S1.T.C.SD._Z._Z._Z.EUR._T._X.N.ALL", ["Turismo", "Ingresos"], "M  EUR", 1e6, "M"),
    # New business volumes (flows, original data). "Nuevas operaciones" total, which includes renegotiations;
    # "Importes totales estimados" separates them from the rates (TEDR) of the same table.
    "bde.new_housing_loans": ("DN_1TI2TIE96", ["Importes totales estimados", "HOGARES", "VIVIENDA", "NUEVAS OPERACIONES"], "M  EUR", 1e6, "M"),
    "bde.new_consumer_loans": ("DN_1TI2TIE99", ["Importes totales estimados", "HOGARES", "CONSUMO", "NUEVAS OPERACIONES"], "M  EUR", 1e6, "M"),
    "bde.new_corporate_loans": ("DN_1TI2TIE105", ["Importes totales estimados", "SOCIEDADES NO FINANCIERAS", "TOTAL", "NUEVAS OPERA"], "M  EUR", 1e6, "M"),
    "bde.npl_ratio": ("D_BEEA2020", ["créditos dudosos"], "%", 1, "M"),
    "bde.social_security_affiliates": ("DEPSEGS1AF_XRTODS.M", ["Afiliados a fin de mes", "Total regímenes"], None, 1, "M"),
    # BdE's symbol says "m pers." (thousands) but the values are persons (2.4 million).
    "bde.registered_unemployment": ("D_1JA0D000", ["Paro registrado"], "m pers.", 1, "M"),
    "bde.government_debt_pde": ("DMNPDE2010_P00000_PS_APU", ["Deuda PDE", "Total"], "K  EUR", 1e3, "M"),
}
GROWTH = {
    "bde.credit_households_total": "DCF_M.N.ES.W0.S1M.S1.N.L.LE.FD.T._Z.XDC._T.M.V.TVA._T",
    "bde.credit_nfc_total": "DCF_M.N.ES.W0.S11.S1.N.L.LE.F4.T._Z.XDC._T.M.V.TVA._T",
}
NEW_BUSINESS = ["bde.new_housing_loans", "bde.new_consumer_loans", "bde.new_corporate_loans"]
SPREADS = {"bde.spread_10y_de": ("D_1NBBO320", "D_1NBBO308"), "bde.spread_10y_it": ("D_1NBBO320", "D_1NBBO309")}
CURVE = {0.25: "D_DTES00B7", 0.5: "D_DTES00S7", 1.0: "D_DTES00U7", 3.0: "D_G0B1F0ZN", 5.0: "D_G0B1F0ZO",
         10.0: "D_G0B1F0ZP", 15.0: "D_G0B1F0ZQ"}


def bde_date(ts: str, freq: str) -> str:
    # Timestamps look like 2026-10-26T09:15:00Z (daily) or 2026-09-01T08:15:00Z (monthly):
    # the calendar part is the period / publication date in Madrid.
    d = ts[:10]
    if freq in ("M", "Q"):
        d = d[:8] + "01"
    return d


def fetch(code: str, freq: str):
    rango = "36M" if freq == "D" else "60M"
    j = http_json(API, {"idioma": "ES", "series": code, "rango": rango})[0]
    data = {}
    for t, v in zip(j.get("fechas") or [], j.get("valores") or []):
        if v is not None:
            data[bde_date(t, freq)] = float(v)
    meta = {"desc": f"{j.get('descripcion')} || {j.get('descripcionCorta')}", "unit": j.get("simbolo"),
            "freq": j.get("codFrecuencia")}
    return meta, data


def run(rep: Report):
    jobs = {ds: (c, f) for ds, (c, _, _, _, f) in SPEC.items()}
    with ThreadPoolExecutor(max_workers=6) as ex:
        got = dict(zip(jobs, ex.map(lambda k: fetch(*jobs[k]), jobs)))
    by_code = {SPEC[ds][0]: got[ds][1] for ds in got}

    for ds, (code, tokens, unit, factor, freq) in SPEC.items():
        meta, data = got[ds]
        miss = [t for t in tokens if t.lower() not in meta["desc"].lower()]
        if miss:
            rep.add(ds, "identity", "FAIL", f"{code}: description lacks {miss}: {meta['desc'][:160]}")
        elif unit is not None and meta["unit"] != unit:
            rep.add(ds, "identity", "FAIL", f"{code}: unit symbol {meta['unit']!r} != expected {unit!r}")
        elif meta["freq"] != freq or load(ds)["frequency"] != freq:
            rep.add(ds, "identity", "FAIL", f"{code}: frequency API {meta['freq']} site {load(ds)['frequency']} expected {freq}")
        else:
            rep.add(ds, "identity", "PASS", f"{code}: {meta['desc'].split('||')[-1].strip()[:90]}")
        f = load(ds)["fields"][0]
        scale = 10 ** f.get("scale", 0)
        pub = {k: v * scale for k, v in series(ds, load(ds)["series"][0]["key"], "value").items()}
        off = {k: v * factor for k, v in data.items()}
        tol = 1e-4 * max(1.0, factor)
        if ds == "bde.spain_10y_bond" or freq == "D":
            n = 24
        else:
            n = 24
        rep.compare(ds, "values", pub, off, tol=tol + 1e-9 * max(abs(v) for v in off.values()), label=f"{code}", last_n=n)

    # New business flows: each dataset is checked on its own against the official series.
    for ds in NEW_BUSINESS:
        code = SPEC[ds][0]
        d = load(ds)
        official_eur = {k: v * 1e6 for k, v in got[ds][1].items()}      # euros
        # keys / fields: part of the promise made to the page agents
        ok_keys = [x["key"] for x in d["fields"]] == ["value", "sum_12m", "yoy"] and series_keys(ds) == ["es"]
        ok_units = all(x["unit"] == "currency" and x["currency"] == "EUR" and x.get("scale") == 6
                       for x in d["fields"][:2]) and d["fields"][2]["unit"] == "pct_change"
        rep.add(ds, "contract", "PASS" if ok_keys and ok_units else "FAIL",
                f"series es; fields {[x['key'] for x in d['fields']]}; value/sum_12m EUR scale 6; yoy pct_change; no mom")
        # notes: original data, new business and not the outstanding stock
        bad = [x["key"] for x in d["fields"]
               if "Datos originales (sin corregir de estacionalidad)" not in (x.get("note_es") or "")
               or "nuevas operaciones" not in (x.get("note_es") or "").lower()
               or "saldo vivo" not in (x.get("note_es") or "").lower()]
        rep.add(ds, "notes", "FAIL" if bad else "PASS",
                f"fields without NSA / nuevas operaciones / saldo vivo statement: {bad}" if bad else "NSA + new business vs stock stated in every field")
        # 12-month sum: from the official months only where 12 consecutive months exist
        months = sorted(official_eur)
        exp_sum = {}
        for i in range(11, len(months)):
            win = months[i - 11:i + 1]
            if add_months(win[0], 11) == win[-1]:
                exp_sum[win[-1]] = sum(official_eur[m] for m in win)
        pub_sum = {k: v * 1e6 for k, v in series(ds, "es", "sum_12m").items()}
        rep.compare(ds, "sum_12m", pub_sum, exp_sum, tol=1e-6 * max(exp_sum.values()), label=f"{code} rolling 12m", last_n=36)
        # yoy: relative change of the monthly value vs the same month a year earlier
        exp_yoy = {m: (official_eur[m] / official_eur[add_months(m, -12)] - 1) * 100
                   for m in months if add_months(m, -12) in official_eur}
        rep.compare(ds, "yoy", series(ds, "es", "yoy"), exp_yoy, tol=1e-3, label=f"{code} value vs same month t-12", last_n=36)
        # ten years of history and null sum_12m only when fewer than 12 months precede
        first = min(series(ds, "es", "value"))
        span = (datetime.now(timezone.utc).year - int(first[:4])) * 12 + datetime.now(timezone.utc).month - int(first[5:7])
        rep.add(ds, "history", "PASS" if 118 <= span + 1 <= 124 else "FAIL", f"first month {first} ({span} months back)")

    # Audit M3: the credit "yoy" is BdE's published transaction-based growth rate (BE 3.20 / 3.21)
    for ds, code in GROWTH.items():
        _, gdata = fetch(code, "M")
        rep.compare(ds, "yoy vs BdE published growth rate", series(ds, "es", "yoy"), gdata, tol=0.005 + 1e-9, label=code, last_n=60)

    # Spreads: Spain minus peer, monthly Maastricht yields.
    for ds, (a, b) in SPREADS.items():
        A, B = by_code[a], by_code[b]
        off = {k: round(A[k] - B[k], 2) for k in A if k in B}
        rep.compare(ds, "values", series(ds, "es", "value"), off, tol=1e-6, label=f"{a} - {b}", last_n=24)
        if load(ds)["series"][0]["data"]:
            rep.add(ds, "identity", "PASS", f"{a} (España) minus {b}")

    # Yield curve: each point equals the official value at the as_of date.
    yc = load("bde.yield_curve")
    s = yc["series"][0]
    asof = s.get("as_of")
    bad = []
    for x, y in s["data"]:
        code = CURVE.get(x)
        if code is None:
            bad.append(f"unexpected maturity {x}")
            continue
        ds_daily = next(d for d, v in SPEC.items() if v[0] == code)
        ser = got[ds_daily][1]
        prior = [k for k in ser if k <= asof]
        v = ser[max(prior)] if prior else None
        if v is None or abs(v - y) > 1e-6:
            bad.append(f"{x}y: published {y} vs {code}@{asof} {v}")
    common_last = min(max(got[next(d for d, v in SPEC.items() if v[0] == c)][1]) for c in CURVE.values())
    if asof != common_last:
        bad.append(f"as_of {asof} != latest date common to all maturities {common_last}")
    rep.add("bde.yield_curve", "identity", "PASS" if sorted(x for x, _ in s["data"]) == sorted(CURVE) else "FAIL",
            "maturities 0.25/0.5/1/3/5/10/15 map to " + ", ".join(CURVE.values()))
    rep.add("bde.yield_curve", "values", "FAIL" if bad else "PASS",
            "; ".join(bad) or f"7 maturities equal official values at {asof}")
    desc = yc.get("description_es", "") + " " + yc["source"]["dataset"]
    rep.add("bde.yield_curve", "meta", "WARN" if ("2 años" in desc or "G0B1F0ZE" in desc) else "PASS",
            "description/source still mention the dropped 'más de 2 años' series" if ("2 años" in desc or "G0B1F0ZE" in desc) else "ok")
    return got


if __name__ == "__main__":
    rep = Report()
    run(rep)
    rep.print()
    sys.exit(1 if rep.failed else 0)
