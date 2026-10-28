# ws/eurostat notes (Phase 2)

Branch `ws/eurostat`. Run on 2026-10-28.

## Datasets

All `site/data/eurostat/*.json`. Series `es` = España, `eu27` = UE-27. Fields: see the unit rules below the table.

| id | title_es | frequency | fields | series | last_observation |
|---|---|---|---|---|---|
| eurostat.gdp_growth | Crecimiento del PIB (trimestral) | Q | qoq | es, eu27 | 2026-04-01 |
| eurostat.gdp_index | PIB real, comparación entre países | Q | value (1T 2019 = 100) | es, eu27, de, fr, it | 2026-04-01 |
| eurostat.industrial_production | Producción industrial | M | value (2021 = 100), yoy | es, eu27 | 2026-08-01 |
| eurostat.economic_sentiment | Indicador de sentimiento económico | M | value, yoy | es, eu27 | 2026-09-01 |
| eurostat.unemployment | Tasa de paro (Eurostat) | M | value, yoy (pp) | es, eu27 | 2026-08-01 |
| eurostat.employment_growth | Crecimiento del empleo (trimestral) | Q | qoq | es, eu27 | 2026-04-01 |
| eurostat.labor_participation | Tasa de actividad | Q | value, yoy (pp) | es, eu27 | 2026-04-01 |
| eurostat.hicp | Inflación armonizada (IPCA) | M | yoy | es, eu27 | 2026-09-01 |
| eurostat.core_inflation | Inflación subyacente (IPCA sin energía ni alimentos) | M | yoy | es, eu27 | 2026-09-01 |
| eurostat.producer_prices | Precios industriales (mercado interior) | M | value (2021 = 100, NSA), yoy | es, eu27 | 2026-09-01 (UE-27: 2026-08-01) |
| eurostat.trade_balance | Comercio exterior de bienes de España | M | balance, exports, imports (EUR, scale 6) | es | 2026-08-01 |
| eurostat.government_debt | Deuda pública (% del PIB) | Q | value, yoy (pp) | es, eu27 | 2026-04-01 |
| eurostat.budget_deficit | Déficit público (% del PIB) | A | value | es, eu27 | 2025-01-01 |
| eurostat.consumer_confidence | Confianza del consumidor | M | value, yoy (points) | es, eu27 | 2026-09-01 |
| eurostat.retail_trade | Comercio minorista | M | value (2021 = 100), yoy | es, eu27 | 2026-08-01 |
| eurostat.house_prices | Precios de la vivienda | Q | value (2015 = 100), yoy | es, eu27 | 2026-04-01 |

Field conventions
- `yoy` on indices (IPI, PPI, retail, house prices, ESI): % change on the same period a year earlier (`pct_change`).
- `yoy` on rates and balances (unemployment, participation, debt/GDP): difference with a year earlier, unit `pp`; consumer confidence: unit `points`.
- HICP and core inflation: the Eurostat value already is the annual rate, so the only field is `yoy`.
- `gdp_growth` and `employment_growth` export `qoq` only. The old `yoy_change` on a quarterly growth rate (difference or ratio of two growth rates) was not an economic quantity and is no longer produced.
- Periods on the first day (quarter 2 2026 = 2026-04-01, year 2025 = 2025-01-01).

## HICP and core inflation: what replaced `prc_hicp_manr`

Eurostat moved the HICP to ECOICOP ver. 2 in 2026. The old tables (`prc_hicp_manr`, `prc_hicp_midx`, ...) are archived and frozen at 2025-12 (TOC: last update 2026-02-06). The successor is `prc_hicp_minr` (indices and rates of change, monthly). Differences for the fetcher: the classification dimension is `coicop18` (not `coicop`), all-items is `TOTAL` (was `CP00`), core is still `TOT_X_NRG_FOOD`. Units unchanged (`RCH_A`).

Handling of the break
- `prc_hicp_minr` already contains the full history back to 1996 on the new classification (Eurostat recomputed it), so there is no splice: the whole series comes from one table and is internally consistent.
- Checked against the cached old series: 264 overlapping observations per series (2015-01 to 2025-12, Spain and EU27), all values equal except differences of at most 0.1 pp (7 of 264 for HICP, 8 of 264 for core), i.e. rounding and minor revisions. Overlap values 2025-08..12 are identical to the previous export.
- Latest values (2026-09): HICP España 5.0, UE-27 3.8; core España 3.5, UE-27 2.7. Checked against the Eurostat dissemination API (same numbers).
- Because the history is rebuilt, the exported series from 2015 can differ by 0.1 pp in a handful of months from what the old dashboard showed. This is expected.

## Other fixes

- `pct_change` with the implicit forward-fill (`eurostat_processor.py`): replaced. `_calculate_yoy_change` now compares each date with the same date one year earlier (calendar lookup, no forward fill). A missing period gives NaN rather than a growth rate against a wrong period. No `pct_change` call remains. The previous code also produced yoy for rows whose value was NaN (the latest placeholder month), which showed up as rows with a yoy but no level.
- Placeholder periods with no value (Eurostat lists the next month for some series) are dropped on load, so `last_observation` is the last real observation.
- Trade balance was wrong: `ext_lt_intratrd` has a `sitc06` dimension that was not filtered, and the processor took `first` over product groups, so the exported "balance, exports, imports" were the food and drink group (SITC 0+1), not total trade. Replaced with the monthly `ext_st_27_2020msbec` (Spain, partner WORLD, BEC total, `TRD_VAL`, million EUR, not seasonally adjusted); balance = exports - imports. Annual sums of the monthly series equal the old annual totals (2015: exports 254,599.4, imports 281,221.9 vs 281,222.1; rounding). This changes the frequency from annual to monthly, which also fixes its staleness.
- Rates and balances now use a difference in pp for yoy instead of a percent change of a percent (unemployment, participation, debt/GDP, consumer confidence). Consumer confidence yoy had values like 422 percent because the balance crosses zero.
- Fetch script now prints the latest observation per indicator, so a frozen table is visible in the log.
- `data_sources_eurostat.md` updated (dataset codes, filters).

## Staleness (`validate_contract.py --strict`)

Seven warnings remain under `eurostat/*`; none can be fixed on our side.

| dataset | last obs | age | limit | explanation |
|---|---|---|---|---|
| gdp_growth, gdp_index | 2026-04-01 (2T 2026) | 210 d | 200 | 3T 2026 not yet published (Eurostat `namq_10_gdp`, updated 2026-10-26, last period 2026-Q2) |
| employment_growth | 2026-04-01 | 210 d | 200 | 3T has an empty slot in `namq_10_a10_e`; no value yet |
| labor_participation | 2026-04-01 | 210 d | 200 | `lfsi_emp_q` ends 2026-Q2 |
| government_debt | 2026-04-01 | 210 d | 200 | `gov_10q_ggdebt` ends 2026-Q2 (updated 2026-10-21) |
| house_prices | 2026-04-01 | 210 d | 200 | `prc_hpi_q` ends 2026-Q2 (updated 2026-10-01) |
| budget_deficit | 2025-01-01 (2025) | 665 d | 550 | 2025 is the latest year in `gov_10dd_edpt1` (updated 2026-10-21); 2026 appears in 2027 |

Cause: the contract dates a period on its first day and warns at 200 days for Q and 550 for A, but Eurostat publishes quarterly aggregates about 100 to 130 days after the quarter ends (190 to 225 days after its first day), and the annual deficit about 10 months after year end (up to about 640 days after 1 January). Every Q series will warn each quarter in the weeks before the next release, and the annual deficit warns for about 9 months a year. These are false positives for a healthy pipeline.

REQUEST → ws/lead: either widen the thresholds in `scripts/validate_contract.py` (suggested: Q 240 days, A 700 days) or measure staleness against the end of the period; or accept these seven warnings for Eurostat. I did not edit the validator.

The quarterly deficit alternative (`gov_10q_ggnfa`) was considered and rejected: the quarterly B9 ratio is not comparable with the annual EDP figure.

## Decisions

- One dataset per indicator, ids as specified; dataset codes in the export are read from `DATASET_CODES` in the fetcher so they cannot drift.
- `trade_balance` moved to monthly (see above) instead of keeping the broken annual one. If the frontend wants annual bars it has to take them from a pipeline field; none is exported.
- Not exported: `summary.csv` (internal KPI helper of the old app), `*_spain.csv` / `*_eu27.csv` duplicates of the comparison files.
- Exported `budget_deficit` (annual) although stale by the validator rule, because the dashboard shows it.

## Remaining issues

- The seven staleness warnings above.
- `parse_eurostat_data` keeps only ES and EU27 plus the GDP comparison countries; no euro-area series (EA20) is fetched. Not requested.
- A genuine annual GDP growth (`CLV_PCH_SM` in `namq_10_gdp`) is not fetched; only quarter-on-quarter growth and the level index are available.
- The client swallows fetch exceptions and returns an empty frame; the cached raw file is then kept silently. The new "Latest observation" printout shows EMPTY in that case, but the run still exits 0.

## Requests to others

- REQUEST → ws/lead: staleness thresholds for Q and A, see above.
