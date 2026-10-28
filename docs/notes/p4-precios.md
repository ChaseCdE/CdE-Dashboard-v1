# Phase 4: Precios (`site/pages/precios.html`, `site/assets/js/pages/precios.js`)

## What the page shows
- KPIs (7): `ine.cpi_special_groups` headline/core `yoy`; `ine.ipri` `total` and `total_sin_energia` `yoy` (change `mom`); `ine.house_prices` `es` `yoy`; `eurostat.hicp` `es` and `eu27` `yoy`.
- Inflación general y subyacente: line `ine.cpi_special_groups` headline+core `yoy` (ref 2 %); bars `ine.cpi` `yoy` by month.
- Composición: stacked `ine.cpi_ecoicop_groups` 4 series `contribution` + total line `ine.cpi` `yoy` (subtitle states current weights over the whole history); lines of the 4 groups `yoy`; horizontal bars `ine.cpi_weights` `weight` (13 groups).
- CCAA: horizontal bars `ine.cpi_ccaa` `yoy` sorted; `latestTable` `yoy`, `mom`.
- IPRI: two line charts (total / sin energía; consumo, equipo, intermedios, energía) with toggle Índice / Anual / Mensual (`value`, `yoy`, `mom`).
- Vivienda: `ine.house_prices` `es`, toggle `value` / `yoy`.
- UE-27: lines `eurostat.hicp` and `eurostat.core_inflation` `es` vs `eu27` `yoy`.
Total 11 charts + 1 table + 7 KPIs.

## Not ported
- Donut of weights of the 4 special groups: replaced by the bar chart of the 13 ECOICOP group weights (`ine.cpi_weights`); the 4-group weights are constant in `cpi_ecoicop_groups`.
- IPRI "Jan 2021 = 100": the exported `value` is base 2021 = 100 (annual average) and is shown as is; the factory only rebases to the start of a window. 
- Coste laboral (old prices.py section) belongs to Laboral. Old CCAA row colour bands, choropleth map: not ported (decision).

## Test
Playwright Chromium, served from /tmp/p4-precios on port 8803, widths 375 and 1440: zero console errors/warnings, zero failed requests, no horizontal page overflow (scrollWidth = clientWidth), 11 Plotly charts rendered, no error cards. Screenshots inspected. At 375 px the CCAA table scrolls horizontally inside its card (page itself does not overflow).

## Requests
- REQUEST → lead: `groupedBarChart` horizontal at 375 px truncates long category labels (weights of ECOICOP groups); needs label wrapping or a taller left margin.
- REQUEST → lead: `lineChart` option to rebase a series to a fixed date (e.g. IPRI 2021-01 = 100) if that is wanted instead of the exported base.
- REQUEST → lead: weights bar chart x-axis tick labels are rotated/crowded on narrow widths.
