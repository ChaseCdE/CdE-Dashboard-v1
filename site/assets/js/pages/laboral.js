// Mercado laboral, por concepto: empleo, paro, participación y población, costes laborales.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, periodTable } from '../charts.js';

mountLayout({ active: 'laboral' });
const $ = (id) => document.getElementById(id);
const pair = (ds, f) => ['es', 'eu27'].map((s) => ({ dataset: ds, series: s, field: f }));

kpiGrid($('kpis'), [
  { dataset: 'bde.social_security_affiliates', series: 'es', field: 'value', change: { field: 'mom_diff', label: 'en el mes' }, positiveIsGood: true },
  { dataset: 'ine.employed', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: true },
  { dataset: 'ine.unemployment', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.registered_unemployment', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'ine.employment_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: true },
  { dataset: 'ine.temporary_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'ine.youth_unemployment', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'ine.labor_cost', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
]);

// Monthly changes of affiliation and registered unemployment are of unadjusted end-of-month data
// (no seasonally adjusted series is available): they include seasonal swings; the field note says so.
const varToggle = (ds) => [
  { id: 'yoy', label: 'Var. interanual', series: [{ dataset: ds, series: 'es', field: 'yoy' }] },
  { id: 'mom', label: 'Var. mensual', series: [{ dataset: ds, series: 'es', field: 'mom' }] },
  { id: 'mom_diff', label: 'Var. mensual (miles)', series: [{ dataset: ds, series: 'es', field: 'mom_diff' }] },
];

/* Empleo */
lineChart($('c-afil'), {
  title: 'Afiliados a la Seguridad Social, último día del mes',
  series: [{ dataset: 'bde.social_security_affiliates', series: 'es', field: 'value' }],
  range: { default: '5A' },
});
barChart($('c-afil-var'), {
  title: 'Variación de los afiliados, último día del mes',
  toggle: varToggle('bde.social_security_affiliates'),
  colorBySign: 'neutral',
  range: { default: '5A' },
});
lineChart($('c-ocup'), {
  title: 'Ocupados (EPA)',
  toggle: [
    { id: 'value', label: 'Nivel', series: [{ dataset: 'ine.employed', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'ine.employed', series: 'es', field: 'yoy' }], ref: { y: 0 } },
  ],
  markers: true,
  range: { default: '5A' },
});
const sectores = (field) => ['agricultura', 'industria', 'construccion', 'servicios']
  .map((k) => ({ dataset: 'ine.employed_sectors', series: k, field }));
lineChart($('c-sectores'), {
  title: 'Ocupados por sector económico',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: sectores('yoy') },
    { id: 'value', label: 'Nivel', series: sectores('value') },
  ],
  range: { default: '5A' },
});
lineChart($('c-emp-eu'), {
  title: 'Crecimiento trimestral del empleo: España frente a la UE-27',
  series: pair('eurostat.employment_growth', 'qoq'),
  ref: { y: 0 },
  range: { default: '5A' },
});
lineChart($('c-vacantes'), {
  title: 'Tasa de vacantes: España frente a la UE-27',
  series: pair('eurostat.job_vacancy_rate', 'value'),
  range: { default: '5A' },
});
lineChart($('c-temp'), {
  title: 'Temporalidad y parcialidad del empleo',
  series: [
    { dataset: 'ine.temporary_rate', series: 'es', field: 'value', label: 'Tasa de temporalidad' },
    { dataset: 'ine.parttime_rate', series: 'es', field: 'value', label: 'Tasa de parcialidad' },
  ],
  range: { default: '5A' },
});

/* Paro */
lineChart($('c-paro'), {
  title: 'Tasa de paro (EPA)',
  toggle: [
    { id: 'value', label: 'Nivel', series: [{ dataset: 'ine.unemployment', series: 'es', field: 'value' }] },
    { id: 'yoy_pp', label: 'Var. interanual (p. p.)', series: [{ dataset: 'ine.unemployment', series: 'es', field: 'yoy_pp' }], ref: { y: 0 } },
  ],
  markers: true,
  range: { default: '5A' },
});
lineChart($('c-paro-eu'), {
  title: 'Tasa de paro: España frente a la UE-27',
  series: pair('eurostat.unemployment', 'value'),
  range: { default: '5A' },
});
lineChart($('c-pr'), {
  title: 'Paro registrado',
  series: [{ dataset: 'bde.registered_unemployment', series: 'es', field: 'value' }],
  range: { default: '5A' },
});
barChart($('c-pr-var'), {
  title: 'Variación del paro registrado',
  toggle: varToggle('bde.registered_unemployment'),
  colorBySign: 'neutral',
  range: { default: '5A' },
});
lineChart($('c-juvenil'), {
  title: 'Paro juvenil frente al paro total',
  series: [
    { dataset: 'ine.youth_unemployment', series: 'es', field: 'value', label: 'Menores de 25 años' },
    { dataset: 'ine.unemployment', series: 'es', field: 'value', label: 'Total' },
  ],
  range: { default: '5A' },
});
lineChart($('c-larga'), {
  title: 'Paro de larga duración: España frente a la UE-27',
  series: pair('eurostat.long_term_unemployment', 'value'),
  range: { default: '5A' },
});

/* Participación y población */
lineChart($('c-tasas'), {
  title: 'Tasas de empleo y de actividad',
  series: [
    { dataset: 'ine.activity_rate', series: 'es', field: 'value', label: 'Tasa de actividad' },
    { dataset: 'ine.employment_rate', series: 'es', field: 'value', label: 'Tasa de empleo' },
  ],
  range: { default: '5A' },
});
lineChart($('c-actividad-eu'), {
  title: 'Tasa de actividad: España frente a la UE-27',
  series: pair('eurostat.labor_participation', 'value'),
  range: { default: '5A' },
});
periodTable($('c-tabla'), {
  title: 'Datos recientes, últimos trimestres',
  columns: [
    { dataset: 'ine.unemployment', series: 'es', field: 'value', label: 'Paro' },
    { dataset: 'ine.employment_rate', series: 'es', field: 'value', label: 'Empleo' },
    { dataset: 'ine.activity_rate', series: 'es', field: 'value', label: 'Actividad' },
  ],
  last: 12,
});
lineChart($('c-pob'), {
  title: 'Población residente por nacionalidad',
  toggle: [
    { id: 'value', label: 'Nivel', series: ['total', 'espanola', 'extranjera'].map((s) => ({ dataset: 'ine.population_nationality', series: s, field: 'value' })) },
    { id: 'yoy', label: 'Var. interanual', series: ['espanola', 'extranjera'].map((s) => ({ dataset: 'ine.population_nationality', series: s, field: 'yoy' })) },
  ],
  range: { default: 'max' },
});

/* Costes laborales */
lineChart($('c-coste'), {
  title: 'Coste laboral por trabajador',
  toggle: [
    { id: 'nivel', label: 'Nivel', series: [{ dataset: 'ine.labor_cost', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'ine.labor_cost', series: 'es', field: 'yoy' }] },
  ],
  range: { default: '5A' },
});
lineChart($('c-hora'), {
  title: 'Coste laboral por hora efectiva',
  toggle: [
    { id: 'nivel', label: 'Nivel', series: [{ dataset: 'ine.labor_cost_hour', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'ine.labor_cost_hour', series: 'es', field: 'yoy' }] },
  ],
  range: { default: '5A' },
});
lineChart($('c-indice'), {
  title: 'Coste laboral total y coste salarial, índice',
  series: [
    { dataset: 'ine.labor_cost_components', series: 'total', field: 'index_2019q1' },
    { dataset: 'ine.labor_cost_components', series: 'salarial', field: 'index_2019q1' },
  ],
  range: { default: 'max' },
});
