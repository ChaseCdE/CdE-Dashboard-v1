# ws/frontend notes (Phase 3)

## Decisions

- **Stack:** plain HTML, CSS, native ES modules. No build step, no npm. Fonts from Google Fonts (Source Serif 4, Source Sans 3) with system fallbacks.
- **Plotly 3.1.0, `plotly-basic`**, from cdnjs, loaded lazily by `charts.js` with SRI hashes, plus `plotly-locale-es` 3.1.0. The suggested 2.35.2 was **not usable**: `plotly-basic.min.js` and the locale return 404 at that version on cdnjs (checked). 3.1.0 is the same major used by current Plotly docs; versions 2.27.0 and 3.0.1 also exist. `plotly-basic` has scatter, bar and pie only: no choropleth, no indicator/gauge, no heatmap (the inventory accounts for this).
- A custom locale `es-cde` is registered on top of the CDN Spanish locale: lowercase month names, decimal comma, thousands dot. Hover text is formatted by `format.js` (not by d3 templates), so numbers are formatted by one code path.
- All URLs derive from `import.meta.url` (`config.js`), so pages at any depth and sub-path deployments work. `file://` is not supported (documented in the style guide).
- `loadDataset` checks the manifest first: an unknown id fails with a clear error and no 404 request, so a missing dataset leaves no console error.
- KPI "change" is never computed in the browser: `kpiTile` shows another exported field (e.g. `yoy`). Differences between series (Spain minus EU) and YTD returns must come from the pipeline.
- Beige `#C2AE93` has 2.2:1 contrast on white. Kept for EU-27 as specified; mitigation and alternative in `docs/style-guide.md`. Needs a decision from the project lead.
- `site/index.html` and `site/assets/js/pages/portada.js` are a starter (a few KPIs and two charts). The Phase 4 Portada agent should replace `portada.js` (and edit `index.html`); the plan lists `site/pages/` only for the other pages, so ownership of `index.html` must be assigned.
- `site/assets/img/logo-circulo.png` (white outlined, transparent) is used in the navy header; `logo-circulo.jpg` (1398 px) is a copy kept for later use.

## API summary

### data.js
`loadManifest(): Promise<manifest>` · `loadDataset(id): Promise<ds>` (cached; `DataError` with `.code`) · `datasetPath(id)` · `manifestEntry(manifest, id)` · `getSeries(ds, key)` · `fieldDef(ds, key)` · `fieldIndex(ds, key)` (row index, first field = 1) · `columns(ds, seriesKey, fieldKey, {dropNull?}) -> {x, y}` · `allNull(col)` · `lastPoint(col)` · `firstPoint(col)` · `latest(manifestEntry, seriesKey, fieldKey) -> [x, v] | null` · `sliceFrom(xs, ys, iso) -> {x, y}` · `shiftYears(iso, n)` · `maxDate(list)`.

### format.js
`fmtNumber(v, decimals, {sign})` · `fmtNumberTrim(v, max)` · `fmtValue(v, field, {sign, compact, unit})` · `unitText(field)` · `unitShort(field)` · `fmtPeriod(iso, freq)` (D "26 oct 2026", M "sep 2026", Q "T2 2026", A "2025") · `lastObservationCaption(iso, freq)` · `fmtDateLong(iso)` · `signClass(v)` · `arrow(v)` · `parseIso`, `plotlyNumberFormat`, `hoverDateFormat`.

### charts.js (every function: `(container, spec) => Promise`, never rejects)
Series ref = `{dataset, series, field, label?, color?, dash?}`. Common spec keys: `title?` (default: dataset title), `subtitle?` (default: field label + unit + `note_es`), `height?`, `card?: false`, `stale?: false`, `range?: false | {default: '1A'|'5A'|'max', buttons?, years?, options?: [{id,label,years}]}`.

- `lineChart(el, {series[], toggle?: [{id,label,series[]}], selectable?, ref?: {y,label?}|[...], endLabels?, markers?, zero?, yRange?, range?})`
- `barChart(el, {series[], colorBySign?: true|'neutral', overlay?: seriesRef, ref?, range?})`
- `stackedBarChart(el, {components[], total?, range?})`
- `groupedBarChart(el, {dataset, field, series?[], orientation?, sort?, colorBySign?, toggle?: [{id,label,field}]} | {categories: [{label, bars: [{dataset, series, field, name, color?}]}]})`
- `crossSectionChart(el, {series[], xTitle?, xSuffix?})` (shows `as_of`)
- `rebasedComparison(el, {series[], range?})` (base 100 at the start of the visible window)
- `donutChart(el, {dataset, field, series?[]})`
- `latestTable(el, {dataset | rows: [{label, dataset?, series}], columns: [{field, label?, dataset?, signColor?, invert?}], sort?, rowHeader?})`
- `periodTable(el, {columns: [{dataset, series, field, label?, signColor?}], last?})`
- `kpiTile(el, {dataset, series, field, title?, change?: {field, label?}, positiveIsGood?, href?})` · `kpiGrid(el, specs[])`
- Building blocks: `chartCard(el, {title, subtitle})`, `errorCard(el, {title, message, details})`, `staleInfo(ds)`, `ensurePlotly()`.

Behaviour on every function: missing dataset, series or field gives a visible error card (no throw); a field with only nulls gives an empty card; partial failures render what exists and add a warning note; stale data (thresholds of the contract, relative to `generated_at`) adds a "Desactualizado" badge in the footer.

### layout.js
`mountLayout({active})` mounts skip link, header (logo, title, nav) and footer into `#site-header` / `#site-footer`; `NAV` lists the 8 pages.

## Test evidence

Served with `python -m http.server` from the repo root (so the site ran under the sub-path `/site/`), Chromium via Playwright, Plotly from the real cdnjs CDN (no vendored copy was needed). `site/dev/fixtures.html` and `site/index.html`: zero console errors and no failed requests at 375 and 1440 px; fixtures show one console **warning** (the intentional missing-dataset case). No horizontal overflow (scrollWidth = clientWidth). Screenshots: `site/dev/screenshots/fixtures-375.png` and `fixtures-1440.png`. Also checked: nav toggle at 375 px, keyboard focus ring, hover tooltips, range buttons, toggle, checkbox series selection. Quarterly hover format (`T%q %Y`) was checked in isolation only: no quarterly sample dataset exists yet.

## Not done / limits

- No sample dataset has quarterly or annual frequency, a `weight` field, or `persons`/`currency` units: those formatting paths are unit-tested only in Node (`fmtValue`, `fmtPeriod`), and the donut and `rebasedComparison` were exercised with substitute data (format test only).
- The "all null" fixture is derived at run time from the real `ine.cpi` file by a fetch shim in `fixtures.js`; nothing in `site/data/` was touched.
- No choropleth map, gauge or per-period range slider (not in `plotly-basic`; see the inventory for the replacements).
- Charts have `aria-label` summaries but no hidden data table per chart.
- Accessibility was checked by inspection and keyboard, not with an automated audit.

## Requests

- REQUEST → ws/ine: export the fields marked NEEDS PIPELINE FIELD in `docs/indicator-inventory.md`: `gdp` (`qoq`, `value_2019`), `business_confidence` (`yoy`), `industrial_production` and `services_production` (`mom`, `value_2021_01`), `ipri` (`value_2021_01`). Confirm whether `yoy_change` of rates is a difference in pp or a % change, and set the unit accordingly (`pp` vs `pct_change`).
- REQUEST → ws/eurostat: a `gap` series (Spain minus EU-27, unit `pp`) in `eurostat.unemployment` and `eurostat.hicp`; export `gdp_index` with series `es`, `eu27`, `de`, `fr`, `it`.
- REQUEST → ws/bde: `current_account_balance` field `sum_12m`; `yoy_pp` for rates and debt ratios; `chg_30d`, `chg_ytd`, `chg_1y` (unit `pp`) for the daily rates in the markets table; `spain_10y_bond_monthly` as a dataset (confirm month-end vs average).
- REQUEST → ws/yahoo: per-index fields `ytd`, `ret_1w`, `ret_1m`, `ret_1y`, `ret_1d`, `sma_200` (unit `pct_change` / `index`); FX `ret_30d`, `ytd`, `ret_1y`; drop `fed_funds`.
- REQUEST → lead: decide Consumo merge (see inventory), map vs bar for CCAA, ownership of `site/index.html`, and beige contrast for lines.
- REQUEST → ws/export (contract owner), for v1.1 only if wanted: put `unit` and `decimals` of each field in the manifest so `kpiTile` need not load the full dataset file.
