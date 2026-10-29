// Sectores · Servicios: producción del sector servicios (total y por ramas), cifra de negocios y valor añadido.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, groupedBarChart } from '../charts.js';

mountLayout({ active: 'servicios' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'ine.services_production', series: 'es', field: 'yoy', title: 'Producción de servicios, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'ine.services_turnover', series: 'es', field: 'yoy', title: 'Cifra de negocios de los servicios, variación interanual' },
  { dataset: 'ine.gva_sectors', series: 'servicios', field: 'yoy', title: 'Valor añadido de los servicios, variación interanual', change: { field: 'qoq', label: 'trimestral' } },
]);

/* Producción */
const ipss = (f) => [{ dataset: 'ine.services_production', series: 'es', field: f }];
lineChart($('ipss'), {
  title: 'Índice de Producción del Sector Servicios',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: ipss('yoy') },
    { id: 'mom', label: 'Var. mensual', series: ipss('mom') },
    { id: 'value', label: 'Índice (2021 = 100)', rebase: { year: 2021 }, series: ipss('value') },
  ],
  range: { default: '5A' },
});
groupedBarChart($('ipss-sect'), {
  title: 'Producción de servicios por ramas de actividad',
  dataset: 'ine.ipss_sectors', orientation: 'h', sort: 'desc', colorBySign: true,
  toggle: [{ id: 'yoy', label: 'Var. interanual', field: 'yoy' }, { id: 'ytd', label: 'Acumulado del año', field: 'ytd' }],
});

/* Cifra de negocios y valor añadido */
lineChart($('turnover'), {
  title: 'Cifra de negocios de los servicios',
  series: [{ dataset: 'ine.services_turnover', series: 'es', field: 'yoy' }],
  ref: { y: 0 },
  range: { default: '5A' },
});
const gva = (f) => [
  { dataset: 'ine.gva_sectors', series: 'servicios', field: f, label: 'Servicios' },
  { dataset: 'ine.gva_sectors', series: 'pib', field: f, label: 'PIB', dash: 'dot' },
];
lineChart($('gva'), {
  title: 'Valor añadido de los servicios',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: gva('yoy') },
    { id: 'qoq', label: 'Var. trimestral', series: gva('qoq') },
  ],
  range: { default: '5A' },
});
