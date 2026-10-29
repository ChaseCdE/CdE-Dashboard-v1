// Página Precios. Todo (cifras, unidades, fechas, fuentes) viene del JSON.
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart, stackedBarChart, groupedBarChart, latestTable } from '../charts.js';

mountLayout({ active: 'precios' });
const $ = (id) => document.getElementById(id);

kpiGrid($('kpis'), [
  { dataset: 'ine.cpi_special_groups', series: 'headline', field: 'yoy', title: 'Inflación general (IPC)', positiveIsGood: false },
  { dataset: 'ine.cpi_special_groups', series: 'core', field: 'yoy', title: 'Inflación subyacente', positiveIsGood: false },
  { dataset: 'ine.ipri', series: 'total', field: 'yoy', title: 'Precios industriales', change: { field: 'mom', label: 'mensual' }, positiveIsGood: false },
  { dataset: 'ine.ipri', series: 'total_sin_energia', field: 'yoy', title: 'Precios industriales sin energía', change: { field: 'mom', label: 'mensual' }, positiveIsGood: false },
  { dataset: 'ine.house_prices', series: 'es', field: 'yoy', title: 'Precio de la vivienda', positiveIsGood: false },
  { dataset: 'eurostat.hicp_energy', series: 'es', field: 'yoy', title: 'Inflación de la energía (IPCA España)', positiveIsGood: false },
  { dataset: 'eurostat.hicp', series: 'es', field: 'yoy', title: 'IPCA España', positiveIsGood: false },
  { dataset: 'eurostat.hicp', series: 'eu27', field: 'yoy', title: 'IPCA UE-27', positiveIsGood: false },
]);

// Inflación general y subyacente
lineChart($('cpi-core'), {
  title: 'Inflación general y subyacente, España',
  series: [
    { dataset: 'ine.cpi_special_groups', series: 'headline', field: 'yoy' },
    { dataset: 'ine.cpi_special_groups', series: 'core', field: 'yoy' },
  ],
  ref: { y: 2, label: 'Objetivo BCE' },
  range: { default: '5A' },
});
barChart($('cpi-bars'), {
  title: 'Variación anual del IPC general, por mes',
  series: [{ dataset: 'ine.cpi', series: 'es', field: 'yoy' }],
  colorBySign: 'neutral',
  range: { default: '5A' },
});

// Composición
stackedBarChart($('contrib'), {
  title: 'Aportaciones a la inflación por grupo de gasto',
  subtitle: 'Puntos porcentuales; la línea es el IPC general. Las aportaciones usan las ponderaciones vigentes para toda la serie, por lo que en años anteriores no suman exactamente la inflación general.',
  components: ['servicios', 'alimentos_bebidas_y_tabaco', 'bienes_industriales_sin_productos_energeticos', 'productos_energeticos']
    .map((s) => ({ dataset: 'ine.cpi_ecoicop_groups', series: s, field: 'contribution' })),
  total: { dataset: 'ine.cpi', series: 'es', field: 'yoy', label: 'IPC general' },
  range: { years: 3 },
});
lineChart($('groups-yoy'), {
  title: 'Inflación por grupo de gasto',
  series: ['servicios', 'alimentos_bebidas_y_tabaco', 'bienes_industriales_sin_productos_energeticos', 'productos_energeticos']
    .map((s) => ({ dataset: 'ine.cpi_ecoicop_groups', series: s, field: 'yoy' })),
  range: { default: '5A' },
  endLabels: false,
});
groupedBarChart($('weights'), {
  title: 'Peso de cada grupo en la cesta del IPC',
  dataset: 'ine.cpi_weights', field: 'weight',
  orientation: 'h', sort: 'desc',
});

// Energía
lineChart($('energy-hicp'), {
  title: 'Inflación de la energía: España frente a la UE-27',
  series: [
    { dataset: 'eurostat.hicp_energy', series: 'es', field: 'yoy' },
    { dataset: 'eurostat.hicp_energy', series: 'eu27', field: 'yoy' },
  ],
  range: { default: '5A' },
});

// CCAA
groupedBarChart($('ccaa-bars'), {
  title: 'Inflación por comunidad autónoma',
  dataset: 'ine.cpi_ccaa', field: 'yoy',
  orientation: 'h', sort: 'desc',
});
latestTable($('ccaa-table'), {
  title: 'Último dato por comunidad autónoma',
  dataset: 'ine.cpi_ccaa', rowHeader: 'Comunidad',
  columns: [{ field: 'yoy', signColor: true }, { field: 'mom', signColor: true }],
  sort: { column: 0, dir: 'desc' },
});

// IPRI
lineChart($('ipri-general'), {
  title: 'Precios industriales: total y sin energía',
  toggle: ['value', 'yoy', 'mom'].map((f) => ({
    id: f, label: { value: 'Índice', yoy: 'Anual', mom: 'Mensual' }[f],
    ...(f === 'value' ? { rebase: { year: 2022 } } : {}),
    series: ['total', 'total_sin_energia'].map((s) => ({ dataset: 'ine.ipri', series: s, field: f })),
  })),
  range: { default: '5A' },
});
lineChart($('ipri-destino'), {
  title: 'Precios industriales por destino económico',
  toggle: ['value', 'yoy', 'mom'].map((f) => ({
    id: f, label: { value: 'Índice', yoy: 'Anual', mom: 'Mensual' }[f],
    ...(f === 'value' ? { rebase: { year: 2022 } } : {}),
    series: ['consumo', 'equipo', 'intermedios', 'energia'].map((s) => ({ dataset: 'ine.ipri', series: s, field: f })),
  })),
  range: { default: '5A' },
  endLabels: false,
});

// Vivienda
lineChart($('house'), {
  title: 'Precio de la vivienda, España',
  toggle: [
    { id: 'value', label: 'Índice', series: [{ dataset: 'ine.house_prices', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Variación anual', series: [{ dataset: 'ine.house_prices', series: 'es', field: 'yoy' }] },
  ],
  range: { default: 'max' },
});

lineChart($('house-rent'), {
  title: 'Compra y alquiler de vivienda: variación anual',
  series: [
    { dataset: 'ine.house_prices', series: 'es', field: 'yoy', label: 'Precio de la vivienda' },
    { dataset: 'ine.cpi_rent', series: 'es', field: 'yoy', label: 'Alquiler' },
  ],
  range: { default: 'max' },
});

// Precio de la vivienda: INE, MIVAU (valor tasado) y Registradores
lineChart($('house-sources'), {
  title: 'Precio de la vivienda según tres fuentes: variación anual',
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

// Precios de exportación e importación
lineChart($('trade-prices'), {
  title: 'Precios industriales de exportación e importación',
  toggle: ['yoy', 'value'].map((f) => ({
    id: f, label: { yoy: 'Anual', value: 'Índice' }[f],
    series: ['exportacion', 'importacion'].map((s) => ({ dataset: 'ine.trade_prices', series: s, field: f })),
  })),
  range: { default: '5A' },
});

// UE
lineChart($('hicp'), {
  title: 'Inflación armonizada: España frente a la UE-27',
  series: [
    { dataset: 'eurostat.hicp', series: 'es', field: 'yoy' },
    { dataset: 'eurostat.hicp', series: 'eu27', field: 'yoy' },
  ],
  range: { default: '5A' },
});
lineChart($('core-eu'), {
  title: 'Inflación subyacente armonizada: España frente a la UE-27',
  series: [
    { dataset: 'eurostat.core_inflation', series: 'es', field: 'yoy' },
    { dataset: 'eurostat.core_inflation', series: 'eu27', field: 'yoy' },
  ],
  range: { default: '5A' },
});
