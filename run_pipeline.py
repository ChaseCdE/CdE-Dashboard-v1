#!/usr/bin/env python3
"""
CdE Dashboard — Full Pipeline Runner

Runs the complete data pipeline: fetch → process → export → validate → (optionally) serve.

Export writes site/data/ (docs/data-contract.md); validate runs
scripts/validate_contract.py. A validation error makes the run exit non-zero.

Usage:
    python run_pipeline.py                  # fetch + process + export + validate all sources
    python run_pipeline.py --no-export      # stop after processing
    python run_pipeline.py --serve          # fetch + process + start dashboard
    python run_pipeline.py --process-only   # skip fetching, just reprocess cached data
    python run_pipeline.py --sources ine yahoo  # only run specific sources
    python run_pipeline.py --serve-only     # just start the dashboard server
"""

import argparse
import importlib
import sys
import time
import traceback
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

ALL_SOURCES = ["ine", "eurostat", "bde", "yahoo"]

# Map source -> (fetch module path, process module path)
PIPELINE_MODULES = {
    "ine": (
        "src.scripts.fetch_ine_data",
        "src.scripts.process_ine_data",
    ),
    "eurostat": (
        "src.scripts.fetch_eurostat_data",
        "src.scripts.process_eurostat_data",
    ),
    "bde": (
        "src.scripts.fetch_bde_data",
        "src.scripts.process_bde_data",
    ),
    "yahoo": (
        "src.scripts.fetch_yahoo_data",
        "src.scripts.process_yahoo_data",
    ),
}


def run_step(module_path: str, label: str) -> bool:
    """
    Run a pipeline step by importing and calling its main().
    Returns True on success, False on failure.
    """
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        mod = importlib.import_module(module_path)
        # Reset argv so argparse-based scripts don't choke
        saved_argv = sys.argv
        sys.argv = [module_path]
        try:
            mod.main()
        finally:
            sys.argv = saved_argv
        elapsed = time.time() - t0
        print(f"  [OK] {label} completed in {elapsed:.1f}s")
        return True
    except Exception:
        elapsed = time.time() - t0
        print(f"  [FAIL] {label} FAILED after {elapsed:.1f}s")
        traceback.print_exc()
        return False


def run_fetch(sources: list[str]) -> dict[str, bool]:
    """Run fetch step for each source. Returns dict of source -> success."""
    results = {}
    for src in sources:
        fetch_mod, _ = PIPELINE_MODULES[src]
        ok = run_step(fetch_mod, f"FETCH {src.upper()}")
        results[src] = ok
    return results


def run_process(sources: list[str]) -> dict[str, bool]:
    """Run process step for each source. Returns dict of source -> success."""
    results = {}
    for src in sources:
        _, proc_mod = PIPELINE_MODULES[src]
        ok = run_step(proc_mod, f"PROCESS {src.upper()}")
        results[src] = ok
    return results


def run_export_and_validate() -> bool:
    """Rebuild site/data/ from data/processed/ and validate it. Returns True if valid."""
    import subprocess

    print(f"\n{'='*60}")
    print("  EXPORT site/data")
    print(f"{'='*60}")
    from src.export import export_site_data
    if export_site_data.main([]) != 0:
        print("  [FAIL] export failed; site/data left unchanged")
        return False

    print(f"\n{'='*60}")
    print("  VALIDATE site/data")
    print(f"{'='*60}")
    sys.stdout.flush()
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "validate_contract.py")])
    return result.returncode == 0


def run_serve():
    """Start the dashboard server."""
    print(f"\n{'='*60}")
    print("  STARTING DASHBOARD SERVER")
    print(f"{'='*60}")
    import serve
    serve.main()


def print_summary(fetch_results: dict, process_results: dict):
    """Print a final summary table."""
    print(f"\n{'='*60}")
    print("  PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Source':<12} {'Fetch':<12} {'Process':<12}")
    print(f"  {'-'*36}")

    all_sources = set(list(fetch_results.keys()) + list(process_results.keys()))
    for src in ALL_SOURCES:
        if src not in all_sources:
            continue
        f = fetch_results.get(src)
        p = process_results.get(src)
        f_str = "[OK]" if f else ("[FAIL]" if f is not None else "-")
        p_str = "[OK]" if p else ("[FAIL]" if p is not None else "-")
        print(f"  {src.upper():<12} {f_str:<12} {p_str:<12}")

    total_ok = sum(1 for v in process_results.values() if v)
    total = len(process_results)
    print(f"\n  Processed: {total_ok}/{total} sources successful")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="CdE Dashboard — Full Pipeline Runner"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=ALL_SOURCES,
        default=ALL_SOURCES,
        help="Sources to run (default: all)"
    )
    parser.add_argument(
        "--process-only",
        action="store_true",
        help="Skip fetching, only process cached raw data"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the dashboard server after pipeline completes"
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip exporting and validating site/data"
    )
    parser.add_argument(
        "--serve-only",
        action="store_true",
        help="Skip pipeline, just start the dashboard server"
    )
    args = parser.parse_args()

    if args.serve_only:
        run_serve()
        return

    t_start = time.time()
    fetch_results = {}
    process_results = {}

    # Fetch
    if not args.process_only:
        fetch_results = run_fetch(args.sources)
    else:
        print("\n  Skipping fetch (--process-only)")

    # Process
    process_results = run_process(args.sources)

    # Export + validate
    export_ok = True
    if not args.no_export:
        export_ok = run_export_and_validate()

    # Summary
    elapsed_total = time.time() - t_start
    print_summary(fetch_results, process_results)
    if not args.no_export:
        print(f"  site/data export + validation: {'[OK]' if export_ok else '[FAIL]'}")
    print(f"  Total time: {elapsed_total:.1f}s\n")

    # Serve
    if args.serve:
        run_serve()

    if not export_ok or not all(process_results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
