# Indicator inventory

Spec for Phase 4 page agents (what to build, with which factory call) and for Phase 2 pipeline agents (which datasets, series and fields must exist). Built from `src/app/pages/*.py`, `src/app/charts.py`, `src/app/data.py`, `src/app/helpers.py` and the processed CSVs.

## How to read this document

- **Factory** = function of `site/assets/js/charts.js`: `lineChart`, `barChart`, `stackedBarChart`, `groupedBarChart`, `crossSectionChart`, `rebasedComparison`, `donutChart`, `latestTable`, `periodTable`, `kpiTile` / `kpiGrid`. Options in brackets are spec keys (see `docs/notes/ws-frontend.md`).
- **Dataset ids** follow the Phase 2 rules: INE `ine.<csv stem>`; Eurostat `eurostat.<indicator>` (suffixes `_spain/_eu27/_comparison` removed, series `es`, `eu27`; `gdp_index` adds `de`, `fr`, `it`); BdE `bde.<csv stem without _processed>`; Yahoo `yahoo.<csv stem without _processed>`.
- **Field** = contract field key. Reserved names (`value`, `yoy`, `qoq`, `mom`, `contribution`, `weight`, `close`) are used where they apply; other proposed names are marked `(proposed)`. The source CSV column is given as `csv:<column>` so Phase 2 can reconcile. `ytd` is already used by the sample `ine.ipi_sectors`.
- **`NEEDS PIPELINE FIELD`** = the old Shiny code computed this in Python at display time. The contract forbids the frontend from computing it, so the pipeline must export it. A page agent must not build the chart until the field exists in `site/data/` (use the other parts of the page meanwhile).
- **`RECONCILE`** = the CSV column or its meaning is unclear and must be checked against the processor.
- KPI tiles: `kpiTile` shows the latest value of `field` and, optionally, the latest value of ANOTHER field as the change (`change: {field, label}`), never a difference computed in the browser. `positiveIsGood` colours the change: `true` (growth, employment), `false` (unemployment, inflation, debt, rates for borrowers), omit for neutral.
- "Window" = range buttons (1A / 5A / Máx, display only). The old Shiny pages used a period selector (all / 5y / 3y / 1y); the buttons replace it per chart.
- Titles below are proposals (sentences, Spanish, no accents dropped). Subtitle, unit, source and last date come from the JSON; do not type them.

## Cross-cutting findings (old code defects, do not port)

1. `overview.py` executive summary compares Spain GDP **yoy** (INE) with EU-27 GDP **qoq** (Eurostat): apples to oranges. Do not port; see Portada.
2. `overview.py` titles the GDP chart "Variación trimestral" but plots `yoy_change`.
3. KPI cards for rates showed `change_pct` (relative change of the rate), which is not meaningful; use a pp change field.
4. `fed_funds` is `^IRX` (3-month T-bill), mislabelled: drop from the rates table (already decided in `docs/migration-plan.md`).
5. `markets.py` rates table reports basis-point changes computed in Python; the contract has no `bp` unit: export pp and display "p. p.".
6. The CCAA choropleth fetches a GeoJSON from GitHub at runtime; `plotly-basic` has no choropleth. Replace with a ranked horizontal bar plus table (below).
7. Old code hard-codes editorial thresholds and prose (pulse dots, "por encima del objetivo", table colour bands at 2,0 / 2,5 %). Not ported: tiles show data, sign colours only.

---

## 1. Portada (`index.html`, from `overview.py`)

Purpose: headline tiles and 4 to 6 key charts. Replaces Shiny "Resumen".

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| Claves | KPI PIB | `kpiTile` change yoy, `positiveIsGood: true` | `ine.gdp` es `value` (csv:gdp_index), change `yoy` (csv:yoy_change) | Quarterly |
| | KPI Paro | `kpiTile` change `yoy` (pp), `positiveIsGood: false` | `ine.unemployment` `value` (csv:unemployment_rate), `yoy` (csv:yoy_change) RECONCILE: pp or %? | |
| | KPI Tasa de empleo | `kpiTile` | `ine.employment_rate` `value`, `yoy` | |
| | KPI IPC | `kpiTile` | `ine.cpi` `yoy` as the value (csv:inflation_rate / yoy_change) or `value` with change `yoy`; `positiveIsGood: false` | Sample dataset exists |
| | KPI Producción industrial | `kpiTile` | `ine.industrial_production` `value` (csv:ipi_index), `yoy` | |
| | KPI Comercio minorista | `kpiTile` | `ine.retail_sales` `value` (csv:retail_index), `yoy` | |
| | KPI Euribor 12M | `kpiTile` | `bde.euribor_12m_monthly` `value`, change `yoy_pp` (proposed, csv:yoy_change_abs) RECONCILE | |
| | KPI Deuda hogares/PIB | `kpiTile`, `positiveIsGood: false` | `bde.household_debt_gdp` `value`, `yoy_pp` (proposed) | |
| | KPI IBEX 35 | `kpiTile` | `yahoo.ibex_35` `close`, change `ret_1d` (proposed, csv:daily_return_pct) NEEDS PIPELINE FIELD | Old card showed 1-day change |
| España vs UE | 4 comparison cards (PIB t/t, paro, IPCA, deuda/PIB) | `groupedBarChart` mode B, one per indicator, or one chart per indicator with `categories` | `eurostat.gdp_growth` es/eu27 `qoq` (csv:gdp_growth_qoq); `eurostat.unemployment` `value` (csv:unemployment_rate); `eurostat.hicp` `yoy`; `eurostat.government_debt` `value` (csv:debt_to_gdp) | Old "pp difference" badge was computed: NEEDS PIPELINE FIELD (series `gap`, see Comparativa UE) or drop. Recommended: drop. |
| Tendencias | PIB, variación anual, last ~20 quarters | `barChart` [`colorBySign: 'neutral'`, `range: {years: 5}`] | `ine.gdp` es `yoy` | Old title said "trimestral": it is yoy |
| | Inflación, last 24 months, line at ECB 2 % | `barChart` [`ref: {y: 2, label}`, `colorBySign: 'neutral'`, `range: {years: 2}`] | `ine.cpi` es `yoy` | Old coloured bars red above 2 %: not ported |
| Mercados | YTD return of IBEX 35, Euro Stoxx 50, S&P 500, DAX | `groupedBarChart` mode B (one category per index) [`colorBySign: true`] | `yahoo.ibex_35`, `yahoo.euro_stoxx_50`, `yahoo.sp_500`, `yahoo.dax` field `ytd` (proposed, csv:ytd_return_pct) | NEEDS PIPELINE FIELD |
| | Tipos de interés: Euribor 12M and Bono España 10A, last 36 months | `lineChart` [`range: {years: 3}`] | `bde.euribor_12m_monthly` `value`; `bde.spain_10y_bond_monthly` `value` | Old code resampled the daily bond to month-end in Python; use the monthly dataset. RECONCILE month-end vs monthly average |
| Pulso, resumen ejecutivo | Headline text, pulse dots, bullets | Not ported | | Editorial prose built from computed differences (ES minus EU, unemployment minus a year earlier). If wanted, the pipeline exports the differences as fields; otherwise omit |
| Pie | "Actualizado" date and sources | Layout footer (automatic) | `manifest.json` `generated_at` | |

## 2. Actividad (`pages/actividad.html`, from `activity.py`)

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| PIB | GDP with 3 modes: index 2019=100, yoy, qoq | `lineChart` with `toggle` of three field sets, markers on | `ine.gdp` es: `value_2019` (proposed, index 2019 average = 100) NEEDS PIPELINE FIELD; `yoy` (csv:yoy_change); `qoq` NEEDS PIPELINE FIELD (old: `pct_change` of gdp_index) | The 2019 average base is not a "start of window" rebase, so it must be exported. Old code also showed a range slider for the change modes: not ported |
| PIB comparado | Index 2019T1 = 100: Spain, Germany, France, Italy, EU-27 | `lineChart` [`endLabels: true`] (not `rebasedComparison`: the base is fixed 2019T1 and already in the CSV) | `eurostat.gdp_index` series `es`, `de`, `fr`, `it`, `eu27` field `value` (csv:gdp_index_spain, _germany, _france, _italy, _eu27) | Sample note says `gdp_index` adds `de`, `fr`, `it` |
| Descomposición del crecimiento | Contributions of private consumption, public consumption, GFCF, external demand, last 3 years, stacked | `stackedBarChart` [`range: {years: 3}`] | `ine.gdp_demand` series `private_consumption`, `public_consumption`, `gfcf`, `external_demand`, field `contribution` (pp) | Old code had no total line; a total series `gdp` (field `contribution`) is optional (NEEDS PIPELINE FIELD if wanted) |
| PIB y productividad | 5 indices 2019T1 = 100 (PIB, per capita, per working-age person, per employed, per hour) | `lineChart` [`yRange`] | `ine.gdp_productivity` series `pib`, `pib_per_capita`, `pib_per_working_age`, `pib_per_employed`, `pib_per_hour`, field `value` (csv:pib_index, pib_per_capita_index, pib_per_working_age_index, pib_per_employed_index, pib_per_hour_index) | Already indexed in the CSV; the pipeline reshapes columns into series |
| Confianza empresarial | ICE index, or yoy | `lineChart` with `toggle` | `ine.business_confidence` series `ice` field `value` (csv:value where indicator=ice); `yoy` NEEDS PIPELINE FIELD (old: `pct_change(4)` of a quarterly index) | Other indicators (`situacion`, `expectativas`) exist but the old page showed only ICE. Reference "100 = neutro": `ref: {y: 100}` for the index mode only |
| Producción | Industrial and services production: yoy, mom, index 2021 = 100 (Jan 2021) | `lineChart` with `toggle`, two series each | `ine.industrial_production` es `yoy` (csv:yoy_change), `mom` NEEDS PIPELINE FIELD, `value_2021_01` (proposed) NEEDS PIPELINE FIELD; `ine.services_production` same fields (csv:services_prod_index) | Old window: last 3 years for yoy and mom, from 2021 for the index |
| Sectores industriales | Latest value by sector, YTD or yoy, sorted | `groupedBarChart` mode A [`orientation: 'h'`, `sort: 'desc'`, `colorBySign: true`, `toggle`] | `ine.ipi_sectors` series `consumo`, `equipo`, `intermedios`, `energia`, `total`; fields `ytd` (csv:ytd_change), `yoy` (csv:yoy_change) | Sample dataset exists. Old chart omitted nothing; `total` optional |
| Sectores de servicios | Same by services sector | same | `ine.ipss_sectors` series `hosteleria`, `inmobiliarias`, `mayoristas`, `minoristas`, `profesionales`, `tic`, `transporte`, `vehiculos`; fields `ytd`, `yoy` | Series labels in Spanish from `label_es` (csv:sector_label) |
| Not shown in the old UI | `ine.industry_turnover`, `ine.services_turnover` (csv:turnover_yoy) | optional `lineChart` | field `yoy` | Defined in `data.py` but not displayed; low priority |

## 3. Precios (`pages/precios.html`, from `prices.py`)

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| IPC | General vs subyacente, yoy, window 1A/3A/Máx | `lineChart` [`range`] | `ine.cpi_special_groups` series `headline`, `core`, field `yoy` (csv:yoy_change) | Old default 3 years. `ine.cpi` (sample) holds the headline only; either can serve `headline` |
| Composición del IPC | Weights of 4 special groups, latest | `donutChart` | `ine.cpi_ecoicop_groups` series `servicios`, `alimentos`, `bienes_industriales`, `energia` (csv:group_name), field `weight` (pct) | Series slugs proposed; labels from the CSV names |
| Descomposición de la inflación | Contributions by group, last 12 months, stacked | `stackedBarChart` [`range: {years: 1}`] | same dataset, field `contribution` (pp) | Optional total line: series `total` NEEDS PIPELINE FIELD |
| IPRI general | General and general excluding energy; index (Jan 2021 = 100), yoy, mom | `lineChart` with `toggle` | `ine.ipri` series `total`, `total_sin_energia`; `yoy`, `mom` (csv:yoy_change, mom_change); `value_2021_01` (proposed) NEEDS PIPELINE FIELD (old rebased in Python; csv:ipri_index) | |
| IPRI por destino | Consumo, equipo, intermedios, energía; same 3 measures; window 5/3/1 years | `lineChart` with `toggle` [`range` options 1A, 3A, 5A] | `ine.ipri` series `consumo`, `equipo`, `intermedios`, `energia` | Same fields |
| Coste laboral | Total and salarial; index 2019T1 = 100, yoy, qoq | `lineChart` with `toggle` | `ine.labor_cost_components` series `total`, `salarial`; `index_2019q1` (csv), `yoy`, `qoq` (csv:yoy_change, qoq_change) | Quarterly. Fields exist in the CSV already |
| IPC por CCAA | Choropleth map, latest yoy | **Replace** with `groupedBarChart` mode A [`orientation: 'h'`, `sort: 'desc'`] | `ine.cpi_ccaa` one series per CCAA (`an`, `ar`, `as`, `cb`, `ce`, `cl`, `cm`, `cn`, `ct`, `ex`, `ga`, `ib`, `mc`, `md`, `ml`, `nc`, `pv`, `ri`, `vc`; csv:ccaa_code), field `yoy` | Decision for the project lead: map vs bar. A map needs a Plotly build with choropleth plus a vendored GeoJSON |
| IPC por CCAA | Table sorted by yoy, with mom | `latestTable` [`columns: yoy, mom`, `sort`] | `ine.cpi_ccaa` fields `yoy`, `mom` (csv:yoy_change, mom_change) | Old row colour bands (2,0 / 2,5 %, 0,3 %) not ported: sign colour only |

## 4. Mercado laboral (`pages/laboral.html`, from `labor.py`, unregistered)

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| Indicadores clave | KPIs: paro, tasa de empleo, tasa de actividad, ocupados | `kpiGrid` | `ine.unemployment` `value` (csv:unemployment_rate) change `yoy` `positiveIsGood: false`; `ine.employment_rate` `value`, `yoy`; `ine.activity_rate` `value`, `yoy`; `ine.employed` `value` (persons, scale 3), `yoy` | Old cards used `yoy_change` as "interanual". For rates RECONCILE whether `yoy_change` is pp or % |
| Empleo y desempleo | Tasa de paro | `lineChart` [`range`] | `ine.unemployment` `value` | Quarterly |
| | Tasa de empleo | `lineChart` | `ine.employment_rate` `value` | |
| | Variación del paro (pp) | `barChart` [`colorBySign: 'neutral'`] | `ine.unemployment` `yoy` (unit `pp`) | Old `create_yoy_bar_chart` |
| | Table "Datos recientes", last 12 quarters | `periodTable` [`last: 12`] | `ine.unemployment` `value`, `ine.employment_rate` `value` | |
| Costes laborales | KPIs coste por trabajador, coste por hora | `kpiGrid` | `ine.labor_cost` `value` (currency EUR), `yoy`; `ine.labor_cost_hour` `value`, `yoy` | |
| | Coste laboral por trabajador (euros per month) with yoy | `lineChart` [`toggle`: value / yoy] | `ine.labor_cost` | Old `show_yoy=True` overlay: use the toggle |
| | Coste laboral por hora | `lineChart` [`toggle`] | `ine.labor_cost_hour` | |
| Calidad del empleo | KPIs temporalidad, paro juvenil | `kpiGrid` | `ine.temporary_rate` `value`, `yoy`; `ine.youth_unemployment` `value` (csv:youth_unemployment_rate), `yoy` | `positiveIsGood: false` |
| | Tasa de temporalidad | `lineChart` | `ine.temporary_rate` `value` | |
| | Paro juvenil frente a total | `lineChart` two datasets | `ine.youth_unemployment` `value` (label "Menores de 25 años"), `ine.unemployment` `value` (label "Total") | |
| Not shown | `ine.parttime_rate` (parcialidad), `ine.cntr_employment` (unused, plan says decide), `ine.population` (unused) | | | Optional |

## 5. Crédito y tipos (`pages/credito.html`, from `credit.py`, unregistered; plus rates/yield curve)

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| Crédito al sector privado | KPIs crédito a hogares y a empresas | `kpiGrid` | `bde.credit_households_total` `value` (currency EUR, scale 6; csv:value), change `yoy` (pct_change; csv:yoy_change_pct); `bde.credit_nfc_total` same | Old change was `change_pct` (month on month): use `yoy` for consistency |
| | Evolución del crédito, yoy | `lineChart` [`range`, `ref: {y: 0}`] | same two datasets field `yoy` | Old default window 5 years |
| Tipos bancarios | KPIs hipotecas, consumo, empresas, depósitos | `kpiGrid` | `bde.mortgage_rate`, `bde.consumer_credit_rate`, `bde.corporate_lending_rate`, `bde.household_deposit_rate` `value` (pct), change `yoy_pp` (proposed, csv:yoy_change_abs) RECONCILE | `positiveIsGood: false` for loans, `true` for deposits |
| | Tipos de interés bancarios (new business) | `lineChart` four series | same, field `value` | |
| Endeudamiento | KPIs deuda hogares/PIB y empresas/PIB | `kpiGrid` | `bde.household_debt_gdp`, `bde.nfc_debt_gdp` `value` (pct), `yoy_pp` | Quarterly |
| | Deuda sobre PIB | `lineChart` two series | same | |
| | "Indicadores de deuda" gauge (0 to 150, bands 60 / 100) | **Replace** with the two KPI tiles above | | `plotly-basic` has no gauge and the bands were editorial |
| Sector exterior | KPIs saldo por cuenta corriente, ingresos por turismo | `kpiGrid` | `bde.current_account_balance` `value` (currency EUR, scale 6), `bde.tourism_receipts` `value` | |
| | Balanza por cuenta corriente: monthly bars by sign + rolling 12-month sum line | `barChart` [`colorBySign: true`, `overlay`] | `bde.current_account_balance` `value`; overlay `sum_12m` (proposed, csv:rolling_12m_sum) NEEDS PIPELINE FIELD | |
| Curva de rendimientos | Latest yield curve | `crossSectionChart` [`xTitle: 'Plazo (años)'`] | `bde.yield_curve` es `yield` (sample) | Shows `as_of` |

## 6. Mercados (`pages/mercados.html`, from `markets.py`)

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| Índices | One index at a time (IBEX 35, S&P 500, Nasdaq, Euro Stoxx 50, DAX) + 200-day average | `lineChart` with `toggle` of 5 field sets (two series each: `close`, `sma_200` dashed) | `yahoo.ibex_35`, `yahoo.sp_500`, `yahoo.nasdaq_composite`, `yahoo.euro_stoxx_50`, `yahoo.dax`: `close`; `sma_200` (proposed, csv:sma_200) NEEDS PIPELINE FIELD | Old window: from Jan 2022 |
| Comparativa | Five indices rebased to 100, windows 1 / 3 years / all | `rebasedComparison` [`range` options 1A, 3A, Máx] | same datasets `close` | Display-only rebase, allowed |
| Cotizaciones | Table: actual, 1 week, 30 days, YTD, 1 year | `latestTable` [`columns: close, ret_1w, ret_1m, ytd, ret_1y`, signColor] | same datasets; fields `ret_1w`, `ret_1m`, `ytd`, `ret_1y` (proposed, unit `pct_change`; csv:return_1w_pct, return_1m_pct, ytd_return_pct, return_1y_pct) NEEDS PIPELINE FIELD | |
| VIX | Volatility, windows 6m / 1y / 5y | `lineChart` [`range` options, `ref` at 20 and 30] | `yahoo.vix` `close` | Old chart had colour bands 12 / 20 / 30 labelled "Baja, Moderada, Elevada, Alta": reduce to reference lines or drop |
| Tipos de interés | Table: €STR, Euribor 3M and 12M, Spain 5Y and 10Y, US Treasury 5Y and 10Y with change at 30 days, YTD, 1 year (bp) | `latestTable` [`columns: value, chg_30d, chg_ytd, chg_1y`] | `bde.ester_daily`, `bde.euribor_3m_daily`, `bde.euribor_12m_daily`, `bde.spain_5y_bond`, `bde.spain_10y_bond` `value`; `yahoo.us_treasury_5y`, `yahoo.us_treasury_10y` `close`; changes `chg_30d`, `chg_ytd`, `chg_1y` (proposed, unit `pp`) NEEDS PIPELINE FIELD | Drop `fed_funds` (mislabelled ^IRX). Display in p. p., not bp |
| Tipos de cambio | EUR/USD, GBP/USD, USD/JPY with % changes | `latestTable` | `yahoo.eur_usd`, `yahoo.gbp_usd`, `yahoo.usd_jpy` `close`; `ret_30d`, `ytd`, `ret_1y` (proposed, `pct_change`) NEEDS PIPELINE FIELD | Same table or a second one |
| Tipos de referencia | €STR, Euribor 3M, Euribor 12M daily, window all / 2y / 1y | `lineChart` [`range` options] | same BdE daily datasets `value` | |
| Deuda a 10 años | Spain, Germany, France, Italy (monthly, BdE) and US (daily, Yahoo), user selects countries, last 5 years | `lineChart` [`selectable: true`, `range: {years: 5}`] | `bde.spain_10y_bond_monthly`, `bde.germany_10y_bond`, `bde.france_10y_bond`, `bde.italy_10y_bond` `value`; `yahoo.us_treasury_10y` `close` | Mixed frequencies: footer lists each last date. Default on: Spain, Germany, Italy (`off: true` on the others) |

## 7. Comparativa UE (`pages/ue.html`, from `eu_comparison.py`, unregistered)

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| Comparativa actual | 4 cards: PIB t/t, paro, IPCA, deuda pública, Spain vs EU-27 latest | `groupedBarChart` mode B (4 charts or 4 categories) | `eurostat.gdp_growth` `qoq`; `eurostat.unemployment` `value`; `eurostat.hicp` `yoy`; `eurostat.government_debt` `value` | Different units: keep one chart per indicator |
| Tendencias | Tasa de paro, España vs UE-27 (monthly, 25 to 74 years) | `lineChart` [`range`] | `eurostat.unemployment` es, eu27 `value` | |
| | Inflación IPCA | `lineChart` | `eurostat.hicp` es, eu27 `yoy` | Sample dataset exists |
| | Indicador de sentimiento económico (100 = long-run mean) | `lineChart` [`ref: {y: 100}`] | `eurostat.economic_sentiment` es, eu27 `value` (csv:esi) | |
| | Deuda pública sobre PIB (quarterly) | `lineChart` | `eurostat.government_debt` es, eu27 `value` (csv:debt_to_gdp) | |
| Diferencial | Paro: Spain minus EU-27 | `barChart` or `lineChart` [`ref: {y: 0}`] | `eurostat.unemployment` series `gap` (proposed), field `value`, unit `pp` NEEDS PIPELINE FIELD | Old `create_difference_chart` subtracted in Python |
| | Inflación: Spain minus EU-27 | same | `eurostat.hicp` series `gap`, field `yoy`, unit `pp` NEEDS PIPELINE FIELD | |
| Not shown in the old UI | Eurostat datasets already fetched: `industrial_production`, `core_inflation`, `producer_prices`, `employment_growth`, `labor_participation`, `trade_balance` (es only: `trade_balance`, `exports`, `imports`), `budget_deficit`, `consumer_confidence`, `retail_trade`, `house_prices`, `gdp_growth` | | | Candidates for an extended page; see Consumo for the last three |

## 8. Consumo (`pages/consumo.html`, from `consumer.py`, unregistered)

| Section | Element | Factory and spec | Datasets / series / fields | Notes |
|---|---|---|---|---|
| KPIs | Comercio minorista, precio de vivienda | `kpiGrid` | `ine.retail_sales` `value` (csv:retail_index), `yoy`; `ine.house_prices` `value` (csv:hpi_index, base 2015 = 100), `yoy` | |
| Comercio minorista | Index, monthly | `lineChart` [`toggle`: value / yoy, `range`] | `ine.retail_sales` | Old subtitle "deflactado" is an editorial claim: confirm against the INE table before reusing; use `note_es` |
| Precios de vivienda | Index, quarterly, base 2015 = 100 | `lineChart` [`toggle`] | `ine.house_prices` | |

### Proposal (not a decision): merge Consumo into Actividad?

Reasons to merge:
- The old page has two KPIs and two charts; as its own page it is thin and breaks the 8-item navigation rhythm.
- Retail sales is a demand-side activity indicator; house prices are the only real outlier (they fit Precios).
- Fewer pages means less maintenance and a shorter nav on phones.

Reasons to keep it separate:
- `content.md` defines "Consumer & Household" as its own category with confidence, retail and house prices; Eurostat already provides `consumer_confidence`, `retail_trade` and `house_prices` comparisons, so the page can grow into a real household section (confidence, retail Spain vs EU, house prices Spain vs EU).
- Actividad is already the longest page (6 sections, about 10 charts).

Suggested middle path: keep `consumo.html` but enrich it with the three Eurostat datasets above (unused today) so it stands as "Consumo y vivienda"; if that data is not wanted, merge retail sales into Actividad (Producción section) and house prices into Precios.

## Dataset checklist for Phase 2

One line per proposed id; fields in brackets. `(+)` marks fields that are NEEDS PIPELINE FIELD.

- **INE:** `gdp` [value, yoy, qoq(+), value_2019(+)], `gdp_demand` [contribution], `gdp_productivity` [value], `business_confidence` [value, yoy(+)], `industrial_production` [value, yoy, mom(+), value_2021_01(+)], `services_production` [same], `ipi_sectors` [yoy, ytd] (sample), `ipss_sectors` [yoy, ytd], `unemployment`, `employment_rate`, `activity_rate`, `temporary_rate`, `youth_unemployment` [value, yoy], `employed` [value, yoy], `labor_cost`, `labor_cost_hour` [value, yoy], `labor_cost_components` [index_2019q1, yoy, qoq], `cpi` [value, yoy] (sample), `cpi_special_groups` [value, yoy], `cpi_ecoicop_groups` [yoy, weight, contribution], `ipri` [value, yoy, mom, value_2021_01(+)], `cpi_ccaa` [yoy, mom], `retail_sales`, `house_prices` [value, yoy].
- **Eurostat:** `gdp_growth` [qoq], `gdp_index` [value; es, eu27, de, fr, it], `economic_sentiment` [value], `unemployment` [value, gap series(+)], `hicp` [yoy, gap series(+)] (sample), `government_debt` [value], optional the rest.
- **BdE:** `credit_households_total`, `credit_nfc_total` [value, yoy], `mortgage_rate`, `consumer_credit_rate`, `corporate_lending_rate`, `household_deposit_rate`, `household_debt_gdp`, `nfc_debt_gdp` [value, yoy_pp], `current_account_balance` [value, sum_12m(+)], `tourism_receipts` [value], `euribor_12m_monthly`, `euribor_3m_daily`, `euribor_12m_daily`, `ester_daily` [value, chg_30d(+), chg_ytd(+), chg_1y(+)], `spain_10y_bond`, `spain_5y_bond` [same], `spain_10y_bond_monthly`, `germany_10y_bond`, `france_10y_bond`, `italy_10y_bond` [value], `yield_curve` [yield] (sample).
- **Yahoo:** `ibex_35` [close, ret_1d(+), ret_1w(+), ret_1m(+), ytd(+), ret_1y(+), sma_200(+)] (sample has close only), `euro_stoxx_50`, `sp_500`, `nasdaq_composite`, `dax` [same], `vix` [close], `eur_usd`, `gbp_usd`, `usd_jpy` [close, ret_30d(+), ytd(+), ret_1y(+)], `us_treasury_5y`, `us_treasury_10y` [close, chg_30d(+), chg_ytd(+), chg_1y(+)].


## Reconciliation with the exported data (lead, 2026-10-28, contract v1.1)

Phase 2 and Phase 3 ran in parallel, so the field keys proposed above were guesses. **This table overrides them.** The authoritative list of datasets, series keys and field keys is `site/data/manifest.json`; page agents must read it before writing a chart spec and must not use a key that is not in the manifest.

| Inventory item | Proposed above | Resolution |
|---|---|---|
| KPI IBEX 35, 1-day change | `ret_1d` NEEDS PIPELINE FIELD | Exists: `yahoo.ibex_35` `ret_1d` |
| España vs UE cards | various | Exist: `eurostat.gdp_growth` `qoq`; `eurostat.unemployment` `value`; `eurostat.hicp` `yoy`; `eurostat.government_debt` `value` |
| Mercados YTD by index | field `ytd` | Use `ret_ytd` (all Yahoo price datasets) |
| PIB index 2019 = 100 | `value_2019` NEEDS PIPELINE FIELD | Frontend rebases `ine.gdp` `value` to the 2019 average (allowed by contract v1.1, display-only). `qoq` and `yoy` exist |
| Descomposición del crecimiento, total line | NEEDS PIPELINE FIELD | Overlay `ine.gdp` `yoy`. Series keys: `private_consumption`, `public_consumption`, `gfcf`, `external_demand` |
| Confianza empresarial yoy | NEEDS PIPELINE FIELD | Exists: `ine.business_confidence` `yoy`; series `ice`, `situacion`, `expectativas` |
| Producción, mom | NEEDS PIPELINE FIELD | Exists: `mom` on `ine.industrial_production`, `ine.services_production` |
| Producción, index 2021 = 100 | `value_2021` | Frontend rebases `value` to the 2021 average |
| Descomposición de la inflación, total line | NEEDS PIPELINE FIELD | Overlay `ine.cpi` `yoy`. Note: contributions use current weights for the whole history (see `docs/notes/ws-ine.md`), so the bars will not sum exactly to the headline in earlier years; say so in the chart note. Series keys: `servicios`, `alimentos_bebidas_y_tabaco`, `bienes_industriales_sin_productos_energeticos`, `productos_energeticos` |
| IPRI index Jan 2021 = 100 | `value_2021_01` | Frontend rebases `value` to 2021-01-01. `yoy`, `mom` exist; series `total`, `total_sin_energia`, `consumo`, `equipo`, `intermedios`, `energia` |
| Balanza por cuenta corriente, 12-month sum | NEEDS PIPELINE FIELD | Exists: `bde.current_account_balance` `sum_12m` |
| Índices with 200-day average | `sma_200` | Exists on the 9 equity-index datasets |
| Cotizaciones table | `ret_1w, ret_1m, ytd, ret_1y` | Use `ret_1w`, `ret_1m`, `ret_ytd`, `ret_1y` |
| Tipos de interés table | `chg_30d, chg_ytd, chg_1y` (bp) | Use `chg_1m`, `chg_ytd`, `chg_1y`, unit `pp` (displayed "p. p."). BdE `chg_1m` is 30 calendar days; Yahoo (US Treasuries) `chg_1m` is 21 sessions; the field `note_es` says which |
| Tipos de cambio | `ret_30d, ytd, ret_1y` | Use `ret_1m`, `ret_ytd`, `ret_1y` |
| Diferencial España − UE-27 (paro, inflación) | series `gap` NEEDS PIPELINE FIELD | **Not exported.** Phase 4 shows both series on one chart instead. If a gap chart is wanted later, ws/eurostat adds a `gap` series |
| Changes of rates (paro, actividad, deuda/PIB) | `yoy` | Contract v1.1: differences of rates are `yoy_pp` (INE EPA rates, `eurostat.unemployment`, `eurostat.labor_participation`, `eurostat.government_debt`); `eurostat.consumer_confidence` uses `yoy_diff` (points); BdE monthly/quarterly rate changes are `mom_pp` / `qoq_pp` |
| `ine.cntr_employment`, `ine.population` | dataset ids | Not exported; their information is in `ine.gdp_productivity` (series `pib`, `pib_per_capita`, `pib_per_working_age`, `pib_per_employed`, `pib_per_hour`) |
| Series key for global/US markets | `es`/`eu27` | Yahoo FX uses `global`; US instruments `us`; BdE euro-area rates (`ester_daily`, Euribor) use `ea` |

Datasets exported but not used by any old page (40, e.g. `eurostat.core_inflation`, `bde.euribor_6m_daily`, `yahoo.gold`): available to Phase 4 where they add value; not required.
