# Phase 4: Comparativa UE (`site/pages/ue.html`, `site/assets/js/pages/ue.js`)

## What the page shows
All datasets `eurostat.*`, series `es` and `eu27` unless noted.
- Situación actual: 8 KPIs (PIB t/t `gdp_growth.qoq`; paro `unemployment.value`, change `yoy_pp`; IPCA `hicp.yoy`; deuda `government_debt.value`, change `yoy_pp`; each for es and eu27). Four `groupedBarChart` (mode B), latest Spain vs EU-27 for the same four indicators.
- Crecimiento: `gdp_growth.qoq` (barChart), `gdp_index.value` (lineChart, es, eu27, de, fr, it).
- Mercado de trabajo: `unemployment.value`, `labor_participation.value`, `employment_growth.qoq`.
- Precios: `hicp.yoy`, `core_inflation.yoy` (both with ECB 2 % reference), `producer_prices.yoy`.
- Finanzas públicas: `government_debt.value`, `budget_deficit.value` (annual, markers).
- Actividad y demanda: `industrial_production.yoy`, `retail_trade.yoy`, `house_prices.yoy`.
- Sentimiento: `economic_sentiment.value` (ref 100), `consumer_confidence.value`.
- Comercio exterior (es only): `trade_balance.balance` (barChart, colour by sign), `exports` + `imports` (lineChart).
Total: 8 KPIs, 21 charts. Differences shown as two lines (no gap series).

## Not ported
- Old "Diferencial" charts (Spain minus EU-27 for paro and IPCA): dropped by decision (two lines instead).
- No compact latest-value table: `latestTable` cannot mix per-row field keys across datasets (see request).
- Old page had no toggles; none added.

## Test
Served from /tmp/p4-ue on port 8807, Chromium (Playwright) at 375 and 1440 px: 0 console errors/warnings, 0 failed requests, scrollWidth = clientWidth (no horizontal overflow), 21 Plotly charts rendered, 8 KPI tiles, no error cards. Full-page screenshots reviewed.
Note: line chart x axes show "ene 2027" as last tick (axis padding by the factory, no data beyond latest).

## REQUEST → lead:
- `latestTable` rows accept one `dataset` + `series` per row but columns share a field key; a Spain vs EU-27 summary table across indicators with different fields (qoq, value, yoy) is not expressible. Allow per-row `field` if such a table is wanted.
