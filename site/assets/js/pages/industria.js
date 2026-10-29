// Sectores · Industria: producción industrial (total, destino económico, divisiones),
// cifra de negocios, valor añadido y utilización de la capacidad.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, groupedBarChart } from '../charts.js';

mountLayout({ active: 'industria' });
const $ = (id) => document.getElementById(id);
const pair = (ds, f) => ['es', 'eu27'].map((s) => ({ dataset: ds, series: s, field: f }));
const rates = [{ id: 'yoy', label: 'Var. interanual', field: 'yoy' }, { id: 'ytd', label: 'Acumulado del año', field: 'ytd' }];

kpiGrid($('kpis'), [
  { dataset: 'ine.industrial_production', series: 'es', field: 'yoy', title: 'Producción industrial, variación interanual', change: { field: 'mom', label: 'mensual' } },
  { dataset: 'ine.ipi_sectors', series: 'total', field: 'ytd', title: 'Producción industrial, media en lo que va de año' },
  { dataset: 'ine.industry_turnover', series: 'es', field: 'yoy', title: 'Cifra de negocios de la industria, variación interanual' },
  { dataset: 'eurostat.capacity_utilization', series: 'es', field: 'value', title: 'Utilización de la capacidad productiva, España' },
]);

/* Producción industrial */
const ipi = (f) => [{ dataset: 'ine.industrial_production', series: 'es', field: f }];
lineChart($('ipi'), {
  title: 'Índice de Producción Industrial',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: ipi('yoy') },
    { id: 'mom', label: 'Var. mensual', series: ipi('mom') },
    { id: 'value', label: 'Índice (2021 = 100)', rebase: { year: 2021 }, series: ipi('value') },
  ],
  range: { default: '5A' },
});
lineChart($('ipi-eu'), {
  title: 'Producción industrial: España frente a la UE-27',
  series: pair('eurostat.industrial_production', 'yoy'),
  ref: { y: 0 },
  range: { default: '5A' },
});

/* Destino económico y divisiones */
groupedBarChart($('ipi-dest'), {
  title: 'Producción industrial por destino económico de los bienes',
  dataset: 'ine.ipi_sectors', orientation: 'h', sort: 'desc', colorBySign: true,
  toggle: rates,
});
groupedBarChart($('ipi-div'), {
  title: 'Producción industrial por divisiones de actividad (CNAE)',
  dataset: 'ine.ipi_divisions', orientation: 'h', sort: 'desc', colorBySign: true,
  toggle: rates,
});

/* Cifra de negocios, valor añadido y capacidad */
lineChart($('turnover'), {
  title: 'Cifra de negocios de la industria',
  series: [{ dataset: 'ine.industry_turnover', series: 'es', field: 'yoy' }],
  ref: { y: 0 },
  range: { default: '5A' },
});
const gva = (f) => [
  { dataset: 'ine.gva_sectors', series: 'industria', field: f, label: 'Industria' },
  { dataset: 'ine.gva_sectors', series: 'pib', field: f, label: 'PIB', dash: 'dot' },
];
lineChart($('gva'), {
  title: 'Valor añadido de la industria',
  toggle: [
    { id: 'yoy', label: 'Var. interanual', series: gva('yoy') },
    { id: 'qoq', label: 'Var. trimestral', series: gva('qoq') },
  ],
  range: { default: '5A' },
});
lineChart($('capacity'), {
  title: 'Utilización de la capacidad productiva: España frente a la UE-27',
  series: pair('eurostat.capacity_utilization', 'value'),
  range: { default: '5A' },
});
