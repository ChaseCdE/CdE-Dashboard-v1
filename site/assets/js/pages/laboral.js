import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, periodTable } from '../charts.js';

mountLayout({ active: 'laboral' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'bde.social_security_affiliates', series: 'es', field: 'value', change: { field: 'mom_diff', label: 'en el mes' }, positiveIsGood: true },
  { dataset: 'bde.registered_unemployment', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'ine.unemployment', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'ine.employment_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: true },
  { dataset: 'ine.activity_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: true },
  { dataset: 'ine.employed', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: true },
]);

lineChart($('c-afil'), {
  title: 'Afiliados a la Seguridad Social, último día del mes',
  series: [{ dataset: 'bde.social_security_affiliates', series: 'es', field: 'value' }],
  range: { default: '5A' },
});
// Monthly changes are of unadjusted end-of-month data (no seasonally adjusted series is
// available): they include seasonal swings; the field note says so.
const varToggle = (ds) => [
  { id: 'yoy', label: 'Interanual (%)', series: [{ dataset: ds, series: 'es', field: 'yoy' }] },
  { id: 'mom', label: 'Mensual (%)', series: [{ dataset: ds, series: 'es', field: 'mom' }] },
  { id: 'mom_diff', label: 'Mensual (miles)', series: [{ dataset: ds, series: 'es', field: 'mom_diff' }] },
];
barChart($('c-afil-var'), {
  title: 'Variación de los afiliados, último día del mes',
  toggle: varToggle('bde.social_security_affiliates'),
  colorBySign: 'neutral',
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

lineChart($('c-paro'), {
  title: 'Tasa de paro, España',
  series: [{ dataset: 'ine.unemployment', series: 'es', field: 'value' }],
  range: { default: '5A' },
});
barChart($('c-paro-var'), {
  title: 'Variación interanual de la tasa de paro',
  series: [{ dataset: 'ine.unemployment', series: 'es', field: 'yoy_pp' }],
  colorBySign: 'neutral',
  range: { default: '5A' },
});
lineChart($('c-tasas'), {
  title: 'Tasas de empleo y de actividad',
  series: [
    { dataset: 'ine.activity_rate', series: 'es', field: 'value', label: 'Tasa de actividad' },
    { dataset: 'ine.employment_rate', series: 'es', field: 'value', label: 'Tasa de empleo' },
  ],
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

const sectores = (field) => [
  ['agricultura', 'Agricultura'], ['industria', 'Industria'],
  ['construccion', 'Construcción'], ['servicios', 'Servicios'],
].map(([k]) => ({ dataset: 'ine.employed_sectors', series: k, field }));
lineChart($('c-sectores'), {
  title: 'Ocupados por sector económico',
  toggle: [
    { id: 'yoy', label: 'Interanual (%)', series: sectores('yoy') },
    { id: 'value', label: 'Nivel (miles)', series: sectores('value') },
  ],
  range: { default: '5A' },
});
lineChart($('c-vacantes'), {
  title: 'Las vacantes en España y en la UE-27',
  series: [
    { dataset: 'eurostat.job_vacancy_rate', series: 'es', field: 'value' },
    { dataset: 'eurostat.job_vacancy_rate', series: 'eu27', field: 'value' },
  ],
  range: { default: '5A' },
});

kpiGrid($('kpis-calidad'), [
  { dataset: 'ine.temporary_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'ine.youth_unemployment', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
]);
lineChart($('c-temp'), {
  title: 'Temporalidad y parcialidad del empleo',
  series: [
    { dataset: 'ine.temporary_rate', series: 'es', field: 'value', label: 'Tasa de temporalidad' },
    { dataset: 'ine.parttime_rate', series: 'es', field: 'value', label: 'Tasa de parcialidad' },
  ],
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

lineChart($('c-pob'), {
  title: 'Población residente por nacionalidad',
  series: [
    { dataset: 'ine.population_nationality', series: 'total', field: 'value' },
    { dataset: 'ine.population_nationality', series: 'espanola', field: 'value' },
    { dataset: 'ine.population_nationality', series: 'extranjera', field: 'value' },
  ],
  range: { default: 'max' },
});
lineChart($('c-pob-var'), {
  title: 'Crecimiento interanual de la población española y extranjera',
  series: [
    { dataset: 'ine.population_nationality', series: 'espanola', field: 'yoy' },
    { dataset: 'ine.population_nationality', series: 'extranjera', field: 'yoy' },
  ],
  range: { default: 'max' },
});

kpiGrid($('kpis-costes'), [
  { dataset: 'ine.labor_cost', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'ine.labor_cost_hour', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
]);
lineChart($('c-coste'), {
  title: 'Coste laboral por trabajador',
  toggle: [
    { id: 'nivel', label: 'Nivel', series: [{ dataset: 'ine.labor_cost', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Variación interanual', series: [{ dataset: 'ine.labor_cost', series: 'es', field: 'yoy' }] },
  ],
  range: { default: '5A' },
});
lineChart($('c-hora'), {
  title: 'Coste laboral por hora efectiva',
  toggle: [
    { id: 'nivel', label: 'Nivel', series: [{ dataset: 'ine.labor_cost_hour', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Variación interanual', series: [{ dataset: 'ine.labor_cost_hour', series: 'es', field: 'yoy' }] },
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
