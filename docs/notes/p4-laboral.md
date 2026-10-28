# p4-laboral: Mercado laboral

Files: `site/pages/laboral.html`, `site/assets/js/pages/laboral.js`.

## Contents (section, chart, data)
- Indicadores clave (4 KPI): `ine.unemployment`, `ine.employment_rate`, `ine.activity_rate` (`value`, change `yoy_pp`); `ine.employed` (`value`, change `yoy`).
- Empleo y desempleo: line "Tasa de paro, España" (`ine.unemployment` value); bar "Variación interanual de la tasa de paro" (`yoy_pp`, colorBySign neutral); line "Tasas de empleo y de actividad" (`ine.employment_rate`, `ine.activity_rate` value); periodTable last 12 (unemployment, employment, activity).
- Calidad del empleo (3 KPI: `ine.temporary_rate`, `ine.youth_unemployment`, `ine.parttime_rate`, change `yoy_pp`): line temporalidad + parcialidad; line paro juvenil vs total.
- Costes laborales (2 KPI: `ine.labor_cost`, `ine.labor_cost_hour`, change `yoy`): lineChart with toggle Nivel / Variación interanual for each; line `ine.labor_cost_components` `index_2019q1` (total, salarial).
Totals: 9 KPIs, 8 charts, 1 table.

## Not ported
- `ine.cntr_employment`, `ine.population`: not in the manifest or unused.
- Old period select: replaced by the 1A/5A/Máx buttons.

## Test
Served on port 8804, Playwright Chromium, 375 and 1440 px: zero console errors/warnings, zero failed requests or HTTP >= 400, scrollWidth = clientWidth, 8 Plotly plots rendered, no error cards. Screenshots inspected.

## Observations
- At 375 px the KPI value "22,9 M personas" wraps mid-word ("per sonas") in the 2-column KPI grid.
- REQUEST → lead: KPI tile value should not break words at narrow widths (e.g. `overflow-wrap: normal`, or shorter unit text) in main.css.
- Labour-cost index end labels (total and salarial) overlap slightly as the lines coincide.
