# P4 Actividad

Files: `site/pages/actividad.html`, `site/assets/js/pages/actividad.js`. 6 KPIs, 15 charts.

## Contents (section, chart, dataset/series/field)
- KPIs: `ine.gdp` es yoy (qoq); `ine.industrial_production` yoy (mom); `ine.services_production` yoy (mom); `ine.business_confidence` ice value (yoy); `ine.retail_sales` yoy (mom); `eurostat.consumer_confidence` es value (yoy_diff).
- PIB: line with toggle yoy / qoq (`ine.gdp` es) / level 2019T1=100 (`ine.gdp_productivity` pib value); demand contributions stacked (`ine.gdp_demand`, 4 series `contribution`, last 3 years) with `ine.gdp` yoy overlay as total; GDP comparison (`eurostat.gdp_index` es, de, fr, it, eu27 `value`); productivity (`ine.gdp_productivity`, 5 series `value`).
- Producción y confianza: industry vs services toggle yoy / mom / index (`ine.industrial_production`, `ine.services_production` es); turnover yoy (`ine.industry_turnover`, `ine.services_turnover`); sector bars `ine.ipi_sectors`, `ine.ipss_sectors` (yoy / ytd toggle); business confidence ICE `value` (`ine.business_confidence`).
- Consumo y hogares (Consumo page merged here by lead decision): `ine.retail_sales` toggle yoy / mom / index; `eurostat.consumer_confidence` es vs eu27 value; `eurostat.retail_trade` yoy es vs eu27; `eurostat.house_prices` yoy es vs eu27; `bde.credit_households_total` yoy; `bde.mortgage_rate` value.

## Not ported
- GDP level "2019 = 100 average" and production "2021 = 100": the factory has no fixed-period rebase. GDP level uses the pipeline's 2019T1 = 100 index (`ine.gdp_productivity` pib); production index mode shows the native index base.
- Business confidence yoy toggle and `situacion`/`expectativas`: dropped so the "100 = neutral" reference line could be kept (ref is per chart, not per toggle option). Note ICE is not centred on 100 in the data, so no ref line was added.
- `ine.house_prices` (INE index): Eurostat Spain vs EU-27 used instead. Range sliders of the old change modes.

## Test
Chromium via Playwright at 375 and 1440 px on http://localhost:8802/site/pages/actividad.html: zero console errors/warnings, zero failed requests, scrollWidth = clientWidth, 15 of 15 chart containers rendered, no error cards. Screenshots reviewed (full page at both widths for top section at 375).
Observation: default 5A window of GDP yoy includes the 2021 rebound (~20 %), which compresses the axis.

## REQUEST → lead:
- Fixed-period rebase (e.g. `rebase: {to: '2019'}` average of a year) in `lineChart` for GDP and production indices.
- Per-toggle `ref` in `lineChart`.
