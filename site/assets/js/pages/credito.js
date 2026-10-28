// Página "Crédito y tipos". Todo número, unidad y fecha procede de los JSON.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, crossSectionChart } from '../charts.js';

mountLayout({ active: 'credito' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'bde.ester_daily', series: 'ea', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.euribor_12m_daily', series: 'ea', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.spain_10y_bond', series: 'es', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.mortgage_rate', series: 'es', field: 'value', change: { field: 'mom_pp', label: 'mensual' }, positiveIsGood: false },
  { dataset: 'bde.consumer_credit_rate', series: 'es', field: 'value', change: { field: 'mom_pp', label: 'mensual' }, positiveIsGood: false },
  { dataset: 'bde.corporate_lending_rate', series: 'es', field: 'value', change: { field: 'mom_pp', label: 'mensual' }, positiveIsGood: false },
  { dataset: 'bde.household_deposit_rate', series: 'es', field: 'value', change: { field: 'mom_pp', label: 'mensual' }, positiveIsGood: true },
  { dataset: 'bde.credit_households_total', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.credit_nfc_total', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' } },
  { dataset: 'bde.household_debt_gdp', series: 'es', field: 'value', change: { field: 'qoq_pp', label: 'trimestral' }, positiveIsGood: false },
  { dataset: 'bde.nfc_debt_gdp', series: 'es', field: 'value', change: { field: 'qoq_pp', label: 'trimestral' }, positiveIsGood: false },
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
