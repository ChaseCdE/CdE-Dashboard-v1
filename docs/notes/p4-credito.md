# Página Crédito y tipos (credito)

Ficheros: `site/pages/credito.html`, `site/assets/js/pages/credito.js`.

## Contenido (sección, gráfico, dato)
- Indicadores clave (13 KPI): €STR (`bde.ester_daily` value, chg_1y); Euríbor 12m diario (`bde.euribor_12m_daily`, chg_1y); bono 10 años (`bde.spain_10y_bond`, chg_1y); hipotecas, consumo, empresas, depósitos a plazo (`bde.*_rate` value, mom_pp); crédito a hogares y a SNF (`bde.credit_*_total` value, yoy); deuda/PIB hogares y SNF (value, qoq_pp); cuenta corriente 12 meses (`bde.current_account_balance` sum_12m); turismo (`bde.tourism_receipts` value, yoy).
- Tipos de interés: lineChart €STR + Euríbor 3m + 12m (diarios); lineChart tipos bancarios (4 series, `value`).
- Deuda pública: crossSectionChart `bde.yield_curve` es yield; lineChart 10 años España (`spain_10y_bond_monthly`), Alemania, Francia, Italia (niveles, sin diferenciales).
- Crédito y endeudamiento: lineChart yoy hogares y SNF con ref 0; lineChart deuda/PIB (rango Máx).
- Sector exterior: barChart `current_account_balance` value, colorBySign, overlay sum_12m; barChart `tourism_receipts` value.

## No portado
- Gauge "Indicadores de deuda" (sustituido por los KPI, según inventario).
- Euríbor 1s/1m/6m, mensual de 12m, letras y bonos 2/3/5/15 años: ya dan la curva; no añaden gráfico.
- Depósitos a la vista: omitido por simplicidad.

## Observaciones
- Los campos reales del manifest son `mom_pp`, `chg_1m/ytd/1y`, `qoq_pp` (no `yoy_pp`/`chg_30d` de la propuesta).
- La serie yoy de crédito a hogares muestra una caída brusca y rebote hacia 2026 (dato de origen, a revisar en el pipeline).
- Las series de bonos a 10 años tienen último dato distinto (DE sep, FR ago, IT jul 2026); el pie lo indica.
- `bde.credit_nfc_total` está en miles de millones y `credit_households_total` en millones (escalas del JSON); los KPI muestran "mM€" y "M€".

## Test
Servidor local puerto 8805, Chromium (Playwright) a 375 y 1440 px: 0 errores/avisos de consola, 0 peticiones fallidas, sin desbordamiento horizontal (scrollWidth = clientWidth), 8 gráficos Plotly renderizados, 0 tarjetas de error. Capturas revisadas a mano.

## REQUEST → lead
- Ninguna. (Opcional: unificar escala de moneda de crédito hogares/SNF en el export.)
