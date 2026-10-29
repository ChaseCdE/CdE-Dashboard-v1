// Página "Crédito y tipos". Todo número, unidad y fecha procede de los JSON.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, crossSectionChart } from '../charts.js';

mountLayout({ active: 'credito' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'bde.ester_daily', series: 'ea', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.euribor_12m_daily', series: 'ea', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.spain_10y_bond', series: 'es', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.mortgage_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.corporate_lending_rate', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.credit_households_total', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.credit_nfc_total', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.spread_10y_de', series: 'es', field: 'value', title: 'Diferencial a 10 años frente a Alemania', change: { field: 'chg_1m', label: 'mensual' }, positiveIsGood: false },
  { dataset: 'bde.npl_ratio', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.household_debt_gdp', series: 'es', field: 'value', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'bde.current_account_balance', series: 'es', field: 'sum_12m', title: 'Saldo por cuenta corriente, 12 meses' },
  { dataset: 'bde.tourism_receipts', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: true },
]);

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

crossSectionChart($('curve'), {
  title: 'Curva de rentabilidad de la deuda pública española',
  series: [{ dataset: 'bde.yield_curve', series: 'es', field: 'yield' }],
  xTitle: 'Plazo (años)',
});

lineChart($('bonds'), {
  title: 'Rentabilidad de la deuda a 10 años: España, Alemania, Francia e Italia',
  series: [
    { dataset: 'bde.spain_10y_bond_monthly', series: 'es', field: 'value' },
    { dataset: 'bde.germany_10y_bond', series: 'de', field: 'value' },
    { dataset: 'bde.france_10y_bond', series: 'fr', field: 'value' },
    { dataset: 'bde.italy_10y_bond', series: 'it', field: 'value' },
  ],
  range: { default: '5A' },
});

lineChart($('credit'), {
  title: 'Crédito a hogares y a sociedades no financieras',
  series: [
    { dataset: 'bde.credit_households_total', series: 'es', field: 'yoy' },
    { dataset: 'bde.credit_nfc_total', series: 'es', field: 'yoy' },
  ],
  ref: { y: 0 },
  range: { default: '5A' },
});

lineChart($('debt'), {
  title: 'Deuda sobre el PIB de hogares y sociedades no financieras',
  series: [
    { dataset: 'bde.household_debt_gdp', series: 'es', field: 'value' },
    { dataset: 'bde.nfc_debt_gdp', series: 'es', field: 'value' },
  ],
  range: { default: 'max' },
});

barChart($('ca'), {
  title: 'Saldo por cuenta corriente, mensual y acumulado en 12 meses',
  series: [{ dataset: 'bde.current_account_balance', series: 'es', field: 'value', label: 'Saldo mensual' }],
  colorBySign: true,
  overlay: { dataset: 'bde.current_account_balance', series: 'es', field: 'sum_12m', label: 'Acumulado 12 meses' },
  range: { default: '5A' },
});

barChart($('tourism'), {
  title: 'Ingresos por turismo',
  series: [{ dataset: 'bde.tourism_receipts', series: 'es', field: 'value' }],
  range: { default: '5A' },
});

lineChart($('spreads'), {
  title: 'Diferencial de rentabilidad a 10 años de España frente a Alemania e Italia',
  subtitle: 'Un valor positivo indica que España paga más que el país de comparación; uno negativo, que paga menos.',
  series: [
    { dataset: 'bde.spread_10y_de', series: 'es', field: 'value', label: 'Frente a Alemania' },
    { dataset: 'bde.spread_10y_it', series: 'es', field: 'value', label: 'Frente a Italia' },
  ],
  ref: { y: 0 },
  range: { default: '5A' },
});

lineChart($('pde'), {
  title: 'Deuda de las Administraciones Públicas (PDE)',
  toggle: [
    { id: 'value', label: 'Nivel', series: [{ dataset: 'bde.government_debt_pde', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Variación anual', series: [{ dataset: 'bde.government_debt_pde', series: 'es', field: 'yoy' }] },
  ],
  range: { default: '5A' },
});

lineChart($('npl'), {
  title: 'Ratio de créditos dudosos',
  series: [{ dataset: 'bde.npl_ratio', series: 'es', field: 'value' }],
  range: { default: 'max' },
});

const newLoans = (ids, labels) => ['sum_12m', 'yoy'].map((f) => ({
  id: f,
  label: f === 'sum_12m' ? 'Suma 12 meses' : 'Variación anual',
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

barChart($('deficit'), {
  title: 'Déficit público trimestral de España y la UE-27',
  series: [
    { dataset: 'eurostat.gov_deficit_quarterly', series: 'es', field: 'value' },
    { dataset: 'eurostat.gov_deficit_quarterly', series: 'eu27', field: 'value' },
  ],
  ref: { y: 0 },
  range: { default: '5A' },
});

lineChart($('interest'), {
  title: 'Gasto en intereses de la deuda pública',
  series: ['es', 'eu27', 'de', 'fr', 'it'].map((k) => ({ dataset: 'eurostat.interest_expenditure', series: k, field: 'value' })),
  range: { default: 'max' },
});
