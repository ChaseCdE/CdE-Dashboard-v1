// Data loader and read-only helpers for the JSON data contract (docs/data-contract.md).
// Nothing here computes economic quantities: it selects, slices and shifts dates only.
import { DATA_ROOT, SUPPORTED_CONTRACT_MAJOR } from './config.js';

export class DataError extends Error {
  constructor(message, code, detail) {
    super(message);
    this.name = 'DataError';
    this.code = code;       // 'bad_id' | 'not_found' | 'network' | 'invalid' | 'version' | 'no_series' | 'no_field'
    this.detail = detail || '';
  }
}

const ID_RE = /^[a-z0-9_]+\.[a-z0-9_]+$/;
const cache = new Map();   // key -> Promise (so concurrent callers share one request)

async function fetchJson(url, what) {
  let res;
  try {
    res = await fetch(url, { cache: 'no-cache' });
  } catch (e) {
    throw new DataError(`No se pudo descargar ${what}.`, 'network', `${url}: ${e.message}`);
  }
  if (res.status === 404) throw new DataError(`No existe ${what}.`, 'not_found', url);
  if (!res.ok) throw new DataError(`Error ${res.status} al descargar ${what}.`, 'network', url);
  try {
    return await res.json();
  } catch (e) {
    throw new DataError(`${what} no es un JSON válido.`, 'invalid', `${url}: ${e.message}`);
  }
}

function checkVersion(obj, what) {
  const v = String(obj && obj.contract_version || '');
  if (v.split('.')[0] !== SUPPORTED_CONTRACT_MAJOR) {
    throw new DataError(
      `${what} usa la versión de contrato ${v || '(desconocida)'}; el sitio soporta ${SUPPORTED_CONTRACT_MAJOR}.x.`,
      'version');
  }
}

/** Path of a dataset file relative to site/data/: 'ine.cpi' -> 'ine/cpi.json'. */
export function datasetPath(id) {
  if (typeof id !== 'string' || !ID_RE.test(id)) {
    throw new DataError(`Identificador de dataset no válido: "${id}".`, 'bad_id');
  }
  const [source, indicator] = id.split('.');
  return `${source}/${indicator}.json`;
}

export function loadManifest() {
  if (!cache.has('manifest')) {
    const p = fetchJson(DATA_ROOT + 'manifest.json', 'el índice de datos (manifest.json)')
      .then((m) => {
        checkVersion(m, 'manifest.json');
        if (!Array.isArray(m.datasets)) throw new DataError('manifest.json no tiene la lista "datasets".', 'invalid');
        return m;
      });
    p.catch(() => cache.delete('manifest'));
    cache.set('manifest', p);
  }
  return cache.get('manifest');
}

export function loadDataset(id) {
  const key = 'ds:' + id;
  if (!cache.has(key)) {
    let p;
    try {
      const path = datasetPath(id);
      // Check the manifest first: an unknown id fails fast without a 404 request.
      p = loadManifest().then((m) => {
        if (!manifestEntry(m, id)) throw new DataError(`El dataset "${id}" no figura en el manifest.`, 'not_found');
        return fetchJson(DATA_ROOT + path, `el dataset "${id}"`);
      }).then((ds) => {
        checkVersion(ds, `El dataset "${id}"`);
        if (ds.id !== id) throw new DataError(`El archivo de "${id}" declara el id "${ds.id}".`, 'invalid');
        if (!Array.isArray(ds.fields) || !Array.isArray(ds.series)) {
          throw new DataError(`El dataset "${id}" no tiene "fields" o "series".`, 'invalid');
        }
        return ds;
      });
    } catch (e) {
      p = Promise.reject(e);
    }
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return cache.get(key);
}

/** Entry of the manifest for a dataset id, or null. */
export function manifestEntry(manifest, id) {
  return (manifest && manifest.datasets || []).find((d) => d.id === id) || null;
}

/** Series object by key, or null. */
export function getSeries(ds, key) {
  return (ds.series || []).find((s) => s.key === key) || null;
}

/** Field definition by key, or null. */
export function fieldDef(ds, key) {
  return (ds.fields || []).find((f) => f.key === key) || null;
}

/** Index of a field inside a data row (row[0] is x, so the first field is 1). -1 if unknown. */
export function fieldIndex(ds, key) {
  const i = (ds.fields || []).findIndex((f) => f.key === key);
  return i < 0 ? -1 : i + 1;
}

/**
 * Column extraction: {x: [...], y: [...]} for one series and one field.
 * Nulls are kept (so gaps stay gaps) unless opts.dropNull is true.
 * Throws DataError if the series or field does not exist.
 */
export function columns(ds, seriesKey, fieldKey, opts = {}) {
  const s = getSeries(ds, seriesKey);
  if (!s) throw new DataError(`El dataset "${ds.id}" no tiene la serie "${seriesKey}".`, 'no_series');
  const i = fieldIndex(ds, fieldKey);
  if (i < 0) throw new DataError(`El dataset "${ds.id}" no tiene el campo "${fieldKey}".`, 'no_field');
  const x = [];
  const y = [];
  for (const row of s.data) {
    const v = row[i];
    if (opts.dropNull && (v === null || v === undefined)) continue;
    x.push(row[0]);
    y.push(v === undefined ? null : v);
  }
  return { x, y };
}

/** True if every value of the column is null (or there are no rows). */
export function allNull(col) {
  return !col.y.some((v) => v !== null && v !== undefined);
}

/** Last non-null [x, value] of a column, or null. */
export function lastPoint(col) {
  for (let i = col.y.length - 1; i >= 0; i--) {
    if (col.y[i] !== null && col.y[i] !== undefined) return [col.x[i], col.y[i]];
  }
  return null;
}

/** First non-null [x, value] of a column, or null. */
export function firstPoint(col) {
  for (let i = 0; i < col.y.length; i++) {
    if (col.y[i] !== null && col.y[i] !== undefined) return [col.x[i], col.y[i]];
  }
  return null;
}

/**
 * Latest non-null [x, value] of a field in a series, read from a manifest entry.
 * Returns null if the entry, series or field is missing, or the field is entirely null.
 */
export function latest(entry, seriesKey, fieldKey) {
  if (!entry) return null;
  const s = (entry.series || []).find((x) => x.key === seriesKey);
  if (!s || !s.latest) return null;
  const v = s.latest[fieldKey];
  return Array.isArray(v) ? v : null;
}

/**
 * Keep points with x >= isoDate. ISO 'YYYY-MM-DD' strings compare correctly as text.
 * For numeric x (cross-sections) pass a number. Returns {x, y}.
 */
export function sliceFrom(xs, ys, isoDate) {
  if (isoDate === null || isoDate === undefined) return { x: xs.slice(), y: ys.slice() };
  const x = [];
  const y = [];
  for (let i = 0; i < xs.length; i++) {
    if (xs[i] >= isoDate) { x.push(xs[i]); y.push(ys[i]); }
  }
  return { x, y };
}

/** ISO date n years before another ISO date (display windows such as "last 5 years"). */
export function shiftYears(iso, years) {
  const d = new Date(iso + 'T00:00:00Z');
  d.setUTCFullYear(d.getUTCFullYear() - years);
  return d.toISOString().slice(0, 10);
}

/** Maximum last_observation across loaded datasets (ISO string) or null. */
export function maxDate(values) {
  const v = values.filter(Boolean).sort();
  return v.length ? v[v.length - 1] : null;
}
