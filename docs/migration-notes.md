# Migration notes

Running log of findings and cross-workstream requests. Append; do not rewrite other agents' entries.
Format: `## <date> <phase/workstream>`, then findings. Requests to another workstream start with `REQUEST → ws/<name>:`.

## 2026-10-28 Phase 0

Pipeline: `python run_pipeline.py` completes, 4/4 fetch and 4/4 process, ~165 s. Smoke test passes, including `--run-processors`.

Fixed in Phase 0:
- HEAD b3a7e40 had `ine_processor.py` and `process_ine_data.py` truncated. Valid syntax, runtime AttributeError at the end of INE processing. Restored in 8e4f195.
- `requirements.txt` did not list `eurostat`. Because `src/fetchers/__init__.py` imports every client, this broke all four fetchers, not only Eurostat. Added; all deps pinned.

Data freshness after the 2026-10-28 run (latest observation):
- Monthly INE, BdE, Yahoo, most Eurostat: Sept/Oct 2026. OK.
- Quarterly series: Q2 2026 (dated 2026-04-01). OK, Q3 not yet published.
- Annual series (deficit, trade balance, part-time rate): 2025. OK.

REQUEST → ws/eurostat: HICP and core inflation (`hicp_*`, `core_inflation_*`) stop at 2025-12 while every other monthly series reaches 2026-09. Likely the 2026 HICP rebasing / ECOICOP 2 change froze the dataset code used in `eurostat_indicators.py`. Verify and repoint.

REQUEST → ws/ine: IPRI (`ipri.csv`) stops at 2026-02 and the raw fetch returned an empty frame ("Skipping save of empty DataFrame ... ipri_raw.csv"). Same pattern as the CPI/IPV base-2026 rebase fixed in a8579ab; probably needs a new table id. `population_age_raw.csv` also fetched empty.

REQUEST → ws/yahoo (PRIORITY): every European ticker is dated one day early. `yahoo_client.py:77` does `pd.to_datetime(df['date'], utc=True).dt.date`, which converts exchange-local midnight (CET/CEST) to the previous day in UTC. IBEX 35 has 252 rows dated Sunday and none dated Friday; EUR/USD also has Sunday rows; S&P 500 and Brent are unaffected. Consequences: Spain/Europe vs US comparisons are misaligned by one day, and `correlation_matrix.csv` and `stock_indices_comparison.csv` are computed on misaligned returns. Fix: take the date in the exchange's own timezone (drop `utc=True` and use `.dt.tz_localize(None)` before `.dt.date`, or equivalent), then rerun fetch. The contract requires local trading dates.

REQUEST → ws/yahoo: dead tickers, no data returned: `SPGB.L` (spain_govt_bond_etf), `IBGE.AS` (euro_govt_bond_etf), `^V2X` (vstoxx). Replace or drop. Also `fed_funds` uses `^IRX`, which is the 13-week T-bill, not Fed Funds: relabel or drop.

REQUEST → ws/eurostat, ws/bde: pandas FutureWarnings on `pct_change` default fill method (`eurostat_processor.py:110`, `bde_processor.py:138,151`). Pass `fill_method=None` explicitly and handle gaps deliberately; the implicit forward fill will change behaviour in pandas 3 and currently computes growth rates across missing periods.

Unused processed outputs: `cntr_employment.csv`, `population.csv`. Decide in Phase 2 whether they are exported.

## 2026-10-28 Phase 1

Contract v1.0 frozen (`docs/data-contract.md`). Exporter, validator and five sample datasets in place; `run_pipeline.py` exports and validates on every run.

Design decisions worth knowing before Phase 2/3:
- Page assignment moved out of the manifest (plan originally had it there). The frontend owns it via `docs/indicator-inventory.md`.
- The plan said "numbers unrounded"; the contract stores up to 4 decimals instead. Processor floats carry 15 digits of noise (e.g. 4.9160995012942355) that would only bloat files.
- The frontend may not compute economic quantities. Yahoo returns, moving averages and volatility are therefore exported as fields if a page needs them, not computed in JS. The Phase 1 `yahoo.ibex_35` sample exports only `close`.
- `ine.cpi` yoy is computed by `ine_processor.py` from the index, not taken from INE's published rate. For a base-2026 series this is fine within the table, but ws/ine should confirm it matches INE's published tasa anual for recent months.
- Validator correctly reports `eurostat.hicp` as stale (331 days). Expected until ws/eurostat repoints the dataset.
