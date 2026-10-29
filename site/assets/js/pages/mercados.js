// Página Mercados: bolsas, tipos de interés de mercado, divisas y materias primas.
import { mountLayout } from '../layout.js';
import {
  kpiGrid, lineChart, groupedBarChart, rebasedComparison, latestTable,
} from '../charts.js';

mountLayout({ active: 'mercados' });
const $ = (id) => document.getElementById(id);

const INDICES = [
  { id: 'ibex', ds: 'yahoo.ibex_35', s: 'es', label: 'IBEX 35' },
  { id: 'ez50', ds: 'yahoo.euro_stoxx_50', s: 'ez', label: 'Euro Stoxx 50' },
  { id: 'sp500', ds: 'yahoo.sp_500', s: 'us', label: 'S&P 500' },
  { id: 'nasdaq', ds: 'yahoo.nasdaq_composite', s: 'us', label: 'Nasdaq' },
  { id: 'dax', ds: 'yahoo.dax', s: 'de', label: 'DAX 40' },
];
const retCols = [
  { field: 'close', label: 'Último' },
  { field: 'ret_1w', label: '1 semana', signColor: true },
  { field: 'ret_1m', label: '1 mes', signColor: true },
  { field: 'ret_ytd', label: 'En el año', signColor: true },
  { field: 'ret_1y', label: '1 año', signColor: true },
];

kpiGrid($('kpis'), [
  { dataset: 'yahoo.ibex_35', series: 'es', field: 'close', change: { field: 'ret_1d', label: 'en el día' }, positiveIsGood: true },
  { dataset: 'yahoo.euro_stoxx_50', series: 'ez', field: 'close', change: { field: 'ret_1d', label: 'en el día' }, positiveIsGood: true },
  { dataset: 'yahoo.sp_500', series: 'us', field: 'close', change: { field: 'ret_1d', label: 'en el día' }, positiveIsGood: true },
  { dataset: 'ecb.eur_usd', series: 'global', field: 'close', change: { field: 'ret_1d', label: 'en el día' } },
  { dataset: 'eia.brent_crude', series: 'global', field: 'close', change: { field: 'ret_1d', label: 'en el día' } },
  { dataset: 'fed.us_treasury_10y', series: 'us', field: 'close', change: { field: 'chg_1d', label: 'en el día' } },
]);

// Bolsas
lineChart($('indices'), {
  title: 'Cierre diario de los principales índices bursátiles',
  toggle: INDICES.map((i) => ({
    id: i.id, label: i.label,
    series: [
      { dataset: i.ds, series: i.s, field: 'close', label: i.label },
      { dataset: i.ds, series: i.s, field: 'sma_200', label: 'Media de 200 sesiones', dash: 'dash' },
    ],
  })),
  range: { default: '5A' },
});

rebasedComparison($('comparativa'), {
  title: 'Evolución comparada de los índices',
  series: INDICES.map((i) => ({ dataset: i.ds, series: i.s, field: 'close', label: i.label })),
  range: { default: '1A' },
});

groupedBarChart($('ytd'), {
  title: 'Rentabilidad de los índices en lo que va de año',
  orientation: 'h',
  categories: [
    ...INDICES.map((i) => ({ label: i.label, bars: [{ dataset: i.ds, series: i.s, field: 'ret_ytd', name: '' }] })),
    { label: 'CAC 40', bars: [{ dataset: 'yahoo.cac_40', series: 'fr', field: 'ret_ytd', name: '' }] },
    { label: 'FTSE 100', bars: [{ dataset: 'yahoo.ftse_100', series: 'uk', field: 'ret_ytd', name: '' }] },
  ],
  colorBySign: true,
});

rebasedComparison($('bancos'), {
  title: 'Bolsa española y banca europea, ETF comparados',
  series: [
    { dataset: 'yahoo.msci_spain_etf', series: 'es', field: 'close' },
    { dataset: 'yahoo.european_banks_etf', series: 'eu', field: 'close' },
  ],
  range: { default: '1A' },
});

latestTable($('t-cotizaciones'), {
  title: 'Cotizaciones de los índices bursátiles',
  rowHeader: 'Índice',
  rows: [
    ...INDICES.map((i) => ({ label: i.label, dataset: i.ds, series: i.s })),
    { label: 'STOXX Europe 600', dataset: 'yahoo.stoxx_600', series: 'eu' },
    { label: 'CAC 40', dataset: 'yahoo.cac_40', series: 'fr' },
    { label: 'FTSE 100', dataset: 'yahoo.ftse_100', series: 'uk' },
  ],
  columns: retCols,
});

lineChart($('vix'), {
  title: 'Volatilidad implícita del S&P 500 (VIX)',
  series: [{ dataset: 'yahoo.vix', series: 'us', field: 'close' }],
  range: { default: '1A' },
});

// Tipos de interés de mercado
const chgCols = [
  { field: 'chg_1m', label: '1 mes', signColor: true },
  { field: 'chg_ytd', label: 'En el año', signColor: true },
  { field: 'chg_1y', label: '1 año', signColor: true },
];
latestTable($('t-tipos-eur'), {
  title: 'Tipos de interés en el euro y deuda española',
  rowHeader: 'Instrumento',
  rows: [
    { label: '€STR', dataset: 'bde.ester_daily', series: 'ea' },
    { label: 'Euríbor 3 meses', dataset: 'bde.euribor_3m_daily', series: 'ea' },
    { label: 'Euríbor 12 meses', dataset: 'bde.euribor_12m_daily', series: 'ea' },
    { label: 'Bono español a 5 años', dataset: 'bde.spain_5y_bond', series: 'es' },
    { label: 'Bono español a 10 años', dataset: 'bde.spain_10y_bond', series: 'es' },
  ],
  columns: [{ field: 'value', label: 'Último' }, ...chgCols],
});
latestTable($('t-tipos-us'), {
  title: 'Deuda del Tesoro de EE. UU.',
  rowHeader: 'Instrumento',
  rows: [
    { label: 'Tesoro a 3 meses', dataset: 'fed.us_tbill_3m', series: 'us' },
    { label: 'Bono a 5 años', dataset: 'fed.us_treasury_5y', series: 'us' },
    { label: 'Bono a 10 años', dataset: 'fed.us_treasury_10y', series: 'us' },
    { label: 'Bono a 30 años', dataset: 'fed.us_treasury_30y', series: 'us' },
  ],
  columns: [{ field: 'close', label: 'Último' }, ...chgCols],
});
lineChart($('tesoro-us'), {
  title: 'Rentabilidad de la deuda del Tesoro de EE. UU.',
  series: [
    { dataset: 'fed.us_tbill_3m', series: 'us', field: 'close', label: 'Tesoro a 3 meses' },
    { dataset: 'fed.us_treasury_5y', series: 'us', field: 'close', label: 'Bono a 5 años' },
    { dataset: 'fed.us_treasury_10y', series: 'us', field: 'close', label: 'Bono a 10 años' },
    { dataset: 'fed.us_treasury_30y', series: 'us', field: 'close', label: 'Bono a 30 años' },
  ],
  selectable: true,
  range: { default: '5A' },
});

// Divisas
lineChart($('eurusd'), {
  title: 'Tipo de cambio euro / dólar',
  series: [{ dataset: 'ecb.eur_usd', series: 'global', field: 'close' }],
  range: { default: '5A' },
});
lineChart($('dxy'), {
  title: 'Índice del dólar frente a una cesta de divisas',
  series: [{ dataset: 'fed.usd_broad_index', series: 'global', field: 'close' }],
  range: { default: '5A' },
});
latestTable($('t-divisas'), {
  title: 'Tipos de cambio',
  rowHeader: 'Par',
  rows: [
    ['ecb.eur_usd', 'Euro / dólar'], ['ecb.eur_gbp', 'Euro / libra'], ['ecb.eur_jpy', 'Euro / yen'],
    ['ecb.eur_chf', 'Euro / franco suizo'], ['ecb.gbp_usd', 'Libra / dólar'], ['ecb.usd_jpy', 'Dólar / yen'],
    ['fed.usd_broad_index', 'Índice amplio del dólar (Fed)'],
  ].map(([dataset, label]) => ({ label, dataset, series: 'global' })),
  columns: retCols,
});

// Materias primas
lineChart($('petroleo'), {
  title: 'Precio del petróleo, Brent y WTI',
  series: [
    { dataset: 'eia.brent_crude', series: 'global', field: 'close', label: 'Brent' },
    { dataset: 'eia.wti_crude', series: 'global', field: 'close', label: 'WTI' },
  ],
  range: { default: '5A' },
});
lineChart($('oro'), {
  title: 'Precio del oro',
  series: [{ dataset: 'yahoo.gold', series: 'global', field: 'close' }],
  range: { default: '5A' },
});
lineChart($('gas'), {
  title: 'Precio del gas natural (Henry Hub)',
  series: [{ dataset: 'eia.natural_gas', series: 'global', field: 'close' }],
  range: { default: '5A' },
});
latestTable($('t-materias'), {
  title: 'Cotizaciones de materias primas',
  rowHeader: 'Materia prima',
  rows: [
    ['eia.brent_crude', 'Petróleo Brent'], ['eia.wti_crude', 'Petróleo WTI'], ['eia.natural_gas', 'Gas natural (Henry Hub)'],
    ['yahoo.gold', 'Oro'], ['yahoo.silver', 'Plata'],
  ].map(([dataset, label]) => ({ label, dataset, series: 'global' })),
  columns: retCols,
});
