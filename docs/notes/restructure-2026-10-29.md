# Page structure by topic (2026-10-29)

Reviewed from a macroeconomist's point of view: blocks were split by source or geography (housing on three
pages, external sector and public finance spread over Crédito y tipos and Comparativa UE). New structure:

| Menu | Content |
|---|---|
| Portada | Summary |
| Actividad | GDP and demand; monthly activity (IPI and IPSS totals, turnover); economic climate; consumption and households; firms (creation, dissolution, bankruptcies, registrations); productivity and convergence |
| Sectores (dropdown) | Industria (IPI total, by economic destination and by CNAE division, turnover, GVA, capacity); Servicios (IPSS total and by branch, turnover, GVA); Construcción y vivienda (INE IPCO by type of work, Eurostat construction, GVA, house prices INE/MIVAU/Registradores/Eurostat, rent, transactions, mortgages, mortgage rate, new housing loans); Turismo |
| Mercado laboral | By concept: employment, unemployment, participation and population, labour costs |
| Precios | CPI, composition (incl. energy), regions, industrial prices; housing moved to Construcción y vivienda |
| Sector exterior | Current account, goods trade, export and import prices |
| Sector público | Debt, deficit, financing cost (10-year yields, spreads, interest expenditure) |
| Crédito y tipos | Rates, private credit, private debt and NPLs |
| Mercados | Now also the Spanish yield curve (moved from Crédito y tipos at the user's request) |
| Comparativa UE | Kept as a separate page; some charts are repeated on purpose |

New data: `ine.ipi_divisions` (IPI by CNAE division, table 60282, INE yoy and year-to-date rates, SCA;
divisions 07 and 12 are confidential and left out) and `ine.construction_ipco` (Índice de Producción de la
Construcción, table 79683, base 2021, SCA; INE publishes it only from January 2025, so the long history stays
with Eurostat sts_copr_m, which is the same index chained back).

Conventions: toggle labels are "Var. interanual", "Var. trimestral", "Var. mensual", "Nivel", "Índice (base)",
"Suma 12 meses", "Acumulado del año"; comparison titles are "<concepto>: España frente a la UE-27";
level and rate of the same indicator share one card with a toggle; KPI tiles only at the top of each page.
Removed page: empresas.html (business demography to Actividad, tourism to Sectores · Turismo).
