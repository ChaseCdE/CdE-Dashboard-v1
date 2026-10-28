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

## 2026-10-28 Phases 2 and 3 (merged into main)

Per-workstream detail: `docs/notes/ws-{ine,eurostat,bde,yahoo,frontend}.md`.

Result: 105 datasets (INE 28, Eurostat 16, BdE 31, Yahoo 30), `validate_contract.py --strict` 0 errors, 0 warnings. Site renders with real data at 375 and 1440 px, no console errors.

Errors in the old dashboard found and fixed:
- Yahoo: European tickers dated one day early (UTC conversion). Fixed; no weekend rows remain.
- Eurostat: trade balance summed food and drink (SITC 0+1) only, not total trade. Now total trade, monthly (`ext_st_27_2020msbec`).
- Eurostat: HICP and core inflation frozen at 2025-12 (`prc_hicp_manr` discontinued with ECOICOP 2). Now `prc_hicp_minr`, full history, max 0.1 pp difference on overlap.
- INE: retail sales were the "empresas unilocalizadas" subset, not the national total (Aug 2026 yoy +1.0 % vs +0.2 % shown before).
- INE: part-time rate used an annual table, so its "yoy" was a 4-year change.
- INE: business confidence was never fetched by `fetch_all`.
- INE: IPRI and population tables renamed series; repointed.
- BdE: daily yoy assumed 252 rows = 1 year; now date-based.
- All sources: growth rates no longer forward-fill across gaps (`fill_method=None`, date-based comparisons).
- Rates: year-on-year change of a rate (unemployment, debt/GDP) was a relative % change; now a difference in pp.
- Yahoo: dead tickers dropped (SPGB.L, ^V2X); IBGE.AS → EUNH.DE; `fed_funds` (actually ^IRX) renamed `us_tbill_3m`.

Lead decisions at merge:
- Contract v1.1: field-key rules enforced by the validator (`yoy/qoq/mom/ret_*` = % change; `*_pp`, `chg_*` = pp; `*_diff` = own unit); staleness measured from period end (v1.0 flagged every quarterly series between releases); frontend may rebase to a fixed reference period.
- Harmonised keys: Eurostat rate changes `yoy` → `yoy_pp`, consumer confidence `yoy` → `yoy_diff`; BdE `change` → `mom_pp`/`qoq_pp`, `change_30d/ytd/1y` → `chg_1m/chg_ytd/chg_1y`; Yahoo yields get `chg_*` (pp) instead of `ret_*` (a yield going from 4,0 % to 4,2 % is +0,2 p. p., not +5 %).
- Inventory reconciled with the export (table at the end of `docs/indicator-inventory.md`). Spain − EU27 gap charts are not exported; Phase 4 shows both lines.

Open for the project lead:
- Consumo as its own page or merged into Actividad (frontend notes argue both).
- Beige `#C2AE93` has 2.2:1 contrast on white: fine for lines/areas next to navy, not for text. See `docs/style-guide.md`.
- CCAA: bar chart instead of a map (`plotly-basic` has no maps).
- `ine.cpi_ecoicop_groups` contributions use current weights for the whole history (INE API returns only the current year's weights).
- `bde.spain_2y_bond` is "more than 2 years" and `bde.spain_tbill_3m` is "1 to 3 months" (BdE series definitions): loose proxies on the yield curve.

Operational:
- On the linked computer's workspace, background processes die when the shell call ends. Run the pipeline in the foreground, by source if needed (all four sources take ~100 s).

## 2026-10-28 Phases 4, 5 and 6

Decisions (project lead): Consumo merged into Actividad ("Consumo y hogares"). Defaults taken without objection: Spain vs EU-27 as two lines (no gap series); CCAA as bars (no map); beige for lines/areas only; FRED out of v1.

Phase 4: 7 pages (Portada, Actividad, Precios, Mercado laboral, Crédito y tipos, Mercados, Comparativa UE), 7 Sonnet agents in parallel; per-page notes in `docs/notes/p4-*.md`. Lead re-test after the factory changes below: all 7 pages at 375 and 1440 px, 0 console errors, 0 failed requests, no overflow, no error cards (6 + 15 + 11 + 8 + 8 + 11 + 21 = 80 charts).

Factory changes by the lead (from page-agent requests):
- `lineChart`: `rebase: {year}` / `{date}` (display-only, contract v1.1) and per-toggle `ref` / `rebase`.
- Reference-line labels get a background so they stay legible over bars.
- `groupedBarChart`: bars centred when each category has one bar (overlay mode); long horizontal labels wrap; fewer value ticks.
- KPI values: number and magnitude stay together but the noun can wrap ("22,9 M" / "personas"); smaller KPI font under 420 px.

Phase 5: `.github/workflows/refresh-data.yml` (weekdays 12:23 UTC, Actions cache of `data/` as fallback, validation report in the run summary, commit `site/data`, then deploy) and `deploy.yml` (Pages; excludes `site/dev/`). Setup steps for the repository owner in `docs/deploy.md`. Not yet run: needs a push and Pages enabled.

Phase 6: removed `src/app/` (Shiny), `serve.py`, `src/scripts/run_dashboard.py`, `.env.example`, `docs/sharing-setup.md`, `layout.md`, `content.md`, the old white logo; `run_pipeline.py --serve*` removed; `requirements.txt` without shiny/shinywidgets/plotly/uvicorn, verified in a fresh environment (smoke test with processors, export, validation). New `README.md`, rewritten `claude.md`. The local `.env` (old Basic Auth credentials, untracked) is left for the owner to delete.

Data observations (not bugs):
- `bde.credit_households_total`: the BdE stock (not seasonally adjusted) jumps ~2 % every June and November and reverses the next month; in June 2026 the jump did not happen, so yoy dips to 0,8 % for one month. Source behaviour.
- Germany/France/Italy 10Y yields end in different months (BdE publication), so the 10Y chart lines end at different dates.

Backlog:
- `latestTable` with a per-row field, so BdE (`value`) and Yahoo (`close`) rates fit one table (Mercados currently shows two tables; Comparativa UE has no cross-indicator summary table).
- `yahoo.spanish_banks_etf` is EWP (iShares MSCI Spain, whole market): rename the id to `yahoo.msci_spain_etf` together with `mercados.js`.
- Monthly charts can show an axis tick one month past the last observation (e.g. "ene 2027"); cosmetic.
- 375 px screenshots were checked only partially for some long pages (Actividad, Comparativa UE).
