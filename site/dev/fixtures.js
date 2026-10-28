// Acceptance harness: every factory function against the five sample datasets.
// The only synthetic input is "dev.allnull", derived at run time from the real ine.cpi file
// (all values of one field set to null) to exercise the all-null path.
import { mountLayout } from '../assets/js/layout.js';
import { DATA_ROOT } from '../assets/js/config.js';
import { loadManifest } from '../assets/js/data.js';
import {
  kpiGrid, kpiTile, lineChart, barChart, stackedBarChart, groupedBarChart,
  crossSectionChart, rebasedComparison, latestTable, donutChart, periodTable,
} from '../assets/js/charts.js';

const realFetch = window.fetch.bind(window);
window.fetch = async (url, opts) => {
  if (String(url).endsWith('/dev/allnull.json')) {
    const res = await realFetch(DATA_ROOT + 'ine/cpi.json', opts);
    const ds = await res.json();
    ds.id = 'dev.allnull';
    ds.title_es = 'Campo sin datos (prueba)';
    for (const s of ds.series) for (const row of s.data) row[2] = null;
    return new Response(JSON.stringify(ds), { status: 200, headers: { 'Content-Type': 'application/json' } });
  }
  if (String(url).endsWith('/manifest.json')) {
    const m = await (await realFetch(url, opts)).json();
    m.datasets.push({ id: 'dev.allnull', path: 'dev/allnull.json', title_es: 'Campo sin datos (prueba)', source: 'INE', frequency: 'M', fields: ['value', 'yoy'], series: [] });
    return new Response(JSON.stringify(m), { status: 200, headers: { 'Content-Type': 'application/json' } });
  }
  return realFetch(url, opts);
};

mountLayout({ active: null });
const $ = (id) => document.getElementById(id);

// 1. KPI tiles built from the manifest: first series and first field of every dataset.
loadManifest().then((m) => {
  const specs = m.datasets.filter((d) => !d.id.startsWith('dev.')).map((d) => ({
    dataset: d.id, series: d.series[0].key, field: d.fields[0],
    change: d.fields[1] ? { field: d.fields[1], label: '' } : undefined,
  }));
  return kpiGrid($('kpis'), specs);
}).catch((e) => { $('kpis').textContent = 'No se pudo cargar el manifest: ' + e.message; });

// 2. ine.cpi
lineChart($('cpi-line'), {
  title: 'Inflación general, tasa interanual',
  series: [{ dataset: 'ine.cpi', series: 'es', field: 'yoy' }],
  ref: { y: 2, label: '2 %' }, range: { default: 'max' },
});
lineChart($('cpi-toggle'), {
  title: 'IPC: índice o variación anual',
  toggle: [
    { id: 'value', label: 'Índice', series: [{ dataset: 'ine.cpi', series: 'es', field: 'value' }] },
    { id: 'yoy', label: 'Variación anual', series: [{ dataset: 'ine.cpi', series: 'es', field: 'yoy' }] },
  ],
  range: { default: '5A' },
});
barChart($('cpi-bars'), {
  title: 'Variación anual del IPC por mes',
  series: [{ dataset: 'ine.cpi', series: 'es', field: 'yoy' }],
  colorBySign: 'neutral', range: { default: '5A' },
});

barChart($('cpi-overlay'), {
  title: 'Barras con línea superpuesta (prueba de formato)',
  series: [{ dataset: 'ine.ipi_sectors', series: 'total', field: 'yoy' }],
  overlay: { dataset: 'ine.ipi_sectors', series: 'total', field: 'ytd', label: 'Media en lo que va de año' },
  colorBySign: true, range: { default: '5A' },
});
periodTable($('cpi-period'), {
  title: 'Últimos datos del IPC',
  columns: [{ dataset: 'ine.cpi', series: 'es', field: 'value', label: 'Índice' }, { dataset: 'ine.cpi', series: 'es', field: 'yoy', label: 'Variación anual', signColor: true }],
  last: 8,
});

// 3. ine.ipi_sectors
lineChart($('ipi-lines'), {
  title: 'Producción industrial por destino económico, variación anual',
  series: ['total', 'consumo', 'equipo', 'intermedios', 'energia'].map((s) => ({ dataset: 'ine.ipi_sectors', series: s, field: 'yoy' })),
  range: { default: '5A' }, endLabels: false, selectable: true,
});
groupedBarChart($('ipi-bars'), {
  title: 'Producción industrial por sector, último dato',
  dataset: 'ine.ipi_sectors', series: ['consumo', 'equipo', 'intermedios', 'energia', 'total'],
  toggle: [{ id: 'ytd', label: 'En lo que va de año', field: 'ytd' }, { id: 'yoy', label: 'Interanual', field: 'yoy' }],
  orientation: 'h', sort: 'desc', colorBySign: true,
});
stackedBarChart($('ipi-stack'), {
  title: 'Apilado por componentes (prueba de formato)',
  components: ['consumo', 'equipo', 'intermedios', 'energia'].map((s) => ({ dataset: 'ine.ipi_sectors', series: s, field: 'yoy' })),
  total: { dataset: 'ine.ipi_sectors', series: 'total', field: 'yoy' },
  range: { years: 2 },
});
latestTable($('ipi-table'), {
  title: 'Último dato por sector',
  dataset: 'ine.ipi_sectors', rowHeader: 'Sector',
  columns: [{ field: 'yoy', signColor: true }, { field: 'ytd', signColor: true }],
  sort: { column: 0, dir: 'desc' },
});

// 4. eurostat.hicp
lineChart($('hicp-line'), {
  title: 'Inflación armonizada: España frente a la UE-27',
  series: [{ dataset: 'eurostat.hicp', series: 'es', field: 'yoy' }, { dataset: 'eurostat.hicp', series: 'eu27', field: 'yoy' }],
  range: { default: 'max' },
});
groupedBarChart($('hicp-grouped'), {
  title: 'Inflación armonizada, último dato',
  categories: [{ label: 'IPCA', bars: [
    { dataset: 'eurostat.hicp', series: 'es', field: 'yoy', name: 'España' },
    { dataset: 'eurostat.hicp', series: 'eu27', field: 'yoy', name: 'UE-27' },
  ] }],
});

// 5. bde.yield_curve
crossSectionChart($('yc'), {
  title: 'Curva de rendimientos de la deuda pública española',
  series: [{ dataset: 'bde.yield_curve', series: 'es', field: 'yield' }],
  xTitle: 'Plazo (años)',
});
latestTable($('yc-table'), {
  title: 'Curva de tipos: serie',
  dataset: 'bde.yield_curve', columns: [{ field: 'yield' }],
});

// 6. yahoo.ibex_35 and rebased comparison
lineChart($('ibex'), {
  title: 'Cierre diario del IBEX 35',
  series: [{ dataset: 'yahoo.ibex_35', series: 'es', field: 'close' }],
  range: { default: '5A' },
});
rebasedComparison($('rebased'), {
  title: 'IBEX 35 frente al IPC, base 100 (prueba de formato)',
  series: [
    { dataset: 'yahoo.ibex_35', series: 'es', field: 'close' },
    { dataset: 'ine.cpi', series: 'es', field: 'value', label: 'IPC' },
  ],
  range: { default: '1A' },
});

// 7. Edge cases
lineChart($('err-missing'), { title: 'Dataset inexistente', series: [{ dataset: 'ine.no_existe', series: 'es', field: 'value' }] });
lineChart($('err-field'), { title: 'Campo inexistente', series: [{ dataset: 'ine.cpi', series: 'es', field: 'nope' }] });
lineChart($('err-allnull'), { title: 'Campo con todos los valores nulos', series: [{ dataset: 'dev.allnull', series: 'es', field: 'yoy' }] });
kpiTile($('err-kpi'), { dataset: 'ine.no_existe', series: 'es', field: 'value', title: 'KPI con dataset inexistente' });
donutChart($('donut'), {
  title: 'Anillo (prueba de formato con dos series)',
  dataset: 'eurostat.hicp', field: 'yoy',
});

// Display-only rebasing to a fixed reference period (contract v1.1).
lineChart($('rebase-year'), {
  title: 'PIB, índice rebasado a la media de 2019 (prueba de rebase por año)',
  series: [{ dataset: 'ine.gdp', series: 'es', field: 'value' }],
  rebase: { year: 2019 }, ref: { y: 100, label: 'Media 2019' },
});
lineChart($('rebase-date'), {
  title: 'IPRI general, base enero 2022 = 100 (prueba de rebase por fecha)',
  series: [{ dataset: 'ine.ipri', series: 'total', field: 'value' }],
  rebase: { date: '2022-01-01' },
});
