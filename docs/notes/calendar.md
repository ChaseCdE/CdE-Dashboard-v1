# Release calendar ("Calendario" page, "Próximas publicaciones" on the Portada)

Pipeline source `calendar` (run_pipeline.py): `src/fetchers/calendars.py` downloads, `src/scripts/process_calendar.py`
normalises (`src/export/calendar.py`), the export writes `site/data/calendar.json` (31 days back, 190 ahead).

| Source | Format | Notes |
|---|---|---|
| INE | iCalendar feed `dynt3/Calendario/calendario.ics` | Every release of the current year with time. Next year's calendar appears around December. |
| Eurostat | JSON behind the euro-indicators calendar page (`/eurostat/o/calendars/eventsJson`) | Undocumented: checked on every run (minimum 20 events). |
| Banco de España | Annual PDF `calendario-bde-<year>.pdf` | Parsed by column position. Every release date must fall in its month column (95 %) or the previous file is kept. Revised during the year. |
| Trabajo e Inclusión (MTES-MISSM) | One-page annual PDF | Source for afiliación (AFI) and paro registrado (MLR). The server omits its intermediate certificate: the FNMT intermediate is bundled in `src/fetchers/certs/` (verification stays on). Must find both statistics in at least 11 months, all in the first ten days. |

- Which statistics are shown by default (`tracked`), their Spanish names and pages: `RULES` in `src/export/calendar.py`.
  A rule may name a `value` (dataset, series, field): past releases then show the site's figure for that period
  (for Eurostat releases, Spain's figure).
- On any download or parsing failure the previous raw file is kept and the run is flagged (warning in the log).
- When a new year starts, check that the Banco de España and MTES-MISSM PDFs for the new year have been read
  (their URL or layout can change).
