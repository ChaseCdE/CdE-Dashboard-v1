# Pipeline audit: "La economía en datos"

Independent audit of the data pipeline (fetch, process, export) and of the 125 datasets in `site/data/`, run on 2026-10-28 against the live INE, Eurostat, Banco de España and Yahoo Finance APIs. Branch `audit/pipeline`. The pipeline code was not modified.

## Verdict: FAIL

Three published datasets contain wrong numbers for what they claim to show, two of them on headline charts (the unemployment chart on the Portada page and the GDP demand-contribution chart on Actividad). The pipeline itself runs cleanly, and 109 of 125 datasets pass every check. A source failure, however, does not stop a run: the site is then republished with old data and a new timestamp.

| Severity | Count |
|---|---|
| CRITICAL (wrong number published) | 3 |
| HIGH (wrong label/definition, silent staleness) | 2 |
| MEDIUM (fragility likely to break / misleading derived data) | 6 |
| LOW (cosmetic) | 6 |

## How this was checked

- **Pipeline run**: `run_pipeline.py --sources ine` (39 s) and `--sources eurostat bde yahoo` (55 s) both exit 0. `validate_contract.py --strict` reports 0 errors and 0 warnings, and `smoke_test.py --run-processors` passes. Re-running reproduces the committed `site/data` exactly, apart from 5 ETF datasets whose dividend-adjusted history is recomputed by Yahoo (see H2).
- **Oracle** (`scripts/audit/`, uses only requests and pandas, imports nothing from `src/`): `python scripts/audit/check_all.py [--coverage] [--offline]` exits 1 on any FAIL.
  - `check_ine.py`: pins the INE series code for every published series and field (133 series). It asserts the INE series name (identity: geography, concept, SA/NSA, unit), dates periods from `Anyo`+`FK_Periodo`, compares the last 24 observations, and compares computed rates with INE's published rates. It also recomputes `gdp_productivity`, `mortgages.avg_amount` and the CPI weights from the API.
  - `check_eurostat.py`: JSON-stat API with every non-geo/time dimension pinned. A dimension with more than one category is an identity FAIL. It compares levels and recomputes `yoy`, `*_pp`, `*_diff`, the 2019Q1 rebasing and the trade balance.
  - `check_bde.py`: BdE `listaSeries`, checking the Spanish description and unit symbol (identity) and values×scale. It recomputes the spreads and the yield curve snapshot.
  - `check_yahoo.py`: Yahoo chart API without yfinance. It checks name, currency and instrument type, the close against the traded and adjusted close, and the exchange-local session dates.
  - `check_cross.py`: same quantity from two official sources. BdE 10Y yields vs Eurostat `irt_lt_mcby_m` (ES/DE/FR/IT), Eurostat HICP vs INE IPCA8090, Eurostat GDP q/q vs INE CNTR6653.
  - `check_transforms.py` (offline): recomputes every derived field over the whole published history from the published levels. It also checks period-start dating, sort order and uniqueness, units against key naming, "Base YYYY = 100" notes (the base year must average 100) and manifest vs file, plus two additivity checks.
- **Press releases**: the published headline figures match INE CPI September 2026 (CPI 4.9 %, core 3.1 %, HICP 5.0 %; https://ine.es/dyngs/Prensa/en/IPC0926.htm), EPA Q2 2026 (unemployment 9.87 %, employed 22,779 thousand; https://ine.es/dyngs/Prensa/en/EPA2T26.htm) and the Euribor 12M September 2026 monthly average (3.247 %; https://www.hipotecas.me/euribor-hoy/euribor-septiembre-2026, a secondary source; the same figure comes from BdE D_1NBAF472).
- **Failure test**: the full pipeline was run with all four APIs unreachable (proxy pointed to a closed port). See H1.
- **Earlier fixes, verified**:
  - France and Italy 10Y now equal Eurostat FR/IT (max diff 0.005).
  - Retail sales is ICM4062 (General, constant prices, SA).
  - The trade balance uses `bclas_bec=TOTAL, partner=WORLD`.
  - The yield curve no longer uses the "más de 2 años" series.
  - No Yahoo date falls on a weekend, and Yahoo dates equal the exchange-local sessions.

## Findings

| # | Sev. | Dataset | Finding and evidence | Root cause | Recommended fix |
|---|---|---|---|---|---|
| C1 | CRITICAL | eurostat.unemployment | The data shown as "Tasa de paro" (Portada chart "Tasa de paro, España y UE-27"; UE tiles "Tasa de paro, España") is the **25-74** sub-population. Aug 2026: published ES 8.9 % / EU27 5.2 %. The headline harmonised rate (`une_rt_m`, `age=TOTAL`, 15-74) is **10.0 % / 6.1 %**. Max gap 1.2 pp (Oct 2024: 9.7 vs 10.9). `yoy_pp` also differs (up to 0.2 pp). | `src/fetchers/eurostat_indicators.py:189` `'age': ['Y25-74']  # (Y15-74 not available)`. The headline code is `TOTAL`, not `Y15-74`. The title in `src/export/eurostat.py:123` does not say 25-74. | Use `age=TOTAL`. Update the description and note to "15 a 74 años". |
| C2 | CRITICAL | ine.ipss_sectors (`mayoristas`) | The series labelled "Comercio mayorista" is IPSS487/486, **section G** (wholesale + retail + motor vehicles). Wholesale trade (CNAE 46) is IPSS469/468. Aug 2026 yoy: published -1.9 vs wholesale -3.4. Mar 2025: 7.1 vs 9.7. ytd up to 2.1 pp off. | `src/processors/ine_processor.py:1064`: the substring `"Comercio al por mayor"` first matches "Comercio al por mayor **y al por menor**; reparación…", and the first match is taken. | Pin codes IPSS469/IPSS468, or anchor the pattern to "Comercio al por mayor e intermediarios". Also see L4. |
| C3 | CRITICAL | ine.gdp_demand | The contributions are from **non-seasonally-adjusted** data (CNTR7001/7031/7056/7105), and inventories are omitted. The Actividad stacked chart draws them against the SA GDP yoy line (`ine.gdp`) as the total. Bars minus line: 2024Q4 4.75 vs 3.72; 2026Q1 3.02 vs 2.62. They are not INE's headline contributions (SA, CNTR7160/7190/7215/7264): private consumption 2026Q1 published 1.88 vs INE SA 1.65; max diff 2.13 pp. Missing inventories contribution (CNTR7262): 0.07-0.31 pp. | `src/processors/ine_processor.py:942-963`: there is no SA/NSA filter, and `iloc[0]` takes the first matching code, which is NSA in table order. | Use the SA codes and add "Variación de existencias" (CNTR7262), or plot national and external demand (CNTR7150 + CNTR7264). State "corregidos de estacionalidad y calendario". |
| H1 | HIGH | all (pipeline) | **Silent staleness on source failure.** With all four APIs unreachable, `run_pipeline.py` **exits 0**. The summary shows Fetch **[OK]** for Eurostat, BdE and Yahoo (only INE shows [FAIL]), and `site/data` is rebuilt from cached raw files with a fresh `generated_at` and identical data. The validator passes. In CI the commit step would push a "Data refresh" and deploy. A missed monthly release is flagged only 100 days after the period ends (Q: 200, A: 550). An INE exception aborts all remaining INE fetches, which then keep old raw files. | `run_pipeline.py:192` (exit code ignores fetch results). `src/fetchers/eurostat_client.py:56`, `bde_client.py:84-92` and `yahoo_client.py:89` swallow errors. `_save_csv` keeps cached data on empty results (`ine_indicators.py:116`, `bde_indicators.py:612`, `eurostat_indicators.py:97`, `yahoo_indicators.py:488`). | Make a fetch failure fail the run, or per dataset record `fetched_at` / `source_ok` and refuse to publish. Count fetch failures in the exit code. Show the fetch date in the frontend. |
| H2 | HIGH | yahoo.euro_govt_bond_etf, us_treasury_20y_etf, us_treasury_7_10y_etf, spanish_banks_etf, european_banks_etf | "Cierre" ("Precio de la participación") is the **dividend-adjusted** close, not the traded price. TLT on 2026-09-24: published 79.10 vs traded 79.42. Over 2 years the gap reaches 7.83 USD (TLT), 7.04 (IEF), 5.46 EUR (EUNH), 2.2 USD (EWP, EUFN). The whole history is rewritten at each distribution, so runs are not reproducible: 356-1353 values changed between two runs on the same day. | `src/fetchers/yahoo_client.py:60`: `history()` with yfinance's default `auto_adjust=True`. | Use `auto_adjust=False` (traded close) for the level. If total return is wanted, export it as a separate, labelled field. |
| M1 | MEDIUM | INE (many) | Series are selected by `str.contains` plus "take the first code" (`filtered["series_code"].iloc[0]`) throughout `ine_processor.py` (e.g. lines 194, 299, 342, 382, 419, 456, 564, 596, 688, 720, 758, 791, 826, 864, 962). The result depends on INE's table ordering and name wording; it caused C2 and C3. The `select_series` helper (line 88), which warns on ambiguity, is unused. | ditto | Pin INE codes (as `check_ine.py` does). Fail if a pattern matches 0 or more than 1 code. |
| M2 | MEDIUM | ine.cpi_ecoicop_groups | Group weights are **hard-coded** (`expected_weights`, `ine_processor.py:1271`). The weights fetched from table 76161 are computed and then ignored. In January 2027 the site will keep showing 2026 weights with no warning. Applying 2026 weights to 2021-2025 makes contributions miss the headline by up to **1.5 pp** (Jul 2022: 9.30 vs 10.8). Last 12 months: ≤0.11 pp. The description says "aproximada", but the chart shows 5 years. | `ine_processor.py:1244-1321` | Use the weights of each year (INE publishes them annually) or restrict the chart to the current year. Use the fetched weights and fail if they are missing. |
| M3 | MEDIUM | bde.credit_households_total, bde.credit_nfc_total | `mom`/`yoy` ("Variación interanual") are changes in the **stock**, so reclassifications, write-offs and securitisations show up as growth. Households yoy 3.88 → 2.38 → 0.79 → 2.53 % (Mar-Jul 2026), following stock jumps (2025-11 +1.99 % m/m, 2025-12 -1.13 %). BdE's own growth rates are transaction-based. Not verified against BdE's official rate (series code not identified). | `bde_processor.py:183-202` (`calculate_changes`, called from `process_credit_data` at :307) | Use BdE's published growth-rate series, or label the field "variación del saldo". |
| M4 | MEDIUM | ine.cpi, retail_sales, house_prices, industrial_production (mom), services_production (mom), tourist_arrivals, tourist_spending | The pipeline recomputes rates from rounded indices instead of using the rates INE publishes. As a result, the displayed (1-decimal) figure occasionally differs from INE's. Retail yoy Mar 2026: 4.35 shown as 4.4 vs INE 4.3. IPI m/m Oct 2025: 0.5 vs 0.6. IPV yoy Jul 2024: 8.2 vs 8.1. IPSS m/m Jan 2025: 1.5 vs 1.6. FRONTUR/EGATUR 2-decimal rates. CPI: no mismatch in 36 months. | `_calculate_yoy_change` / `pct_change_by_date` used where official series exist (ICM4079/4080, IPV1376, IPI15381, IPSS491, FREG321/623, IPC290750) | Fetch INE's published rates. |
| M5 | MEDIUM | ine.gdp_productivity | CNTR codes are hard-coded (`ine_processor.py:1470-1474`, CNTR7659/7818/7896). A missing code only prints "WARNING" and the column becomes empty, so the line disappears silently. Values currently correct (max diff 0.005). | ditto | Assert the presence of every input series. |
| M6 | MEDIUM | all (export) | `build_dataset` silently de-duplicates rows with the same x (keeps the last), so a processor that concatenated two series for one key would publish one of them without error. | `src/export/core.py:201-204` | Raise on duplicate x. |
| L1 | LOW | bde.yield_curve | The description and `source.dataset` still mention the dropped "más de 2 años" point (D_G0B1F0ZE). The data has no 2-year point. | `src/export/bde.py:132-133` | Update the text. |
| L2 | LOW | yahoo.spanish_banks_etf | The id says "banks", but EWP is iShares MSCI Spain (whole market). The title is correct. | `src/export/yahoo.py` | Rename the id (frontend reference). |
| L3 | LOW | yahoo FX/commodities | `ret_1y`/`chg_1y` = 252 sessions. FX trades about 260 sessions a year, so "1 año" covers about 48 weeks. This is documented in `note_es`. | `yahoo_processor.py:122` | Use a calendar-date window (as BdE does). |
| L4 | LOW | ine.ipss_sectors | The intended "total" sector ("Total servicios") is never produced, because the table calls it "Índice General". It is silently missing. | `ine_processor.py:1062` | Pin IPSS490/489, or drop it from the dict. |
| L5 | LOW | ine.cpi, ine.services_production | Stale comments: `TABLE_IDS` says CPI "base 2026" (it is base 2025) and IPSS "base 2015" (it is base 2021). The published notes are correct (the base year averages 100.00). | `ine_indicators.py:38,25` | Fix the comments. |
| L6 | LOW | bde.social_security_affiliates | End-of-month affiliates; the Ministry's headline is the monthly average. The title does not say "a fin de mes" (the description does). | `bde_indicators.py` export meta | Add "(último día del mes)" to the title. |

Other observations (no finding):
- Dating is correct everywhere: periods start on the first day, daily data uses local dates, and the yield-curve snapshot is the latest date common to all maturities.
- Units and scale are correct:
  - EUR millions for EGATUR, the current account and tourism receipts.
  - BdE household credit in EUR millions and NFC credit in EUR billions.
  - PDE debt is converted correctly from BdE's thousands to millions.
  - Registered unemployment: BdE's symbol says "miles", but the values are persons; they are exported correctly as persons.
- Yahoo excludes the current (possibly open) session; dates use the exchange-local calendar.
- Contract rules hold: `sum_12m` is null unless 12 consecutive months exist; all yoy/qoq/mom are date-based with no fill across gaps; contributions = yoy × weight / 100 (exact).

## Coverage (125 datasets)

Status of the worst check of each type: `identity` = source identifier and metadata match the title and labels; `values` = latest ~24 observations equal the API; `transform` = derived fields recomputed; `cross` = second official source; `dating`; `meta` = units, base-year notes, manifest. `-` = not applicable (no field of that type) or covered by another check. Generated by `python scripts/audit/check_all.py --coverage`.

| Dataset | identity | values | transform | cross | dating | meta | Result |
|---|---|---|---|---|---|---|---|
| ine.gdp | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.gdp_demand | PASS | FAIL | FAIL | - | PASS | PASS | FAIL |
| ine.gdp_productivity | PASS | - | PASS | - | PASS | PASS | PASS |
| ine.industrial_production | PASS | PASS | WARN | - | PASS | PASS | WARN |
| ine.ipi_sectors | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.industry_turnover | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.services_turnover | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.services_production | PASS | PASS | WARN | - | PASS | PASS | WARN |
| ine.ipss_sectors | PASS | FAIL | - | - | PASS | PASS | FAIL |
| ine.business_confidence | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.unemployment | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.youth_unemployment | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.employment_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.activity_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.temporary_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.parttime_rate | PASS | - | PASS | - | PASS | PASS | PASS |
| ine.employed | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.labor_cost | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.labor_cost_hour | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.labor_cost_components | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.cpi | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.cpi_special_groups | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.cpi_ecoicop_groups | PASS | PASS | WARN | - | PASS | PASS | WARN |
| ine.cpi_weights | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.cpi_ccaa | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.ipri | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.retail_sales | PASS | PASS | WARN | - | PASS | PASS | WARN |
| ine.house_prices | PASS | PASS | WARN | - | PASS | PASS | WARN |
| ine.tourist_arrivals | PASS | PASS | WARN | - | PASS | PASS | WARN |
| ine.tourist_spending | PASS | PASS | WARN | - | PASS | PASS | WARN |
| ine.hotel_overnight_stays | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.housing_transactions | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.mortgages | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.companies | PASS | PASS | PASS | - | PASS | PASS | PASS |
| ine.household_saving_rate | PASS | PASS | - | - | PASS | PASS | PASS |
| ine.population_nationality | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.gdp_growth | PASS | PASS | - | PASS | PASS | PASS | PASS |
| eurostat.gdp_index | PASS | - | PASS | - | PASS | PASS | PASS |
| eurostat.industrial_production | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.economic_sentiment | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.unemployment | PASS | FAIL | FAIL | - | PASS | PASS | FAIL |
| eurostat.employment_growth | PASS | PASS | - | - | PASS | PASS | PASS |
| eurostat.labor_participation | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.hicp | PASS | PASS | - | PASS | PASS | PASS | PASS |
| eurostat.core_inflation | PASS | PASS | - | - | PASS | PASS | PASS |
| eurostat.producer_prices | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.trade_balance | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.government_debt | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.budget_deficit | PASS | PASS | - | - | PASS | PASS | PASS |
| eurostat.consumer_confidence | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.retail_trade | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.house_prices | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.gdp_per_capita_pps | PASS | PASS | - | - | PASS | PASS | PASS |
| eurostat.labour_productivity_pps | PASS | PASS | - | - | PASS | PASS | PASS |
| eurostat.rd_expenditure | PASS | PASS | - | - | PASS | PASS | PASS |
| eurostat.youth_unemployment | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.long_term_unemployment | PASS | PASS | PASS | - | PASS | PASS | PASS |
| eurostat.hicp_energy | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.euribor_12m_monthly | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.euribor_12m_daily | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.euribor_6m_daily | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.euribor_3m_daily | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.euribor_1m_daily | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.euribor_1w_daily | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.ester_daily | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.spain_10y_bond | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.spain_5y_bond | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.spain_3y_bond | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.spain_2y_bond | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.spain_15y_bond | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.spain_tbill_3m | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.spain_tbill_6m | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.spain_tbill_1y | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.spain_10y_bond_monthly | PASS | PASS | - | PASS | PASS | PASS | PASS |
| bde.germany_10y_bond | PASS | PASS | - | PASS | PASS | PASS | PASS |
| bde.france_10y_bond | PASS | PASS | - | PASS | PASS | PASS | PASS |
| bde.italy_10y_bond | PASS | PASS | - | PASS | PASS | PASS | PASS |
| bde.mortgage_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.consumer_credit_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.corporate_lending_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.household_deposit_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.household_overnight_deposit_rate | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.credit_households_total | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.credit_nfc_total | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.household_debt_gdp | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.nfc_debt_gdp | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.current_account_balance | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.tourism_receipts | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.npl_ratio | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.social_security_affiliates | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.registered_unemployment | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.government_debt_pde | PASS | PASS | PASS | - | PASS | PASS | PASS |
| bde.spread_10y_de | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.spread_10y_it | PASS | PASS | - | - | PASS | PASS | PASS |
| bde.yield_curve | PASS | PASS | - | - | PASS | WARN | WARN |
| yahoo.ibex_35 | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.euro_stoxx_50 | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.stoxx_600 | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.sp_500 | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.nasdaq_composite | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.dax | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.cac_40 | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.ftse_100 | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.vix | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.eur_usd | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.eur_gbp | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.eur_jpy | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.eur_chf | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.gbp_usd | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.usd_jpy | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.dxy | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.brent_crude | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.wti_crude | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.natural_gas | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.gold | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.silver | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.us_tbill_3m | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.us_treasury_5y | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.us_treasury_10y | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.us_treasury_30y | PASS | PASS | PASS | - | PASS | PASS | PASS |
| yahoo.euro_govt_bond_etf | PASS | WARN | PASS | - | PASS | PASS | WARN |
| yahoo.us_treasury_20y_etf | PASS | WARN | PASS | - | PASS | PASS | WARN |
| yahoo.us_treasury_7_10y_etf | PASS | WARN | PASS | - | PASS | PASS | WARN |
| yahoo.spanish_banks_etf | PASS | WARN | PASS | - | PASS | PASS | WARN |
| yahoo.european_banks_etf | PASS | WARN | PASS | - | PASS | PASS | WARN |

## Not verified

- **Older history**: values older than the last ~24 observations (36 for INE official-rate comparisons) were not compared with the APIs. Derived fields were recomputed over the full published history, but only from the published levels.
- **Credit growth**: BdE's official transaction-based credit growth rates were not fetched (M3 is unquantified against them).
- **Data flags**: Eurostat and INE flags (provisional, estimated, break in series) were not checked.
- **Yahoo**: prices were compared only with Yahoo itself, not with exchange or official fixings (e.g., ECB reference rates for FX).
- **CI**: GitHub Actions behaviour (cache save/restore, commit, deploy) was inferred from the workflow files, not executed.
- **Revisions**: no actual source revision happened during the audit. Robustness is inferred from the fact that each run re-downloads the full window (INE `nult`, Eurostat since 2015, BdE 36M/60M, Yahoo 5 years).
- **Frontend**: only the page configs that reference the affected datasets were read, not the rendering.
