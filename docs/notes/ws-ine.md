# ws/ine notes (Phase 2)

Branch `ws/ine`. Owner of `src/fetchers/ine_*`, `src/processors/ine_processor.py`, `src/scripts/*_ine_*`, `src/export/ine.py`, `data_sources_ine.md`, `ine_conventions.md`.

## Datasets exported (28)

One dataset per INE processed CSV loaded by `src/app/data.py` (summary.csv excluded). Id = `ine.<csv stem>`. Last observations are from the 2026-10-28 run.

| id | title_es | frequency | fields | series | last_observation |
|---|---|---|---|---|---|
| `ine.gdp` | Producto Interior Bruto (PIB) | Q | value, yoy, qoq | 1 | 2026-04-01 |
| `ine.gdp_demand` | PIB por componentes de demanda | Q | contribution | 4 | 2026-04-01 |
| `ine.gdp_productivity` | PIB y productividad (2019T1 = 100) | Q | value | 5 | 2026-04-01 |
| `ine.industrial_production` | Índice de Producción Industrial (IPI) | M | value, yoy, mom | 1 | 2026-08-01 |
| `ine.ipi_sectors` | Producción industrial por destino económico | M | yoy, ytd | 5 | 2026-08-01 |
| `ine.industry_turnover` | Cifra de negocios de la industria | M | yoy | 1 | 2026-08-01 |
| `ine.services_turnover` | Cifra de negocios del sector servicios (IASS) | M | yoy | 1 | 2026-08-01 |
| `ine.services_production` | Indicador de Producción del Sector Servicios (IPSS) | M | value, yoy, mom | 1 | 2026-08-01 |
| `ine.ipss_sectors` | Servicios por sector de actividad | M | yoy, ytd | 8 | 2026-08-01 |
| `ine.business_confidence` | Confianza empresarial (ICEA) | Q | value, yoy | 3 | 2026-10-01 |
| `ine.unemployment` | Tasa de paro (EPA) | Q | value, yoy_pp | 1 | 2026-07-01 |
| `ine.youth_unemployment` | Tasa de paro de menores de 25 años (EPA) | Q | value, yoy_pp | 1 | 2026-07-01 |
| `ine.employment_rate` | Tasa de empleo (EPA) | Q | value, yoy_pp | 1 | 2026-07-01 |
| `ine.activity_rate` | Tasa de actividad (EPA) | Q | value, yoy_pp | 1 | 2026-07-01 |
| `ine.temporary_rate` | Tasa de temporalidad (EPA) | Q | value, yoy_pp | 1 | 2026-07-01 |
| `ine.parttime_rate` | Tasa de parcialidad (EPA) | Q | value, yoy_pp | 1 | 2026-07-01 |
| `ine.employed` | Ocupados (EPA) | Q | value, yoy | 1 | 2026-07-01 |
| `ine.labor_cost` | Coste laboral por trabajador (ETCL) | Q | value, yoy | 1 | 2026-04-01 |
| `ine.labor_cost_hour` | Coste laboral por hora efectiva (ETCL) | Q | value, yoy | 1 | 2026-04-01 |
| `ine.labor_cost_components` | Coste laboral total y coste salarial (ETCL) | Q | value, yoy, qoq, index_2019q1 | 2 | 2026-04-01 |
| `ine.cpi` | Índice de Precios de Consumo (IPC) | M | value, yoy | 1 | 2026-09-01 |
| `ine.cpi_special_groups` | Inflación general y subyacente | M | yoy | 2 | 2026-09-01 |
| `ine.cpi_ecoicop_groups` | Inflación por grupos especiales: aportaciones | M | yoy, weight, contribution | 4 | 2026-09-01 |
| `ine.cpi_weights` | Ponderaciones del IPC por grupos | A | weight | 13 | 2026-01-01 |
| `ine.cpi_ccaa` | IPC por comunidades autónomas | M | yoy, mom | 19 | 2026-09-01 |
| `ine.ipri` | Índice de Precios Industriales (IPRI) | M | value, yoy, mom | 6 | 2026-09-01 |
| `ine.retail_sales` | Comercio minorista (ICM) | M | value, yoy, mom | 1 | 2026-08-01 |
| `ine.house_prices` | Índice de Precios de Vivienda (IPV) | Q | value, yoy | 1 | 2026-04-01 |

Field conventions
- `value` is the level, `yoy` / `qoq` / `mom` are % changes (`pct_change`), `contribution` and `weight` as in the contract.
- Rates (unemployment, employment, activity, temporary, part-time): `value` in `pct`, plus `yoy_pp` (unit `pp`) = rate minus the rate a year earlier. This key is not one of the reserved ones: the reserved `yoy` means a relative % change, which is not meaningful for a rate (the old `yoy_change` for rates was the relative change, and the Shiny chart "Variación Tasa de Paro (pp)" was mislabeled). Frontend: use `yoy_pp` for these.
- `cpi_weights` and `cpi_ecoicop_groups.weight` are in % of the basket (INE publishes per mille; the processor adds `weight_pct`).
- `business_confidence.yoy` is filled only for the `ice` series (balances can be negative, so a % change is meaningless; they are null).
- `gdp_productivity` is wide: five series, one field `value` (2019T1 = 100).
- Index bases (checked against the data, not only the metadata): CPI 2025 = 100, house prices 2025 = 100, GDP 2020 = 100, IPI / IPSS / ICM 2021 = 100, IPRI 2021 (table code), ICE 2013.

## Fixes made

1. IPRI (`ipri.csv`) was stuck at 2026-02: table 76655 is still current, but INE renamed the series from `Total Nacional. ...` to `Nacional. Mercado interior. ...`, so the fetcher filter returned an empty frame and the cache was kept. Fetcher and processor now accept both prefixes; category patterns are anchored (`. Energía.` can no longer match `... sin energía`). Now reaches 2026-09.
2. `population_age_raw.csv` fetched empty: INE renamed `... Todas las edades. Personas.` to `... Total. Valor absoluto.`. Filters in fetcher and processor accept both. Population now reaches 2026-07 (was 2025-10), which also fills the last two quarters of GDP per capita / per working-age person in `gdp_productivity`.
3. Retail sales (`retail_sales.csv`) used the wrong series: table 75809 has no total, and "first matching index" picked `Empresas unilocalizadas`. Repointed to table 67178, series ICM4062 (`General`, constant prices, seasonally and calendar adjusted). Values changed (Aug 2026: 112.2, yoy +1.0%; before 102.5, yoy +0.2%).
4. Part-time rate used table 65970, which is annual, so `yoy_change` (a 4-period `pct_change`) was a 4-year change and the series stopped at 2025. Repointed to the quarterly table 65148; now to 2026-07 with a proper 12-month comparison.
5. `fetch_all` never fetched business confidence (`business_confidence_raw.csv` only existed as a stale local file, so a clean checkout or CI would have had no ICE data). Added. ICE now reaches 2026-10.
6. `pct_change` calls: the four uses in `ine_processor.py` (`_calculate_yoy_change`, part-time, labor cost yoy and qoq) were positional with the deprecated default fill. All replaced by `pct_change_by_date` / `diff_by_date` (comparison with the same calendar date 12 / 3 / 1 months earlier; a missing period gives NaN, no fill). No `pct_change` call is left in INE code. No FutureWarning from INE code in the pipeline or smoke test.
7. Added derived columns needed by pages that previously computed them in the app: `qoq_change` (GDP), `mom_change` (IPI, services production, retail), `yoy_pp` (six EPA rates), `yoy_change` for ICE, `weight_pct` and a `date` column for `cpi_weights.csv`. Existing columns are unchanged, so the Shiny app still works.
8. `ine.cpi` note said "Base 2026 = 100"; the data have 2025 average = 100. Corrected to "Base 2025 = 100".
9. Script lists (`AVAILABLE_INDICATORS` in `fetch_ine_data.py`, `process_ine_data.py`) were limited to six indicators; now complete. `data_sources_ine.md` and `ine_conventions.md` updated (table ids, bases, rename pitfalls).

## Verification

- CPI: computed yoy equals INE's published `Variación anual` (series IPC290750) for all 14 months compared (2025-08 to 2026-09) once rounded to one decimal; last three: Jul 3.6, Aug 4.3, Sep 4.9. Kept the computed value (more decimals); no need to substitute INE's rate.
- Latest values against INE series fetched separately: CPI Sep 2026 index 104.978, yoy 4.9; unemployment Q3 2026 10.18% (EPA453100), yoy -0.27 pp; GDP Q2 2026 index 126.4212, yoy 2.64% and qoq 0.68% (CNTR6654 / CNTR6653).
- Period convention: every date is the first day of the period; quarterly x are 01-01 / 04-01 / 07-01 / 10-01, annual 01-01 (checked programmatically over all `ine/*.json`).
- `run_pipeline.py --sources ine` exit 0; `validate_contract.py --strict`: 0 errors; `smoke_test.py --run-processors` passes.

## Decisions

- `cntr_employment.csv` and `population.csv` are not exported. They are only inputs to `gdp_productivity.csv` (exported), which is what the productivity chart shows. Persons / FTE / hours worked and population would only be needed for a different chart; they can be added as `ine.cntr_employment` / `ine.population` in a few lines if the inventory asks for them.
- `ine.cpi` yoy is the computed one (matches INE's published rate).
- `cpi_special_groups` exports only `yoy` (its `value` column is identical to `yoy_change`); `cpi.csv` `inflation_rate` is likewise not exported twice.

## Remaining issues

- Staleness warnings under `--strict` for seven quarterly datasets: `ine.gdp`, `gdp_demand`, `gdp_productivity`, `house_prices`, `labor_cost`, `labor_cost_hour`, `labor_cost_components`. All end at 2026-04-01 (Q2 2026), which is the latest INE has published: the Q3 GDP flash estimate is due at the end of October, house prices and labor cost Q3 later in the autumn. The validator measures age from the first day of the period (210 days, limit 200), so any quarterly series with a lag over about 110 days warns for weeks every quarter; the warnings clear by themselves when INE publishes. This is not fixable in the INE pipeline.
- `cpi_ecoicop_groups.contribution` applies the 2026 weights to the whole history because INE's weights table returns only the current year; contributions before 2026 are approximate (stated in the field note). Year-specific weights would need the older weights tables.
- `industry_turnover` / `services_turnover` carry only INE's published yoy (no index), as in the old app.
- `ine.gdp` yoy / qoq are computed from the seasonally adjusted index; they match INE's published rates (checked for the last three quarters).

## Requests

REQUEST → lead (owner of `scripts/validate_contract.py` / `docs/data-contract.md`): measure staleness of Q and A series from the end of the period (or raise the limits to about 290 days for Q and 700 for A), otherwise the `--strict` acceptance fails every quarter between INE's publication dates. Annual series would also warn from July to the following publication.
REQUEST → ws/frontend (indicator inventory): for EPA rates use field `yoy_pp`, not `yoy`; for the GDP qoq and MoM charts use `qoq` / `mom` instead of computing them in the page; `ine.cpi_weights` is annual (x = 2026-01-01, one series per ECOICOP group).
