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

REQUEST → ws/yahoo: dead tickers, no data returned: `SPGB.L` (spain_govt_bond_etf), `IBGE.AS` (euro_govt_bond_etf), `^V2X` (vstoxx). Replace or drop. Also `fed_funds` uses `^IRX`, which is the 13-week T-bill, not Fed Funds: relabel or drop.

REQUEST → ws/eurostat, ws/bde: pandas FutureWarnings on `pct_change` default fill method (`eurostat_processor.py:110`, `bde_processor.py:138,151`). Pass `fill_method=None` explicitly and handle gaps deliberately; the implicit forward fill will change behaviour in pandas 3 and currently computes growth rates across missing periods.

Unused processed outputs: `cntr_employment.csv`, `population.csv`. Decide in Phase 2 whether they are exported.
