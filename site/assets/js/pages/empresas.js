// Página Empresas: demografía empresarial, ventas y costes (Observatorio de Márgenes Empresariales,
// AEAT), clima empresarial y financiación de las empresas.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, groupedBarChart } from '../charts.js';

mountLayout({ active: 'empresas' });
const $ = (id) => document.getElementById(id);
const pair = (ds, f) => ['es', 'eu27'].map((s) => ({ dataset: ds, series: s, field: f }));

kpiGrid($('kpis'), [
  { dataset: 'ine.companies', series: 'created', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'ine.companies', series: 'dissolved', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: false },
  { dataset: 'eurostat.bankruptcies', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual (trimestre)' }, positiveIsGood: false },
  { dataset: 'aeat.ome_totals', series: 'sales', field: 'yoy', title: 'Ventas de las sociedades no financieras, variación anual' },
  { dataset: 'aeat.ome_totals', series: 'wages', field: 'yoy', title: 'Masa salarial de las sociedades no financieras, variación anual' },
  { dataset: 'ine.business_confidence', series: 'ice', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.credit_nfc_total', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.corporate_lending_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
]);

/* Demografía empresarial */
const soc = (f) => [
  { dataset: 'ine.companies', series: 'created', field: f },
  { dataset: 'ine.companies', series: 'dissolved', field: f },
];
lineChart($('companies'), {
  title: 'Sociedades mercantiles creadas y disueltas',
  toggle: [
    { id: 'sum', label: 'Suma 12 meses', series: soc('sum_12m') },
    { id: 'yoy', label: 'Var. interanual', series: soc('yoy') },
  ],
  range: { default: '5A' },
});
lineChart($('registrations'), {
  title: 'Altas de empresas: España frente a la UE-27',
  toggle: [
    { id: 'value', label: 'Índice (2021 = 100)', series: pair('eurostat.business_registrations', 'value') },
    { id: 'yoy', label: 'Var. interanual', series: pair('eurostat.business_registrations', 'yoy') },
  ],
  range: { default: '5A' },
});
lineChart($('bankruptcies'), {
  title: 'Declaraciones de quiebra: España frente a la UE-27',
  toggle: [
    { id: 'value', label: 'Índice (2021 = 100)', series: pair('eurostat.bankruptcies', 'value') },
    { id: 'yoy', label: 'Var. interanual', series: pair('eurostat.bankruptcies', 'yoy') },
  ],
  range: { default: '5A' },
});

/* Ventas y costes (Observatorio de Márgenes Empresariales, AEAT) */
const ome = (f) => ['sales', 'purchases', 'wages'].map((k) => ({ dataset: 'aeat.ome_totals', series: k, field: f }));
lineChart($('ome'), {
  title: 'Ventas, compras y masa salarial de las sociedades no financieras',
  subtitle: 'Declaraciones de IVA y retenciones. Datos corregidos de efectos estacionales y de calendario (CVEC).',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: ome('yoy'), ref: { y: 0 } },
    { id: 'idx', label: 'Índice (2019 = 100)', series: ome('index_2019'), ref: { y: 100 } },
  ],
  endLabels: false,
  range: { default: '5A' },
});
groupedBarChart($('ome-div'), {
  title: 'Ventas por divisiones de actividad: las cinco que más y las cinco que menos crecen',
  subtitle: 'Variación anual del último trimestre, datos CVEC. Divisiones de la CNAE-2009 a dos dígitos.',
  dataset: 'aeat.ome_divisions', field: 'yoy', orientation: 'h', sort: 'desc', top: 5, bottom: 5, colorBySign: true,
});

/* Clima empresarial */
lineChart($('confidence'), {
  title: 'Confianza empresarial',
  series: [{ dataset: 'ine.business_confidence', series: 'ice', field: 'value' }],
  markers: true,
  range: { default: 'max' },
});
lineChart($('capacity'), {
  title: 'Utilización de la capacidad productiva: España frente a la UE-27',
  series: pair('eurostat.capacity_utilization', 'value'),
  range: { default: '5A' },
});

/* Financiación de las empresas */
lineChart($('credit'), {
  title: 'Crédito a las sociedades no financieras',
  series: [{ dataset: 'bde.credit_nfc_total', series: 'es', field: 'yoy' }],
  ref: { y: 0 },
  range: { default: '5A' },
});
lineChart($('newcorp'), {
  title: 'Nuevo crédito a las sociedades no financieras',
  subtitle: 'Volumen de operaciones nuevas, incluidas las renegociaciones.',
  toggle: [
    { id: 'sum', label: 'Suma 12 meses', series: [{ dataset: 'bde.new_corporate_loans', series: 'es', field: 'sum_12m' }] },
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'bde.new_corporate_loans', series: 'es', field: 'yoy' }], ref: { y: 0 } },
  ],
  range: { default: '5A' },
});
lineChart($('rate'), {
  title: 'Tipo de interés de los préstamos a sociedades no financieras',
  series: [{ dataset: 'bde.corporate_lending_rate', series: 'es', field: 'value' }],
  range: { default: '5A' },
});
lineChart($('debt'), {
  title: 'Deuda de las sociedades no financieras sobre el PIB',
  series: [{ dataset: 'bde.nfc_debt_gdp', series: 'es', field: 'value' }],
  range: { default: 'max' },
});
