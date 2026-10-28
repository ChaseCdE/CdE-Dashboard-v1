# Agent: pipeline auditor

Purpose: independently determine whether the pipeline runs and whether every published dataset holds the right data with correct transformations. Read-only on pipeline code. Run on a strong model, without being told the authors' conclusions.

Isolation: its own git worktree and branch (`audit/pipeline`) with a copy of `data/`. It may only add `scripts/audit/` and `docs/audit/pipeline-audit.md`.

What it establishes, for every dataset in `site/data/manifest.json`:
1. **The pipeline runs:** full run exits 0; validator (strict) and smoke test pass; swallowed exceptions and silent cached fallbacks are identified.
2. **Identity:** the source identifier (INE table/series, Eurostat dataset and filters, BdE series code, Yahoo ticker) is what the labels say: geography, sector, unit, seasonal adjustment, base, nominal/real, stock/flow, end-of-period/average. (Past bugs of this kind: France/Italy 10Y were Finland/Portugal; retail sales was a sub-population; trade balance covered food only; the "2-year" bond was an over-2-years average.)
3. **Values:** latest ~24 observations re-fetched with independent code (not the project's fetchers) and compared; one headline figure per source checked against the official publication.
4. **Transformations:** every derived field recomputed independently (yoy/qoq/mom, *_pp, chg_*, *_diff, sum_12m, contributions, returns, spreads, rebasing).
5. **Dating and units:** period dating, local dates, scale, percent vs fraction, decimals, Spanish labels.
6. **Robustness:** revisions, gaps, duplicates, base changes, behaviour when an API fails.

Deliverables: re-runnable `scripts/audit/` (the project's regression oracle) and `docs/audit/pipeline-audit.md` with a verdict, severity-ranked findings (CRITICAL wrong number published; HIGH wrong label/unit/definition or silent staleness; MEDIUM fragility; LOW cosmetic) with evidence, root cause and recommended fix, and a coverage table for all datasets. Anything not checked is reported as "not verified".

The full prompt used on 2026-10-28 is recorded in the session; this file is the reusable specification.
