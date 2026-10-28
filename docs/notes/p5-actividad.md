# P5 Actividad

Changes on top of p4 (`site/pages/actividad.html`, `site/assets/js/pages/actividad.js`).

## Added (section renamed "Consumo, hogares y vivienda")
- `ine.household_saving_rate` es `value`: line with markers, title says "desestacionalizada"; the subtitle carries the JSON note (quarterly, adjusted for seasonality and calendar).
- `ine.housing_transactions` `nueva` and `usada`, field `sum_12m`: two lines.
- `ine.mortgages` es: toggle `sum_12m` (number, 12 months) / `avg_amount` (average amount).

## Removed
- `eurostat.retail_trade` yoy Spain vs EU-27 (weakest: duplicates the INE retail chart): section is at 8 charts (retail, consumer confidence, house prices, credit, mortgage rate, saving, housing, mortgages).

## Changed
- GDP toggle "Nivel": now `ine.gdp` es `value` with `rebase: {year: 2019}` (was `ine.gdp_productivity` pib, 2019T1 = 100). Label "Índice (2019 = 100)".
- Production toggle "Índice": `rebase: {year: 2021}`; label "Índice (2021 = 100)".
- Lead text and meta description mention saving and housing. No KPI tile added (6 tiles keep the grid even).

## Test
Playwright, 375 and 1440 px, http://localhost:8812: zero console errors/warnings, zero failed requests, no horizontal overflow, 17 of 17 charts rendered, 0 `.error-card`. Full-page 1440 screenshot (lower half) viewed. Toggles clicked at 1440: GDP rebase and production rebase subtitles show base 2019 / 2021; mortgage average amount renders. The 375 screenshot was taken but not viewed.

## REQUEST → lead:
- None.
