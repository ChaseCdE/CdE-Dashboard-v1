// Starter for the Portada page (replaced in Phase 4). Shows the pattern pages must follow:
// mount the layout, then call the chart factory with declarative specs.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart } from '../charts.js';

mountLayout({ active: 'portada' });

kpiGrid(document.getElementById('kpis'), [
  { dataset: 'ine.cpi', series: 'es', field: 'yoy', title: 'Inflación (IPC)', change: null, positiveIsGood: false },
  { dataset: 'ine.cpi', series: 'es', field: 'value', title: 'IPC, índice', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'eurostat.hicp', series: 'es', field: 'yoy', title: 'Inflación armonizada (IPCA)', positiveIsGood: false },
  { dataset: 'yahoo.ibex_35', series: 'es', field: 'close', title: 'IBEX 35' },
]);

lineChart(document.getElementById('chart-ipc'), {
  title: 'Inflación general en España, tasa interanual',
  series: [{ dataset: 'ine.cpi', series: 'es', field: 'yoy' }],
  range: { default: 'max' },
  ref: { y: 2, label: 'Objetivo BCE 2 %' },
});

lineChart(document.getElementById('chart-ibex'), {
  title: 'Evolución del IBEX 35',
  series: [{ dataset: 'yahoo.ibex_35', series: 'es', field: 'close' }],
  range: { default: '5A' },
});
