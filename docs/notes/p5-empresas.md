# p5 Empresas y turismo

Files: site/pages/empresas.html, site/assets/js/pages/empresas.js.

KPIs (value sum_12m, change yoy of the month): ine.tourist_arrivals/es, ine.tourist_spending/es, ine.hotel_overnight_stays/total, ine.companies/created, ine.companies/dissolved (dissolved: positiveIsGood false).

Charts (8):
- Arrivals sum_12m (line); arrivals yoy (bars, default 3A: the 2021-22 post-COVID spikes of 500-1000 % crush the scale in 5A).
- Spending sum_12m; spending yoy (bars, 3A).
- Hotel overnight stays residentes vs no_residentes, toggle sum_12m / yoy.
- bde.tourism_receipts/es yoy (bars, 3A); level omitted (monthly, seasonal).
- ine.companies created vs dissolved sum_12m (two lines); created yoy (bars).

Left out: insolvencies (INE discontinued the Estadística del Procedimiento Concursal after 2020), stated in the page lead.
Spending/arrivals yoy and sum_12m combo on one chart not possible (no line+bar factory): split into two charts.

Test (port 8811, Playwright 375 and 1440 px): 0 console errors, 0 failed requests, no horizontal overflow, 8 plots, 0 .error-card, CSV download event OK; screenshots reviewed.
REQUEST -> lead: a lineChart+bar combo (sum_12m line with yoy bars on secondary axis) would let arrivals/spending be one chart each.
