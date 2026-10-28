# Pipeline optimisation report

Branch `opt/pipeline`. Scope: fetching and processing for INE, Eurostat, Banco de España (BdE) and Yahoo.
Rule: no published number changes except for the audit findings M2, M3, M4, M5, L2, L3, L4 (M1 is
delivered by the INE code pinning). Each fix is its own commit with before/after values.

## 1. Baseline vs after

Baseline = commit `8fb522f` (cold run, fresh `data/`). After = branch head. Same machine, same network, one run each
(`scripts/measure_source.py`; times vary by a second or two between runs). MB are decoded response bytes.
Peak memory is the cumulative process peak RSS.

| Source | Wall time fetch | Requests | MB downloaded | Raw MB on disk | Process time |
|---|---|---|---|---|---|
| INE | 28.4 s -> 4.0 s | 37 -> 175 | 48.5 -> 0.94 | 40.4 -> 1.06 | 6.2 s -> 1.0 s |
| Eurostat | 23.8 s -> 1.4 s | 100 -> 22 | 0.3 -> 0.2 | 0.21 -> 0.21 | 0.6 s -> 0.6 s |
| BdE | 17.1 s -> 1.2 s | 34 -> 3 | 0.62 -> 0.63 | 1.81 -> 1.85 | 1.6 s -> 1.8 s |
| Yahoo | 5.8 s -> 2.6 s | 31 -> 31 | 3.99 -> 3.99 | 5.68 -> 5.67 | 3.2 s -> 3.6 s |

INE has more requests because the 37 whole-table downloads (48 MB) became 175 single-series requests (0.9 MB, 4 in
parallel): requests are tiny, bytes fell 50x. Peak RSS per source: INE 170 -> 112 MB, others unchanged at 100-136 MB.

Whole pipeline, `run_pipeline.py` (fetch + process):

| | Baseline | After |
|---|---|---|
| Wall time | 89.1 s (without export) | 20.9 s (with export and validation) |
| Peak RSS | 174 MB | 144 MB |
| `data/raw` | 46 MB | 9 MB |

Simulated outage (`HTTPS_PROXY=http://127.0.0.1:9`, cached raw files present): exit code 3, all four sources `[WARN]`,
published from cache, 60 s for the whole pipeline (INE 24 s, Eurostat 22 s, BdE 11.5 s, Yahoo 8 s when run alone).
The H1 behaviour is unchanged: fetch failures are logged with the words the summary handler matches.

## 2. Changes

1. **Tools** (`scripts/measure_source.py`, `scripts/compare_outputs.py`): per-source measurement and a dataset-by-dataset
   output comparison (identical / identical on the overlap / differs, with max absolute difference).
2. **Imports**: every package is imported as `src.*` (the BdE, Eurostat and Yahoo scripts imported `fetchers.*` as top level
   and broke `smoke_test.py`).
3. **INE by stable code** (`src/fetchers/ine_series.py`, `ine_indicators.py`): 160 series (now 175 requests with the M2/M4
   additions) fetched with `DATOS_SERIE/{COD}?nult=N` instead of 37 whole tables. Each response is validated (COD matches,
   data not empty, expected name tokens). Any failure keeps the cached file and logs an error (exit 3). The processor picks
   series by code (`_pick`) and raises `SeriesNotFound`; all name regexes, `select_series` and "first match" code are gone (M1).
4. **Request layer** (`src/fetchers/http_session.py`): one pooled `requests.Session` per client, retries with backoff on
   429/5xx (honours Retry-After), default timeout (10 s connect, 60 s read), `CircuitBreaker` (8 consecutive failures, so an
   outage costs seconds, not minutes) and `map_bounded` (4 workers for INE, Eurostat, Yahoo; 2 for BdE). Fixed sleeps removed.
5. **Eurostat**: the `eurostat` package (which downloaded whole datasets, 100 requests) was replaced by the Statistics API
   (JSON-stat 2.0) with server-side filters and `sinceTimePeriod`: 22 requests. `eurostat==1.1.1` removed from
   `requirements.txt`; no dependency added.
6. **BdE**: series are requested 20 per `listaSeries` call, grouped by range (36M daily, 60M otherwise): 34 -> 3 requests.
7. **Yahoo**: 4 parallel symbols with retry; `auto_adjust=False` explicit.
8. **Raw writes only on change**, so cached files and CI cache stay stable; an empty or failed fetch never overwrites a cache.
9. **Shared helpers** (`src/processors/series_ops.py`): `value_months_earlier`, `pct_change_by_date`, `diff_by_date`,
   `sum_by_date` (vectorised, bit-identical to the old loop), `asof_values`, `pct_change_asof`, `diff_asof`. Used by the INE,
   BdE and Yahoo processors. `INEProcessor` loads each raw file once (`_raw` cache) and `process_ipri` and
   `process_population_age` are vectorised.
10. **Tests**: `python -m unittest discover -s tests -t .` (28 tests): series helpers, `map_bounded`, `CircuitBreaker`, session
    timeout/retry, INE `validate_series`, Eurostat `jsonstat_to_long`, `_pick` / `SeriesNotFound`, M5 input checks.
11. **Oracle** (`scripts/audit/*`): updated for M2, M3, M4, L2, L3. It does not import `src`.

## 3. Rejected options

| Option | Reason |
|---|---|
| `yf.download` batching for Yahoo | It is not a batch API: it runs the same 31 chart requests in threads. No gain over the bounded pool, and timezone handling would need re-verification. |
| Incremental Yahoo fetching with a revision window | The whole download is 4 MB. Split-adjusted history changes retroactively on splits, so a window cannot be shown to give identical output. |
| Incremental INE / Eurostat / BdE | After the changes a full refetch is 0.9 / 0.2 / 0.6 MB. Revisions can touch any period, so a window adds risk for no measurable gain. |
| Parquet for raw files | Raw INE is now 1 MB; the new dependency (pyarrow) is not justified by any measurement. |
| Higher concurrency | 4 workers already bring each source to a few seconds; BdE limited to 2 to stay polite. |
| `requests-cache` / HTTP caching | The pipeline wants fresh data; the CSV cache already serves outages. |

## 4. Equivalence evidence

Command: `python scripts/compare_outputs.py --golden-site $HOME/golden/site_data --site site/data --golden-processed $HOME/golden/processed --processed data/processed`
(full output in `docs/optimization/compare-vs-golden.txt`). Result at branch head: site 85 identical, 40 differ; processed CSV 144 identical,
42 differ. Every difference maps to a finding:

| Dataset(s) | Finding |
|---|---|
| ine.cpi, retail_sales, house_prices, industrial_production, services_production, tourist_arrivals, tourist_spending (+ `summary`) | M4 |
| ine.cpi_ecoicop_groups | M2 |
| bde.credit_households_total, bde.credit_nfc_total (+ `bde_summary`) | M3 |
| 31 yahoo datasets (`ret_1y`, `chg_1y` only) | L3 |
| yahoo.spanish_banks_etf -> yahoo.msci_spain_etf, `yahoo.market_summary`, manifest | L2 |

All Eurostat datasets, all other INE and BdE datasets are identical. Before each finding commit the comparison against the previous
output was 126/126 site files and 187/187 processed files identical (INE, Eurostat, BdE and Yahoo commits).
`scripts/audit/check_all.py`: PASS 981, SKIP 7, FAIL 0, WARN 4 (below). `validate_contract.py --strict`: 0 errors.
`smoke_test.py --run-processors`: passes. The run also contains whatever the sources published since the golden snapshot
(new observations count as "identical (overlap)").

## 5. Audit findings fixed

| Finding | Fix | Before -> after |
|---|---|---|
| M1 | INE series pinned by code, validated on download; 0 or ambiguous match raises. | No value change. |
| M2 | CPI group contribution uses INE's weight of each year (table 76161 and the previous-base weights); a year without weight raises. | Servicios 2024-03 weight 50.31 % -> 46.86 %; Alimentos 20.92 % -> 23.01 %; max weight change 11.9 pp (Servicios 2021); max contribution change 1.86 pp; gap between the sum of contributions and headline CPI 1.50 pp (2022-07) -> 1.12 pp (2023-03); last 12 months still 0.11 pp. |
| M3 | Option 1: BdE's published transaction-based year-on-year rates (BE 3.21 households total financing `DCF_M.N.ES.W0.S1M.S1.N.L.LE.FD.T._Z.XDC._T.M.V.TVA._T`; BE 3.20 NFC loans from credit institutions `DCF_M.N.ES.W0.S11.S1.N.L.LE.F4.T._Z.XDC._T.M.V.TVA._T`). The monthly change stays a stock change and is relabelled "Variación mensual del saldo". | Households yoy: Mar 3.88 -> 5.00, Apr 2.38 -> 5.16, Jun 0.79 -> 5.29, Jul 2.53 -> 5.22, Aug 2.47 -> 5.16 %. NFC: Mar 3.68 -> 3.95, Jul 4.54 -> 4.32, Aug 4.36 -> 4.19 %. 12 earlier months gain a value. |
| M4 | INE's published rates (IPC290750, ICM4079/4080, IPV1376, IPI15381, IPSS491, FREG321, FREG623). | cpi yoy: 48 values change (max 0.05); retail yoy 48 (max 0.05; 2026-03 4.35 -> 4.3), mom 59; house prices yoy 36; IPI mom 71 (2022-08 0.55 -> 0.5); services mom 66; arrivals yoy 114 (max 0.005); spending yoy 114 (max 0.066). |
| M5 | `gdp_productivity` raises if a file, column or the 2019Q1 base is missing. | No value change. |
| L2 | Id and path `spanish_banks_etf` -> `msci_spain_etf`; `mercados.js` updated. | Id, path, manifest only. |
| L3 | Yahoo `ret_1y` / `chg_1y` compare with the last close on or before the same date one year earlier. | Latest ret_1y: gold -1.53 -> 1.37; vix 6.70 -> 10.96; silver 12.23 -> 16.60; gbp_usd 2.48 -> 0.17; eur_usd -2.71 -> -3.94; nasdaq 14.11 -> 12.02; ibex 19.45 -> 19.75. |
| L4 | The dead "total" sector was dropped; the services total is already published as `services_production`. | No value change. |

## 6. Open issues

- `ine.cpi_ecoicop_groups`: contributions (annual weight x yoy) still miss the headline by up to 1.12 pp (2023-03). Exact additivity needs chain-linked weights.
- `ine.tourist_arrivals` / `tourist_spending`: INE publishes 2 decimals, the field displays 1 (oracle WARN, display only; `decimals` left unchanged to avoid a frontend change).
- `bde.yield_curve` text still mentions the dropped "más de 2 años" point (L1, not part of this pass).
- `services_production` has history before 2021-01 available from the series endpoint; the registry `since` keeps the published window.
- INE names the same code differently in the series and table endpoints; labels for the CPI groups are fixed by code (`CPI_GROUP_LABELS`).
- M3 households uses "total financing" (BE 3.21): BdE publishes no single rate for total household loans; its components (housing 4.1 %, consumer 12.4 %, other -0.1 %) are consistent with 5.2 %.
- CI (`refresh-data.yml`) was inferred, not run. It installs `requirements.txt` (no longer needs `eurostat`), restores `data/` and honours exit code 3. A cache restored from before this branch holds the old Yahoo file `spanish_banks_etf_raw.csv` (harmless) and old INE raw files: if the INE API is down on the first run, the processor raises `SeriesNotFound` for codes missing from those files instead of publishing wrong series.
