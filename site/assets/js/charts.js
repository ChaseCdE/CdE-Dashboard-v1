// Chart factory. Every page must build its charts through this module: pages pass a
// declarative spec (dataset ids, series keys, field keys) and never raw Plotly config.
// Titles, units, source and last-observation text come from the dataset JSON.
//
// All public functions take a container element, replace its content, and return a
// Promise that never rejects: failures are rendered as a visible error card.
import {
  CHART, COLORS, SERIES_COLORS, CYCLE, FONT, PLOTLY, STALE_DAYS,
} from './config.js';
import {
  loadDataset, loadManifest, manifestEntry, getSeries, fieldDef, columns, allNull,
  lastPoint, firstPoint, sliceFrom, shiftYears, latest as manifestLatest, DataError,
} from './data.js';
import {
  fmtValue, fmtNumber, fmtNumberTrim, fmtPeriod, plotlyNumberFormat, unitShort, signClass, arrow,
  hoverDateFormat, MONTHS, fmtDateLong,
} from './format.js';

/* ------------------------------------------------------------------ DOM helpers */

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'text') el.textContent = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return el;
}

/* ------------------------------------------------------------------ Plotly loader */

let plotlyPromise = null;

function loadScript(src, integrity) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.async = true;
    if (integrity) { s.integrity = integrity; s.crossOrigin = 'anonymous'; }
    s.onload = resolve;
    s.onerror = () => reject(new Error(`No se pudo cargar ${src}`));
    document.head.append(s);
  });
}

/** Loads Plotly (pinned, from cdnjs) and registers the Spanish locale once. */
export function ensurePlotly() {
  if (!plotlyPromise) {
    plotlyPromise = (async () => {
      if (!window.Plotly) await loadScript(PLOTLY.js, PLOTLY.jsIntegrity);
      try { await loadScript(PLOTLY.localeEs, PLOTLY.localeEsIntegrity); } catch (e) { /* locale is cosmetic */ }
      const base = (window.Plotly.locales && window.Plotly.locales.es) || {};
      const baseFormat = base.format || {};
      window.Plotly.register({
        moduleType: 'locale',
        name: PLOTLY.localeName,
        dictionary: base.dictionary || {},
        format: {
          ...baseFormat,
          months: MONTHS.long,
          shortMonths: MONTHS.short,
          decimal: ',',
          thousands: '.',
          date: '%d/%m/%Y',
        },
      });
      return window.Plotly;
    })();
    plotlyPromise.catch(() => { plotlyPromise = null; });
  }
  return plotlyPromise;
}

/* ------------------------------------------------------------------ cards */

/**
 * Card wrapper: title, subtitle, controls area, body, notes and footer.
 * Returns {card, body, controls, notes, foot, setSubtitle}. Exposed for page code that needs
 * a custom body (e.g. a table next to charts).
 */
export function chartCard(el, { title, subtitle, className } = {}) {
  el.replaceChildren();
  const titleEl = h('h3', { class: 'card-title', text: title || '' });
  const subEl = h('p', { class: 'card-sub', text: subtitle || '' });
  if (!subtitle) subEl.hidden = true;
  const controls = h('div', { class: 'card-controls' });
  const body = h('div', { class: 'chart-body' });
  const notes = h('div', { class: 'chart-notes' });
  const foot = h('footer', { class: 'card-foot' });
  const card = h('section', { class: 'card chart-card' + (className ? ' ' + className : '') },
    h('header', { class: 'card-head' }, h('div', { class: 'card-titles' }, titleEl, subEl), controls),
    body, notes, foot);
  el.append(card);
  return {
    card, body, controls, notes, foot,
    setSubtitle(t) { subEl.textContent = t || ''; subEl.hidden = !t; },
    setTitle(t) { titleEl.textContent = t || ''; },
  };
}

/** Visible error card in place of a chart. */
export function errorCard(el, { title, message, details } = {}) {
  el.replaceChildren();
  const det = (details || []).filter(Boolean);
  el.append(h('section', { class: 'card error-card', role: 'alert' },
    h('h3', { class: 'card-title', text: title || 'Indicador no disponible' }),
    h('p', { class: 'error-msg', text: message || 'No se han podido cargar los datos.' }),
    det.length ? h('details', { class: 'error-detail' },
      h('summary', { text: 'Detalle técnico' }),
      h('ul', {}, det.map((d) => h('li', { text: d })))) : null));
}

function emptyCard(el, title, message) {
  el.replaceChildren();
  el.append(h('section', { class: 'card empty-card' },
    h('h3', { class: 'card-title', text: title || '' }),
    h('p', { class: 'empty-msg', text: message || 'Sin datos disponibles para este indicador.' })));
}

/* ------------------------------------------------------------------ staleness and footers */

function daysBetween(isoA, isoB) {
  const a = Date.parse(String(isoA).slice(0, 10) + 'T00:00:00Z');
  const b = Date.parse(String(isoB).slice(0, 10) + 'T00:00:00Z');
  return Math.round((b - a) / 86400000);
}

/** {stale, days, limit, last} for a dataset, using the thresholds of the contract validator. */
/** First day after the period starting on iso ('2026-04-01', 'Q' -> '2026-07-01'). */
function periodEnd(iso, freq) {
  const [y, m, d] = iso.split('-').map(Number);
  const months = { M: 1, Q: 3, A: 12 }[freq];
  if (months) {
    const t = new Date(Date.UTC(y, m - 1 + months, 1));
    return t.toISOString().slice(0, 10);
  }
  const t = new Date(Date.UTC(y, m - 1, d + (freq === 'W' ? 7 : 1)));
  return t.toISOString().slice(0, 10);
}

export function staleInfo(ds) {
  let last = ds.last_observation;
  let freq = ds.frequency;
  if (!last) {
    const asOf = (ds.series || []).map((s) => s.as_of).filter(Boolean).sort();
    last = asOf.length ? asOf[asOf.length - 1] : null;
    freq = 'D';
  }
  const limit = STALE_DAYS[freq];
  if (!last || !limit || !ds.generated_at) return { stale: false, days: null, limit, last };
  // Contract v1.1: age is measured from the END of the last period.
  const days = daysBetween(periodEnd(last, freq), ds.generated_at);
  return { stale: days > limit, days, limit, last };
}

function sourceLinks(datasets) {
  const seen = new Map();
  for (const ds of datasets) {
    const k = ds.source && ds.source.name;
    if (k && !seen.has(k)) seen.set(k, ds.source.url);
  }
  const out = [];
  let i = 0;
  for (const [name, url] of seen) {
    if (i++) out.push(', ');
    out.push(url
      ? h('a', { href: url, target: '_blank', rel: 'noopener noreferrer', text: name })
      : name);
  }
  return out;
}

/**
 * Footer: "Fuente: <name> (<link>) · Último dato: <period>" plus stale badge.
 * `observed` is a list of {label, iso, freq} (one per plotted series); identical periods are merged.
 */
function fillFooter(foot, datasets, observed, opts = {}) {
  foot.replaceChildren();
  const src = sourceLinks(datasets);
  foot.append(h('span', { class: 'foot-source' }, 'Fuente: ', ...src));
  const obs = observed.filter((o) => o.iso);
  if (obs.length) {
    const periods = new Map();
    for (const o of obs) {
      const p = fmtPeriod(o.iso, o.freq);
      if (!periods.has(p)) periods.set(p, []);
      periods.get(p).push(o.label);
    }
    let text;
    if (opts.asOf) text = `Datos a ${[...periods.keys()].join('; ')}`;
    else if (periods.size === 1) text = `Último dato: ${[...periods.keys()][0]}`;
    else text = 'Último dato: ' + [...periods].map(([p, ls]) => `${[...new Set(ls)].join(', ')} ${p}`).join(' · ');
    foot.append(h('span', { class: 'foot-sep', 'aria-hidden': 'true', text: '·' }),
      h('span', { class: 'foot-last', text }));
  }
  if (opts.stale !== false) {
    const stale = datasets.map(staleInfo).filter((s) => s.stale);
    if (stale.length) {
      const worst = stale.sort((a, b) => b.days - a.days)[0];
      foot.append(h('span', {
        class: 'badge badge-stale',
        title: `Último dato hace ${worst.days} días respecto a la generación del archivo (umbral ${worst.limit} días).`,
        text: 'Desactualizado',
      }));
    }
  }
}

/* ------------------------------------------------------------------ data gathering */

/**
 * Resolve a list of {dataset, series, field, label?, color?, dash?} into traces.
 * Never throws: failures go to `problems`.
 */
async function gather(specs) {
  const ids = [...new Set(specs.map((s) => s.dataset))];
  const loaded = new Map();
  const problems = [];
  await Promise.all(ids.map(async (id) => {
    try { loaded.set(id, await loadDataset(id)); }
    catch (e) { problems.push({ id, kind: 'missing', message: e.message, detail: e.detail }); }
  }));
  const traces = [];
  for (const s of specs) {
    const ds = loaded.get(s.dataset);
    if (!ds) continue;
    try {
      const ser = getSeries(ds, s.series);
      if (!ser) throw new DataError(`La serie "${s.series}" no existe en "${s.dataset}".`, 'no_series');
      const field = fieldDef(ds, s.field);
      if (!field) throw new DataError(`El campo "${s.field}" no existe en "${s.dataset}".`, 'no_field');
      const col = columns(ds, s.series, s.field);
      if (allNull(col)) {
        problems.push({ id: s.dataset, kind: 'empty', message: `"${s.dataset}" · ${ser.label_es}: sin datos en "${field.label_es}".` });
        continue;
      }
      traces.push({
        spec: s, ds, field, ser, col,
        key: s.series,
        label: s.label || ser.label_es,
        freq: ds.frequency,
      });
    } catch (e) {
      problems.push({ id: s.dataset, kind: 'bad', message: e.message });
    }
  }
  return { traces, problems, loaded };
}

function assignColors(traces) {
  const used = new Set(traces.map((t) => t.spec.color).filter(Boolean));
  for (const t of traces) {
    if (t.spec.color) { t.color = t.spec.color; continue; }
    const sem = SERIES_COLORS[t.key];
    if (sem && !traces.some((o) => o !== t && o.color === sem)) { t.color = sem; used.add(sem); }
  }
  let i = 0;
  for (const t of traces) {
    if (t.color) continue;
    while (i < CYCLE.length && used.has(CYCLE[i])) i++;
    t.color = CYCLE[i % CYCLE.length];
    used.add(t.color);
    i++;
  }
}

/** If no trace could be built, render the right kind of card and return true. */
function bailIfEmpty(el, spec, g) {
  if (g.traces.length) return false;
  const missing = g.problems.filter((p) => p.kind !== 'empty');
  if (missing.length) {
    errorCard(el, {
      title: spec.title,
      message: 'No se han podido cargar los datos de este indicador.',
      details: g.problems.map((p) => `${p.message}${p.detail ? ' (' + p.detail + ')' : ''}`),
    });
  } else {
    emptyCard(el, spec.title, 'Sin datos disponibles para este indicador.');
  }
  return true;
}

function noteProblems(ui, problems) {
  if (!problems.length) return;
  ui.notes.append(h('p', { class: 'chart-note warn', role: 'status',
    text: 'Parte de los datos no está disponible: ' + problems.map((p) => p.message).join(' ') }));
}

function autoTitle(traces) {
  const titles = [...new Set(traces.map((t) => t.ds.title_es))];
  return titles.length === 1 ? titles[0] : '';
}

function autoSubtitle(traces) {
  const fields = [];
  for (const t of traces) {
    if (!fields.some((f) => f.key === t.field.key && f.unit === t.field.unit)) fields.push(t.field);
  }
  const notes = [...new Set(traces.map((t) => t.field.note_es).filter(Boolean))];
  let head;
  if (fields.length === 1) {
    const f = fields[0];
    const u = unitShort(f);
    head = u && !f.label_es.toLowerCase().includes(u) ? `${f.label_es} (${u})` : f.label_es;
  } else {
    head = [...new Set(fields.map(unitShort).filter(Boolean))].join(' / ');
  }
  return [head, ...notes].filter(Boolean).join(' · ');
}

function observedOf(traces) {
  return traces.map((t) => {
    if (t.freq === 'X') return { label: t.label, iso: t.ser.as_of || null, freq: 'D' };   // snapshot date
    const lp = lastPoint(t.col);
    return { label: t.label, iso: lp ? lp[0] : null, freq: t.freq };
  });
}

/* ------------------------------------------------------------------ ranges */

function normalizeRange(range, fallbackDefault) {
  if (range === false) return { options: [], current: null, buttons: false };
  const r = range || {};
  if (r.years) {
    return { options: [{ id: 'fixed', label: '', years: r.years }], current: 'fixed', buttons: false };
  }
  const options = r.options || CHART.ranges;
  let current = r.default || fallbackDefault || CHART.defaultRange;
  if (!options.some((o) => o.id === current)) current = options[options.length - 1].id;
  return { options, current, buttons: r.buttons !== false && options.length > 1 };
}

function windowStartIso(traces, range) {
  const opt = range.options.find((o) => o.id === range.current);
  if (!opt || !opt.years) return null;
  const lasts = traces.map((t) => (lastPoint(t.col) || [null])[0]).filter(Boolean).sort();
  if (!lasts.length) return null;
  return shiftYears(lasts[lasts.length - 1], opt.years);
}

function buildRangeButtons(ui, range, onChange) {
  if (!range.buttons) return;
  const group = h('div', { class: 'range-btns', role: 'group', 'aria-label': 'Periodo mostrado' });
  const btns = range.options.map((o) => {
    const b = h('button', { type: 'button', class: 'range-btn', 'aria-pressed': String(o.id === range.current), text: o.label });
    b.addEventListener('click', () => {
      range.current = o.id;
      btns.forEach((x, i) => x.setAttribute('aria-pressed', String(range.options[i].id === o.id)));
      onChange();
    });
    return b;
  });
  group.append(...btns);
  ui.controls.append(group);
}

/** Optional toggle between alternative field sets ("Variación anual / trimestral / Índice"). */
function buildToggle(ui, options, current, onChange) {
  const group = h('div', { class: 'range-btns toggle-btns', role: 'group', 'aria-label': 'Medida mostrada' });
  const btns = options.map((o) => {
    const b = h('button', { type: 'button', class: 'range-btn', 'aria-pressed': String(o.id === current.id), text: o.label });
    b.addEventListener('click', () => {
      current.id = o.id;
      btns.forEach((x, i) => x.setAttribute('aria-pressed', String(options[i].id === o.id)));
      onChange();
    });
    return b;
  });
  group.append(...btns);
  ui.controls.append(group);
}

/* ------------------------------------------------------------------ Plotly layout */

const PLOT_CONFIG = {
  responsive: true,
  displaylogo: false,
  displayModeBar: false,
  scrollZoom: false,
  locale: PLOTLY.localeName,
};

function xHover(freq) {
  return freq === 'Q' ? 'T%q %Y' : hoverDateFormat(freq);
}

function baseLayout({ height, legend, freq, numericX, yField, zero, rightMargin, extra } = {}) {
  const fmt = yField ? plotlyNumberFormat(yField) : { axisSuffix: '' };
  const layout = {
    height: height || CHART.height,
    autosize: true,
    separators: ',.',
    dragmode: false,
    font: { family: FONT.family, size: FONT.size, color: COLORS.inkSoft },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 8, r: rightMargin || 12, t: legend ? 34 : 10, b: 8, pad: 4 },
    hovermode: 'x unified',
    hoverlabel: {
      bgcolor: '#FFFFFF', bordercolor: COLORS.axis,
      font: { family: FONT.family, size: FONT.size, color: COLORS.ink },
    },
    showlegend: !!legend,
    legend: { orientation: 'h', x: 0, xanchor: 'left', y: 1.0, yanchor: 'bottom', font: { size: FONT.size, color: COLORS.ink }, itemclick: false, itemdoubleclick: false },
    xaxis: {
      showgrid: false, zeroline: false, showline: true, linecolor: COLORS.axis,
      ticks: 'outside', tickcolor: COLORS.axis, ticklen: 4, automargin: true, fixedrange: true,
      tickfont: { size: 12, color: COLORS.inkSoft },
    },
    yaxis: {
      showgrid: true, gridcolor: COLORS.grid, gridwidth: 1,
      zeroline: !!zero, zerolinecolor: COLORS.zero, zerolinewidth: 1.2,
      showline: false, ticks: '', automargin: true, fixedrange: true,
      separatethousands: true, exponentformat: 'none', ticksuffix: fmt.axisSuffix,
      tickfont: { size: 12, color: COLORS.inkSoft },
    },
  };
  if (!numericX) {
    layout.xaxis.type = 'date';
    layout.xaxis.hoverformat = xHover(freq);
    layout.xaxis.tickformatstops = [
      { dtickrange: [null, 86400000 * 2], value: '%-d %b' },
      { dtickrange: [86400000 * 2, 'M1'], value: '%-d %b %Y' },
      { dtickrange: ['M1', 'M12'], value: '%b %Y' },
      { dtickrange: ['M12', null], value: '%Y' },
    ];
  }
  return deepMerge(layout, extra || {});
}

function deepMerge(a, b) {
  for (const [k, v] of Object.entries(b)) {
    if (v && typeof v === 'object' && !Array.isArray(v) && a[k] && typeof a[k] === 'object' && !Array.isArray(a[k])) deepMerge(a[k], v);
    else a[k] = v;
  }
  return a;
}

// Hover text is pre-formatted with format.js (one es-ES formatter for the whole site);
// Plotly only has to print it.
function hoverTpl(field, name) {
  return `%{text}<extra>${name}</extra>`;
}
function texts(y, field) {
  return y.map((v) => (v === null || v === undefined ? '' : fmtValue(v, field)));
}

function refShapes(ref) {
  const list = (Array.isArray(ref) ? ref : (ref ? [ref] : [])).filter((r) => r && r.y !== undefined);
  return {
    shapes: list.map((r) => ({ type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: r.y, y1: r.y,
      line: { color: COLORS.zero, width: 1.2, dash: 'dot' } })),
    annotations: list.filter((r) => r.label).map((r) => ({ xref: 'paper', x: 1, xanchor: 'right', yref: 'y', y: r.y, yanchor: 'bottom',
      text: r.label, showarrow: false, font: { size: 11, color: COLORS.inkSoft },
      bgcolor: 'rgba(255,255,255,0.85)', borderpad: 2 })),
  };
}

function endLabelAnnotations(traces, plotted) {
  return plotted.map(({ t, x, y }) => {
    let i = y.length - 1;
    while (i >= 0 && (y[i] === null || y[i] === undefined)) i--;
    if (i < 0) return null;
    return {
      xref: 'x', yref: 'y', x: x[i], y: y[i], xanchor: 'left', yanchor: 'middle', xshift: 8,
      text: `<b>${fmtValue(y[i], t.field, { unit: t.field.unit === 'pct' || t.field.unit === 'pct_change' })}</b>`,
      showarrow: false, font: { size: 12, color: COLORS.ink },
    };
  }).filter(Boolean);
}

async function draw(ui, data, layout) {
  const Plotly = await ensurePlotly();
  ui.body.replaceChildren();
  const div = h('div', { class: 'plot' });
  ui.body.append(div);
  await Plotly.react(div, data, layout, PLOT_CONFIG);
  return div;
}

async function redraw(ui, data, layout) {
  const Plotly = await ensurePlotly();
  let div = ui.body.querySelector('.plot');
  if (!div) { div = h('div', { class: 'plot' }); ui.body.replaceChildren(div); }
  await Plotly.react(div, data, layout, PLOT_CONFIG);
}

function loadingBody(ui) {
  ui.body.replaceChildren(h('div', { class: 'chart-loading', role: 'status', text: 'Cargando datos…' }));
}

function ariaLabel(ui, title, subtitle, observed) {
  const last = observed.filter((o) => o.iso).map((o) => `${o.label}: ${fmtPeriod(o.iso, o.freq)}`).join('; ');
  ui.body.setAttribute('role', 'img');
  ui.body.setAttribute('aria-label', [title, subtitle, last && `Último dato ${last}`].filter(Boolean).join('. '));
}

/** Wrapper: never rejects; unexpected errors become an error card. */
async function guard(el, spec, fn) {
  try {
    if (!(el instanceof Element)) throw new Error('El contenedor del gráfico no existe.');
    return await fn();
  } catch (e) {
    console.warn('[charts]', e);
    if (el instanceof Element) {
      errorCard(el, { title: spec && spec.title, message: 'No se ha podido dibujar este gráfico.', details: [e.message] });
    }
    return { ok: false, error: e };
  }
}

function makeUi(el, spec, traces) {
  if (spec.card === false) {
    el.replaceChildren();
    const body = h('div', { class: 'chart-body' });
    const controls = h('div', { class: 'card-controls' });
    const notes = h('div', { class: 'chart-notes' });
    const foot = h('footer', { class: 'card-foot' });
    el.append(controls, body, notes, foot);
    return { card: el, body, controls, notes, foot, setSubtitle() {}, setTitle() {} };
  }
  return chartCard(el, {
    title: spec.title !== undefined ? spec.title : autoTitle(traces),
    subtitle: spec.subtitle !== undefined ? spec.subtitle : autoSubtitle(traces),
  });
}

function seriesNeedsZero(traces) {
  return traces.some((t) => t.field.unit === 'pct_change' || t.field.unit === 'pp');
}

function placeholder(el, spec) {
  el.replaceChildren(h('section', { class: 'card chart-card is-loading', 'aria-busy': 'true' },
    h('div', { class: 'chart-loading', role: 'status', text: 'Cargando datos…' })));
}

function asList(v) { return Array.isArray(v) ? v : (v ? [v] : []); }

/* ------------------------------------------------------------------ lineChart */

/**
 * Lines for one or more series (possibly from several datasets).
 * spec: {
 *   title?, subtitle?, series: [{dataset, series, field, label?, color?, dash?}],
 *   toggle?: [{id, label, series: [...]}],     // alternative field sets switched by buttons
 *   range?: false | {default: '1A'|'5A'|'max', buttons?: bool, years?: n},
 *   ref?: {y, label?}, endLabels?: bool, markers?: bool, height?: px, card?: false, stale?: false
 * }
 */
/**
 * Display-only rebasing (contract v1.1): divide a level series by its value at a reference
 * period and multiply by 100. rebase = {date: 'YYYY-MM-DD'} (single period) or
 * {year: 2019} (average of that calendar year's observations). Changes the base, not the
 * dynamics. Returns the original column if rebase is falsy or the base is unavailable.
 */
function rebaseColumn(col, field, rebase) {
  if (!rebase) return { y: col.y, field };
  let base = null;
  if (rebase.date) {
    const i = col.x.indexOf(rebase.date);
    base = i >= 0 ? col.y[i] : null;
  } else if (rebase.year) {
    const vals = col.y.filter((v, i) => v !== null && String(col.x[i]).startsWith(String(rebase.year)));
    base = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  }
  if (base === null || base === 0 || !Number.isFinite(base)) {
    console.warn('rebase: no base value for', rebase, '- showing the series unrebased');
    return { y: col.y, field };
  }
  return {
    y: col.y.map((v) => (v === null ? null : (v / base) * 100)),
    field: { ...field, unit: 'index', decimals: 1, note_es: undefined },
  };
}

function rebaseSubtitle(rebase, freq) {
  const label = rebase.year ? String(rebase.year) : fmtPeriod(rebase.date, freq);
  return `Índice, base ${label} = 100`;
}

export function lineChart(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    const toggle = spec.toggle ? { id: spec.toggle[0].id } : null;
    const specsFor = () => (toggle ? spec.toggle.find((o) => o.id === toggle.id).series : spec.series);
    const allSpecs = toggle ? spec.toggle.flatMap((o) => o.series) : spec.series;
    const gAll = await gather(allSpecs);
    const g0 = toggle ? await gather(specsFor()) : gAll;
    if (bailIfEmpty(el, spec, g0)) return { ok: false };
    const ui = makeUi(el, spec, g0.traces);
    noteProblems(ui, g0.problems);
    const range = normalizeRange(spec.range, spec.range && spec.range.default);

    let current = g0;
    const render = async () => {
      current = toggle ? await gather(specsFor()) : g0;
      const traces = current.traces;
      if (!traces.length) { ui.body.replaceChildren(h('p', { class: 'empty-msg', text: 'Sin datos para esta medida.' })); return; }
      assignColors(traces);
      const shown = spec.selectable ? traces.filter((t) => !off.has(t.label)) : traces;
      if (!shown.length) { await redraw(ui, [], baseLayout({ height: spec.height })); return; }
      const opt = toggle ? spec.toggle.find((o) => o.id === toggle.id) : null;
      const rb = (opt && opt.rebase !== undefined) ? opt.rebase : spec.rebase;
      const start = windowStartIso(shown, range);
      const plotted = shown.map((t) => {
        const { y: yAll, field } = rebaseColumn(t.col, t.field, rb);
        const s = sliceFrom(t.col.x, yAll, start);
        return { t: field === t.field ? t : { ...t, field }, x: s.x, y: s.y };
      });
      const data = plotted.map(({ t, x, y }) => ({
        type: 'scatter', mode: spec.markers ? 'lines+markers' : 'lines', x, y, name: t.label,
        line: { color: t.color, width: CHART.lineWidth, dash: t.spec.dash || 'solid', shape: 'linear' },
        marker: { size: 5, color: t.color },
        connectgaps: false,
        text: texts(y, t.field),
        hovertemplate: hoverTpl(t.field, t.label),
      }));
      const endLabels = spec.endLabels !== undefined ? spec.endLabels : shown.length <= 3;
      const ref = refShapes((opt && opt.ref !== undefined) ? opt.ref : spec.ref);
      const layout = baseLayout({
        height: spec.height, legend: shown.length > 1, freq: shown[0].freq,
        yField: plotted[0].t.field, zero: spec.zero !== undefined ? spec.zero : seriesNeedsZero(shown),
        rightMargin: endLabels ? 58 : 14,
        extra: {
          shapes: ref.shapes,
          annotations: [...ref.annotations, ...(endLabels ? endLabelAnnotations(shown, plotted) : [])],
          yaxis: spec.yRange ? { range: spec.yRange, autorange: false } : {},
        },
      });
      await redraw(ui, data, layout);
      if (rb) ui.setSubtitle(spec.subtitle !== undefined && !toggle ? spec.subtitle : rebaseSubtitle(rb, shown[0].freq));
      else if (toggle) { ui.setSubtitle(spec.subtitle !== undefined ? spec.subtitle : autoSubtitle(traces)); }
      fillFooter(ui.foot, [...current.loaded.values()].filter((d) => shown.some((t) => t.ds === d)), observedOf(shown), { stale: spec.stale });
      ariaLabel(ui, spec.title || autoTitle(traces), spec.subtitle || autoSubtitle(traces), observedOf(shown));
    };
    const off = new Set();
    if (spec.selectable) {
      const group = h('div', { class: 'series-select', role: 'group', 'aria-label': 'Series mostradas' });
      g0.traces.forEach((t, i) => {
        if (t.spec.off) off.add(t.label);
        const id = `sel-${Math.random().toString(36).slice(2, 8)}-${i}`;
        const cb = h('input', { type: 'checkbox', id, checked: !t.spec.off });
        cb.addEventListener('change', () => { if (cb.checked) off.delete(t.label); else off.add(t.label); render(); });
        group.append(h('label', { class: 'series-opt', for: id }, cb, ' ', t.label));
      });
      ui.controls.append(group);
    }
    if (toggle) buildToggle(ui, spec.toggle, toggle, render);
    buildRangeButtons(ui, range, render);
    loadingBody(ui);
    await render();
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ barChart */

/**
 * Time-series bars. One series (optionally coloured by sign) or several (grouped).
 * spec: {title?, subtitle?, series: [...], colorBySign?: true|'neutral', ref?, range?, height?}
 */
export function barChart(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    const gAll = await gather(spec.overlay ? [...spec.series, { ...spec.overlay, _overlay: true }] : spec.series);
    const overlay = gAll.traces.find((t) => t.spec._overlay);
    const g = { ...gAll, traces: gAll.traces.filter((t) => !t.spec._overlay) };
    if (bailIfEmpty(el, spec, g)) return { ok: false };
    const ui = makeUi(el, spec, g.traces);
    noteProblems(ui, g.problems);
    const traces = g.traces;
    assignColors(traces);
    const range = normalizeRange(spec.range, spec.range && spec.range.default);
    const render = async () => {
      const start = windowStartIso(traces, range);
      const multi = traces.length > 1;
      const data = traces.map((t) => {
        const s = sliceFrom(t.col.x, t.col.y, start);
        let color = t.color;
        if (!multi && spec.colorBySign) {
          const up = spec.colorBySign === 'neutral' ? COLORS.neutralUp : COLORS.positive;
          const down = spec.colorBySign === 'neutral' ? COLORS.neutralDown : COLORS.negative;
          color = s.y.map((v) => (v !== null && v < 0 ? down : up));
        }
        return {
          type: 'bar', x: s.x, y: s.y, name: t.label, marker: { color }, text: texts(s.y, t.field), textposition: 'none',
          hovertemplate: hoverTpl(t.field, t.label),
        };
      });
      if (overlay) {
        const so = sliceFrom(overlay.col.x, overlay.col.y, start);
        data.push({ type: 'scatter', mode: 'lines', x: so.x, y: so.y, name: overlay.label,
          line: { color: COLORS.ink, width: 2 }, text: texts(so.y, overlay.field), hovertemplate: hoverTpl(overlay.field, overlay.label) });
      }
      const ref = refShapes(spec.ref);
      const layout = baseLayout({
        height: spec.height, legend: multi || !!overlay, freq: traces[0].freq, yField: traces[0].field, zero: true,
        extra: { barmode: 'group', bargap: CHART.barGap, shapes: ref.shapes, annotations: ref.annotations },
      });
      await redraw(ui, data, layout);
      fillFooter(ui.foot, [...g.loaded.values()].filter((d) => traces.concat(overlay ? [overlay] : []).some((t) => t.ds === d)), observedOf(traces.concat(overlay ? [overlay] : [])), { stale: spec.stale });
    };
    buildRangeButtons(ui, range, render);
    loadingBody(ui);
    ariaLabel(ui, spec.title || autoTitle(traces), spec.subtitle || autoSubtitle(traces), observedOf(traces));
    await render();
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ stackedBarChart */

/**
 * Contributions by component (stacked, negatives stack below zero) with an optional total line.
 * spec: {title?, subtitle?, components: [{dataset, series, field, label?, color?}],
 *        total?: {dataset, series, field, label?}, range?: {years: 3} | {...}, height?}
 */
export function stackedBarChart(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    const comps = spec.components;
    const specs = spec.total ? [...comps, { ...spec.total, _total: true }] : comps;
    const g = await gather(specs);
    const bars = g.traces.filter((t) => !t.spec._total);
    const total = g.traces.find((t) => t.spec._total);
    if (!bars.length) { bailIfEmpty(el, spec, { ...g, traces: [] }); return { ok: false }; }
    const ui = makeUi(el, spec, bars);
    noteProblems(ui, g.problems);
    assignColors(bars);
    const range = normalizeRange(spec.range, spec.range && spec.range.default);
    const render = async () => {
      const start = windowStartIso(g.traces, range);
      const data = bars.map((t) => {
        const s = sliceFrom(t.col.x, t.col.y, start);
        return { type: 'bar', x: s.x, y: s.y, name: t.label, marker: { color: t.color }, text: texts(s.y, t.field), textposition: 'none',
          hovertemplate: hoverTpl(t.field, t.label) };
      });
      if (total) {
        const s = sliceFrom(total.col.x, total.col.y, start);
        data.push({ type: 'scatter', mode: 'lines+markers', x: s.x, y: s.y, name: total.label,
          line: { color: COLORS.ink, width: 2 }, marker: { size: 6, color: '#FFFFFF', line: { color: COLORS.ink, width: 2 } }, text: texts(s.y, total.field),
          hovertemplate: hoverTpl(total.field, total.label) });
      }
      const layout = baseLayout({
        height: spec.height, legend: true, freq: bars[0].freq, yField: bars[0].field, zero: true,
        extra: { barmode: 'relative', bargap: CHART.barGap },
      });
      await redraw(ui, data, layout);
      const used = g.traces.map((t) => t.ds);
      fillFooter(ui.foot, [...g.loaded.values()].filter((d) => used.includes(d)), observedOf(g.traces), { stale: spec.stale });
    };
    buildRangeButtons(ui, range, render);
    loadingBody(ui);
    ariaLabel(ui, spec.title || autoTitle(bars), spec.subtitle || autoSubtitle(bars), observedOf(bars));
    await render();
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ groupedBarChart */

/**
 * Latest value per category.
 * Mode A (categories are the series of one dataset, e.g. sectors, CCAA):
 *   {dataset, field, series?: [keys], orientation?: 'h'|'v', sort?: 'asc'|'desc', colorBySign?, toggle?: [{id,label,field}]}
 * Mode B (grouped, e.g. Spain vs EU27 per indicator):
 *   {categories: [{label, bars: [{dataset, series, field, name, color?}]}], orientation?}
 */
/** Wrap a long category label onto two or more lines for horizontal bars (narrow screens). */
function wrapLabel(label, max = 22) {
  const words = String(label).split(' ');
  const lines = [];
  let cur = '';
  for (const w of words) {
    if (cur && (cur + ' ' + w).length > max) { lines.push(cur); cur = w; } else cur = cur ? cur + ' ' + w : w;
  }
  if (cur) lines.push(cur);
  return lines.join('<br>');
}

function oneBarPerCategory(data, horizontal) {
  if (data.length < 2) return false;
  const n = (horizontal ? data[0].y : data[0].x).length;
  for (let k = 0; k < n; k++) {
    const filled = data.filter((d) => { const v = (horizontal ? d.x : d.y)[k]; return v !== null && v !== undefined; }).length;
    if (filled > 1) return false;
  }
  return true;
}

export function groupedBarChart(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    const toggle = spec.toggle ? { id: spec.toggle[0].id } : null;
    const build = async () => {
      const field = toggle ? spec.toggle.find((o) => o.id === toggle.id).field : spec.field;
      let cats;   // [{label, bars:[{name, spec}]}]
      if (spec.categories) {
        cats = spec.categories.map((c) => ({ label: c.label, bars: c.bars.map((b) => ({ name: b.name, color: b.color, spec: b })) }));
      } else {
        const ds = await loadDataset(spec.dataset).catch((e) => { throw e; });
        const keys = spec.series || ds.series.map((s) => s.key);
        cats = keys.map((k) => {
          const s = getSeries(ds, k);
          return { label: s ? s.label_es : k, bars: [{ name: '', spec: { dataset: spec.dataset, series: k, field } }] };
        });
      }
      const flat = cats.flatMap((c) => c.bars.map((b) => b.spec));
      const g = await gather(flat);
      return { cats, g };
    };
    let first;
    try { first = await build(); }
    catch (e) { errorCard(el, { title: spec.title, message: 'No se han podido cargar los datos de este indicador.', details: [e.message, e.detail] }); return { ok: false }; }
    if (bailIfEmpty(el, spec, first.g)) return { ok: false };
    const ui = makeUi(el, spec, first.g.traces);
    noteProblems(ui, first.g.problems);
    const horizontal = (spec.orientation || (spec.categories ? 'v' : 'h')) === 'h';

    const render = async () => {
      const { cats, g } = toggle ? await build() : first;
      const val = new Map();   // spec object -> {trace, point}
      for (const t of g.traces) val.set(t.spec, { t, p: lastPoint(t.col) });
      const barNames = [...new Set(cats.flatMap((c) => c.bars.map((b) => b.name)))];
      let rows = cats.map((c) => ({ ...c }));
      if (spec.sort && !spec.categories) {
        const key = (c) => { const v = val.get(c.bars[0].spec); return v && v.p ? v.p[1] : -Infinity; };
        rows.sort((a, b) => (spec.sort === 'asc' ? key(a) - key(b) : key(b) - key(a)));
      }
      const colorTrace = (name, i) => {
        const b = cats.flatMap((c) => c.bars).find((x) => x.name === name);
        if (b && b.color) return b.color;
        const sem = b && SERIES_COLORS[b.spec.series];
        return sem || CYCLE[i % CYCLE.length];
      };
      const single = barNames.length === 1 && barNames[0] === '';
      const data = barNames.map((name, i) => {
        const vals = rows.map((c) => {
          const b = c.bars.find((x) => x.name === name);
          const v = b && val.get(b.spec);
          return v && v.p ? v.p[1] : null;
        });
        const fieldOf = (c) => { const b = c.bars.find((x) => x.name === name); const v = b && val.get(b.spec); return v ? v.t.field : null; };
        const fld = rows.map(fieldOf).find(Boolean) || {};
        const labels = rows.map((c) => (horizontal ? wrapLabel(c.label) : c.label));
        let color = colorTrace(name, i);
        if (single && spec.colorBySign) {
          const up = spec.colorBySign === 'neutral' ? COLORS.neutralUp : COLORS.positive;
          const down = spec.colorBySign === 'neutral' ? COLORS.neutralDown : COLORS.negative;
          color = vals.map((v) => (v !== null && v < 0 ? down : up));
        } else if (single) color = COLORS.navy;
        const text = rows.map((c, k) => (vals[k] === null ? '' : fmtValue(vals[k], fieldOf(c) || fld)));
        const { fmt, suffix } = plotlyNumberFormat(fld);
        const trace = {
          type: 'bar', name: name || (fld.label_es || ''), marker: { color },
          text, textposition: 'outside', cliponaxis: false, textfont: { size: 12, color: COLORS.ink },
          hovertemplate: horizontal
            ? '%{y}: %{text}<extra></extra>'
            : `%{x}: %{text}<extra>${name}</extra>`,
        };
        if (horizontal) { trace.orientation = 'h'; trace.x = vals; trace.y = labels; } else { trace.x = labels; trace.y = vals; }
        return trace;
      });
      const fld0 = g.traces[0].field;
      const n = rows.length;
      const allVals = data.flatMap((d) => (horizontal ? d.x : d.y)).filter((v) => v !== null);
      const vmin = Math.min(0, ...allVals);
      const vmax = Math.max(0, ...allVals);
      const pad = (vmax - vmin || 1) * 0.3;   // room for outside value labels (display only)
      const valueRange = [vmin < 0 ? vmin - pad : 0, vmax > 0 ? vmax + pad : 0];
      const layout = baseLayout({
        height: spec.height || (horizontal ? Math.max(220, 34 * n * Math.max(1, single ? 1 : barNames.length * 0.7) + 50) : CHART.heightSmall + 40),
        legend: !single, freq: 'M', numericX: true, yField: fld0, zero: true,
        rightMargin: horizontal ? 64 : 12,
        extra: {
          // One bar per category (e.g. one dataset per index): overlay keeps each bar centred.
          barmode: oneBarPerCategory(data, horizontal) ? 'overlay' : 'group', bargap: 0.3, hovermode: 'closest',
          xaxis: horizontal ? { range: valueRange, showgrid: true, gridcolor: COLORS.grid, showline: false, ticksuffix: plotlyNumberFormat(fld0).axisSuffix, zeroline: true, zerolinecolor: COLORS.zero, separatethousands: true, ticks: '', nticks: 5 } : { type: 'category' },
          yaxis: horizontal ? { autorange: 'reversed', showgrid: false, ticksuffix: '', zeroline: false } : { range: valueRange, ticksuffix: plotlyNumberFormat(fld0).axisSuffix },
        },
      });
      await redraw(ui, data, layout);
      const used = g.traces.map((t) => t.ds);
      fillFooter(ui.foot, [...g.loaded.values()].filter((d) => used.includes(d)), observedOf(g.traces), { stale: spec.stale });
      if (toggle) ui.setSubtitle(spec.subtitle !== undefined ? spec.subtitle : autoSubtitle(g.traces));
      ariaLabel(ui, spec.title || autoTitle(g.traces), spec.subtitle || autoSubtitle(g.traces), observedOf(g.traces));
    };
    if (toggle) buildToggle(ui, spec.toggle, toggle, render);
    loadingBody(ui);
    await render();
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ crossSectionChart */

/**
 * Numeric x (e.g. maturity in years). Shows the snapshot date (as_of) of each series.
 * spec: {title?, subtitle?, series: [{dataset, series, field, label?, color?}], xTitle?, xSuffix?, height?}
 */
export function crossSectionChart(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    const g = await gather(spec.series);
    if (bailIfEmpty(el, spec, g)) return { ok: false };
    const traces = g.traces;
    assignColors(traces);
    const asOf = [...new Set(traces.map((t) => t.ser.as_of).filter(Boolean))].sort();
    const base = autoSubtitle(traces);
    const asOfText = asOf.length ? `Datos a ${asOf.map((d) => fmtPeriod(d, 'D')).join('; ')}` : '';
    const sub = spec.subtitle !== undefined ? spec.subtitle : [base, asOfText].filter(Boolean).join(' · ');
    const ui = makeUi(el, { ...spec, subtitle: sub }, traces);
    noteProblems(ui, g.problems);
    const xs = traces[0].col.x;
    const tickvals = xs.length <= 14 ? xs.filter((v) => v >= 1) : undefined;
    const suffix = spec.xSuffix || '';
    const data = traces.map((t) => ({
      type: 'scatter', mode: 'lines+markers', x: t.col.x, y: t.col.y, name: t.label,
      line: { color: t.color, width: CHART.lineWidth }, marker: { size: 7, color: t.color },
      text: t.col.y.map((v, i) => `${fmtNumberTrim(t.col.x[i], 2)}${suffix}: ${fmtValue(v, t.field)}`),
      hovertemplate: `%{text}<extra>${t.label}</extra>`,
    }));
    const layout = baseLayout({
      height: spec.height || CHART.heightSmall + 20, legend: traces.length > 1, numericX: true, yField: traces[0].field, zero: false,
      extra: {
        hovermode: 'closest',
        xaxis: {
          type: 'linear', tickmode: tickvals ? 'array' : 'auto', tickvals,
          ticktext: tickvals ? tickvals.map((v) => fmtNumberTrim(v, 2)) : undefined,
          title: spec.xTitle ? { text: spec.xTitle, font: { size: 12, color: COLORS.muted }, standoff: 6 } : undefined,
          showgrid: false,
        },
      },
    });
    ariaLabel(ui, spec.title || autoTitle(traces), sub, []);
    await draw(ui, data, layout);
    const obs = traces.map((t) => ({ label: t.label, iso: t.ser.as_of || null, freq: 'D' }));
    fillFooter(ui.foot, [...g.loaded.values()], obs, { asOf: true, stale: spec.stale });
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ rebasedComparison */

/**
 * Several series rebased to 100 at the start of the visible window (display-only transform).
 * spec: {title?, subtitle?, series: [{dataset, series, field, label?, color?}], range?, height?}
 */
export function rebasedComparison(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    const g = await gather(spec.series);
    if (bailIfEmpty(el, spec, g)) return { ok: false };
    const traces = g.traces;
    assignColors(traces);
    const range = normalizeRange(spec.range, spec.range && spec.range.default || '5A');
    const ui = makeUi(el, { ...spec, subtitle: spec.subtitle !== undefined ? spec.subtitle : '' }, traces);
    noteProblems(ui, g.problems);
    const render = async () => {
      const start = windowStartIso(traces, range);
      // Common base date: the latest "first non-null" among series, so all start on the same day.
      const sliced = traces.map((t) => sliceFrom(t.col.x, t.col.y, start));
      const firsts = sliced.map((s) => (firstPoint(s) || [null])[0]).filter(Boolean).sort();
      const baseIso = firsts.length ? firsts[firsts.length - 1] : null;
      const data = [];
      let freqBase = traces[0].freq;
      traces.forEach((t, i) => {
        const s = sliceFrom(sliced[i].x, sliced[i].y, baseIso);
        const fp = firstPoint(s);
        if (!fp || !fp[1]) return;
        const y = s.y.map((v) => (v === null ? null : (v / fp[1]) * 100));
        data.push({ type: 'scatter', mode: 'lines', x: s.x, y, name: t.label,
          line: { color: t.color, width: CHART.lineWidth }, connectgaps: false,
          text: y.map((v) => (v === null ? '' : fmtNumber(v, 1))), hovertemplate: `%{text}<extra>${t.label}</extra>` });
      });
      const sub = spec.subtitle !== undefined ? spec.subtitle
        : `Base 100 = ${baseIso ? fmtPeriod(baseIso, freqBase) : 'inicio del periodo'}`;
      ui.setSubtitle(sub);
      const ref = refShapes({ y: 100 });
      const layout = baseLayout({
        height: spec.height, legend: data.length > 1, freq: freqBase, yField: { unit: 'index', decimals: 1 }, zero: false,
        extra: { shapes: ref.shapes, yaxis: { tickformat: ',.0f' } },
      });
      await redraw(ui, data, layout);
      fillFooter(ui.foot, [...g.loaded.values()], observedOf(traces), { stale: spec.stale });
    };
    buildRangeButtons(ui, range, render);
    loadingBody(ui);
    ariaLabel(ui, spec.title || '', 'Series rebasadas a 100', observedOf(traces));
    await render();
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ donutChart */

/**
 * Composition (latest value of each series of a dataset, e.g. CPI weights).
 * spec: {title?, subtitle?, dataset, field, series?: [keys], height?}
 */
export function donutChart(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    let ds;
    try { ds = await loadDataset(spec.dataset); }
    catch (e) { errorCard(el, { title: spec.title, message: 'No se han podido cargar los datos de este indicador.', details: [e.message] }); return { ok: false }; }
    const keys = spec.series || ds.series.map((s) => s.key);
    const g = await gather(keys.map((k) => ({ dataset: spec.dataset, series: k, field: spec.field })));
    if (bailIfEmpty(el, spec, g)) return { ok: false };
    const traces = g.traces;
    const ui = makeUi(el, spec, traces);
    noteProblems(ui, g.problems);
    const pts = traces.map((t) => ({ t, p: lastPoint(t.col) }));
    const f = traces[0].field;
    const colors = pts.map((_, i) => CYCLE[i % CYCLE.length]);
    const data = [{
      type: 'pie', hole: 0.55, sort: false, direction: 'clockwise',
      labels: pts.map((x) => x.t.label), values: pts.map((x) => x.p[1]),
      marker: { colors, line: { color: '#FFFFFF', width: 2 } },
      textinfo: 'text', texttemplate: '%{text}',
      textfont: { color: '#FFFFFF', size: 12 },
      text: pts.map((x) => fmtValue(x.p[1], f)), hovertemplate: '%{label}: %{text}<extra></extra>',
    }];
    const layout = baseLayout({ height: spec.height || 340, legend: false, numericX: true, extra: {
      showlegend: true, hovermode: 'closest',
      legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: -0.05, yanchor: 'top' },
      margin: { l: 8, r: 8, t: 8, b: 8 },
    } });
    delete layout.xaxis; delete layout.yaxis;
    ariaLabel(ui, spec.title || autoTitle(traces), spec.subtitle || autoSubtitle(traces), observedOf(traces));
    await draw(ui, data, layout);
    fillFooter(ui.foot, [ds], observedOf(traces), { stale: spec.stale });
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ latestTable */

/**
 * Table of latest values: one row per series (or per explicit row spec), one column per field.
 * spec: {title?, subtitle?, dataset?, rows?: [{label, dataset?, series}], columns: [{field, label?, dataset?, signColor?, invert?}],
 *        sort?: {column: index, dir: 'asc'|'desc'}}
 * With `dataset` and no `rows`, every series of the dataset becomes a row.
 */
export function latestTable(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    let rows = spec.rows;
    if (!rows) {
      let ds;
      try { ds = await loadDataset(spec.dataset); }
      catch (e) { errorCard(el, { title: spec.title, message: 'No se han podido cargar los datos de este indicador.', details: [e.message] }); return { ok: false }; }
      rows = ds.series.map((s) => ({ label: s.label_es, series: s.key }));
    }
    const specs = [];
    rows.forEach((r, ri) => spec.columns.forEach((c, ci) => specs.push({
      dataset: c.dataset || r.dataset || spec.dataset, series: r.series, field: c.field, _r: ri, _c: ci,
    })));
    const g = await gather(specs);
    if (bailIfEmpty(el, spec, g)) return { ok: false };
    const cell = new Map(g.traces.map((t) => [`${t.spec._r}:${t.spec._c}`, t]));
    const ui = makeUi(el, spec, g.traces);
    noteProblems(ui, g.problems);
    let order = rows.map((_, i) => i);
    if (spec.sort) {
      const val = (i) => { const t = cell.get(`${i}:${spec.sort.column}`); const p = t && lastPoint(t.col); return p ? p[1] : -Infinity; };
      order.sort((a, b) => (spec.sort.dir === 'asc' ? val(a) - val(b) : val(b) - val(a)));
    }
    const thead = h('thead', {}, h('tr', {},
      h('th', { scope: 'col', text: spec.rowHeader || '' }),
      spec.columns.map((c, ci) => {
        const t = g.traces.find((x) => x.spec._c === ci);
        return h('th', { scope: 'col', class: 'num', text: c.label || (t ? t.field.label_es : c.field) });
      })));
    const tbody = h('tbody', {}, order.map((ri) => h('tr', {},
      h('th', { scope: 'row', text: rows[ri].label }),
      spec.columns.map((c, ci) => {
        const t = cell.get(`${ri}:${ci}`);
        const p = t && lastPoint(t.col);
        if (!p) return h('td', { class: 'num muted', text: '–' });
        let cls = 'num';
        if (c.signColor) {
          const s = signClass(p[1]);
          cls += ' ' + (s === 'flat' ? '' : ((s === 'up') !== !!c.invert ? 'pos' : 'neg'));
        }
        return h('td', { class: cls, text: fmtValue(p[1], t.field) });
      }))));
    ui.body.replaceChildren(h('div', { class: 'table-wrap', tabindex: '0', role: 'region', 'aria-label': spec.title || 'Tabla' },
      h('table', { class: 'data-table' }, thead, tbody)));
    fillFooter(ui.foot, [...g.loaded.values()], observedOf(g.traces), { stale: spec.stale });
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ periodTable */

/**
 * Table with one row per period (most recent first) and one column per series/field.
 * spec: {title?, subtitle?, columns: [{dataset, series, field, label?, signColor?}], last?: 12}
 */
export function periodTable(el, spec) {
  return guard(el, spec, async () => {
    placeholder(el, spec);
    const g = await gather(spec.columns.map((c, i) => ({ ...c, _c: i })));
    if (bailIfEmpty(el, spec, g)) return { ok: false };
    const ui = makeUi(el, spec, g.traces);
    noteProblems(ui, g.problems);
    const master = g.traces[0];
    const xs = [...new Set(g.traces.flatMap((t) => t.col.x))].sort().reverse().slice(0, spec.last || 12);
    const lookup = new Map(g.traces.map((t) => [t.spec._c, new Map(t.col.x.map((x, i) => [x, t.col.y[i]]))]));
    const thead = h('thead', {}, h('tr', {}, h('th', { scope: 'col', text: 'Periodo' }),
      g.traces.map((t) => h('th', { scope: 'col', class: 'num', text: t.spec.label || t.label }))));
    const tbody = h('tbody', {}, xs.map((x) => h('tr', {},
      h('th', { scope: 'row', text: fmtPeriod(x, master.freq) }),
      g.traces.map((t) => {
        const v = lookup.get(t.spec._c).get(x);
        if (v === null || v === undefined) return h('td', { class: 'num muted', text: '–' });
        let cls = 'num';
        if (t.spec.signColor && v !== 0) cls += v > 0 ? ' pos' : ' neg';
        return h('td', { class: cls, text: fmtValue(v, t.field) });
      }))));
    ui.body.replaceChildren(h('div', { class: 'table-wrap', tabindex: '0', role: 'region', 'aria-label': spec.title || 'Tabla' },
      h('table', { class: 'data-table' }, thead, tbody)));
    fillFooter(ui.foot, [...g.loaded.values()], observedOf(g.traces), { stale: spec.stale });
    return { ok: true };
  });
}

/* ------------------------------------------------------------------ kpiTile */

/**
 * Headline tile: latest value (formatted), period, and an optional change taken from ANOTHER
 * field of the same series (e.g. yoy). The frontend never subtracts or divides to build a change.
 * spec: {dataset, series, field, title?, change?: {field, label?}, positiveIsGood?: true|false|null, href?}
 */
export function kpiTile(el, spec) {
  return guard(el, spec, async () => {
    el.replaceChildren(h('article', { class: 'kpi is-loading', 'aria-busy': 'true' }, h('p', { class: 'kpi-label', text: spec.title || '' }), h('p', { class: 'kpi-value', text: '…' })));
    let ds;
    try { ds = await loadDataset(spec.dataset); }
    catch (e) {
      el.replaceChildren(h('article', { class: 'kpi kpi-error', role: 'alert' },
        h('p', { class: 'kpi-label', text: spec.title || spec.dataset }),
        h('p', { class: 'kpi-value', text: '–' }),
        h('p', { class: 'kpi-meta', text: 'Dato no disponible' })));
      console.warn('[charts]', e);
      return { ok: false, error: e };
    }
    let manifest = null;
    try { manifest = await loadManifest(); } catch (e) { /* fall back to the dataset itself */ }
    const entry = manifest ? manifestEntry(manifest, spec.dataset) : null;
    const ser = getSeries(ds, spec.series);
    const field = fieldDef(ds, spec.field);
    if (!ser || !field) {
      el.replaceChildren(h('article', { class: 'kpi kpi-error', role: 'alert' },
        h('p', { class: 'kpi-label', text: spec.title || spec.dataset }),
        h('p', { class: 'kpi-value', text: '–' }),
        h('p', { class: 'kpi-meta', text: 'Serie o campo inexistente' })));
      return { ok: false };
    }
    const pick = (fk) => manifestLatest(entry, spec.series, fk) || lastPoint(columns(ds, spec.series, fk));
    const main = pick(spec.field);
    const chg = spec.change ? pick(spec.change.field) : null;
    const chgField = spec.change ? fieldDef(ds, spec.change.field) : null;
    const title = spec.title || (ser.label_es && ds.series.length > 1 ? `${ds.title_es}: ${ser.label_es}` : ds.title_es);
    const kids = [h('p', { class: 'kpi-label', text: title })];
    kids.push(h('p', { class: 'kpi-value', text: main ? fmtValue(main[1], field) : '–' }));
    if (chg && chgField) {
      const s = signClass(chg[1]);
      let tone = 'neutral';
      if (s !== 'flat' && spec.positiveIsGood !== undefined && spec.positiveIsGood !== null) {
        tone = ((s === 'up') === !!spec.positiveIsGood) ? 'good' : 'bad';
      }
      const word = s === 'up' ? 'sube' : s === 'down' ? 'baja' : 'sin cambios';
      kids.push(h('p', { class: `kpi-change tone-${tone} dir-${s}` },
        h('span', { class: 'kpi-arrow', 'aria-hidden': 'true', text: arrow(chg[1]) }),
        h('span', { class: 'sr-only', text: word + ' ' }),
        ' ', fmtValue(chg[1], chgField), ' ',
        spec.change.label ? h('span', { class: 'kpi-change-label', text: spec.change.label }) : null));
    }
    const when = ds.frequency === 'X'
      ? (ser.as_of ? fmtPeriod(ser.as_of, 'D') : null)
      : (main ? fmtPeriod(main[0], ds.frequency) : null);
    const meta = [when, ds.source && ds.source.name].filter(Boolean).join(' · ');
    const metaEl = h('p', { class: 'kpi-meta', text: meta });
    if (staleInfo(ds).stale) metaEl.append(' ', h('span', { class: 'badge badge-stale', text: 'Desactualizado' }));
    kids.push(metaEl);
    const tile = h('article', { class: 'kpi' }, ...kids);
    if (spec.href) {
      const a = h('a', { class: 'kpi-link', href: spec.href }, tile);
      el.replaceChildren(a);
    } else el.replaceChildren(tile);
    return { ok: true };
  });
}

/** Grid of KPI tiles: kpiGrid(container, [spec, spec, ...]). */
export function kpiGrid(el, specs) {
  el.classList.add('kpi-grid');
  el.replaceChildren();
  return Promise.all(specs.map((s) => {
    const cell = h('div', { class: 'kpi-cell' });
    el.append(cell);
    return kpiTile(cell, s);
  }));
}
