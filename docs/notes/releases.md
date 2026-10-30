# "Últimos datos" (Portada) and flash estimates

## What the reader sees
Cards for headline indicators, newest release first ("Publicado hoy / ayer / hace N días", last
21 days), then the other headline indicators by period. Selecting a card shows a factual sentence
("Inflación (IPC): +4,9 % en oct 2026 (avance), frente a +4,9 % en sep 2026.") and its chart.

## How it is produced (no manual step)
- `src/export/releases.py` holds `HIGHLIGHTS`: the indicators, the value and change on each card
  and the chart of each one. Edit it to add or remove indicators; the site needs no JS changes.
- On every full export (`python -m src.export.export_site_data`, run by the daily refresh) the
  new manifest is compared with the one being replaced. When the latest period of a highlighted
  series moves forward, an event is logged with the export date (Spanish time). The refresh runs
  after the INE (09:00) and Eurostat (11:00) releases, so that is the publication date.
- Statuses: `nuevo`, `avance` (new period that is an INE flash estimate), `definitivo` (the flash
  of a period replaced by the full release). The log keeps 400 days.
- `scripts/backfill_releases.py` rebuilds the log from the git history of manifest.json.

## Flash estimates ("avance")
- The INE API marks each observation with `FK_TipoDato`: 1 definitive, 2 provisional,
  3 avance. `src/fetchers/ine_indicators.py` writes the type-3 dates by series code to
  `data/raw/ine/flash.json`; the export adds `provisional` to the datasets built from those
  series. Type 2 is not flagged: most recent INE figures are provisional for months or years.
- The CPI flash publishes only the annual rates (headline and core), with no index: the CPI
  processor keeps those months with an empty index.
- The INE marks the quarterly GDP flash as provisional (2), not as avance (3), so GDP is not
  labelled "Avance" on the site.
