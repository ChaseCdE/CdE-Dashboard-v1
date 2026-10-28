#!/usr/bin/env python3
"""
Smoke test for the data pipeline.

Checks that:
  1. Every .py file under src/, scripts/ and the project root compiles.
  2. Every pipeline module (fetchers, processors, scripts, export) imports.
  3. Every CSV in data/processed/ loads and is non-empty.
  4. (--run-processors) Every process_* script runs on the cached raw data.
     This is the check that catches truncated code that is still valid
     syntax, e.g. `summary = processor.create_su` in b3a7e40, which compiles
     and only fails at runtime. It rewrites data/processed/ from data/raw/.

Never touches the network. Exit code 0 on success, 1 on any failure.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --run-processors
"""

import importlib
import py_compile
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

IMPORT_PACKAGES = ["src.fetchers", "src.processors", "src.scripts", "src.export"]


def check_compile() -> list[str]:
    errors = []
    files = list((ROOT / "src").rglob("*.py")) + list(ROOT.glob("*.py")) + list((ROOT / "scripts").glob("*.py"))
    for f in files:
        if "__pycache__" in f.parts:
            continue
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"compile: {f.relative_to(ROOT)}: {e.msg.strip().splitlines()[-1]}")
    return errors


def check_imports() -> list[str]:
    errors = []
    for pkg in IMPORT_PACKAGES:
        pkg_dir = ROOT / Path(*pkg.split("."))
        if not pkg_dir.exists():
            continue
        for f in sorted(pkg_dir.glob("*.py")):
            mod = f"{pkg}.{f.stem}" if f.stem != "__init__" else pkg
            try:
                importlib.import_module(mod)
            except Exception as e:  # noqa: BLE001 - report every failure
                errors.append(f"import: {mod}: {type(e).__name__}: {e}")
    return errors


def check_processed_csvs() -> list[str]:
    errors = []
    proc = ROOT / "data" / "processed"
    files = sorted(proc.rglob("*.csv"))
    if not files:
        return [f"data: no CSV files under {proc.relative_to(ROOT)} (run run_pipeline.py first)"]
    for f in files:
        try:
            df = pd.read_csv(f)
            if df.empty:
                errors.append(f"data: {f.relative_to(ROOT)} is empty")
        except Exception as e:  # noqa: BLE001
            errors.append(f"data: {f.relative_to(ROOT)}: {type(e).__name__}: {e}")
    return errors


def check_processors() -> list[str]:
    import contextlib
    import io

    errors = []
    for f in sorted((ROOT / "src" / "scripts").glob("process_*.py")):
        mod_name = f"src.scripts.{f.stem}"
        saved_argv = sys.argv
        sys.argv = [mod_name]
        try:
            mod = importlib.import_module(mod_name)
            with contextlib.redirect_stdout(io.StringIO()):
                mod.main()
        except BaseException as e:  # noqa: BLE001 - includes SystemExit
            errors.append(f"process: {mod_name}: {type(e).__name__}: {e}")
        finally:
            sys.argv = saved_argv
    return errors


def main() -> int:
    checks = [("compile", check_compile), ("imports", check_imports)]
    if "--run-processors" in sys.argv:
        checks.append(("processors on cached raw data", check_processors))
    checks.append(("processed CSVs", check_processed_csvs))
    failed = False
    for name, fn in checks:
        errs = fn()
        status = "OK" if not errs else f"FAIL ({len(errs)})"
        print(f"[{status}] {name}")
        for e in errs:
            print(f"    {e}")
        failed |= bool(errs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
