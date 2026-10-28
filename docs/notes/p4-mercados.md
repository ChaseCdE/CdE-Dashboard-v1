# Página Mercados (p4-mercados)

Ficheros: `site/pages/mercados.html`, `site/assets/js/pages/mercados.js`.

## Qué muestra
- KPI (6): IBEX 35, Euro Stoxx 50, S&P 500 (`yahoo.*` `close`, cambio `ret_1d`), EUR/USD y Brent (`close`, `ret_1d`), Tesoro EE. UU. 10 años (`close`, cambio `chg_1d` en p. p.).
- Bolsas: `lineChart` con toggle de 5 índices, `close` + `sma_200` (dashed) | `rebasedComparison` de los 5 índices (`close`) | `groupedBarChart` (categories) `ret_ytd` de 7 índices, color por signo | `rebasedComparison` `yahoo.spanish_banks_etf` y `yahoo.european_banks_etf` (`close`) | `latestTable` Cotizaciones (8 índices; `close`, `ret_1w`, `ret_1m`, `ret_ytd`, `ret_1y`) | `lineChart` VIX `close`.
- Tipos de interés: `latestTable` €STR, Euríbor 3M/12M, bono ES 5Y/10Y (`value`, `chg_1m`, `chg_ytd`, `chg_1y`); `latestTable` Tesoro EE. UU. 3M/5Y/10Y/30Y (`close`, `chg_*`); `lineChart` selectable de las mismas 4 series `close`.
- Divisas: `lineChart` `yahoo.eur_usd`, `yahoo.dxy`; `latestTable` 7 pares (`close`, `ret_1w`, `ret_1m`, `ret_ytd`, `ret_1y`).
- Materias primas: `lineChart` Brent+WTI, oro, gas natural (`close`); `latestTable` Brent, WTI, gas, oro, plata.

## No portado
- Tabla de tipos de interés en una sola tabla: la tabla acepta un único `field` por columna y BdE usa `value` mientras Yahoo usa `close`; se divide en dos tablas.
- Bandas/referencias de VIX (12/20/30) y deuda a 10 años de ES/DE/FR/IT (es de Crédito y tipos). Tipos de referencia (€STR/Euríbor, gráfico): Crédito y tipos.
- Escala de las ETF: `spanish_banks_etf` es en realidad iShares MSCI España (no bancos); se titula con su nombre real.
- Cambio 1 mes de bonos EE. UU. = 21 sesiones, el de BdE = 30 días naturales (la nota del campo lo indica).

## Prueba
Servido con http.server (puerto 8806), Playwright/Chromium, 375 y 1440 px: 0 errores y 0 avisos de consola, 0 peticiones fallidas, sin desbordamiento horizontal (scrollWidth = clientWidth), 11 gráficos, 5 tablas y 6 KPI renderizados, sin tarjetas de error. Capturas revisadas.

REQUEST → lead: `latestTable` con campo por fila (p. ej. `fieldByRow`) para unir BdE (`value`) y Yahoo (`close`) en una sola tabla de tipos.
REQUEST → lead: `kpiTile` con `ret_1d` sobre datasets de tipos no aplica; el KPI del 10Y usa `chg_1d` (p. p.), correcto.
