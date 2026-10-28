# p4 Portada

## Qué muestra
KPIs (8, todos con enlace a su página):
- PIB variación anual: `ine.gdp` es `yoy`, cambio `qoq`
- Producción industrial: `ine.industrial_production` es `yoy`, cambio `mom`
- IPC: `ine.cpi` es `yoy`
- Paro EPA: `ine.unemployment` es `value`, cambio `yoy_pp`
- Euríbor 12M: `bde.euribor_12m_daily` ea `value`, cambio `chg_1m`
- Bono 10A: `bde.spain_10y_bond` es `value`, cambio `chg_1m`
- IBEX 35: `yahoo.ibex_35` es `close`, cambio `ret_ytd`
- Brent: `yahoo.brent_crude` global `close`, cambio `ret_1m`

Gráficos (6), cada uno con enlace "Más sobre..." debajo:
- Actividad y precios: PIB yoy (barChart, 3 años, `ine.gdp` yoy); IPC yoy (barChart, 2 años, línea BCE 2 %, `ine.cpi` yoy)
- España vs UE-27: paro (`eurostat.unemployment` es/eu27 `value`); IPCA (`eurostat.hicp` es/eu27 `yoy`)
- Tipos y mercados: `bde.euribor_12m_monthly` + `bde.spain_10y_bond_monthly` `value`; groupedBarChart `ret_ytd` de ibex_35, euro_stoxx_50, dax, sp_500

## No portado
- Resumen ejecutivo / puntos de pulso y diferencias España-UE calculadas (prosa editorial; no hay campo `gap`).
- Tarjeta deuda/PIB frente a UE y PIB t/t UE: ya cubiertas en Comparativa UE.
- Barras de IPC coloreadas por encima del 2 %.

## Pruebas
Playwright/Chromium, 375 y 1440 px: 0 errores/avisos de consola, 0 peticiones fallidas, sin desbordamiento horizontal, 8 KPIs y 6 gráficos renderizados, 0 tarjetas de error. Capturas revisadas. Tras la prueba se cambió la ventana del PIB de 5 a 3 años (el rebote de 2021 aplastaba la escala); no repetida la prueba tras ese cambio de un solo parámetro.

## Observaciones
- REQUEST → lead: en `groupedBarChart` con `categories` de una sola barra, las barras quedan desplazadas dentro de su categoría (hueco por las otras series); sería mejor centrarlas cuando cada categoría tiene una barra.
- REQUEST → lead: la etiqueta de `ref` (Objetivo BCE 2 %) se solapa con las barras en el gráfico de IPC.
- Los enlaces "Más sobre..." son HTML de página, no de la fábrica.
