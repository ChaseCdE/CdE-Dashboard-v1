# fill/bde: new business volumes (nuevas operaciones)

Three monthly datasets, series `es`, fields `value`, `sum_12m`, `yoy` (in that order). All are flows of new lending, original data (sin corregir de estacionalidad), not the outstanding stock. Ten years of history (2016-11 to 2026-08). No `mom`.

| id | title | series code | unit / scale | latest value | check |
|---|---|---|---|---|---|
| bde.new_housing_loans | Nuevo crédito a hogares para vivienda | DN_1TI2TIE96 | EUR, scale 6 (millones) | 2026-08: 4.432 M EUR; sum_12m 83.865; yoy +1,1 % | oracle PASS (identity, values maxdiff 0, sum_12m maxdiff 0, yoy, notes) |
| bde.new_consumer_loans | Nuevo crédito al consumo de los hogares | DN_1TI2TIE99 | EUR, scale 6 (millones) | 2026-08: 3.322 M EUR; sum_12m 49.502; yoy +6,5 % | oracle PASS |
| bde.new_corporate_loans | Nuevo crédito a sociedades no financieras | DN_1TI2TIE105 | EUR, scale 6 (millones) | 2026-08: 22.539 M EUR; sum_12m 451.155; yoy -0,3 % | oracle PASS |

## Definition choices

- Series are BdE "Importes totales estimados" of "Nuevas operaciones" (Boletín Estadístico 19.11 / 19.12), found in the BdE series catalogue and verified through `listaSeries` (descriptions, unit "Millones de euros", `M  EUR`, monthly).
- "Nuevas operaciones" is the total including renegotiations (ECB definition of new business). Housing: 4.432 = 4.182 (`DN_1TI2TIE98`, otras operaciones) + 250 (`DN_1TI2TIE97`, renegociados) in 2026-08. These are the volumes that go with the rates `mortgage_rate` (DN_1TI2T0135), `consumer_credit_rate` (0138) and `corporate_lending_rate` (0144), which carry the same label.
- Consumer credit excludes overdrafts and revolving/deferred-payment cards (published separately: DN_1TI2T0141, DN_1TI2TIE80).
- Corporate: the BdE total for NFCs (series starts 2010-06; the size split is published only as rates, not volumes).
- `sum_12m` is null unless 12 consecutive months exist (first 11 months of the window are null, as the window is trimmed to ten years). `yoy` is the relative change of `value` against the same month of the previous year (never of the 12-month sum).
- Monthly volumes are strongly seasonal (August is low); compare like with like (yoy or sum_12m).

## Changes

- `src/fetchers/bde_indicators.py`: three `BDE_INDICATORS` (category `new_business`), group, export meta (`kind="new_business"`).
- `src/processors/bde_processor.py`: category `new_business` uses `process_balance_data` (value, rolling 12m sum, yoy).
- `src/export/bde.py`: fields for `new_business`; every `note_es` states original data, new business (nuevas operaciones) and not the outstanding stock.
- `scripts/audit/check_bde.py`: per dataset identity, values (24 months), contract keys/units, notes, `sum_12m` (36 months), `yoy` (36 months), history.
