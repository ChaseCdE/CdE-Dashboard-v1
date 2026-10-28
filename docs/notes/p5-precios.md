# Phase 5: Precios

## Added / changed
- New section "Energía": line chart `eurostat.hicp_energy` `es` vs `eu27`, field `yoy` (two lines, range default 5A).
- New KPI tile: `eurostat.hicp_energy` `es` `yoy` ("Inflación de la energía (IPCA España)"), 8 KPIs now.
- IPRI "Índice" toggle (both charts) now uses `rebase: {year: 2022}` (subtitle "Índice, base 2022 = 100"); yoy/mom toggles unchanged. Jan 2021 not possible (data start 2021-10).
- `ine.cpi_special_groups` has only `headline` and `core` (no energy series), so nothing was added from it. The CPI energy group already appears in "Inflación por grupo de gasto" (`cpi_ecoicop_groups` productos_energeticos).

## Test
Playwright Chromium, /tmp/p5-precios on port 8816, 375 and 1440 px: 0 console errors/warnings, 0 failed requests, no horizontal overflow, 12 Plotly charts, 0 error cards. 1440 px full-page screenshot inspected; the 375 px one was not viewed (only the numeric checks above).

## Requests
REQUEST → lead: none new. Earlier label-truncation request on the weights bar chart still visible at 1440 px.
