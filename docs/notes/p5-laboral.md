# p5-laboral: Mercado laboral (wave 2)

## Added
- Section "Afiliación y paro registrado" (after KPIs): `bde.social_security_affiliates` es `value` (line) and `yoy` (bars); `bde.registered_unemployment` es `value` (line) and `yoy` (bars). Affiliates JSON has `description_es` (end of month) but no `note_es`, so titles say "último día del mes". 5A default.
- KPI tiles at start of grid: affiliates (`yoy`, positiveIsGood true), registered unemployment (`yoy`, positiveIsGood false).
- Section "Población" (before Costes laborales): `ine.population_nationality` `total`, `espanola`, `extranjera` `value` (line); `espanola`, `extranjera` `yoy` (line). Range default max.
- Lead text and meta description mention afiliación y paro registrado.

## Removed
- KPI tile `ine.parttime_rate` (calidad grid): KPIs would otherwise be 11 (>10). Least useful; the parcialidad series stays in the "Temporalidad y parcialidad" chart.

## Test
Port 8813, Playwright Chromium, 375 and 1440 px: zero console errors/warnings, zero failed requests/HTTP>=400, scrollWidth = clientWidth, 14 plots, 0 error cards. 1440 px screenshot inspected; the 375 px screenshot was generated (/tmp/lab-375.png) but not viewed.

## REQUEST → lead
None.
