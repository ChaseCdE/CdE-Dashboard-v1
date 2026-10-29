// Sector público: deuda, déficit y coste de la financiación (rentabilidades, prima de riesgo e intereses).
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart } from '../charts.js';

mountLayout({ active: 'publico' });
const $ = (id) => document.getElementById(id);
const pair = (ds, f) => ['es', 'eu27'].map((s) => ({ dataset: ds, series: s, field: f }));

kpiGrid($('kpis'), [
  { dataset: 'eurostat.government_debt', series: 'es', field: 'value', title: 'Deuda pública, % del PIB', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'eurostat.budget_deficit', series: 'es', field: 'value', title: 'Saldo público anual, % del PIB' },
  { dataset: 'eurostat.gov_deficit_quarterly', series: 'es', field: 'value', title: 'Saldo público trimestral, % del PIB' },
  { dataset: 'bde.spain_10y_bond', series: 'es', field: 'value', change: { field: 'chg_1y', label: 'en un año' }, positiveIsGood: false },
  { dataset: 'bde.spread_10y_de', series: 'es', field: 'value', title: 'Diferencial a 10 años frente a Alemania', change: { field: 'chg_1m', label: 'mensual' }, positiveIsGood: false },
  { dataset: 'eurostat.interest_expenditure', series: 'es', field: 'value', title: 'Gasto en intereses, % del PIB' },
]);

/* Deuda */
lineChart($('debt-gdp'), {
  title: 'Deuda pública sobre PIB: España frente a la UE-27',
  series: pair('eurostat.government_debt', 'value'),
  range: { default: 'max' },
});
lineChart($('pde'), {
  title: 'Deuda de las Administraciones Públicas (PDE)',
  toggle: [
    { id: 'value', label: 'Nivel', series: [{ dataset: 'bde.government_debt_pde', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'bde.government_debt_pde', series: 'es', field: 'yoy' }] },
  ],
  range: { default: '5A' },
});

/* Déficit */
barChart($('deficit-q'), {
  title: 'Saldo público trimestral: España frente a la UE-27',
  series: pair('eurostat.gov_deficit_quarterly', 'value'),
  ref: { y: 0 },
  range: { default: '5A' },
});
lineChart($('deficit-a'), {
  title: 'Saldo público anual: España frente a la UE-27',
  series: pair('eurostat.budget_deficit', 'value'),
  markers: true,
  ref: { y: 0 },
  range: { default: 'max' },
});

/* Coste de la financiación */
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
lineChart($('interest'), {
  title: 'Gasto en intereses de la deuda pública',
  series: ['es', 'eu27', 'de', 'fr', 'it'].map((k) => ({ dataset: 'eurostat.interest_expenditure', series: k, field: 'value' })),
  range: { default: 'max' },
});
