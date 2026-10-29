// Sectores · Construcción y vivienda: actividad constructora, precios de la vivienda (INE, MIVAU,
// Registradores, Eurostat), alquiler, compraventas e hipotecas.
import { kpiGrid, lineChart } from '../charts.js';

const $ = (id) => document.getElementById('con-' + id);  // ids prefixed in sectores.html
const pair = (ds, f) => ['es', 'eu27'].map((s) => ({ dataset: ds, series: s, field: f }));

kpiGrid($('kpis'), [
  { dataset: 'ine.construction_ipco', series: 'total', field: 'yoy', title: 'Producción de la construcción, variación interanual' },
  { dataset: 'ine.house_prices', series: 'es', field: 'yoy', title: 'Precio de la vivienda (INE), variación interanual', positiveIsGood: false },
  { dataset: 'mivau.appraised_house_prices', series: 'total', field: 'value', title: 'Valor tasado de la vivienda (MIVAU), euros por m²', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'ine.housing_transactions', series: 'total', field: 'sum_12m', title: 'Compraventas de viviendas, últimos 12 meses', change: { field: 'yoy', label: 'interanual (mes)' } },
  { dataset: 'ine.mortgages', series: 'es', field: 'sum_12m', title: 'Hipotecas sobre viviendas, últimos 12 meses', change: { field: 'yoy', label: 'interanual (mes)' } },
  { dataset: 'bde.mortgage_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
]);

/* Actividad constructora */
const ipco = (f) => ['total', 'edificios', 'ingenieria', 'especializada'].map((s) => ({ dataset: 'ine.construction_ipco', series: s, field: f }));
lineChart($('ipco'), {
  title: 'Producción de la construcción por tipo de obra',
  subtitle: 'Índice de Producción de la Construcción del INE (base 2021), disponible desde enero de 2025.',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: ipco('yoy') },
    { id: 'value', label: 'Índice (2021 = 100)', series: ipco('value') },
  ],
  markers: true,
  range: { default: 'max' },
});
lineChart($('construction-eu'), {
  title: 'Producción de la construcción: España frente a la UE-27',
  toggle: [
    { id: 'value', label: 'Índice', series: pair('eurostat.construction_production', 'value') },
    { id: 'yoy', label: 'Var. interanual', series: pair('eurostat.construction_production', 'yoy') },
  ],
  range: { default: '5A' },
});
const gva = (f) => [
  { dataset: 'ine.gva_sectors', series: 'construccion', field: f, label: 'Construcción' },
  { dataset: 'ine.gva_sectors', series: 'pib', field: f, label: 'PIB', dash: 'dot' },
];
lineChart($('gva'), {
  title: 'Valor añadido de la construcción',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: gva('yoy') },
    { id: 'qoq', label: 'Var. trimestral', series: gva('qoq') },
  ],
  range: { default: '5A' },
});

/* Precios de la vivienda */
lineChart($('house'), {
  title: 'Índice de precios de vivienda (INE)',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'ine.house_prices', series: 'es', field: 'yoy' }] },
    { id: 'value', label: 'Índice', series: [{ dataset: 'ine.house_prices', series: 'es', field: 'value' }] },
  ],
  range: { default: 'max' },
});
lineChart($('house-sources'), {
  title: 'Precio de la vivienda según tres fuentes: variación interanual',
  series: [
    { dataset: 'ine.house_prices', series: 'es', field: 'yoy', label: 'INE (índice de precios de vivienda)' },
    { dataset: 'mivau.appraised_house_prices', series: 'total', field: 'yoy', label: 'MIVAU (valor tasado)' },
    { dataset: 'registradores.house_prices', series: 'es', field: 'yoy', label: 'Registradores (€/m²)' },
  ],
  endLabels: false,
  range: { default: 'max' },
});
lineChart($('house-m2'), {
  title: 'Precio de la vivienda por metro cuadrado: tasaciones y compraventas registradas',
  toggle: [
    { id: 'src', label: 'MIVAU y Registradores', series: [
      { dataset: 'mivau.appraised_house_prices', series: 'total', field: 'value', label: 'MIVAU, valor tasado' },
      { dataset: 'registradores.house_prices', series: 'es', field: 'value', label: 'Registradores, compraventas' },
    ] },
    { id: 'age', label: 'MIVAU por antigüedad', series: [
      { dataset: 'mivau.appraised_house_prices', series: 'new', field: 'value' },
      { dataset: 'mivau.appraised_house_prices', series: 'used', field: 'value' },
    ] },
  ],
  range: { default: 'max' },
});
lineChart($('house-eu'), {
  title: 'Precio de la vivienda: España frente a la UE-27',
  series: pair('eurostat.house_prices', 'yoy'),
  ref: { y: 0 },
  range: { default: 'max' },
});
lineChart($('house-rent'), {
  title: 'Compra y alquiler de vivienda: variación interanual',
  series: [
    { dataset: 'ine.house_prices', series: 'es', field: 'yoy', label: 'Precio de la vivienda' },
    { dataset: 'ine.cpi_rent', series: 'es', field: 'yoy', label: 'Alquiler (IPC)' },
  ],
  range: { default: 'max' },
});

/* Compraventas e hipotecas */
lineChart($('housing'), {
  title: 'Compraventas de viviendas',
  toggle: [
    { id: 'sum', label: 'Suma 12 meses', series: ['nueva', 'usada'].map((s) => ({ dataset: 'ine.housing_transactions', series: s, field: 'sum_12m' })) },
    { id: 'yoy', label: 'Var. interanual', series: ['total'].map((s) => ({ dataset: 'ine.housing_transactions', series: s, field: 'yoy' })) },
  ],
  range: { default: '5A' },
});
lineChart($('mortgages'), {
  title: 'Hipotecas sobre viviendas',
  toggle: [
    { id: 'n', label: 'Suma 12 meses', series: [{ dataset: 'ine.mortgages', series: 'es', field: 'sum_12m' }] },
    { id: 'avg', label: 'Importe medio', series: [{ dataset: 'ine.mortgages', series: 'es', field: 'avg_amount' }] },
  ],
  range: { default: '5A' },
});
lineChart($('mortgage-rate'), {
  title: 'Tipo de interés de los préstamos para vivienda',
  series: [{ dataset: 'bde.mortgage_rate', series: 'es', field: 'value' }],
  range: { default: '5A' },
});
lineChart($('new-loans'), {
  title: 'Nuevo crédito a los hogares para vivienda',
  subtitle: 'Volumen de operaciones nuevas, incluidas las renegociaciones.',
  toggle: [
    { id: 'sum', label: 'Suma 12 meses', series: [{ dataset: 'bde.new_housing_loans', series: 'es', field: 'sum_12m' }] },
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'bde.new_housing_loans', series: 'es', field: 'yoy' }], ref: { y: 0 } },
  ],
  range: { default: '5A' },
});
