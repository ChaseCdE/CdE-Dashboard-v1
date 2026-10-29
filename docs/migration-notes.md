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
- `yahoo.spanish_banks_etf` was EWP (iShares MSCI Spain, whole market); the id is now `yahoo.msci_spain_etf` (audit L2, with `mercados.js`).
- Monthly charts can show an axis tick one month past the last observation (e.g. "ene 2027"); cosmetic.
- 375 px screenshots were checked only partially for some long pages (Actividad, Comparativa UE).

## 2026-10-28 Extension: new indicators and downloads

New datasets (20; 125 in total; strict validation clean). Detail in `docs/notes/ext-{ine,eurostat,bde}.md`.
- INE: `tourist_arrivals` (FRONTUR), `tourist_spending` (EGATUR), `hotel_overnight_stays`, `housing_transactions` (ETDP), `mortgages`, `companies` (created/dissolved), `household_saving_rate`, `population_nationality`. Insolvencies not available: INE discontinued the Estadística del Procedimiento Concursal after 2020.
- Eurostat: `gdp_per_capita_pps`, `labour_productivity_pps`, `rd_expenditure`, `youth_unemployment`, `long_term_unemployment`, `hicp_energy`.
- BdE: `npl_ratio`, `spread_10y_de`, `spread_10y_it`, `social_security_affiliates` (end of month, not monthly average), `registered_unemployment`, `government_debt_pde`.

Errors found and fixed:
- `bde.france_10y_bond` and `bde.italy_10y_bond` were Finland's and Portugal's series (D_1NBBO314, D_1NBBO316); now D_1NBBO303 (France) and D_1NBBO309 (Italy).
- Yield curve: the "more than 2 years" BdE aggregate was plotted as the 2-year point and created a false kink; removed from the curve.

Contract v1.2: optional `stale_after_days` per dataset (used for Eurostat R&D, published ~11 months after year end).

Pages: new **Empresas y turismo**; Actividad gains housing, mortgages and saving rate ("Consumo, hogares y vivienda"); Mercado laboral gains affiliation, registered unemployment and population by nationality; Crédito y tipos gains spreads, PDE debt and NPL ratio; Comparativa UE gains "Convergencia con Europa" and youth/long-term unemployment; Precios gains energy inflation; Portada KPIs now include affiliation, spread and tourist arrivals. Per-page notes: `docs/notes/p5-*.md`.

Factory (lead): download buttons on every chart and table card (PNG with title/units/source; CSV of the data shown, `;` and decimal comma); date axes end at the last observation; end-label margin sized to the label; horizontal bar rows sized to wrapped labels.

Lead re-test: 8 pages at 375 and 1440 px, 101 charts, 0 console errors, 0 failed requests, no overflow; downloads tested on 5 pages.

Declined: a line + bar combo chart with a secondary axis (style guide avoids dual axes).

## 2026-10-29 Longer history (+5 years)

Most series started in 2021 (5-year fetch windows) and BdE daily series in 2023 (36 months, the API maximum for daily data). Now about ten years:
- INE: larger `nult` for the series that started in 2020 or later (`src/fetchers/ine_series.py`); `business_confidence` from 2017.
- BdE: `HISTORY_YEARS = 10` (`src/fetchers/bde_indicators.py`). Monthly/quarterly series use `rango=MAX`, trimmed. Daily series use 36M plus the earlier calendar years (`rango=YYYY`), requested only from each series' `fechaInicio` (asking for a year before a series starts makes the API reject the whole batch with 412). Any missing piece keeps the previous file (H1).
- Yahoo: 10 years.
- `eurostat.gdp_index` and `ine.gdp_productivity`: from 2014 or the first available quarter; base still 2019Q1 = 100.
- Source limits, unchanged: €STR starts 2019-10; INE services by sector start 2022-01; `ine.cpi_weights` shows the current basket.

Check: 80 datasets extend further back; 0 previously published values changed; 13,307 previously empty values now filled (first-year rates, 12-month sums, moving averages). Audit oracle PASS 988, FAIL 0. `site/data` 3.2 MB → 6.2 MB (largest files: 10 years of daily index data, ~185 KB each).
