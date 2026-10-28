# Migration plan: Shiny (Python) → static HTML dashboard

Status: draft, 2026-10-28. Target: public static site. Python stays as the data pipeline.

## Principles

1. **Python is the backend, the browser is the frontend.** `src/fetchers`, `src/processors`, `run_pipeline.py` are kept. `src/app/` (Shiny) is deleted at the end.
2. **The data contract is the interface between the two halves.** It is frozen at the end of Phase 1. Pipeline agents produce it; frontend agents consume it. Neither side changes it unilaterally.
3. **No server.** Output is a folder (`site/`) deployable to GitHub Pages / Cloudflare Pages. Data refresh is a scheduled GitHub Action that re-runs the pipeline and commits `site/data/`.
4. **No build step.** Plain HTML + ES modules + Plotly.js from CDN (`plotly-basic`). No Node toolchain to maintain.
5. **Public site.** `serve.py`, `auth_middleware.py`, `.env`, uvicorn and the tunnel docs are removed.

## Agent coordination rules

- One agent per workstream; each workstream owns an explicit set of paths (listed below). An agent does not edit paths it does not own. Cross-cutting needs go into `docs/migration-notes.md` as a request, not as an edit.
- Each workstream is a branch `ws/<name>`, merged to `main` via PR only when its acceptance check passes.
- `python scripts/validate_contract.py` is the single acceptance check for anything that touches `site/data/`. It must pass on `main` at all times after Phase 1.
- Agents read this file, `docs/data-contract.md` and the relevant `data_sources_*.md` before starting. Frontend agents also read `docs/style-guide.md`.
- Temporary files are deleted at the end of every task (existing project rule).

## Phase 0 — Stabilise (sequential, 1 agent, ~1 h) — DONE 2026-10-28

Owns: everything. Blocks all other phases.

- [ ] Commit the uncommitted INE fix (`ine_processor.py`, `process_ine_data.py`); HEAD is currently syntactically broken.
- [ ] Add `.claude/settings.local.json` to `.gitignore` and untrack it; untrack `tmpclaude-2ffa-cwd`.
- [ ] Pin `requirements.txt` to exact versions that currently work.
- [ ] Run `python run_pipeline.py` end to end. Record failures in `docs/migration-notes.md`. Do not fix source-specific failures here; hand them to Phase 2.
- [ ] Add `scripts/smoke_test.py`: imports every module under `src/fetchers`, `src/processors`, `src/scripts`; loads every CSV in `data/processed/`. Must pass.

Acceptance: clean `git status`, pipeline runs, smoke test passes.

## Phase 1 — Data contract (sequential, 1 agent, ~half day) — DONE 2026-10-28

Owns: `docs/data-contract.md`, `scripts/validate_contract.py`, `src/export/`, `site/data/` (schema only, sample files).

Delivered (see `docs/data-contract.md`, which supersedes this summary):
- Contract v1.0, FROZEN. One JSON per dataset at `site/data/<source>/<indicator>.json`; columnar rows `[x, field_1, ...]`; every series in a file shares the same fields; Spain/EU27 comparisons and sector breakdowns are series inside one file. Period dates on the first day of the period. Numbers stored to at most 4 decimals; display rounding via each field's `decimals`. Frontend may not compute economic quantities.
- `site/data/manifest.json` with latest value per series and field. Page assignment is NOT in the manifest; it lives in `docs/indicator-inventory.md` (Phase 3).
- Exporter: `src/export/core.py` (frozen with the contract), one declaration module per source (`src/export/{ine,eurostat,bde,yahoo}.py`), `src/export/export_site_data.py`. Rebuilds `site/data/` atomically; anything not declared disappears.
- `scripts/validate_contract.py`: structural checks, manifest consistency, staleness warnings by frequency; `--strict` fails on warnings. No external dependencies.
- `run_pipeline.py` now runs export + validation after processing and exits non-zero on failure (`--no-export` to skip).
- Five sample datasets, one per data shape: `ine.cpi` (single series), `ine.ipi_sectors` (long format), `eurostat.hicp` (Spain vs EU27), `bde.yield_curve` (cross-section), `yahoo.ibex_35` (daily).

## Phase 2 — Pipeline normalisation (parallel, 4 agents, ~1 day each) — DONE 2026-10-28

One agent per source. Each owns its fetcher, processor, script and export mapping:

| Agent | Owns |
|---|---|
| ws/ine | `src/fetchers/ine_*`, `src/processors/ine_processor.py`, `src/scripts/*_ine_*`, `src/export/ine.py` |
| ws/eurostat | same pattern for eurostat |
| ws/bde | same pattern for bde |
| ws/yahoo | same pattern for yahoo |

Tasks for each:
- Fix any failures logged in Phase 0.
- Declare datasets only in `src/export/<source>.py`. Do not edit `src/export/core.py` or the validator; request changes in `docs/migration-notes.md`.
- Map every indicator the dashboard needs (see `docs/indicator-inventory.md`, produced by ws/frontend-scaffold in Phase 3; until it exists, use `content.md` and the existing `src/app/pages/*.py` as the inventory) to contract-compliant JSON.
- Metadata (Spanish names, units, source URLs) lives in the indicator dictionaries (`*_indicators.py`), not hard-coded in the export.
- Known fixes: `fed_funds` uses `^IRX` (3-month T-bill) and is mislabelled; relabel or drop. `cntr_employment.csv` and `population.csv` are produced but unused: decide.

Acceptance: `validate_contract.py --strict` passes (or each remaining warning is explained in `docs/migration-notes.md`); `run_pipeline.py --sources <src>` completes; manifest entries present for every indicator assigned to that source in the inventory.

## Phase 3 — Frontend scaffold (1 agent, parallel with Phase 2, ~1 day) — DONE 2026-10-28

Owns: `site/` except `site/data/` and `site/pages/`; `docs/style-guide.md`; `docs/indicator-inventory.md`.

- `site/index.html`, `site/assets/css/`, `site/assets/js/` with: data loader (fetch JSON + manifest, cached), chart factory wrapping Plotly.js (line, bar, grouped bar, yield curve, indexed comparison), Spanish number/date formatting, responsive layout, nav, footer with sources.
- Port the visual identity (CdE corporate colours, logo, typography) from `src/app/styles.py` and `src/app/www/` into `docs/style-guide.md` and the CSS. One palette, defined once, used by every chart.
- `docs/indicator-inventory.md`: for each existing Shiny page (including the five unregistered ones: overview, labor, credit, consumer, eu_comparison) list the indicators shown, chart type, transformations. This is the spec Phase 4 agents build from and Phase 2 agents export to.
- Works against the Phase 1 sample fixtures.

Acceptance: `index.html` and `site/dev/fixtures.html` render from a static server with no console errors (`file://` is not supported: browsers block `fetch` there); chart factory renders all fixture files.

## Phase 4 — Pages (parallel, 1 agent per page, ~half day each)

Owns: `site/pages/<page>.html` and `site/assets/js/pages/<page>.js` only. Needs Phase 3 done and the relevant Phase 2 sources merged.

Pages (Spanish titles, URL slugs):
1. Portada (`index`): headline tiles from `manifest.json` (latest value, date, change) and 4–6 key charts. Replaces `overview.py`.
2. Actividad (`actividad`): from `activity.py`.
3. Precios (`precios`): from `prices.py`.
4. Mercado laboral (`laboral`): from `labor.py` (currently unregistered).
5. Crédito y tipos (`credito`): from `credit.py` (unregistered) plus BdE rates/yield curve.
6. Mercados (`mercados`): from `markets.py`.
7. Comparativa UE (`ue`): from `eu_comparison.py` (unregistered).
8. Consumo (`consumo`): from `consumer.py`; decide whether to merge into Actividad.

Each page: reads dataset ids, series keys and field keys from `site/data/manifest.json` and the reconciliation table at the end of `docs/indicator-inventory.md` (which overrides the proposals above it); uses only the chart factory and loader from Phase 3; no inline Plotly config; every chart has title, unit, source and last-date caption taken from the JSON, not typed by hand.

Acceptance: page renders all its indicators from `site/data/`; no hard-coded numbers; checked at 375 px and 1440 px widths.

## Phase 5 — Automation and hosting (1 agent, after Phase 2, ~half day)

Owns: `.github/workflows/`, `docs/deploy.md`.

- `refresh-data.yml`: cron (weekday mornings, Europe/Madrid), runs `run_pipeline.py` then `export_site_data.py` then `validate_contract.py`, commits `site/data/` if changed. Fails loudly (issue or email) on validator failure; does not commit partial data.
- `deploy.yml`: publishes `site/` to GitHub Pages on push to `main`.
- Decide whether `data/raw/` and `data/processed/` stay gitignored (recommended: yes; only `site/data/` is committed).

Acceptance: a scheduled run completes and the public URL serves fresh data.

## Phase 6 — Cut-over and cleanup (1 agent, last)

Owns: everything.

- Delete `src/app/`, `serve.py`, `.env`, `.env.example`, `docs/sharing-setup.md`, `Circulo_Empresarios_white_outlined.png` (if moved to `site/assets/`), `layout.md`.
- Remove `shiny`, `shinywidgets`, `uvicorn`, `plotly` (Python) from `requirements.txt` if no longer imported.
- Rewrite `claude.md` (project status, real directory structure, real sources: INE, Eurostat, BdE, Yahoo; no FRED, no `config/`). Write `README.md`.
- Update `content.md` to match the manifest or delete it in favour of `docs/indicator-inventory.md`.

Acceptance: smoke test and validator pass; repo contains no reference to Shiny.

## Dependency graph

```
P0 ─► P1 ─┬─► P2 (ine | eurostat | bde | yahoo) ─┬─► P5 ─► P6
          └─► P3 ───────────────────────────────┴─► P4 (×8) ─┘
```

P2 and P3 run in parallel. P4 pages start as soon as P3 and their source(s) in P2 are merged. P5 needs all of P2. P6 needs everything.

## Open decisions (owner: project lead)

- Keep Consumo as its own page or fold into Actividad.
- Whether US data (FRED) is in scope for v1. Currently no fetcher exists; `content.md` lists it. Recommendation: out of scope for the migration, add later as a fifth source under the same contract.
- Domain: `username.github.io/CdE-Dashboard-v1` vs a subdomain of circulodeempresarios.org (needs DNS from whoever manages the site).
