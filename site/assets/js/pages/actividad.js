// Página Actividad: PIB y demanda, coyuntura agregada, clima económico, consumo y hogares
// y productividad. El detalle por ramas está en las páginas de Sectores.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, stackedBarChart } from '../charts.js';

mountLayout({ active: 'actividad' });
const $ = (id) => document.getElementById(id);
const pair = (ds, f) => ['es', 'eu27'].map((s) => ({ dataset: ds, series: s, field: f }));

kpiGrid($('kpis'), [
  { dataset: 'ine.gdp', series: 'es', field: 'yoy', title: 'PIB, variación interanual', change: { field: 'qoq', label: 'trimestral' } },
  { dataset: 'ine.industrial_production', series: 'es', field: 'yoy', title: 'Producción industrial, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'ine.services_production', series: 'es', field: 'yoy', title: 'Producción de servicios, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'ine.business_confidence', series: 'ice', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'ine.retail_sales', series: 'es', field: 'yoy', title: 'Comercio minorista, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'eurostat.consumer_confidence', series: 'es', field: 'value', title: 'Confianza del consumidor, España', change: { field: 'yoy_diff', label: 'interanual' } },
]);

/* PIB y demanda */
lineChart($('gdp'), {
  title: 'PIB de España',
  markers: true,
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'ine.gdp', series: 'es', field: 'yoy' }] },
    { id: 'qoq', label: 'Var. trimestral', series: [{ dataset: 'ine.gdp', series: 'es', field: 'qoq' }] },
    { id: 'lvl', label: 'Índice (2019 = 100)', rebase: { year: 2019 }, series: [{ dataset: 'ine.gdp', series: 'es', field: 'value' }] },
  ],
  range: { default: '5A' },
});
stackedBarChart($('demand'), {
  title: 'Contribuciones de la demanda al crecimiento del PIB',
  components: ['private_consumption', 'public_consumption', 'gfcf', 'inventories', 'external_demand']
    .map((s) => ({ dataset: 'ine.gdp_demand', series: s, field: 'contribution' })),
  total: { dataset: 'ine.gdp', series: 'es', field: 'yoy', label: 'PIB, variación interanual' },
  range: { years: 3 },
});
lineChart($('gdp-compare'), {
  title: 'PIB real: España frente a la UE-27 y las grandes economías',
  series: ['es', 'eu27', 'de', 'fr', 'it'].map((s) => ({ dataset: 'eurostat.gdp_index', series: s, field: 'value' })),
  endLabels: true,
  range: { default: '5A' },
});
const gva = (f) => [
  { dataset: 'ine.gva_sectors', series: 'agricultura', field: f, label: 'Agricultura' },
  { dataset: 'ine.gva_sectors', series: 'industria', field: f, label: 'Industria' },
  { dataset: 'ine.gva_sectors', series: 'construccion', field: f, label: 'Construcción' },
  { dataset: 'ine.gva_sectors', series: 'servicios', field: f, label: 'Servicios' },
  { dataset: 'ine.gva_sectors', series: 'pib', field: f, label: 'PIB', dash: 'dot' },
];
lineChart($('gva-sectors'), {
  title: 'Valor añadido de los grandes sectores',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: gva('yoy') },
    { id: 'qoq', label: 'Var. trimestral', series: gva('qoq') },
  ],
  range: { default: '5A' },
});

/* Coyuntura */
const prod = (f) => [
  { dataset: 'ine.industrial_production', series: 'es', field: f, label: 'Industria' },
  { dataset: 'ine.services_production', series: 'es', field: f, label: 'Servicios' },
];
lineChart($('production'), {
  title: 'Producción industrial y de servicios',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: prod('yoy') },
    { id: 'mom', label: 'Var. mensual', series: prod('mom') },
    { id: 'value', label: 'Índice (2021 = 100)', rebase: { year: 2021 }, series: prod('value') },
  ],
  range: { default: '5A' },
});
lineChart($('turnover'), {
  title: 'Cifra de negocios de la industria y de los servicios',
  series: [
    { dataset: 'ine.industry_turnover', series: 'es', field: 'yoy', label: 'Industria' },
    { dataset: 'ine.services_turnover', series: 'es', field: 'yoy', label: 'Servicios' },
  ],
  range: { default: '5A' },
});

/* Clima económico */
lineChart($('confidence'), {
  title: 'Confianza empresarial',
  series: [{ dataset: 'ine.business_confidence', series: 'ice', field: 'value' }],
  markers: true,
  range: { default: 'max' },
});
lineChart($('esi'), {
  title: 'Indicador de sentimiento económico: España frente a la UE-27',
  series: pair('eurostat.economic_sentiment', 'value'),
  ref: { y: 100, label: 'Media de largo plazo' },
  range: { default: '5A' },
});

/* Consumo y hogares */
lineChart($('retail'), {
  title: 'Ventas del comercio minorista',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'ine.retail_sales', series: 'es', field: 'yoy' }] },
    { id: 'mom', label: 'Var. mensual', series: [{ dataset: 'ine.retail_sales', series: 'es', field: 'mom' }] },
    { id: 'value', label: 'Índice', series: [{ dataset: 'ine.retail_sales', series: 'es', field: 'value' }] },
  ],
  range: { default: '5A' },
});
lineChart($('consumer-conf'), {
  title: 'Confianza del consumidor: España frente a la UE-27',
  series: pair('eurostat.consumer_confidence', 'value'),
  range: { default: '5A' },
});
lineChart($('saving'), {
  title: 'Tasa de ahorro de los hogares',
  series: [{ dataset: 'ine.household_saving_rate', series: 'es', field: 'value' }],
  markers: true,
  range: { default: '5A' },
});

/* Productividad y convergencia */
const peers = (ds, keys) => keys.map((k) => ({ dataset: 'eurostat.' + ds, series: k, field: 'value' }));
lineChart($('productivity'), {
  title: 'PIB y productividad',
  series: ['pib', 'pib_per_capita', 'pib_per_working_age', 'pib_per_employed', 'pib_per_hour']
    .map((s) => ({ dataset: 'ine.gdp_productivity', series: s, field: 'value' })),
  endLabels: false,
  range: { default: 'max' },
});
lineChart($('conv-gdppc'), {
  title: 'PIB per cápita en paridad de poder adquisitivo',
  series: peers('gdp_per_capita_pps', ['es', 'de', 'fr', 'it', 'pt']),
  ref: { y: 100, label: 'Media UE-27' },
  range: { default: 'max' },
});
lineChart($('conv-prod'), {
  title: 'Productividad por hora trabajada en paridad de poder adquisitivo',
  series: peers('labour_productivity_pps', ['es', 'de', 'fr', 'it', 'pt']),
  ref: { y: 100, label: 'Media UE-27' },
  range: { default: 'max' },
});
lineChart($('conv-rd'), {
  title: 'Gasto en I+D sobre PIB, España y principales economías',
  series: peers('rd_expenditure', ['es', 'eu27', 'de', 'fr', 'it']),
  range: { default: 'max' },
});
