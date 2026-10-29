// Sectores · Turismo: llegadas y gasto de turistas internacionales, pernoctaciones, precios hoteleros
// e ingresos por turismo en la balanza de pagos.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart } from '../charts.js';

mountLayout({ active: 'turismo' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'ine.tourist_arrivals', series: 'es', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'ine.tourist_spending', series: 'es', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'ine.hotel_overnight_stays', series: 'total', field: 'sum_12m', change: { field: 'yoy', label: 'interanual (mes)' }, positiveIsGood: true },
  { dataset: 'bde.tourism_receipts', series: 'es', field: 'value', change: { field: 'yoy', label: 'interanual' }, positiveIsGood: true },
]);

const lvlYoy = (ds, series = 'es') => [
  { id: 'sum', label: 'Suma 12 meses', series: [{ dataset: ds, series, field: 'sum_12m' }] },
  { id: 'yoy', label: 'Var. interanual', series: [{ dataset: ds, series, field: 'yoy' }], ref: { y: 0 } },
];

/* Turistas internacionales */
lineChart($('arrivals'), { title: 'Llegadas de turistas internacionales', toggle: lvlYoy('ine.tourist_arrivals'), range: { default: '5A' } });
lineChart($('spending'), { title: 'Gasto de los turistas internacionales', toggle: lvlYoy('ine.tourist_spending'), range: { default: '5A' } });

/* Alojamiento */
lineChart($('stays'), {
  title: 'Pernoctaciones hoteleras de residentes y no residentes',
  toggle: [
    { id: 'sum', label: 'Suma 12 meses', series: ['residentes', 'no_residentes'].map((s) => ({ dataset: 'ine.hotel_overnight_stays', series: s, field: 'sum_12m' })) },
    { id: 'yoy', label: 'Var. interanual', series: ['residentes', 'no_residentes'].map((s) => ({ dataset: 'ine.hotel_overnight_stays', series: s, field: 'yoy' })) },
  ],
  range: { default: '5A' },
});
lineChart($('hotel-prices'), {
  title: 'Precios hoteleros',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'ine.hotel_prices', series: 'es', field: 'yoy' }] },
    { id: 'value', label: 'Índice', series: [{ dataset: 'ine.hotel_prices', series: 'es', field: 'value' }] },
  ],
  range: { default: '5A' },
});

/* Balanza de pagos */
barChart($('receipts'), {
  title: 'Ingresos por turismo en la balanza de pagos',
  toggle: [
    { id: 'value', label: 'Nivel', series: [{ dataset: 'bde.tourism_receipts', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Var. interanual', series: [{ dataset: 'bde.tourism_receipts', series: 'es', field: 'yoy' }] },
  ],
  colorBySign: 'neutral',
  range: { default: '5A' },
});
