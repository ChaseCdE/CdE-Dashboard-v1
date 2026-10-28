# Agent: pipeline optimizer

Purpose: make fetching and processing as efficient and robust as possible **without changing any published number**, from a data-management perspective. Run after the pipeline auditor (`docs/agents/pipeline-auditor.md`), whose scripts in `scripts/audit/` are the regression oracle.

Model: a strong coding model is not required for every step, but the equivalence harness is mandatory. Isolation: its own git worktree and branch (`opt/pipeline`), its own copy of `data/`.

## Baseline (before any change)
1. Full run per source; record for each source and step: wall time, number of HTTP requests, bytes downloaded, raw bytes on disk, peak memory (`/usr/bin/time -v` or `tracemalloc`), rows per raw file vs rows actually used downstream.
2. Snapshot `data/processed/` and `site/data/` (copy outside the repo) as the golden output.

## Equivalence rule
After every change: rerun the affected source and compare against the golden output.
- `site/data/*.json`: identical except `generated_at` (and values for periods published after the baseline run, if the run date differs: then compare the overlapping history only).
- `data/processed/*.csv`: identical values for all columns that feed `src/export/*` (other columns may be dropped if unused, documented).
- `scripts/validate_contract.py --strict`, `scripts/smoke_test.py --run-processors` and `scripts/audit/` checks pass.
A change that alters a published value is either reverted or, if it fixes a bug confirmed by the audit report, made in a **separate commit** that names the audit finding.

## Areas to evaluate (measure first; implement what pays off)
- **Fetch only what is used.** INE: request series by code (`DATOS_SERIE`) or filtered tables instead of whole `DATOS_TABLA` downloads that are then filtered by series *name* regex (39 MB of raw INE CSVs today; name matching broke twice when INE renamed series). Define each indicator by stable identifiers, with a check that fails loudly when an identifier disappears.
- **Requests.** One `requests.Session` per source with retries and exponential backoff on 429/5xx, sane timeouts, polite bounded concurrency (e.g. 3 to 4 workers per host) instead of a fixed sleep between sequential calls. Yahoo: batch download (`yf.download` with multiple tickers) if it gives identical data. BdE and Eurostat: confirm batching and server-side filters are used everywhere.
- **Revision-aware incremental fetching.** Official data are revised: if a source is fetched incrementally, re-fetch a revision window (e.g. last 24 months / 8 quarters / 3 years) and replace it; full history refetch only on a schedule or when metadata (base year, unit) changes. Only adopt if it is demonstrably identical to a full refetch.
- **Storage.** Raw layer: keep only the columns and series needed, typed; consider Parquet only if the dependency cost is justified by measured gains. Avoid rewriting unchanged files.
- **Processing.** Load each raw file once; replace bespoke per-indicator code with a small set of tested, vectorised helpers (date-based yoy/qoq/mom, differences in pp, rolling 12-month sums with completeness check, rebasing) driven by indicator definitions; remove dead code and unused processed outputs.
- **Failure semantics.** A source that fails must not silently publish stale data as fresh: keep the cached fallback but make it visible (log, run summary, staleness in the JSON).
- **CI.** Keep `.github/workflows/refresh-data.yml` working; total run time and data cache size should go down.

## Deliverables
- Code changes on `opt/pipeline`, small focused commits, each with before/after numbers.
- `docs/optimization/pipeline-optimization.md`: baseline vs after table (time, requests, bytes, disk, memory per source), what changed, what was evaluated and rejected and why, equivalence evidence.
- Unit tests for the shared transformation helpers (`tests/`, pytest-style but runnable with plain `python -m unittest` if pytest is not installed).
