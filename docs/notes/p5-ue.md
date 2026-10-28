# Phase 5: Comparativa UE
## Added
- "Convergencia con Europa" (after KPIs): 2 KPIs (`eurostat.gdp_per_capita_pps.es.value`, `eurostat.labour_productivity_pps.es.value`); lineChart `gdp_per_capita_pps` (es, de, fr, it, pt; value), lineChart `labour_productivity_pps` (same), both with ref y=100 "Media UE-27"; lineChart `rd_expenditure` (es, eu27, de, fr, it; value).
- Mercado de trabajo: `youth_unemployment.value` and `long_term_unemployment.value`, es vs eu27 (two lines each).
- Lead text updated (no "dieciséis").
## Removed (4 charts)
The four "Situación actual" grouped bars (PIB t/t, paro, IPCA, deuda): each repeated the value already in the KPI tile above and the time-series chart below. Charts: 21 -> 22 (21 - 4 + 5).
## Not fixed
"ene 2027" tick: no chart option (only `yRange` exists for y). REQUEST → lead: x-axis range clamp to last observation in the factory.
## Test
Served /tmp/p5-ue port 8815, Playwright 375 and 1440 px: 0 console errors/warnings, 0 failed requests, no horizontal overflow, 22 plots, 0 error cards. 1440 full-page screenshot viewed (downscaled; layout checked, not fine detail); 375 screenshot taken, not inspected.
