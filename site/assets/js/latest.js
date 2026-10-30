// "Últimos datos" on the Portada: cards for the headline indicators with the most recent
// releases, and a chart of the selected one. Everything comes from site/data/releases.json,
// written by the pipeline (src/export/releases.py): which indicators, their charts, and the log
// of when each new figure appeared. No hand editing is needed to keep it current.
import { DATA_ROOT, SITE_ROOT } from './config.js';
import { loadDataset, getSeries, fieldDef, columns } from './data.js';
import { fmtValue, fmtPeriod, signClass, arrow } from './format.js';
import { lineChart, barChart, isFlash } from './charts.js';

const WINDOW_DAYS = 21;   // releases shown as "new"
const MAX_CARDS = 8;

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v; else if (k === 'text') el.textContent = v; else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c !== null && c !== undefined) el.append(c.nodeType ? c : document.createTextNode(String(c)));
  return el;
}

function daysBetween(isoA, isoB) {
  return Math.round((Date.parse(isoB) - Date.parse(isoA)) / 86400000);
}

function todayMadrid() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid' }).format(new Date());
}

function whenText(detected) {
  const d = daysBetween(detected, todayMadrid());
  if (d <= 0) return 'Publicado hoy';
  if (d === 1) return 'Publicado ayer';
  return `Publicado hace ${d} días`;
}

/** Last two observations of a series/field: [[iso, v], [iso, v] | null]. */
function lastTwo(ds, series, field) {
  const col = columns(ds, series, field);
  const pts = col.x.map((x, i) => [x, col.y[i]]).filter((p) => p[1] !== null);
  return [pts[pts.length - 1] || null, pts[pts.length - 2] || null];
}

function sentence(hl, ds, last, prev) {
  const field = fieldDef(ds, hl.field);
  const flash = isFlash(ds, last[0]) ? ' (avance)' : '';
  let s = `${hl.title_es}: ${fmtValue(last[1], field)} en ${fmtPeriod(last[0], ds.frequency)}${flash}`;
  if (prev) s += `, frente a ${fmtValue(prev[1], field)} en ${fmtPeriod(prev[0], ds.frequency)}`;
  return s + '.';
}

async function card(hl, event, onSelect) {
  const ds = await loadDataset(hl.id);
  const field = fieldDef(ds, hl.field);
  const [last] = lastTwo(ds, hl.series, hl.field);
  if (!field || !last) return null;
  const kids = [h('span', { class: 'lt-title', text: hl.title_es }),
    h('span', { class: 'lt-value', text: fmtValue(last[1], field) })];
  if (hl.change) {
    const cf = fieldDef(ds, hl.change.field);
    const [c] = lastTwo(ds, hl.series, hl.change.field);
    if (cf && c && c[0] === last[0]) {
      const s = signClass(c[1]);
      let tone = 'neutral';
      if (s !== 'flat' && hl.positive_is_good !== null && hl.positive_is_good !== undefined) {
        tone = ((s === 'up') === !!hl.positive_is_good) ? 'good' : 'bad';
      }
      kids.push(h('span', { class: `lt-change kpi-change tone-${tone}` }, arrow(c[1]), ' ', fmtValue(c[1], cf), ' ', hl.change.label || ''));
    }
  }
  const period = h('span', { class: 'lt-period', text: fmtPeriod(last[0], ds.frequency) });
  if (isFlash(ds, last[0])) period.append(' ', h('span', { class: 'badge badge-flash', text: 'Avance' }));
  kids.push(period);
  if (event) {
    const txt = event.status === 'definitivo' ? whenText(event.detected).replace('Publicado', 'Definitivo') : whenText(event.detected);
    kids.push(h('span', { class: 'lt-when is-new', text: txt }));
  }
  const btn = h('button', { type: 'button', class: 'lt-card', 'aria-pressed': 'false' }, ...kids);
  btn.addEventListener('click', () => onSelect(hl, btn));
  return btn;
}

async function showChart(hl, box) {
  const ds = await loadDataset(hl.id);
  const [last, prev] = lastTwo(ds, hl.series, hl.field);
  const c = hl.chart;
  const spec = {
    title: hl.title_es,
    series: c.series.map((s) => ({ dataset: s.dataset, series: s.series, field: s.field, ...(s.label ? { label: s.label } : {}) })),
    range: { years: c.years || 3 },
    ...(c.ref ? { ref: c.ref } : {}),
    ...(c.type === 'bar' && c.series.length === 1 ? { colorBySign: 'neutral' } : {}),
  };
  const chartEl = h('div', {});
  const kids = [];
  if (last) kids.push(h('p', { class: 'lt-sentence', text: sentence(hl, ds, last, prev) }));
  kids.push(chartEl);
  if (hl.page) kids.push(h('p', { class: 'more' }, h('a', { href: SITE_ROOT + hl.page, text: 'Más indicadores de esta sección →' })));
  box.replaceChildren(...kids);
  (c.type === 'bar' ? barChart : lineChart)(chartEl, spec);
}

export async function latestData(el) {
  let rel;
  try {
    const r = await fetch(DATA_ROOT + 'releases.json', { cache: 'no-cache' });
    if (!r.ok) throw new Error(r.status);
    rel = await r.json();
  } catch (e) {
    console.warn('[latest] releases.json not available', e);
    el.closest('section')?.remove();
    return;
  }
  const today = todayMadrid();
  const byId = new Map(rel.highlights.map((x) => [x.id, x]));
  // Recent releases first (newest event per indicator), then the other indicators by period.
  const recent = [];
  for (const e of rel.events || []) {
    if (daysBetween(e.detected, today) > WINDOW_DAYS || !byId.has(e.id) || recent.some((x) => x.e.id === e.id)) continue;
    recent.push({ hl: byId.get(e.id), e });
  }
  const others = [];
  for (const hl of rel.highlights) {
    if (recent.some((x) => x.hl.id === hl.id)) continue;
    try {
      const ds = await loadDataset(hl.id);
      const [last] = lastTwo(ds, hl.series, hl.field);
      if (last) others.push({ hl, e: null, iso: last[0] });
    } catch (e) { /* dataset missing: skip */ }
  }
  others.sort((a, b) => (a.iso < b.iso ? 1 : -1));
  const list = [...recent, ...others].slice(0, Math.max(MAX_CARDS, recent.length));

  const strip = h('div', { class: 'lt-strip', role: 'group', 'aria-label': 'Indicadores con los datos más recientes' });
  const box = h('div', { class: 'lt-chart' });
  el.replaceChildren(strip, box);
  const select = (hl, btn) => {
    for (const b of strip.querySelectorAll('.lt-card')) b.setAttribute('aria-pressed', String(b === btn));
    showChart(hl, box);
  };
  const cards = [];
  for (const { hl, e } of list) {
    try { const c = await card(hl, e, select); if (c) { strip.append(c); cards.push([hl, c]); } }
    catch (err) { console.warn('[latest]', hl.id, err); }
  }
  if (cards.length) select(...cards[0]);
}
