# Crédito y tipos (credito), ronda 5

Ficheros: `site/pages/credito.html`, `site/assets/js/pages/credito.js`.

## Añadido
- Deuda pública: lineChart `bde.spread_10y_de` y `bde.spread_10y_it` (series `es`, `value`), ref y=0, subtítulo que explica el signo.
- Deuda pública: lineChart con toggle Nivel (`bde.government_debt_pde` value) / Variación anual (yoy).
- Crédito y endeudamiento: lineChart `bde.npl_ratio` value (rango Máx).
- KPI: diferencial frente a Alemania (`bde.spread_10y_de` value, chg_1m, positiveIsGood false); ratio de dudosos (`bde.npl_ratio` value, yoy_pp, positiveIsGood false).

## Eliminado (KPI, para quedar en 12)
Tipo de crédito al consumo, tipo de depósitos a plazo y deuda/PIB de SNF (los tres siguen en sus gráficos).

## Revisado
- Gráfico 10 años: Francia e Italia ya muestran series correctas y terminan en sep 2026 junto con España y Alemania; el texto del título no cambia. Curva de rentabilidad: llega a 15 años, sin el punto de más de 2 años.

## Test
Puerto 8814, Chromium 375 y 1440 px: 0 errores/avisos de consola, 0 peticiones fallidas, sin desbordamiento, 11 gráficos Plotly, 0 error-card, 12 KPI. Captura 1440 revisada a mano (la de 375 no se inspeccionó visualmente).

## REQUEST → lead
- La fábrica no admite una nota de texto libre; el signo del diferencial va en `subtitle` del lineChart.
