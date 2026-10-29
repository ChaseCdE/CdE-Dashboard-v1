// Sector exterior: balanza de pagos (cuenta corriente), comercio de bienes y precios del comercio exterior.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart } from '../charts.js';

mountLayout({ active: 'exterior' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'bde.current_account_balance', series: 'es', field: 'sum_12m', title: 'Saldo por cuenta corriente, últimos 12 meses' },
  { dataset: 'eurostat.trade_balance', series: 'es', field: 'balance', title: 'Saldo comercial de bienes, último mes' },
  { dataset: 'ine.trade_prices', series: 'exportacion', field: 'yoy', title: 'Precios de exportación, variación interanual' },
  { dataset: 'ine.trade_prices', series: 'importacion', field: 'yoy', title: 'Precios de importación, variación interanual' },
]);

/* Balanza de pagos */
barChart($('ca'), {
  title: 'Saldo por cuenta corriente, mensual y acumulado en 12 meses',
  series: [{ dataset: 'bde.current_account_balance', series: 'es', field: 'value', label: 'Saldo mensual' }],
  colorBySign: true,
  overlay: { dataset: 'bde.current_account_balance', series: 'es', field: 'sum_12m', label: 'Acumulado 12 meses' },
  range: { default: '5A' },
});

/* Comercio de bienes */
barChart($('trade-bal'), {
  title: 'Saldo comercial de bienes',
  series: [{ dataset: 'eurostat.trade_balance', series: 'es', field: 'balance' }],
  colorBySign: true,
  range: { default: '5A' },
});
lineChart($('trade-flows'), {
  title: 'Exportaciones e importaciones de bienes',
  series: [
    { dataset: 'eurostat.trade_balance', series: 'es', field: 'exports' },
    { dataset: 'eurostat.trade_balance', series: 'es', field: 'imports' },
  ],
  range: { default: '5A' },
});

/* Precios del comercio exterior */
lineChart($('trade-prices'), {
  title: 'Precios industriales de exportación e importación',
  toggle: ['yoy', 'value'].map((f) => ({
    id: f, label: { yoy: 'Var. interanual', value: 'Índice' }[f],
    series: ['exportacion', 'importacion'].map((s) => ({ dataset: 'ine.trade_prices', series: s, field: f })),
  })),
  range: { default: '5A' },
});
