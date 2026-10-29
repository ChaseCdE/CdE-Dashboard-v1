# Seasonal and calendar adjustment audit

Branch `sa/adjustment`, 2026-10-29. Requirement from the project owner: every series uses the **seasonally and calendar adjusted** variant whenever the official source publishes one. Evidence comes from the sources' own metadata: INE series names (`SERIES_TABLA`, `DATOS_SERIE`), Eurostat JSON-stat `s_adj` / `indic_et` categories, and Banco de España descriptions (`listaSeries`, `idioma=ES`). Every code below was queried on 2026-10-29.

## Rules applied

1. Levels and period-on-period changes (`mom`, `qoq`, `*_pp` against the previous period) use the seasonally and calendar adjusted (SCA) variant when the source publishes one. In Eurostat, `SCA` is preferred over `SA`. Period-on-period changes of unadjusted data are removed. The exception is the monthly rate of a price index whose official headline is itself unadjusted (CPI by region, IPRI).
2. `yoy` and `yoy_pp` are the rate of the adjusted series when the level is adjusted. INE's published rate is used where it exists (audit M4). Without an adjusted series, they stay on original data.
3. `sum_12m` of flows is always computed on original data, which is what the statistics publish.
4. Every field's `note_es` states its adjustment with exactly one of these phrases, defined in `src/export/adjustment.py`:
   - "Datos corregidos de efectos estacionales y de calendario" (SCA).
   - "Datos corregidos de efectos estacionales" (the source adjusts for seasonality only).
   - "Datos originales (sin corregir de estacionalidad)".
   - "Dato anual: la corrección de estacionalidad no procede".

   Other note text is kept.
5. Market prices have no adjustment concept and get no statement: Yahoo, plus the Banco de España Euribor, €STR, government bond yields, spreads and yield curve.
6. `bde.social_security_affiliates` and `bde.registered_unemployment` are out of scope (changed in parallel by the lead) and were left byte-identical.

## Datasets changed

"Latest" is the last observation before and after the change, from the same run on 2026-10-29.

| Dataset | Field | Before | After | Source code / filter | Latest before → after | Official check |
|---|---|---|---|---|---|---|
| ine.industry_turnover | yoy | Original (ICN2412, table 61701) | SCA (ICN2920, table 61709) | `DATOS_SERIE/ICN2920`: "Nacional. Total industria. Variación anual. Datos ajustados de estacionalidad y calendario." | Aug 2026: 10.8 → **8.7** | INE ICN August 2026 press release (https://www.ine.es/dyngs/Prensa/ICN0826.htm): "8,7% en la serie corregida de efectos estacionales y de calendario, y en el 10,8% en la original" |
| ine.services_turnover | yoy | Calendar only (IAS3856, table 60289) | SCA (IAS4004, table 60290) | "Cifra de negocio. Datos ajustados de estacionalidad y calendario. Índice General. Nacional. Variación anual." | Aug 2026: 5.6 → **5.5** | IASS August 2026 press release (https://www.ine.es/dyngs/Prensa/IASS0826.htm): "5,5% en la serie corregida de efectos estacionales y de calendario" |
| ine.labor_cost | value, yoy | Original (ETCL68; yoy recomputed) | SCA (ETCL13714; yoy = INE's ETCL13713), table 11221 | "Total Nacional. Datos ajustados de estacionalidad y calendario. Coste total por trabajador. Euros / Tasa de variación anual." The original variant of the same table (ETCL13726) equals ETCL68 exactly. | Q2 2026: 3,388.15 € → **3,339.08 €**; yoy 4.04 → **4.2** % | ETCL Q2 2026 press release (https://www.ine.es/dyngs/Prensa/ETCL2T26.htm): "Con resultados corregidos de calendario y desestacionalizados, el coste laboral por trabajador se incrementó un 4,2% en tasa anual y un 0,8% en tasa trimestral" |
| ine.labor_cost_hour | value, yoy | Original (ETCL925) | SCA (ETCL13732; yoy ETCL13731), table 11222 | "Datos ajustados de estacionalidad y calendario. Coste laboral total por hora. Euros. Total Nacional." The original ETCL13744 equals ETCL925. | Q2 2026: 26.18 € → **26.31 €**; yoy 4.76 → **4.4** % | INE API only (`DATOS_SERIE/ETCL13731` = 4.4); the press release text gives the adjusted figure per worker only |
| ine.labor_cost_components | value, yoy, qoq, index_2019q1 | Original (ETCL68/67) | SCA (ETCL13714/13712; yoy ETCL13713/13711; qoq computed on the adjusted level) | as above | Q2 2026 total: 3,388.15 → **3,339.08**, yoy 4.04 → **4.2**, qoq 3.36 → **0.84**, index 132.85 → **127.84**. Wages: 2,512.68 → **2,464.45**, yoy 3.98 → **4.2**, qoq 4.53 → **0.83**, index 133.92 → **126.76** | ETCL2T26: 4,2 % yoy and 0,8 % q/q per worker (matches 4.2 and 0.84) |
| ine.employed | value, yoy | Original (EPA387796, table 65109) | Seasonally adjusted. INE publishes the adjusted EPA levels only in the workbook https://www.ine.es/daco/daco42/daco4211/epa_desestacional.xlsx ("Series desestacionalizadas EPA. Totales (miles de personas)", column "Ocupación"), not in Tempus. yoy is computed from the adjusted level because INE publishes no adjusted annual rate. | sheet "Totales (miles de personas)", column "Ocupación" | Q3 2026: 22,852.6 → **22,729.6** thousand; yoy 2.08 → **2.09** % | EPA Q3 2026 press release (https://www.ine.es/dyngs/Prensa/EPA3T26.htm): "La tasa de variación trimestral del empleo en términos desestacionalizados fue del 0,31%" (22,729.6 / 22,659.7 − 1 = 0.31 %) |
| ine.gdp | yoy, qoq | SCA, recomputed from CNTR6652 | SCA, INE's published rates CNTR6654 / CNTR6653 | "Datos ajustados de estacionalidad y calendario. Producto interior bruto a precios de mercado. Variación anual / trimestral" | Q2 2026: 2.6374 / 0.6847, unchanged. INE publishes 4 decimals; 21 historical values change by ≤ 0.0001, and 2016Q3-2017Q2 gain a yoy | Oracle: CNTR6654 / CNTR6653 last 24 quarters maxdiff 0 |
| eurostat.trade_balance | balance, exports, imports | Unadjusted (`indic_et=TRD_VAL`) | SCA (`indic_et=TRD_VAL_SCA`, "Seasonally and calendar adjusted trade value in million ECU/EURO") | `ext_st_27_2020msbec?geo=ES&partner=WORLD&bclas_bec=TOTAL&indic_et=TRD_VAL_SCA&stk_flow=EXP\|IMP` | Aug 2026: exports 26,754.4 → **34,246.9**; imports 35,118.7 → **41,278.3**; balance −8,364.3 → **−7,031.4** M€ | Eurostat API (official source of the figure), oracle maxdiff 0 |
| bde.mortgage_rate, consumer_credit_rate, corporate_lending_rate, household_deposit_rate, household_overnight_deposit_rate | mom_pp → yoy_pp | `mom_pp` on original data | `mom_pp` removed; `yoy_pp` (change on a year earlier) added. BdE publishes no adjusted MIR rates. | DN_1TI2T0135/0138/0144/0024, DN_1TI1T0010 | Aug 2026 mortgage: mom_pp 0.15 → yoy_pp **0.36**; consumer 0.20 → **0.04**; NFC −0.11 → **0.33**; time deposits 0.0091 → **0.3916**; overnight 0 → **0.02** | Levels unchanged (oracle); yoy_pp recomputed by the oracle from the published levels |
| bde.credit_households_total, credit_nfc_total | mom removed | `mom` = monthly change of the unadjusted stock | removed; `yoy` (BdE transaction-based rate) kept | DF_MESNAA20A1U62250Z01E ("Ajuste: Datos originales sin ajustar"); DCF_M.N.ES… ("Ajuste: Sin ajuste de estacionalidad") | Aug 2026 households mom 0.03 → —; NFC −1.14 → —; yoy 5.16 / 4.19 unchanged | Unchanged levels and yoy (oracle vs BdE) |
| bde.household_debt_gdp, nfc_debt_gdp | qoq_pp → yoy_pp | `qoq_pp` on original data | `yoy_pp` | DMZ10S80ZH0_TPRPIB.Q, DMZ10S80ZN0_TPRPIB.Q | Q2 2026 households: qoq_pp −0.6 → yoy_pp **−2.0**; NFC 0.3 → **−3.0** | Levels unchanged (oracle) |

Page changes: `site/assets/js/pages/credito.js`. The KPI tiles for the mortgage rate, the NFC lending rate and household debt/GDP now show the year-on-year change ("interanual") instead of the removed monthly or quarterly change. No other page referenced a removed field.

Label fix found on the way: `eurostat.unemployment` still said "25 a 74 años" in its description and note, although the data has been `age=TOTAL` (15-74) since audit C1. The text now says "15 a 74 años". The data is unchanged.

## Inventory: every dataset and field

Abbreviations:
- SCA: seasonally and calendar adjusted.
- SA: seasonally adjusted only.
- CA: calendar adjusted only.
- NSA: original data.

"Available" says whether the same source publishes an adjusted variant of the same concept.

### INE

| Dataset | Fields | Before | After | Adjusted variant available? | Code(s) |
|---|---|---|---|---|---|
| ine.gdp | value, yoy, qoq | SCA | SCA (yoy/qoq now INE's rates) | yes, used | CNTR6652, CNTR6654, CNTR6653 |
| ine.gdp_demand | contribution | SCA | SCA | yes, used | CNTR7160/7190/7215/7262/7264 |
| ine.gdp_productivity | value | GDP, employment and hours SCA; population NSA | same, now stated in the note | Population: no (EPA population levels are original only) | CNTR6652, CNTR7659, CNTR7896, EPA384355, EPA384363-384381 |
| ine.industrial_production | value, yoy, mom | SCA | SCA | yes, used | IPI15360, IPI15374, IPI15381 |
| ine.ipi_sectors | yoy, ytd | SCA | SCA | yes, used | IPI15361-15374 |
| ine.industry_turnover | yoy | NSA | **SCA** | yes (table 61709) | ICN2412 → ICN2920 |
| ine.services_turnover | yoy | CA | **SCA** | yes (table 60290) | IAS3856 → IAS4004 |
| ine.services_production | value, yoy, mom | SCA | SCA | yes, used | IPSS380, IPSS490, IPSS491 |
| ine.ipss_sectors | yoy, ytd | SCA | SCA | yes, used | IPSS387-484 |
| ine.business_confidence | value, yoy | NSA | NSA | no (tables 8027 and 79688 have no adjusted series) | ICE1, ICE53, ICE54 |
| ine.unemployment, youth_unemployment, employment_rate, activity_rate, temporary_rate, parttime_rate | value, yoy_pp | NSA | NSA | no: INE publishes no adjusted EPA rates (the adjusted workbook has employment and unemployment levels only) | EPA453100, EPA452436, EPA441060, EPA388079, EPA416256, EPA404358/404362 |
| ine.employed | value, yoy | NSA | **SA** | yes, workbook only | EPA387796 → epa_desestacional.xlsx "Ocupación" |
| ine.labor_cost, labor_cost_hour, labor_cost_components | all | NSA | **SCA** | yes (tables 11221, 11222) | ETCL68/67/925 → ETCL13714/13712/13732 (+ yoy 13713/13711/13731) |
| ine.cpi | value, yoy | NSA | NSA | no (INE publishes no adjusted CPI) | IPC290751, IPC290750 |
| ine.cpi_special_groups | yoy | NSA | NSA | no | IPC290750, IPC292510 |
| ine.cpi_ecoicop_groups | yoy, contribution / weight | NSA / annual weight | NSA / annual | no | IPC292534/292538/292458/292494; weights IPC3323xx, IPC2332xx |
| ine.cpi_weights | weight | annual | annual | not applicable | IPC331936-331949 |
| ine.cpi_ccaa | yoy, mom | NSA | NSA (mom kept: official unadjusted monthly CPI rate) | no | IPC293603-294613 |
| ine.ipri | value, yoy, mom | NSA | NSA (mom kept, see exceptions) | no (table 76655 and the IPRI tables have no adjusted series) | IPR34515-34954 |
| ine.retail_sales | value, yoy, mom | SCA | SCA | yes, used | ICM4062, ICM4079, ICM4080 |
| ine.house_prices | value, yoy | NSA | NSA | no (IPV tables 80270, 79540: none) | IPV1209, IPV1376 |
| ine.tourist_arrivals, tourist_spending | value, yoy, sum_12m | NSA | NSA | no (no adjusted series found in FRONTUR or EGATUR; see "Not verified") | FREG337/321, FREG647/623 |
| ine.hotel_overnight_stays | value, yoy, sum_12m | NSA | NSA | Total only: EOT44180 (SCA overnight stays) exists but was **discontinued in March 2022** (last observation 2022-03). Residents and non-residents: none | EOT25, EOT33, EOT41 |
| ine.housing_transactions | value, yoy, sum_12m | NSA | NSA | no (ETDP tables 6150, 6155, 49280: none) | ETDP1824-1826 |
| ine.mortgages | value, yoy, sum_12m, avg_amount | NSA | NSA | no (HPT tables 13896, 76316: none) | HPT34618, HPT34565 |
| ine.companies | value, yoy, sum_12m | NSA | NSA | no (SM tables 13912, 13916: none) | SM21483, SM21486 |
| ine.household_saving_rate | value | SCA | SCA | yes, used | CTNFSI11270 |
| ine.population_nationality | value, yoy | NSA | NSA | no (population stocks) | ECP4961, ECP4901, ECP701 |

### Eurostat

`s_adj` categories are those the dataset offers for the pinned slice (JSON-stat dimension, `geo=ES`).

| Dataset | Fields | Before | After | Variants in the dataset | Filter |
|---|---|---|---|---|---|
| eurostat.gdp_growth | qoq | SCA | SCA | NSA, SA, CA, SCA | namq_10_gdp `s_adj=SCA` |
| eurostat.gdp_index | value | SCA | SCA | NSA, SA, CA, SCA | namq_10_gdp `s_adj=SCA` |
| eurostat.industrial_production | value, yoy | SCA | SCA | NSA, CA, SCA | sts_inpr_m `s_adj=SCA` |
| eurostat.economic_sentiment | value, yoy | SA | SA | NSA, SA (no SCA) | ei_bssi_m_r2 `s_adj=SA` |
| eurostat.unemployment | value, yoy_pp | SA | SA | NSA, SA, TC | une_rt_m `s_adj=SA` |
| eurostat.employment_growth | qoq | SCA | SCA | NSA, SA, CA, SCA | namq_10_a10_e `s_adj=SCA` |
| eurostat.labor_participation | value, yoy_pp | SA | SA | NSA, SA, TC | lfsi_emp_q `s_adj=SA` |
| eurostat.hicp, core_inflation, hicp_energy | yoy | NSA | NSA | no `s_adj` dimension (prc_hicp_minr) | — |
| eurostat.producer_prices | value, yoy | NSA | NSA | NSA only | sts_inppd_m `s_adj=NSA` |
| eurostat.trade_balance | balance, exports, imports | NSA | **SCA** | `indic_et` TRD_VAL, TRD_VAL_SCA, … | `indic_et=TRD_VAL_SCA` |
| eurostat.government_debt | value, yoy_pp | NSA | NSA | no `s_adj` dimension (gov_10q_ggdebt) | — |
| eurostat.budget_deficit | value | annual | annual | not applicable | — |
| eurostat.consumer_confidence | value, yoy_diff | SA | SA | NSA, SA | ei_bsco_m `s_adj=SA` |
| eurostat.retail_trade | value, yoy | SCA | SCA | NSA, CA, SCA | sts_trtu_m `s_adj=SCA` |
| eurostat.house_prices | value, yoy | NSA | NSA | no `s_adj` dimension (prc_hpi_q) | — |
| eurostat.gdp_per_capita_pps, labour_productivity_pps, rd_expenditure | value | annual | annual | not applicable | — |
| eurostat.youth_unemployment | value, yoy_pp | SA | SA | NSA, SA, TC | une_rt_m `s_adj=SA` |
| eurostat.long_term_unemployment | value, yoy_pp | SA | SA | NSA, SA, TC | une_ltu_q `s_adj=SA` |

### Banco de España

| Dataset | Fields (after) | Adjustment | Adjusted variant available? | Evidence |
|---|---|---|---|---|
| Euribor (5 daily, 1 monthly), €STR, Spanish bond and bill yields (8 daily, 1 monthly), DE/FR/IT 10Y, spreads, yield curve | unchanged | market prices: not applicable, no note | — | — |
| bde.mortgage_rate, consumer_credit_rate, corporate_lending_rate, household_deposit_rate, household_overnight_deposit_rate | value, yoy_pp | NSA | no (BdE and the ECB publish interest rate statistics unadjusted) | descriptions "TEDR … Nuevas operaciones", no adjusted code |
| bde.credit_households_total, credit_nfc_total | value, yoy | NSA | no | "Ajuste: Datos originales sin ajustar"; `DCF_M.Y.ES…` / `DCF_M.S.ES…` return 404 |
| bde.household_debt_gdp, nfc_debt_gdp | value, yoy_pp | NSA | no | — |
| bde.current_account_balance | value, sum_12m | NSA | no: `DEEM.Y/S/W.ES…` return 404 | "Ajuste: Sin ajuste de estacionalidad" |
| bde.tourism_receipts | value, yoy | NSA | no: `DEEM.Y/S/W.ES…` return 404 | "Ajuste: Sin ajuste de estacionalidad" |
| bde.npl_ratio | value, yoy_pp | NSA | no | — |
| bde.government_debt_pde | value, yoy | NSA | no | — |
| bde.social_security_affiliates, registered_unemployment | — | out of scope (lead) | — | — |

### Yahoo Finance

All 31 datasets are market prices. They have no adjustment concept, so they are unchanged and carry no note.

## Decisions and exceptions

- **`ine.cpi_ccaa.mom` and `ine.ipri.mom` are kept on original data.** INE publishes no adjusted CPI or IPRI, and the official headline of both is the unadjusted monthly rate. The IPRI September 2026 press release headlines "La tasa mensual de los precios industriales fue del 4,0%". The note says "Datos originales".
- **Bank interest rates (MIR) and debt ratios:** their period-on-period changes were removed (rule 1). The tiles use the change on a year earlier, which is legitimate on original data. They were not treated as market prices because they are statistics of bank operations, not traded prices.
- **EPA employment** comes from a workbook, not an API. The new fetcher `src/fetchers/ine_epa_sa.py` uses only the standard library. It checks the sheet title, the header, at least 40 quarters and unique periods. On any failure it keeps the cached file and logs "failed", which gives exit code 3. The published window stays at 40 quarters, like the other EPA series. The workbook says "desestacionalizadas" and does not mention calendar adjustment, so the note says "Datos corregidos de efectos estacionales".
- **EPA rates have no adjusted variant.** An adjusted unemployment rate could be derived from the adjusted employment and unemployment levels, but that is not an official series, so it is not computed.
- **Hotel overnight stays** stay on original data. INE's only adjusted national series (EOT44180, total) stopped in March 2022.
- **Trade:** the processor now refuses a raw file that is not `TRD_VAL_SCA`, so a stale cache from before the switch can never be published as adjusted data.
- **Identity otherwise unchanged:** the concept, geography, unit and base are the same for every switched series. For ETCL, the original variant in the new tables equals the old series exactly.

## Oracle changes (`scripts/audit/`)

- `check_ine.py`:
  - ICN2412 → ICN2920 and IAS3856 → IAS4004, with the "Datos ajustados de estacionalidad y calendario" token required.
  - ETCL68/67/925 → ETCL13714/13712/13732, plus their published yoy ETCL13713/13711/13731 as level checks.
  - `ine.gdp` yoy/qoq move from "official" (recomputed vs published) to "level" (CNTR6654/6653).
  - `ine.employed` drops EPA387796. The new `check_epa_sa()` downloads the workbook, parses it with its own stdlib code (no `src/` import), asserts the title, sheet and column, and compares the last 24 quarters.
- `check_eurostat.py`: trade uses `indic_et=TRD_VAL_SCA`. Identity now fails unless the category label says "Seasonally and calendar adjusted".
- `check_transforms.py`:
  - `ine.gdp` yoy/qoq and the ETCL yoy are added to `OFFICIAL`.
  - New `adjustment_notes()`: every non-market field must carry one adjustment phrase.
  - No `mom`/`qoq`/`mom_pp`/`qoq_pp` may be on original data, except `ine.cpi_ccaa.mom` and `ine.ipri.mom`.
  - The switched datasets must say SCA (or SA for `ine.employed`).

## Verification

- `run_pipeline.py`: exit 0, 125 datasets.
- `validate_contract.py --strict`: 0 errors, 0 warnings.
- `smoke_test.py --run-processors`: OK.
- Unit tests: 33 OK, including 5 new tests for the EPA workbook parser.
- `check_all.py`: 0 FAIL. The 4 WARNs predate this pass: tourism 2-decimal display, CPI contribution additivity, and the yield-curve text.
- Browser: every page at 375 and 1440 px.
- Failure path: an unreachable workbook URL logs "INE employed_sa: fetch failed …" and leaves `employed_sa_raw.csv` unchanged.

## Not verified

- FRONTUR and EGATUR "Resultados detallados mensuales" (tables 13884 and 75723) cannot be listed through the API ("restricciones de volumen"). A search of every FRONTUR series name (operation 330) found no adjusted series, but that search was cut short by a timeout. EGATUR (operation 329) has none.
- The adjusted ETCL cost per hour (4.4 % yoy) was checked against the INE API, not against press-release text.
- No adjusted MIR interest rates, credit stocks or debt ratios were found at BdE. This rests on the series descriptions and on 404s for the adjusted SDMX keys; the BdE catalogue was not searched exhaustively.
