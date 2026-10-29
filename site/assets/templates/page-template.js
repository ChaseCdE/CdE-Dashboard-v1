// Page module template. Copy to site/assets/js/pages/<slug>.js.
// Rules: import only layout.js and charts.js (and format.js if you need a label);
// never pass raw Plotly options; never compute economic quantities (the pipeline exports them
// as fields); never type a number, unit, source or date: all come from the JSON.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, groupedBarChart } from '../charts.js';

mountLayout({ active: 'SLUG' });          // one of: portada, actividad, industria, servicios, construccion, turismo, laboral, precios, exterior, publico, credito, mercados, ue
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  // Latest value of a field; `change` shows ANOTHER exported field (e.g. yoy) with a sign colour.
  { dataset: 'ine.cpi', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: false },
]);

// Title is a sentence; subtitle (unit, note), source and last date come from the JSON.
lineChart($('chart-1'), {
  title: 'La inflación general en España, tasa interanual',
  series: [{ dataset: 'ine.cpi', series: 'es', field: 'yoy' }],
  range: { default: '5A' },                // buttons 1A / 5A / Máx, display-only
  ref: { y: 2, label: 'Objetivo BCE 2 %' },
});

// Several datasets in one chart: colours come from config.js (es = navy, eu27 = beige, then the cycle).
lineChart($('chart-2'), {
  title: 'Inflación armonizada: España frente a la UE-27',
  series: [
    { dataset: 'eurostat.hicp', series: 'es', field: 'yoy' },
    { dataset: 'eurostat.hicp', series: 'eu27', field: 'yoy' },
  ],
});
