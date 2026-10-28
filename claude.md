# CdE Macroeconomic Dashboard ("La economía en datos")

Public dashboard of Spanish and European macroeconomic data by Círculo de Empresarios. Static HTML site fed by a Python data pipeline.

## Architecture

```
INE, Eurostat, Banco de España, Yahoo Finance
        │  src/fetchers/   (download → data/raw/, gitignored)
        │  src/processors/ (clean, derive → data/processed/, gitignored)
        │  src/export/     (→ site/data/*.json, committed)
        ▼
docs/data-contract.md  ← the only interface between pipeline and site (v1.1)
        ▼
site/  (plain HTML + ES modules + Plotly.js from cdnjs; no build step)
```

- `python run_pipeline.py` runs fetch → process → export → validate. Exit code ≠ 0 on failure.
- `scripts/validate_contract.py [--strict]` checks `site/data/` against the contract.
- `scripts/smoke_test.py [--run-processors]` offline checks of the pipeline.
- `.github/workflows/`: scheduled refresh (weekdays) and GitHub Pages deploy. See `docs/deploy.md`.

## Ground rules

### Data contract
- `docs/data-contract.md` is frozen. Changing it requires a version bump, a changelog entry, and updating the exporter (`src/export/core.py`), the validator and the frontend loader together.
- The frontend never computes economic quantities (growth rates, contributions, averages used as indicators). If a page needs one, the pipeline exports it as a field. Display-only rebasing is allowed.
- Field keys: `yoy/qoq/mom/ret_*` are relative changes (`pct_change`); `*_pp` and `chg_*` are differences of rates (`pp`); `*_diff` differences in the level's own unit. The validator enforces this.
- Dataset ids: `<source>.<indicator>`; declare datasets in `src/export/<source>.py` only.

### Site
- Pages use only `site/assets/js/charts.js` (chart factory), `layout.js`, `format.js`. No raw Plotly config in pages, no hard-coded numbers, units, dates or sources.
- Spanish UI, es-ES formatting. Corporate palette: navy `#16254D`, beige `#C2AE93` (beige for lines/areas, never for text). See `docs/style-guide.md`.
- Adding a page: copy `site/assets/templates/page-template.{html,js}`, add it to the nav in `layout.js`, document its charts in `docs/indicator-inventory.md`.
- `site/dev/` is a developer test harness; it is not deployed.

### Process
- Always delete temporary files at the end of each task.
- After changing pipeline code: `python scripts/smoke_test.py --run-processors` and `python scripts/validate_contract.py --strict`.
- After changing the site: serve `site/` locally and check every page at 375 px and 1440 px with no console errors.
- Commit with descriptive messages; keep commits focused.

## Directory structure

```
CdE-Dashboard-v1/
├── run_pipeline.py          # pipeline entry point
├── requirements.txt         # pipeline dependencies (pinned)
├── src/
│   ├── fetchers/            # API clients and indicator definitions per source
│   ├── processors/          # cleaning and derived fields per source
│   ├── scripts/             # fetch_/process_ entry points per source
│   └── export/              # site-data exporter (core.py + one module per source)
├── scripts/                 # smoke_test.py, validate_contract.py
├── site/                    # the public website (GitHub Pages)
│   ├── index.html, pages/   # Portada + 6 pages
│   ├── assets/              # css, js (charts, data, format, layout, config), img, templates
│   ├── data/                # generated JSON (do not edit by hand)
│   └── dev/                 # fixtures test page (not deployed)
├── docs/                    # contract, deploy, style guide, inventory, migration notes
├── data_sources_*.md        # source documentation per provider
└── .github/workflows/       # refresh-data.yml, deploy.yml
```

## Notes

- Maintained by Círculo de Empresarios.
- History of the Shiny → static migration: `docs/migration-plan.md`, `docs/migration-notes.md`, `docs/notes/`.
