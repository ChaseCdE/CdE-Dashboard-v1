# ws/bde: Phase 2 notes

Branch `ws/bde`, 2026-10-28. Scope: BdE fetcher, processor, export mapping.

## Datasets

31 datasets in `site/data/bde/`. Id = `bde.<CSV stem without _processed>`. One series each (key `es`; `ea` for Euríbor and €STR; `de`, `fr`, `it` for the foreign 10Y yields). Fields are defined in `src/export/bde.py`, metadata in `BDE_EXPORT_META`.

| id | title_es | frequency | fields | series (BdE code) | last_observation |
|---|---|---|---|---|---|
| bde.consumer_credit_rate | Tipo de interés del crédito al consumo | M | value, change | DN_1TI2T0138 | 2026-08-01 |
| bde.corporate_lending_rate | Tipo de interés de los préstamos a sociedades no financieras | M | value, change | DN_1TI2T0144 | 2026-08-01 |
| bde.credit_households_total | Crédito a hogares | M | value, mom, yoy | DF_MESNAA20A1U62250Z01E | 2026-08-01 |
| bde.credit_nfc_total | Crédito a sociedades no financieras | M | value, mom, yoy | DF_MESNAA20A1U62240Z01E | 2026-08-01 |
| bde.current_account_balance | Saldo por cuenta corriente | M | value, sum_12m | ver curva (8 códigos) | 2026-07-01 |
| bde.ester_daily | Tipo a corto plazo del euro (€STR) | D | value, change_30d, change_ytd, change_1y | D_DNBAA572 | 2026-10-26 |
| bde.euribor_12m_daily | Euríbor a 12 meses (diario) | D | value, change_30d, change_ytd, change_1y | D_DNBAF172 | 2026-10-26 |
| bde.euribor_12m_monthly | Euríbor a 12 meses (media mensual) | M | value | D_1NBAF472 | 2026-09-01 |
| bde.euribor_1m_daily | Euríbor a 1 mes (diario) | D | value | D_DNBAC172 | 2026-10-26 |
| bde.euribor_1w_daily | Euríbor a 1 semana (diario) | D | value | D_DNBAS172 | 2026-10-26 |
| bde.euribor_3m_daily | Euríbor a 3 meses (diario) | D | value, change_30d, change_ytd, change_1y | D_DNBAD172 | 2026-10-26 |
| bde.euribor_6m_daily | Euríbor a 6 meses (diario) | D | value | D_DNBAE172 | 2026-10-26 |
| bde.france_10y_bond | Rentabilidad de la deuda pública a 10 años: Francia (mensual) | M | value | D_1NBBO314 | 2026-08-01 |
| bde.germany_10y_bond | Rentabilidad de la deuda pública a 10 años: Alemania (mensual) | M | value | D_1NBBO308 | 2026-09-01 |
| bde.household_debt_gdp | Deuda de los hogares sobre el PIB | Q | value, change | DMZ10S80ZH0_TPRPIB.Q | 2026-04-01 |
| bde.household_deposit_rate | Tipo de interés de los depósitos a plazo de los hogares | M | value, change | DN_1TI2T0024 | 2026-08-01 |
| bde.household_overnight_deposit_rate | Tipo de interés de los depósitos a la vista de los hogares | M | value, change | DN_1TI1T0010 | 2026-08-01 |
| bde.italy_10y_bond | Rentabilidad de la deuda pública a 10 años: Italia (mensual) | M | value | D_1NBBO316 | 2026-07-01 |
| bde.mortgage_rate | Tipo de interés de los préstamos para vivienda | M | value, change | DN_1TI2T0135 | 2026-08-01 |
| bde.nfc_debt_gdp | Deuda de las sociedades no financieras sobre el PIB | Q | value, change | DMZ10S80ZN0_TPRPIB.Q | 2026-04-01 |
| bde.spain_10y_bond | Rentabilidad del bono español a 10 años | D | value, change_30d, change_ytd, change_1y | D_G0B1F0ZP | 2026-10-23 |
| bde.spain_10y_bond_monthly | Rentabilidad de la deuda pública a 10 años: España (mensual) | M | value | D_1NBBO320 | 2026-09-01 |
| bde.spain_15y_bond | Rentabilidad del bono español a 15 años | D | value | D_G0B1F0ZQ | 2026-10-23 |
| bde.spain_2y_bond | Rentabilidad de la deuda española a más de 2 años | D | value | D_G0B1F0ZE | 2026-10-23 |
| bde.spain_3y_bond | Rentabilidad del bono español a 3 años | D | value | D_G0B1F0ZN | 2026-10-23 |
| bde.spain_5y_bond | Rentabilidad del bono español a 5 años | D | value, change_30d, change_ytd, change_1y | D_G0B1F0ZO | 2026-10-23 |
| bde.spain_tbill_1y | Rentabilidad de las Letras del Tesoro a 1 año | D | value | D_DTES00U7 | 2026-10-23 |
| bde.spain_tbill_3m | Rentabilidad de las Letras del Tesoro a 1-3 meses | D | value | D_DTES00B7 | 2026-10-23 |
| bde.spain_tbill_6m | Rentabilidad de las Letras del Tesoro a 6 meses | D | value | D_DTES00S7 | 2026-10-23 |
| bde.tourism_receipts | Ingresos por turismo | M | value, yoy | ver curva (8 códigos) | 2026-07-01 |
| bde.yield_curve | Curva de rendimientos de la deuda pública española | X | yield | ver curva (8 códigos) | 2026-10-23 (as_of) |

Field meanings: `change` = difference vs previous period, `pp`; `change_30d`, `change_ytd`, `change_1y` = difference vs the last observation on or before 30 days ago, 31 December of the previous year, and the same date one year ago, `pp`; `mom`, `yoy` = % change; `sum_12m` = rolling 12-month sum. The yield curve has x = maturity in years, field `yield`, `as_of` 2026-10-23.

Units: credit to households and both balance-of-payments series are millions of EUR (`currency` EUR, `scale` 6). Credit to non-financial corporations is billions of EUR (`scale` 9). Debt/GDP and rates are `pct`.

## Fixes

- `pct_change` FutureWarnings (`bde_processor.py:138,151`, plus `resample_to_monthly`): `fill_method=None` everywhere.
- Gaps: monthly, quarterly and annual series are reindexed to the full calendar before any shift, so a missing period gives NaN growth instead of a rate across the gap; the placeholder rows are dropped afterwards (`_drop_filler`). Rolling means and the 12-month sum are NaN if the window contains a gap. Currently no series has a gap.
- Blank values (18 non-publication days in the Euríbor daily series, for example) are dropped as non-observations instead of carrying a NaN row.
- Daily YoY used 252 rows as "one year", which is wrong when days are missing. It is now the change against the last observation on or before the same date a year earlier (`_lookup_asof`).
- Time zone: the `bde_processor.py:105` UserWarning came from `to_period` on tz-aware UTC timestamps. The API stamps 10:15 Madrid time, expressed as 08:15Z or 09:15Z, so the UTC date equalled the local date and no date was shifted. Even so, the client now converts to Europe/Madrid and stores plain dates (`to_local_date`), and the processor does the same for old raw files. Processed CSVs carry naive `YYYY-MM-DD` dates.
- Yield curve: all maturities now use one date (the most recent date for which all eight have data) and the last observation on or before it, instead of each series' own last row. `as_of` = 2026-10-23, which is the correct calendar date (it was the UTC timestamp 08:15Z before).

## Decisions

- Only displayed derived columns are exported. Moving averages, `spread_to_avg`, `cumulative_growth_pct`, `distance_from_peak/trough` are still in the processed CSVs but not exported.
- The old KPI cards showed `change_pct or yoy_change_pct`. For rates and debt ratios the contract field is the change in percentage points (`change`), not the % change of a rate, which is not meaningful. Credit stocks keep `mom` and `yoy` (the old growth chart plots `yoy`).
- Tourism receipts export `yoy` rather than month-on-month (strong seasonality). Current account exports `value` and `sum_12m` only; a growth rate of a balance that changes sign is undefined.
- The Markets table showed 30-day, year-to-date and 1-year changes for €STR, Euríbor 3M and 12M, and the Spain 5Y and 10Y yields. They are exported as the `change_30d`, `change_ytd`, `change_1y` fields (pp, the old page showed basis points: multiply by 100 for display) because the frontend may not compute them. Other daily series export `value` only.
- Not exported: `*_comparison.csv`, `bde_summary.csv`, `yield_curve` history (the dataset is the latest snapshot).
- `source.url` points to the BdE topic page of each series family (tipos-interes, mercados-financieros, instituciones-financieras, cuentas-financieras, estadisticas-exteriores); all return 200. BdE has no stable per-series public page.

## Staleness (validator thresholds, 2026-10-28)

`validate_contract.py --strict` reports five warnings for `bde/*`. They are BdE publication lags, not pipeline faults: the raw API returns no later observation (checked with `rango=MAX`).

| dataset | last observation | age | limit | reason |
|---|---|---|---|---|
| bde.current_account_balance | 2026-07-01 | 119 d | 100 | balance of payments published about 2 months after the month end |
| bde.tourism_receipts | 2026-07-01 | 119 d | 100 | same |
| bde.italy_10y_bond | 2026-07-01 | 119 d | 100 | Italy lags Spain (Sep), Germany (Sep), France (Aug) in BdE's international series |
| bde.household_debt_gdp | 2026-04-01 | 210 d | 200 | Q2 2026 is the latest quarter; age is measured from the first day of the quarter |
| bde.nfc_debt_gdp | 2026-04-01 | 210 d | 200 | same |

All other BdE datasets are inside the limits (daily: 2026-10-23/26; monthly: 2026-08/09).

## Remaining issues

- `spain_2y_bond` (D_G0B1F0ZE) is "bonds and notes with more than 2 years", an aggregate and not a 2Y benchmark; `spain_tbill_3m` is Letras of 1 to 3 months. Both feed the yield curve at 2.0 and 0.25 years. Labelled in the descriptions; the 2Y point is a loose proxy.
- Daily history is 36 months, monthly 60 months (fetch window in `bde_client.get_appropriate_range`); raw daily history is not accumulated across runs.
- Euríbor and bond dailies are published with a lag of 1 to 3 business days (Euríbor 26 Oct, bonds 23 Oct on 28 Oct).
- Spot check, 2026-10-28: Euríbor 12M 3.225 (2026-10-26) and Spain 10Y 4.07 (2026-10-23) in `site/data` equal the live API values.

## Requests

REQUEST → ws/frontend: the validator's Q threshold (200 days) measured from the first day of the quarter always flags the latest quarter for the last ~20 days before the next publication; the debt/GDP warnings are structural. Either accept them for `bde.*_debt_gdp` or raise the Q limit to about 230 days (needs a contract/validator change, not ours).
REQUEST → ws/frontend: Markets-table changes for rates are in pp; multiply by 100 for "pb".
