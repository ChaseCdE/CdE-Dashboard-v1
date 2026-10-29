import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, stackedBarChart, groupedBarChart } from '../charts.js';

mountLayout({ active: 'actividad' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'ine.gdp', series: 'es', field: 'yoy', title: 'PIB, variación interanual', change: { field: 'qoq', label: 'trimestral' } },
  { dataset: 'ine.industrial_production', series: 'es', field: 'yoy', title: 'Producción industrial, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'ine.services_production', series: 'es', field: 'yoy', title: 'Producción de servicios, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'ine.business_confidence', series: 'ice', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'ine.retail_sales', series: 'es', field: 'yoy', title: 'Comercio minorista, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'eurostat.consumer_confidence', series: 'es', field: 'value', title: 'Confianza del consumidor, España', change: { field: 'yoy_diff', label: 'interanual' } },
]);

/* PIB */
lineChart($('gdp'), {
  title: 'PIB de España',
  markers: true,
  toggle: [
    { id: 'yoy', label: 'Interanual', series: [{ dataset: 'ine.gdp', series: 'es', field: 'yoy' }] },
    { id: 'qoq', label: 'Trimestral', series: [{ dataset: 'ine.gdp', series: 'es', field: 'qoq' }] },
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
  title: 'PIB real: España frente a las grandes economías europeas',
  series: ['es', 'de', 'fr', 'it', 'eu27'].map((s) => ({ dataset: 'eurostat.gdp_index', series: s, field: 'value' })),
  endLabels: true,
  range: { default: '5A' },
});
lineChart($('productivity'), {
  title: 'PIB y productividad',
  series: ['pib', 'pib_per_capita', 'pib_per_working_age', 'pib_per_employed', 'pib_per_hour']
    .map((s) => ({ dataset: 'ine.gdp_productivity', series: s, field: 'value' })),
  endLabels: false,
  range: { default: 'max' },
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
    { id: 'yoy', label: 'Interanual', series: gva('yoy') },
    { id: 'qoq', label: 'Trimestral', series: gva('qoq') },
  ],
  range: { default: '5A' },
});

/* Producción y confianza */
const prod = (f) => [
  { dataset: 'ine.industrial_production', series: 'es', field: f, label: 'Industria' },
  { dataset: 'ine.services_production', series: 'es', field: f, label: 'Servicios' },
];
lineChart($('production'), {
  title: 'Producción industrial y de servicios',
  toggle: [
    { id: 'yoy', label: 'Interanual', series: prod('yoy') },
    { id: 'mom', label: 'Mensual', series: prod('mom') },
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
groupedBarChart($('ipi-sectors'), {
  title: 'Producción industrial por destino económico',
  dataset: 'ine.ipi_sectors', orientation: 'h', sort: 'desc', colorBySign: true,
  toggle: [{ id: 'yoy', label: 'Interanual', field: 'yoy' }, { id: 'ytd', label: 'Acumulado del año', field: 'ytd' }],
});
groupedBarChart($('ipss-sectors'), {
  title: 'Producción de servicios por sector',
  dataset: 'ine.ipss_sectors', orientation: 'h', sort: 'desc', colorBySign: true,
  toggle: [{ id: 'yoy', label: 'Interanual', field: 'yoy' }, { id: 'ytd', label: 'Acumulado del año', field: 'ytd' }],
});
lineChart($('confidence'), {
  title: 'Confianza empresarial',
  series: [{ dataset: 'ine.business_confidence', series: 'ice', field: 'value' }],
  markers: true,
  range: { default: 'max' },
});
lineChart($('construction'), {
  title: 'Producción en la construcción: España frente a la UE-27',
  toggle: [
    { id: 'value', label: 'Índice', series: ['es', 'eu27'].map((s) => ({ dataset: 'eurostat.construction_production', series: s, field: 'value' })) },
    { id: 'yoy', label: 'Interanual', series: ['es', 'eu27'].map((s) => ({ dataset: 'eurostat.construction_production', series: s, field: 'yoy' })) },
  ],
  range: { default: '5A' },
});
lineChart($('capacity'), {
  title: 'Utilización de la capacidad productiva: España frente a la UE-27',
  series: ['es', 'eu27'].map((s) => ({ dataset: 'eurostat.capacity_utilization', series: s, field: 'value' })),
  range: { default: '5A' },
});

/* Consumo y hogares */
lineChart($('retail'), {
  title: 'Ventas del comercio minorista',
  toggle: [
    { id: 'yoy', label: 'Interanual', series: [{ dataset: 'ine.retail_sales', series: 'es', field: 'yoy' }] },
    { id: 'mom', label: 'Mensual', series: [{ dataset: 'ine.retail_sales', series: 'es', field: 'mom' }] },
    { id: 'value', label: 'Índice', series: [{ dataset: 'ine.retail_sales', series: 'es', field: 'value' }] },
  ],
  range: { default: '5A' },
});
lineChart($('consumer-conf'), {
  title: 'Confianza del consumidor: España frente a la UE-27',
  series: ['es', 'eu27'].map((s) => ({ dataset: 'eurostat.consumer_confidence', series: s, field: 'value' })),
  range: { default: '5A' },
});
lineChart($('house-prices'), {
  title: 'Precios de la vivienda: España frente a la UE-27',
  series: ['es', 'eu27'].map((s) => ({ dataset: 'eurostat.house_prices', series: s, field: 'yoy' })),
  range: { default: '5A' },
});
lineChart($('credit'), {
  title: 'Crédito a los hogares',
  series: [{ dataset: 'bde.credit_households_total', series: 'es', field: 'yoy' }],
  range: { default: '5A' },
});
lineChart($('mortgage'), {
  title: 'Tipo de interés de los préstamos para vivienda',
  series: [{ dataset: 'bde.mortgage_rate', series: 'es', field: 'value' }],
  range: { default: '5A' },
});
lineChart($('saving'), {
  title: 'Tasa de ahorro de los hogares (desestacionalizada)',
  series: [{ dataset: 'ine.household_saving_rate', series: 'es', field: 'value' }],
  markers: true,
  range: { default: '5A' },
});
lineChart($('housing'), {
  title: 'Compraventas de viviendas, acumulado de 12 meses',
  series: [
    { dataset: 'ine.housing_transactions', series: 'nueva', field: 'sum_12m' },
    { dataset: 'ine.housing_transactions', series: 'usada', field: 'sum_12m' },
  ],
  range: { default: '5A' },
});
lineChart($('mortgages'), {
  title: 'Hipotecas sobre viviendas',
  toggle: [
    { id: 'n', label: 'Número, acumulado 12 meses', series: [{ dataset: 'ine.mortgages', series: 'es', field: 'sum_12m' }] },
    { id: 'avg', label: 'Importe medio', series: [{ dataset: 'ine.mortgages', series: 'es', field: 'avg_amount' }] },
  ],
  range: { default: '5A' },
});
