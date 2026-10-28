# ext/bde: new Banco de España datasets

Branch `ext/bde`, 2026-10-28. All series codes were found in the Boletín Estadístico chapter CSVs and verified against the BdE API (`listaSeries`, `rango=MAX`). Dates are first day of period, no forward fill.

## Datasets

| id | title_es | freq | series | fields | last_observation | series codes |
|---|---|---|---|---|---|---|
| bde.npl_ratio | Ratio de créditos dudosos | M | es | value (pct), yoy_pp (pp) | 2026-08-01 | D_BEEA2020 |
| bde.spread_10y_de | Diferencial de rentabilidad a 10 años: España frente a Alemania | M | es | value (pp), chg_1m (pp), chg_1y (pp) | 2026-09-01 | D_1NBBO320 - D_1NBBO308 |
| bde.spread_10y_it | Diferencial de rentabilidad a 10 años: España frente a Italia | M | es | value (pp), chg_1m (pp), chg_1y (pp) | 2026-09-01 | D_1NBBO320 - D_1NBBO309 |
| bde.social_security_affiliates | Afiliados a la Seguridad Social | M | es | value (persons, scale 0), yoy (pct_change) | 2026-09-01 | DEPSEGS1AF_XRTODS.M |
| bde.registered_unemployment | Paro registrado | M | es | value (persons, scale 0), yoy (pct_change) | 2026-09-01 | D_1JA0D000 |
| bde.government_debt_pde | Deuda de las Administraciones Públicas (PDE) | M | es | value (EUR, scale 6), yoy (pct_change) | 2026-08-01 | DMNPDE2010_P00000_PS_APU |

Ids, series keys and field keys are as requested.

## Deviations and decisions

- **NPL ratio**: the series is the Boletín 4.3 headline, "entidades de crédito y EFC" (créditos dudosos a otros sectores residentes / crédito total). The older "entidades de depósito" concept has no published ratio, only amounts (table 4.14); the credit-institution ratio is the current BdE headline. Description and title say "entidades de crédito".
- **Spreads**: computed from the monthly BdE series for Spain (`D_1NBBO320`, same table as Germany and Italy, Maastricht long-term yield, monthly average) and not from the daily `spain_10y_bond` (D_G0B1F0ZP): Germany and Italy are only monthly in BdE, so the frequency is monthly, and using the monthly Spain series keeps one definition on both legs. The monthly mean of the daily Spanish yield equals the monthly series (Jul 3.53, Aug 3.64, Sep 3.93). Inner join on dates, rounded to 2 decimals. `chg_1m` and `chg_1y` are differences against the previous month and the same month a year earlier on a complete calendar (month-based, since monthly). The Spain-Italy spread is negative (Spain pays less).
- **Affiliates**: the BdE API only has "afiliados a fin de mes, total regímenes", not seasonally adjusted. There is no average-monthly or seasonally adjusted affiliates series in the BdE API (searched Boletín chapters 1-26 for "afiliad", "cotizant", "ocupados ... Seguridad Social"; only table 24.19 matches). Table header says "Miles de personas" but the values are persons; `scale` is 0. The headline press figure (afiliados medios) is therefore not the same number: end of month is higher or lower than the average by some tens of thousands.
- **Paro registrado**: end-of-month, not seasonally adjusted (table 24.15, D_1JA0D000).
- **PDE debt**: source unit is thousands of EUR; the processor divides by 1000 (`value_divisor` in `BDE_INDICATORS`), so `scale` 6 is correct.
- **Bug fix on existing datasets**: `bde.france_10y_bond` used `D_1NBBO314`, which is Finland; it is now `D_1NBBO303` (France). `bde.italy_10y_bond` used `D_1NBBO316`, which is Portugal; it is now `D_1NBBO309` (Italy). Their values change (France Sep 2026: 4.44; Italy Sep 2026: 4.36) and Italy now reaches 2026-09-01, so the earlier staleness warning for Italy disappears. Frontend pages using these datasets should be checked.

## Checks

- `run_pipeline.py --sources bde`: exit 0, 111 datasets.
- `validate_contract.py --strict`: 0 errors, 0 warnings (no `bde/*` staleness; the five warnings in `ws-bde.md` no longer appear on 2026-10-28).
- `smoke_test.py --run-processors`: passes.
- Spot checks against the Boletín CSV and the API: NPL ratio Aug 2026 2.53 (Jul 2.51); affiliates Sep 2026 22,364,242 (Sep 2025 21,622,569, yoy 3.43 %); paro registrado Sep 2026 2,379,505 (yoy -1.74 %); PDE debt Aug 2026 1,749,584.76 million EUR (yoy 2.95 %, equal to the BdE published rate); Spain 10Y Sep 3.93 minus Germany 3.47 = 0.46; minus Italy 4.36 = -0.43.

## Caveats

- Publication lags: NPL and PDE debt Aug 2026; affiliates, paro and monthly yields Sep 2026.
- History is 60 months (fetch window), so `yoy` is empty in the first 12 rows of each series.
