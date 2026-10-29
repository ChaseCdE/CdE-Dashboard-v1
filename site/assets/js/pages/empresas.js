import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart } from '../charts.js';

mountLayout({ active: 'empresas' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'ine.tourist_arrivals', series: 'es', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'ine.tourist_spending', series: 'es', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'ine.hotel_overnight_stays', series: 'total', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'ine.companies', series: 'created', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'ine.companies', series: 'dissolved', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: false },
  { dataset: 'eurostat.bankruptcies', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual (trimestre)' }, positiveIsGood: false },
]);

lineChart($('c-llegadas'), {
  title: 'Llegadas de turistas internacionales, suma de 12 meses',
  series: [{ dataset: 'ine.tourist_arrivals', series: 'es', field: 'sum_12m' }],
  range: { default: '5A' },
});
barChart($('c-llegadas-yoy'), {
  title: 'Llegadas de turistas internacionales, variación interanual mensual',
  series: [{ dataset: 'ine.tourist_arrivals', series: 'es', field: 'yoy' }],
  colorBySign: 'neutral',
  range: { default: '3A', options: [{ id: '2A', label: '2A', years: 2 }, { id: '3A', label: '3A', years: 3 }, { id: 'max', label: 'Máx', years: null }] },
});
lineChart($('c-gasto'), {
  title: 'Gasto de los turistas internacionales, suma de 12 meses',
  series: [{ dataset: 'ine.tourist_spending', series: 'es', field: 'sum_12m' }],
  range: { default: '5A' },
});
barChart($('c-gasto-yoy'), {
  title: 'Gasto de los turistas internacionales, variación interanual mensual',
  series: [{ dataset: 'ine.tourist_spending', series: 'es', field: 'yoy' }],
  colorBySign: 'neutral',
  range: { default: '3A', options: [{ id: '2A', label: '2A', years: 2 }, { id: '3A', label: '3A', years: 3 }, { id: 'max', label: 'Máx', years: null }] },
});
lineChart($('c-hotel'), {
  title: 'Pernoctaciones hoteleras de residentes y no residentes',
  toggle: [
    { id: 'sum', label: 'Suma de 12 meses', series: [
      { dataset: 'ine.hotel_overnight_stays', series: 'residentes', field: 'sum_12m' },
      { dataset: 'ine.hotel_overnight_stays', series: 'no_residentes', field: 'sum_12m' } ] },
    { id: 'yoy', label: 'Variación interanual', series: [
      { dataset: 'ine.hotel_overnight_stays', series: 'residentes', field: 'yoy' },
      { dataset: 'ine.hotel_overnight_stays', series: 'no_residentes', field: 'yoy' } ] },
  ],
  range: { default: '5A' },
});
barChart($('c-ingresos'), {
  title: 'Ingresos por turismo en la balanza de pagos, variación interanual',
  series: [{ dataset: 'bde.tourism_receipts', series: 'es', field: 'yoy' }],
  colorBySign: 'neutral',
  range: { default: '3A', options: [{ id: '2A', label: '2A', years: 2 }, { id: '3A', label: '3A', years: 3 }, { id: 'max', label: 'Máx', years: null }] },
});

lineChart($('c-soc'), {
  title: 'Sociedades mercantiles creadas y disueltas, suma de 12 meses',
  series: [
    { dataset: 'ine.companies', series: 'created', field: 'sum_12m' },
    { dataset: 'ine.companies', series: 'dissolved', field: 'sum_12m' },
  ],
  range: { default: '5A' },
});
barChart($('c-soc-yoy'), {
  title: 'Sociedades mercantiles creadas, variación interanual mensual',
  series: [{ dataset: 'ine.companies', series: 'created', field: 'yoy' }],
  colorBySign: 'neutral',
  range: { default: '5A' },
});

lineChart($('c-precios-hotel'), {
  title: 'Precios hoteleros en España',
  toggle: [
    { id: 'value', label: 'Nivel del índice', series: [{ dataset: 'ine.hotel_prices', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Variación interanual', series: [{ dataset: 'ine.hotel_prices', series: 'es', field: 'yoy' }] },
  ],
  range: { default: '5A' },
});

lineChart($('c-quiebras'), {
  title: 'Declaraciones de quiebra en España y en la UE-27',
  toggle: [
    { id: 'value', label: 'Índice 2021 = 100', series: [
      { dataset: 'eurostat.bankruptcies', series: 'es', field: 'value' },
      { dataset: 'eurostat.bankruptcies', series: 'eu27', field: 'value' } ] },
    { id: 'yoy', label: 'Variación interanual', series: [
      { dataset: 'eurostat.bankruptcies', series: 'es', field: 'yoy' },
      { dataset: 'eurostat.bankruptcies', series: 'eu27', field: 'yoy' } ] },
  ],
  range: { default: '5A' },
});
lineChart($('c-altas'), {
  title: 'Altas de empresas en España y en la UE-27',
  toggle: [
    { id: 'value', label: 'Índice 2021 = 100', series: [
      { dataset: 'eurostat.business_registrations', series: 'es', field: 'value' },
      { dataset: 'eurostat.business_registrations', series: 'eu27', field: 'value' } ] },
    { id: 'yoy', label: 'Variación interanual', series: [
      { dataset: 'eurostat.business_registrations', series: 'es', field: 'yoy' },
      { dataset: 'eurostat.business_registrations', series: 'eu27', field: 'yoy' } ] },
  ],
  range: { default: '5A' },
});
