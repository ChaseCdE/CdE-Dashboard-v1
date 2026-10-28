# ext/eurostat notes

Branch `ext/eurostat`. Run on 2026-10-28. Six datasets added to `site/data/eurostat/`, contract v1.1 unchanged.

## Datasets

| id | title_es | freq | series | fields | last_observation | dataset + filters |
|---|---|---|---|---|---|---|
| eurostat.gdp_per_capita_pps | PIB per cápita en paridad de poder adquisitivo | A | es, de, fr, it, pt | value (index, UE-27 = 100) | 2025-01-01 | `nama_10_pc`, unit PC_EU27_2020_HAB_MPPS_CP, na_item B1GQ |
| eurostat.labour_productivity_pps | Productividad por hora trabajada en paridad de poder adquisitivo | A | es, de, fr, it, pt | value (index, UE-27 = 100) | 2025-01-01 | `tesem160`, unit PC_EU27_2020_MPPS_CP, na_item NLPR_HW |
| eurostat.rd_expenditure | Gasto en I+D (% del PIB) | A | es, eu27, de, fr, it | value (pct) | 2024-01-01 | `rd_e_gerdtot`, sectperf TOTAL, unit PC_GDP |
| eurostat.youth_unemployment | Paro juvenil (menores de 25 años) | M | es, eu27 | value (pct), yoy_pp | 2026-08-01 | `une_rt_m`, age Y_LT25, unit PC_ACT, s_adj SA, sex T |
| eurostat.long_term_unemployment | Paro de larga duración | Q | es, eu27 | value (pct), yoy_pp | 2026-04-01 | `une_ltu_q`, indic_em LTU, age Y15-74, unit PC_ACT, s_adj SA, sex T |
| eurostat.hicp_energy | Inflación de la energía (IPCA) | M | es, eu27 | yoy (pct_change) | 2026-09-01 | `prc_hicp_minr`, coicop18 NRG, unit RCH_A |

Ids, series keys and field keys are as requested. Annual series start in 2005 (pipeline default is 2015); the rest from 2015.

## Choices

- GDP per capita: `nama_10_pc` instead of `tec00114`. Same measure, but `tec00114` is rounded to integers and starts later; `nama_10_pc` gives one decimal (ES 2025: 91.4 vs 92 in `tec00114`).
- Productivity: per hour worked is available (`NLPR_HW`), so no fallback to per person. Nominal productivity in PPS, which is what the EU27 = 100 comparison uses.
- Long-term unemployment: headline is `une_ltu_q` LTU as % of the active population, 15-74, SA (Spain 3.2%, EU-27 1.9% in 2Q 2026). Quarterly, so `yoy_pp` is the difference with the same quarter a year earlier.
- HICP energy: `prc_hicp_minr` with `coicop18` = `NRG` (Energy). The value already is the annual rate, so the only field is `yoy` (same convention as `hicp`).
- `yoy_pp` computed date-based, no forward fill (existing `_calculate_yoy_change`, kind diff).

## Checks

Latest Spain value, pipeline vs Eurostat dissemination API (same day):

| dataset | period | pipeline | API |
|---|---|---|---|
| gdp_per_capita_pps | 2025 | 91.4 | 91.4 (flag p) |
| labour_productivity_pps | 2025 | 95.3 | 95.3 (flag p) |
| rd_expenditure | 2024 | 1.50 | 1.5 |
| youth_unemployment | 2026-08 | 22.7 | 22.7 (2026-09 not yet published) |
| long_term_unemployment | 2026-Q2 | 3.2 | 3.2 (flag d, definition differs) |
| hicp_energy | 2026-09 | 22.1 | 22.1 |

- `python run_pipeline.py --sources eurostat` exits 0; `scripts/smoke_test.py --run-processors` passes.
- `validate_contract.py --strict`: no errors; one warning (below).

## Caveats

- Staleness: `eurostat/rd_expenditure.json` warns (665 days, limit 550 for A). Eurostat's latest year for Spain in `rd_e_gerdtot` is 2024; 2025 is published around the end of 2026. Not fixable on our side; same false-positive pattern as `budget_deficit` in ws-eurostat.md.
- Provisional data: GDP per capita and productivity 2025 carry flag `p`; long-term unemployment carries flag `d` (definition differs) for recent quarters; R&D recent years may be estimates. The flags are only noted (`note_es`), nothing dropped.
- Youth unemployment is volatile (small base, monthly); EU-27 latest month can lag Spain by one month.
- No euro area series, same as the rest of the Eurostat set.

## Skipped

Nothing.
