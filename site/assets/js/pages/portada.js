// Portada: instantánea de la economía española. Todo el contenido sale de los JSON vía la fábrica de gráficos.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, groupedBarChart } from '../charts.js';
import { latestData } from '../latest.js';

mountLayout({ active: 'portada' });

const $ = (id) => document.getElementById(id);

latestData($('latest'));

kpiGrid($('kpis'), [
  { dataset: 'ine.gdp', series: 'es', field: 'yoy', title: 'PIB, variación anual', change: { field: 'qoq', label: 'trimestral' }, positiveIsGood: true, href: 'pages/actividad.html' },
  { dataset: 'ine.industrial_production', series: 'es', field: 'yoy', title: 'Producción industrial, variación anual', change: { field: 'mom', label: 'mensual' }, positiveIsGood: true, href: 'pages/sectores.html#industria' },
  { dataset: 'ine.cpi', series: 'es', field: 'yoy', title: 'Inflación (IPC), variación anual', positiveIsGood: false, href: 'pages/precios.html' },
  { dataset: 'bde.social_security_affiliates', series: 'es', field: 'value', title: 'Afiliados a la Seguridad Social', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: true, href: 'pages/laboral.html' },
  { dataset: 'bde.euribor_12m_daily', series: 'ea', field: 'value', title: 'Euríbor a 12 meses', change: { field: 'chg_1m', label: 'en un mes' }, positiveIsGood: null, href: 'pages/credito.html' },
  { dataset: 'bde.spread_10y_de', series: 'es', field: 'value', title: 'Diferencial a 10 años frente a Alemania', change: { field: 'chg_1m', label: 'en un mes' }, positiveIsGood: false, href: 'pages/sector-publico.html' },
  { dataset: 'yahoo.ibex_35', series: 'es', field: 'close', title: 'IBEX 35', change: { field: 'ret_ytd', label: 'en el año' }, positiveIsGood: true, href: 'pages/mercados.html' },
  { dataset: 'ine.tourist_arrivals', series: 'es', field: 'sum_12m', title: 'Turistas internacionales, últimos 12 meses', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: true, href: 'pages/sectores.html#turismo' },
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
  title: 'Tasa de paro: España frente a la UE-27',
  series: [
    { dataset: 'eurostat.unemployment', series: 'es', field: 'value' },
    { dataset: 'eurostat.unemployment', series: 'eu27', field: 'value' },
  ],
  range: { default: '5A' },
});

lineChart($('chart-ipca'), {
  title: 'Inflación armonizada (IPCA): España frente a la UE-27',
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
