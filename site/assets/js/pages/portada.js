// Portada: instantánea de la economía española. Todo el contenido sale de los JSON vía la fábrica de gráficos.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, groupedBarChart } from '../charts.js';

mountLayout({ active: 'portada' });

const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'ine.gdp', series: 'es', field: 'yoy', title: 'PIB, variación anual', change: { field: 'qoq', label: 'trimestral' }, positiveIsGood: true, href: 'pages/actividad.html' },
  { dataset: 'ine.industrial_production', series: 'es', field: 'yoy', title: 'Producción industrial, variación anual', change: { field: 'mom', label: 'mensual' }, positiveIsGood: true, href: 'pages/actividad.html' },
  { dataset: 'ine.cpi', series: 'es', field: 'yoy', title: 'Inflación (IPC), variación anual', positiveIsGood: false, href: 'pages/precios.html' },
  { dataset: 'ine.unemployment', series: 'es', field: 'value', title: 'Tasa de paro (EPA)', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false, href: 'pages/laboral.html' },
  { dataset: 'bde.euribor_12m_daily', series: 'ea', field: 'value', title: 'Euríbor a 12 meses', change: { field: 'chg_1m', label: 'en un mes' }, positiveIsGood: null, href: 'pages/credito.html' },
  { dataset: 'bde.spain_10y_bond', series: 'es', field: 'value', title: 'Bono español a 10 años', change: { field: 'chg_1m', label: 'en un mes' }, positiveIsGood: null, href: 'pages/credito.html' },
  { dataset: 'yahoo.ibex_35', series: 'es', field: 'close', title: 'IBEX 35', change: { field: 'ret_ytd', label: 'en el año' }, positiveIsGood: true, href: 'pages/mercados.html' },
  { dataset: 'yahoo.brent_crude', series: 'global', field: 'close', title: 'Petróleo Brent', change: { field: 'ret_1m', label: 'en un mes' }, positiveIsGood: null, href: 'pages/mercados.html' },
]);

barChart($('chart-pib'), {
  title: 'Crecimiento del PIB de España, variación anual',
  series: [{ dataset: 'ine.gdp', series: 'es', field: 'yoy' }],
  colorBySign: 'neutral',
  range: { default: '3A', years: 3 },
});

barChart($('chart-ipc'), {
  title: 'Inflación general en España, variación anual',
  series: [{ dataset: 'ine.cpi', series: 'es', field: 'yoy' }],
  colorBySign: 'neutral',
  ref: { y: 2, label: 'Objetivo BCE 2 %' },
  range: { default: '2A', years: 2 },
});

lineChart($('chart-paro'), {
  title: 'Tasa de paro, España y UE-27',
  series: [
    { dataset: 'eurostat.unemployment', series: 'es', field: 'value' },
    { dataset: 'eurostat.unemployment', series: 'eu27', field: 'value' },
  ],
  range: { default: '5A' },
});

lineChart($('chart-ipca'), {
  title: 'Inflación armonizada (IPCA), España y UE-27',
  series: [
    { dataset: 'eurostat.hicp', series: 'es', field: 'yoy' },
    { dataset: 'eurostat.hicp', series: 'eu27', field: 'yoy' },
  ],
  range: { default: '5A' },
});

lineChart($('chart-tipos'), {
  title: 'Euríbor a 12 meses y bono español a 10 años',
  series: [
    { dataset: 'bde.euribor_12m_monthly', series: 'ea', field: 'value' },
    { dataset: 'bde.spain_10y_bond_monthly', series: 'es', field: 'value' },
  ],
  range: { default: '5A' },
});

groupedBarChart($('chart-bolsas'), {
  title: 'Bolsas, rentabilidad en lo que va de año',
  categories: [
    ['yahoo.ibex_35', 'es', 'IBEX 35'],
    ['yahoo.euro_stoxx_50', 'ez', 'Euro Stoxx 50'],
    ['yahoo.dax', 'de', 'DAX'],
    ['yahoo.sp_500', 'us', 'S&P 500'],
  ].map(([dataset, series, label]) => ({ label, bars: [{ dataset, series, field: 'ret_ytd', name: label }] })),
  colorBySign: true,
});
