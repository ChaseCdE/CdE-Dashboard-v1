// Spanish (es-ES) formatting for numbers, units and periods. Pure functions, no DOM.
// Number format: decimal comma, thousands dot (always, from 4 digits: "1.234"),
// non-breaking space before units.

const NBSP = ' ';
const MONTHS_SHORT = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
const MONTHS_LONG = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
  'septiembre', 'octubre', 'noviembre', 'diciembre'];

export const MONTHS = { short: MONTHS_SHORT, long: MONTHS_LONG };

function isNum(v) { return typeof v === 'number' && Number.isFinite(v); }

/** 1234.5, 1 -> "1.234,5". Options: sign (force "+" on positives). Returns "–" for null/NaN. */
export function fmtNumber(v, decimals = 1, opts = {}) {
  if (!isNum(v)) return '–';
  const d = Math.max(0, Math.min(4, decimals));
  let s = Math.abs(v).toFixed(d);
  // Avoid "-0,0": decide the sign after rounding.
  const rounded = Number(s);
  let [int, frac] = s.split('.');
  int = int.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  s = frac ? `${int},${frac}` : int;
  if (v < 0 && rounded !== 0) return '-' + s;
  if (opts.sign && rounded !== 0 && v > 0) return '+' + s;
  return s;
}

const SCALE_PREFIX = { 0: '', 3: 'mil ', 6: 'M', 9: 'mM', 12: 'B' };
const CURRENCY_SYMBOL = { EUR: '€', USD: '$', GBP: '£', JPY: '¥', CHF: 'CHF' };

function currencyUnit(currency, scale) {
  const sym = CURRENCY_SYMBOL[currency] || currency || '';
  const pre = SCALE_PREFIX[scale] !== undefined ? SCALE_PREFIX[scale] : `×10^${scale} `;
  return scale === 0 || !scale ? `${NBSP}${sym}` : `${NBSP}${pre.trim() ? pre.trim() : ''}${sym}`.replace('mil' + sym, 'mil' + NBSP + sym);
}

function compactPersons(v, scale, noun) {
  const actual = v * Math.pow(10, scale || 0);
  const abs = Math.abs(actual);
  // Number and magnitude stay together (NBSP); the noun may wrap to the next line.
  if (abs >= 1e6) return `${fmtNumber(actual / 1e6, 1)}${NBSP}M ${noun}`;
  if (abs >= 1e3) return `${fmtNumber(actual / 1e3, 0)}${NBSP}mil ${noun}`;
  return `${fmtNumber(actual, 0)}${NBSP}${noun}`;
}

/**
 * Format a value according to its field definition (unit, decimals, currency, scale).
 * opts.sign forces "+" on positives for any unit; opts.compact=false keeps persons/hours
 * in the stored scale ("21.912 miles"). opts.unit=false drops the unit suffix.
 */
export function fmtValue(v, field, opts = {}) {
  if (!isNum(v)) return '–';
  const f = field || {};
  const dec = Number.isInteger(f.decimals) ? f.decimals : 1;
  const showUnit = opts.unit !== false;
  switch (f.unit) {
    case 'pct':
      return fmtNumber(v, dec, opts) + (showUnit ? `${NBSP}%` : '');
    case 'pct_change':
      return fmtNumber(v, dec, { sign: true }) + (showUnit ? `${NBSP}%` : '');
    case 'pp':
      return fmtNumber(v, dec, { sign: true }) + (showUnit ? `${NBSP}p.${NBSP}p.` : '');
    case 'currency': {
      const num = fmtNumber(v, dec, opts);
      return showUnit ? num + currencyUnit(f.currency, f.scale || 0) : num;
    }
    case 'persons':
    case 'hours': {
      const noun = f.unit === 'persons' ? 'personas' : 'horas';
      if (opts.compact === false) {
        const sc = f.scale || 0;
        const suffix = sc === 3 ? 'miles' : sc === 6 ? 'millones' : '';
        return fmtNumber(v, dec, opts) + (showUnit ? `${NBSP}${suffix || noun}`.trimEnd() : '');
      }
      return showUnit ? compactPersons(v, f.scale || 0, noun) : fmtNumber(v, dec, opts);
    }
    case 'years':
      return fmtNumber(v, dec, opts) + (showUnit ? `${NBSP}${v === 1 ? 'año' : 'años'}` : '');
    case 'points':
      return fmtNumber(v, dec, opts) + (showUnit ? `${NBSP}pts` : '');
    case 'index':
    case 'rate':
    case 'count':
    default:
      return fmtNumber(v, dec, opts);
  }
}

/** Short description of the unit for subtitles: "%", "Índice", "M€", ... */
export function unitText(field) {
  const f = field || {};
  switch (f.unit) {
    case 'pct': return '%';
    case 'pct_change': return '% de variación';
    case 'pp': return 'puntos porcentuales';
    case 'index': return 'Índice';
    case 'points': return 'Puntos';
    case 'currency': {
      const u = currencyUnit(f.currency, f.scale || 0).replace(NBSP, '');
      return f.scale ? u : (CURRENCY_SYMBOL[f.currency] || f.currency || '');
    }
    case 'rate': return 'Tipo';
    case 'persons': return f.scale === 3 ? 'Miles de personas' : f.scale === 6 ? 'Millones de personas' : 'Personas';
    case 'hours': return f.scale === 3 ? 'Miles de horas' : f.scale === 6 ? 'Millones de horas' : 'Horas';
    case 'years': return 'Años';
    case 'count': return 'Número';
    default: return '';
  }
}

/** Parse 'YYYY-MM-DD' without timezone surprises. */
export function parseIso(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso));
  if (!m) return null;
  return { y: +m[1], m: +m[2], d: +m[3] };
}

/**
 * Period label by frequency: D/W "26 oct 2026", M "sep 2026", Q "T2 2026", A "2025".
 * Unknown frequency falls back to the daily format.
 */
export function fmtPeriod(iso, freq) {
  const p = parseIso(iso);
  if (!p) return iso == null ? '–' : String(iso);
  switch (freq) {
    case 'A': return String(p.y);
    case 'Q': return `T${Math.floor((p.m - 1) / 3) + 1}${NBSP}${p.y}`;
    case 'M': return `${MONTHS_SHORT[p.m - 1]}${NBSP}${p.y}`;
    default: return `${p.d}${NBSP}${MONTHS_SHORT[p.m - 1]}${NBSP}${p.y}`;
  }
}

/** "Último dato: sep 2026" (or "–" when no date). */
export function lastObservationCaption(iso, freq) {
  return iso ? `Último dato: ${fmtPeriod(iso, freq)}` : 'Último dato: –';
}

/** "26 de octubre de 2026" for long captions such as "Actualizado". */
export function fmtDateLong(iso) {
  const p = parseIso(iso);
  if (!p) return '–';
  return `${p.d} de ${MONTHS_LONG[p.m - 1]} de ${p.y}`;
}

/** Sign class for coloured deltas: 'up' | 'down' | 'flat'. */
export function signClass(v) {
  if (!isNum(v) || v === 0) return 'flat';
  return v > 0 ? 'up' : 'down';
}

/** Arrow glyph for a signed change. */
export function arrow(v) {
  if (!isNum(v) || v === 0) return '▬';
  return v > 0 ? '▲' : '▼';
}

/** d3-format hover string for Plotly (%{y:...}) matching a field, e.g. "+,.1f" and its suffix. */
export function plotlyNumberFormat(field) {
  const f = field || {};
  const d = Number.isInteger(f.decimals) ? f.decimals : 1;
  const signed = f.unit === 'pct_change' || f.unit === 'pp';
  const fmt = `${signed ? '+' : ''},.${d}f`;
  let suffix = '';
  if (f.unit === 'pct' || f.unit === 'pct_change') suffix = `${NBSP}%`;
  else if (f.unit === 'pp') suffix = `${NBSP}p.${NBSP}p.`;
  else if (f.unit === 'currency') suffix = currencyUnit(f.currency, f.scale || 0);
  else if (f.unit === 'points') suffix = `${NBSP}pts`;
  else if (f.unit === 'years') suffix = `${NBSP}años`;
  return { fmt, suffix, axisSuffix: (f.unit === 'pct' || f.unit === 'pct_change') ? `${NBSP}%` : '' };
}

/** d3 date format used by Plotly hovers per frequency (quarters are handled by labels). */
export function hoverDateFormat(freq) {
  switch (freq) {
    case 'A': return '%Y';
    case 'M': return '%b %Y';
    default: return '%-d %b %Y';
  }
}

/** Up to `max` decimals, trailing zeros trimmed: 0.25 -> "0,25", 5 -> "5", 0.5 -> "0,5". */
export function fmtNumberTrim(v, max = 2) {
  if (!isNum(v)) return '–';
  const s = fmtNumber(v, max);
  return s.includes(',') ? s.replace(/0+$/, '').replace(/,$/, '') : s;
}

/** Short unit for subtitles: "%", "p. p.", "índice", "M€", "puntos"... */
export function unitShort(field) {
  const f = field || {};
  switch (f.unit) {
    case 'pct':
    case 'pct_change': return '%';
    case 'pp': return 'p. p.';
    case 'index': return 'índice';
    case 'points': return 'puntos';
    case 'currency': return unitText(f);
    case 'rate': return '';
    case 'persons':
    case 'hours':
    case 'years':
    case 'count': return unitText(f).toLowerCase();
    default: return '';
  }
}
