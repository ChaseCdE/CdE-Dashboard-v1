// Página "Crédito y tipos": tipos de interés, crédito al sector privado, endeudamiento y morosidad.
// La deuda pública y su coste están en Sector público; la curva de rentabilidades, en Mercados.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart } from '../charts.js';

mountLayout({ active: 'credito' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'bde.ester_daily', series: 'ea', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.euribor_12m_daily', series: 'ea', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.mortgage_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.corporate_lending_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.credit_households_total', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.credit_nfc_total', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.npl_ratio', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.household_debt_gdp', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
]);

/* Tipos de interés */
lineChart($('money'), {
  title: '€STR y Euríbor',
  series: [
    { dataset: 'bde.ester_daily', series: 'ea', field: 'value' },
    { dataset: 'bde.euribor_3m_daily', series: 'ea', field: 'value' },
    { dataset: 'bde.euribor_12m_daily', series: 'ea', field: 'value' },
  ],
  range: { default: '5A' },
});
lineChart($('lending'), {
  title: 'Tipos de interés de préstamos y depósitos bancarios',
  series: [
    { dataset: 'bde.mortgage_rate', series: 'es', field: 'value' },
    { dataset: 'bde.consumer_credit_rate', series: 'es', field: 'value' },
    { dataset: 'bde.corporate_lending_rate', series: 'es', field: 'value' },
    { dataset: 'bde.household_deposit_rate', series: 'es', field: 'value' },
  ],
  range: { default: '5A' },
});

/* Crédito */
lineChart($('credit'), {
  title: 'Crédito a hogares y a sociedades no financieras',
  series: [
    { dataset: 'bde.credit_households_total', series: 'es', field: 'yoy' },
    { dataset: 'bde.credit_nfc_total', series: 'es', field: 'yoy' },
  ],
  ref: { y: 0 },
  range: { default: '5A' },
});
const newLoans = (ids, labels) => ['sum_12m', 'yoy'].map((f) => ({
  id: f,
  label: f === 'sum_12m' ? 'Suma 12 meses' : 'Var. interanual',
  series: ids.map((d, i) => ({ dataset: d, series: 'es', field: f, label: labels[i] })),
  ref: f === 'yoy' ? { y: 0 } : undefined,
}));
lineChart($('newhh'), {
  title: 'Nuevo crédito a los hogares para vivienda y consumo',
  subtitle: 'Volumen de operaciones nuevas, incluidas las renegociaciones. Suma móvil de 12 meses para evitar la estacionalidad.',
  toggle: newLoans(['bde.new_housing_loans', 'bde.new_consumer_loans'], ['Vivienda', 'Consumo']),
  range: { default: '5A' },
});
lineChart($('newcorp'), {
  title: 'Nuevo crédito a las sociedades no financieras',
  subtitle: 'Volumen de operaciones nuevas, incluidas las renegociaciones. Suma móvil de 12 meses para evitar la estacionalidad.',
  toggle: newLoans(['bde.new_corporate_loans'], ['Sociedades no financieras']),
  range: { default: '5A' },
});

/* Endeudamiento y morosidad */
lineChart($('debt'), {
  title: 'Deuda sobre el PIB de hogares y sociedades no financieras',
  series: [
    { dataset: 'bde.household_debt_gdp', series: 'es', field: 'value' },
    { dataset: 'bde.nfc_debt_gdp', series: 'es', field: 'value' },
  ],
  range: { default: 'max' },
});
lineChart($('npl'), {
  title: 'Ratio de créditos dudosos',
  series: [{ dataset: 'bde.npl_ratio', series: 'es', field: 'value' }],
  range: { default: 'max' },
});
