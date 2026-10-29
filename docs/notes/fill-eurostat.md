# fill/eurostat: new Eurostat datasets

Branch `fill/eurostat`, 2026-10-29. All codes verified against the JSON-stat API (every non-geo dimension pinned; the oracle `scripts/audit/check_eurostat.py` fails if a dimension is left unpinned). Geographies: `es` = ES, `eu27` = EU27_2020, `de`, `fr`, `it`. History from 2015 (annual from 2005). Adjustment is the best the dataset offers: SCA where published, otherwise SA.

| id | title | freq | series | fields | dataset + filters | latest Spain value | check |
|---|---|---|---|---|---|---|---|
| eurostat.construction_production | Producción en la construcción | M | es, eu27 | value (index, 2021=100), yoy (pct_change) | `sts_copr_m`: indic_bt=PRD, nace_r2=F, unit=I21, s_adj=SCA | 109.4 (2026-08); yoy -6.97 % | oracle PASS (values, yoy) |
| eurostat.capacity_utilization | Utilización de la capacidad productiva en la industria | Q | es, eu27 | value (pct), yoy_pp (pp) | `ei_bsin_q_r2`: indic=BS-ICU-PC, s_adj=SA (no SCA offered) | 78.0 % (2026-Q3); yoy_pp -0.3 | oracle PASS |
| eurostat.bankruptcies | Declaraciones de quiebra | Q | es, eu27 | value (index, 2021=100), yoy | `sts_rb_q`: indic_bt=BKRT, nace_r2=B-S_X_O_S94, unit=I21, s_adj=SCA | 148.9 (2026-Q2); yoy -7.80 % | oracle PASS |
| eurostat.business_registrations | Altas de empresas | Q | es, eu27 | value (index, 2021=100), yoy | `sts_rb_q`: indic_bt=REG, nace_r2=B-S_X_O_S94, unit=I21, s_adj=SCA | 126.1 (2026-Q2); yoy -5.61 % | oracle PASS |
| eurostat.job_vacancy_rate | Tasa de vacantes | Q | es, eu27 | value (pct, 2 decimals), yoy_pp | `jvs_q_nace2`: indic_em=JVR, nace_r2=B-S, sizeclas=TOTAL, s_adj=SA (no SCA offered) | 0.9 % (2025-Q4); yoy_pp 0.0 | oracle PASS |
| eurostat.gov_deficit_quarterly | Saldo de las AAPP (trimestral) | Q | es, eu27 | value (pct of GDP) | `gov_10q_ggnfa`: na_item=B9, sector=S13, unit=PC_GDP, s_adj=SCA | -2.2 % (2026-Q2) | oracle PASS |
| eurostat.interest_expenditure | Gasto en intereses de las AAPP | A | es, eu27, de, fr, it | value (pct of GDP) | `gov_10a_main`: na_item=D41PAY, sector=S13, unit=PC_GDP (annual, no s_adj) | 2.4 % (2025) | oracle PASS |

Notes
- `eurostat.job_vacancy_rate` carries `stale_after_days: 400`. The API (also the unadjusted series, all NACE aggregates, ES and EU27) stops at 2025-Q4, about 300 days after the end of that quarter, beyond the 200-day quarterly allowance. This is a source gap, not a pipeline failure; the allowance should be removed once Eurostat publishes 2026 data.
- Bankruptcies and registrations: the headline aggregate B-S_X_O_S94 (industry, construction and market services, excluding public administration and defence, social security and membership organisations). Level 2021=100; the oracle recomputes `yoy` from the API levels.
- `gov_deficit_quarterly` has no `yoy_pp`, as specified. Spain's NSA value for 2026-Q2 would be -7.2 %: the SCA series is the one published here.
- Construction: Spain's CA and NSA series coincide; SCA is used for both geographies.
- Interest expenditure: DE, FR, IT, ES and EU27 verified through 2025; PT not requested.
- Page agents: ids, series keys and field keys are as listed. Fields `yoy_pp` carry unit `pp`, `yoy` unit `pct_change`.
