// Downloads for chart cards: the chart as a PNG (with title, units and source) and the data
// shown as CSV. CSV uses ";" and decimal comma so it opens correctly in Excel configured for
// Spanish, with a UTF-8 BOM for accents. No values are computed here: the CSV holds exactly
// the numbers plotted (or, for tables, the raw value behind each formatted cell).
import { COLORS, PLOTLY } from './config.js';

const ISO = /^\d{4}-\d{2}-\d{2}$/;

function slug(s) {
  return String(s || 'grafico').replace(/€/g, 'eur').normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'grafico';
}

function today() { return new Date().toISOString().slice(0, 10); }

export function fileName(title, ext) { return `${slug(title)}_${today()}.${ext}`; }

function csvCell(v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number') {
    if (!Number.isFinite(v)) return '';
    return String(Math.round(v * 1e4) / 1e4).replace('.', ',');
  }
  const s = String(v).replace(/<br\s*\/?>/gi, ' ');
  return /[;"\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function toCsv(rows) {
  return '﻿' + rows.map((r) => r.map(csvCell).join(';')).join('\r\n') + '\r\n';
}

function save(href, name) {
  const a = document.createElement('a');
  a.href = href;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
}

function saveText(text, name, type) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  save(url, name);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/** Title, subtitle, footer text of a card, read at click time (they change with toggles). */
export function cardMeta(card) {
  const q = (sel) => { const n = card.querySelector(sel); return n && !n.hidden ? n.textContent.trim() : ''; };
  const foot = card.querySelector('.card-foot');
  return {
    title: q('.card-title'),
    subtitle: q('.card-sub'),
    // Footer without the stale badge text, separators normalised.
    source: foot ? [...foot.childNodes].filter((n) => !(n.classList && n.classList.contains('badge')))
      .map((n) => n.textContent.trim()).filter(Boolean).join(' ').replace(/\s*·\s*/g, ' · ') : '',
  };
}

function metaRows(meta, extra = []) {
  return [
    [],
    ['Título', meta.title],
    ...(meta.subtitle ? [['Unidades y notas', meta.subtitle]] : []),
    ...(meta.source ? [['Fuente', meta.source.replace(/^Fuente:\s*/, '')]] : []),
    ...extra,
    ['Descargado de', location.href.split('#')[0]],
    ['Fecha de descarga', today()],
    ['Elaboración', 'Círculo de Empresarios, «La economía en datos»'],
  ];
}

/** CSV of the traces currently drawn in a Plotly element (respects toggles, ranges, rebasing). */
export function plotCsv(gd, meta) {
  const traces = (gd.data || []).filter((t) => t.visible !== false && (t.x || t.y || t.values));
  const cols = traces.map((t, i) => {
    const horizontal = t.orientation === 'h';
    const pie = t.type === 'pie';
    const xs = (pie ? t.labels : horizontal ? t.y : t.x) || [];
    const ys = (pie ? t.values : horizontal ? t.x : t.y) || [];
    return { name: String(t.name || `Serie ${i + 1}`).replace(/<br\s*\/?>/gi, ' '), map: new Map(xs.map((x, k) => [x, ys[k]])), xs };
  });
  const allX = cols.flatMap((c) => c.xs);
  const kind = allX.length && allX.every((x) => typeof x === 'string' && ISO.test(x)) ? 'date'
    : allX.every((x) => typeof x === 'number') ? 'number' : 'category';
  let keys = [...new Set(allX)];
  if (kind === 'date') keys.sort();
  else if (kind === 'number') keys.sort((a, b) => a - b);
  const xHead = kind === 'date' ? 'Fecha (inicio del periodo)' : kind === 'number' ? (meta.xLabel || 'Eje horizontal') : 'Categoría';
  const seen = new Map();
  const head = [xHead, ...cols.map((c) => { const n = seen.get(c.name) || 0; seen.set(c.name, n + 1); return n ? `${c.name} (${n + 1})` : c.name; })];
  const rows = [head, ...keys.map((x) => [x, ...cols.map((c) => (c.map.has(x) ? c.map.get(x) : null))])];
  return toCsv([...rows, ...metaRows(meta, [['Periodo', 'El mostrado en el gráfico al descargar (use «Máx» para la serie completa)']])]);
}

/** CSV of an HTML data table; numeric cells use their raw data-value. */
export function tableCsv(table, meta) {
  const rows = [...table.querySelectorAll('tr')].map((tr) => [...tr.children].map((c) => {
    const v = c.getAttribute('data-value');
    if (v !== null && v !== '') { const n = Number(v); return Number.isFinite(n) ? n : v; }
    const t = c.textContent.trim();
    return t === '–' ? '' : t;
  }));
  return toCsv([...rows, ...metaRows(meta)]);
}

export function downloadCsv(text, title) {
  saveText(text, fileName(title, 'csv'), 'text/csv;charset=utf-8');
}

// SVG rendered as an image cannot load web fonts, and quoted family names ('Source Sans 3',
// 'Segoe UI') make Plotly's SVG fail to load as an image. Use a plain, universally present stack.
const EXPORT_FONT = 'Arial, Helvetica, sans-serif';

function plainFonts(obj) {
  if (Array.isArray(obj)) { obj.forEach(plainFonts); return obj; }
  if (obj && typeof obj === 'object') {
    for (const [k, v] of Object.entries(obj)) {
      if (k === 'family' && typeof v === 'string') obj[k] = EXPORT_FONT;
      else plainFonts(v);
    }
  }
  return obj;
}

function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

/**
 * PNG of a chart with its title, subtitle and source drawn in, at 2400×1350 px (or taller for
 * tall charts). Rendered off-screen so the page's chart is not touched.
 */
export async function downloadPng(Plotly, gd, meta) {
  const W = 1200;
  const ratio = gd.clientWidth ? gd.clientHeight / gd.clientWidth : 0.56;
  const H = Math.round(Math.min(1600, Math.max(560, W * Math.max(ratio, 0.5)))) + 130;
  const src = JSON.parse(JSON.stringify(gd.layout || {}));
  const m = src.margin || {};
  const layout = {
    ...src,
    width: W, height: H, autosize: false,
    paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF',
    margin: { ...m, l: Math.max(m.l || 0, 60), t: (m.t || 10) + 80, b: (m.b || 8) + 64, r: Math.max(m.r || 0, 24) },
    title: {
      text: `<b>${esc(meta.title)}</b>` + (meta.subtitle ? `<br><span style="font-size:13px;color:${COLORS.inkSoft}">${esc(meta.subtitle)}</span>` : ''),
      x: 0.01, xanchor: 'left', xref: 'container', y: 0.975, yanchor: 'top', yref: 'container',
      font: { family: EXPORT_FONT, size: 20, color: COLORS.navy },
    },
    annotations: [...(src.annotations || []), {
      xref: 'paper', yref: 'paper', x: 0, y: 0, xanchor: 'left', yanchor: 'top', yshift: -((m.b || 8) + 30),
      text: esc([meta.source, 'Círculo de Empresarios · La economía en datos'].filter(Boolean).join(' · ')),
      showarrow: false, align: 'left', font: { family: EXPORT_FONT, size: 11, color: COLORS.muted },
    }],
    font: { ...(src.font || {}), family: EXPORT_FONT },
  };
  plainFonts(layout);
  const tmp = document.createElement('div');
  tmp.style.cssText = `position:fixed;left:-20000px;top:0;width:${W}px;height:${H}px;`;
  document.body.append(tmp);
  try {
    await Plotly.newPlot(tmp, plainFonts(JSON.parse(JSON.stringify(gd.data || []))), layout,
      { staticPlot: true, displayModeBar: false, locale: PLOTLY.localeName });
    const url = await Plotly.toImage(tmp, { format: 'png', width: W, height: H, scale: 2 });
    save(url, fileName(meta.title, 'png'));
  } finally {
    Plotly.purge(tmp);
    tmp.remove();
  }
}
