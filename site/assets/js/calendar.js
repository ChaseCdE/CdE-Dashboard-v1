// Release calendar: list view (Calendario page) and the "Próximas publicaciones" box (Portada).
// Data: site/data/calendar.json, written by the pipeline (src/export/calendar.py).
import { DATA_ROOT, SITE_ROOT } from './config.js';
import { loadDataset, fieldDef, columns } from './data.js';
import { fmtValue } from './format.js';

const DAY = 86400000;
const WD = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
const MON = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
const MON_LONG = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
const SHORT = { 'Ministerios de Trabajo e Inclusión': 'Trabajo e Inclusión', 'Banco de España': 'Banco de España' };

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v; else if (k === 'text') el.textContent = v; else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c !== null && c !== undefined) el.append(c.nodeType ? c : document.createTextNode(String(c)));
  return el;
}

const nowMadrid = () => {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
    .formatToParts(new Date()).map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, time: `${p.hour === '24' ? '00' : p.hour}:${p.minute}` };
};
const toDate = (iso) => new Date(iso + 'T12:00:00Z');
const isoOf = (d) => d.toISOString().slice(0, 10);
const dayLabel = (iso) => { const d = toDate(iso); return `${WD[d.getUTCDay()]} ${d.getUTCDate()} ${MON[d.getUTCMonth()]}`; };
function weekStart(iso) { const d = toDate(iso); const wd = (d.getUTCDay() + 6) % 7; return isoOf(new Date(d - wd * DAY)); }
function weekLabel(mon) {
  const a = toDate(mon); const b = new Date(a.getTime() + 4 * DAY);
  return a.getUTCMonth() === b.getUTCMonth()
    ? `Semana del ${a.getUTCDate()} al ${b.getUTCDate()} de ${MON_LONG[b.getUTCMonth()]}`
    : `Semana del ${a.getUTCDate()} de ${MON_LONG[a.getUTCMonth()]} al ${b.getUTCDate()} de ${MON_LONG[b.getUTCMonth()]}`;
}
const released = (e, now) => e.date < now.date || (e.date === now.date && (!e.time || e.time <= now.time));

export async function loadCalendar() {
  const r = await fetch(DATA_ROOT + 'calendar.json', { cache: 'no-cache' });
  if (!r.ok) throw new Error(`calendar.json ${r.status}`);
  return r.json();
}

/** Value of a past release, read from the site's own data at the release's reference period. */
async function valueFor(e) {
  if (!e.value || !e.period_iso) return null;
  try {
    const ds = await loadDataset(e.value.dataset);
    const col = columns(ds, e.value.series, e.value.field);
    const i = col.x.indexOf(e.period_iso);
    const field = fieldDef(ds, e.value.field);
    if (i < 0 || col.y[i] === null || !field) return null;
    const flash = ds.provisional && ds.provisional.dates.includes(e.period_iso);
    const per = { yoy: ' anual', qoq: ' trimestral', mom: ' mensual' }[e.value.field] || '';
    const where = e.source === 'Eurostat' ? 'España: ' : '';   // EU releases: the site shows Spain's figure
    return `${where}${fmtValue(col.y[i], field)}${per}${flash ? ' (avance)' : ''}`;
  } catch (err) { return null; }
}

function item(e, now, withValue) {
  const title = e.tracked && e.page ? h('a', { href: SITE_ROOT + e.page, text: e.title_es }) : h('span', { text: e.title_es });
  const meta = [e.period_es ? h('span', { class: 'cal-period', text: e.period_es }) : null];
  if (e.flash) meta.push(h('span', { class: 'badge badge-flash', text: 'Avance' }));
  const valueEl = h('span', { class: 'cal-value' });
  if (withValue && released(e, now) && e.value) valueFor(e).then((v) => { if (v) valueEl.textContent = v; });
  return h('li', { class: 'cal-item' + (e.tracked ? ' is-tracked' : '') + (released(e, now) ? ' is-past' : '') },
    h('span', { class: 'cal-time', text: e.time || '' }),
    h('span', { class: 'cal-src', 'data-src': SHORT[e.source] || e.source, text: SHORT[e.source] || e.source }),
    h('span', { class: 'cal-what' }, title, ' ', ...meta),
    valueEl);
}

/** Full list with filters (Calendario page). */
export async function calendarPage(el) {
  let cal;
  try { cal = await loadCalendar(); }
  catch (err) { el.replaceChildren(h('p', { class: 'empty-msg', text: 'No se ha podido cargar el calendario.' })); return; }
  const now = nowMadrid();
  const state = { view: 'next', source: 'all', tracked: true };
  const sources = cal.sources.map((s) => s.name);

  const seg = (opts, key) => h('div', { class: 'cal-seg', role: 'group' }, opts.map(([v, label]) => {
    const b = h('button', { type: 'button', class: 'range-btn', 'aria-pressed': String(state[key] === v), text: label });
    b.addEventListener('click', () => { state[key] = v; for (const x of b.parentNode.children) x.setAttribute('aria-pressed', String(x === b)); render(); });
    return b;
  }));
  const chk = h('input', { type: 'checkbox', checked: true });
  chk.addEventListener('change', () => { state.tracked = chk.checked; render(); });
  const controls = h('div', { class: 'cal-controls' },
    seg([['next', 'Próximas'], ['past', 'Recientes']], 'view'),
    seg([['all', 'Todas las fuentes'], ...sources.map((s) => [s, SHORT[s] || s])], 'source'),
    h('label', { class: 'cal-check' }, chk, ' Solo estadísticas de este panel'));
  const list = h('div', { class: 'cal-list', 'aria-live': 'polite' });
  const cover = Object.entries(cal.coverage || {}).filter(([, d]) => d)
    .map(([s, d]) => `${SHORT[s] || s} hasta el ${dayLabel(d).replace(/^\S+ /, '')} ${d.slice(0, 4)}`).join(' · ');
  const foot = h('p', { class: 'cal-foot' }, 'Fuentes: ',
    ...cal.sources.flatMap((s, i) => [i ? ', ' : null, h('a', { href: s.url, target: '_blank', rel: 'noopener noreferrer', text: s.name })]),
    '. Horas en horario de Madrid; sin hora cuando la fuente no la publica. Calendarios disponibles: ', cover, '.');
  el.replaceChildren(controls, list, foot);

  function render() {
    let ev = cal.events.filter((e) => (state.source === 'all' || e.source === state.source) && (!state.tracked || e.tracked));
    if (state.view === 'next') {
      const end = isoOf(new Date(toDate(now.date).getTime() + 42 * DAY));
      ev = ev.filter((e) => e.date >= now.date && e.date <= end);
    } else {
      ev = ev.filter((e) => e.date <= now.date && released(e, now)).reverse();
    }
    if (!ev.length) { list.replaceChildren(h('p', { class: 'empty-msg', text: 'No hay publicaciones con estos filtros.' })); return; }
    const weeks = new Map();
    for (const e of ev) {
      const w = weekStart(e.date);
      if (!weeks.has(w)) weeks.set(w, new Map());
      const days = weeks.get(w);
      if (!days.has(e.date)) days.set(e.date, []);
      days.get(e.date).push(e);
    }
    list.replaceChildren(...[...weeks].map(([w, days]) => h('section', { class: 'cal-week' },
      h('h3', { class: 'cal-week-title', text: weekLabel(w) }),
      ...[...days].map(([d, items]) => h('div', { class: 'cal-day' + (d === now.date ? ' is-today' : '') },
        h('div', { class: 'cal-date' }, h('span', { text: dayLabel(d) }), d === now.date ? h('span', { class: 'cal-today', text: 'Hoy' }) : null),
        h('ul', { class: 'cal-items' }, items.map((e) => item(e, now, true))))))));
  }
  render();
}

/** Next releases of the statistics shown on the site (Portada box). */
export async function nextReleases(el, n = 6) {
  let cal;
  try { cal = await loadCalendar(); } catch (err) { el.closest('section')?.remove(); return; }
  const now = nowMadrid();
  const ev = cal.events.filter((e) => e.tracked && !released(e, now)).slice(0, n);
  el.replaceChildren(
    h('ul', { class: 'cal-items cal-compact' }, ev.map((e) => {
      const li = item(e, now, false);
      li.prepend(h('span', { class: 'cal-date-sm', text: e.date === now.date ? 'Hoy' : dayLabel(e.date) }));
      return li;
    })),
    h('p', { class: 'more' }, h('a', { href: SITE_ROOT + 'pages/calendario.html', text: 'Calendario completo →' })));
}
