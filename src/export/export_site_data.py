#!/usr/bin/env python3
"""
Export data/processed/ to site/data/ following docs/data-contract.md.

site/data/ is rebuilt from scratch on every run: anything not declared in
src/export/registry.py disappears. The new tree is built in a temporary
directory and only swapped in if every dataset exports without error.

Usage:
    python -m src.export.export_site_data
    python -m src.export.export_site_data --only ine.cpi eurostat.hicp
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .core import PROCESSED_DIR, SITE_DATA_DIR, CONTRACT_VERSION, build_dataset, manifest_entry, now_utc
from .registry import DATASETS


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--only", nargs="+", help="Export only these dataset ids (does not rebuild the tree)")
    args = parser.parse_args(argv)

    ids = [d.id for d in DATASETS]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"[FAIL] duplicate dataset ids: {sorted(dupes)}")
        return 1

    generated_at = now_utc()
    selected = [d for d in DATASETS if not args.only or d.id in args.only]
    target = SITE_DATA_DIR if args.only else SITE_DATA_DIR.with_name("data.tmp")
    if not args.only and target.exists():
        shutil.rmtree(target)

    errors, entries = [], []
    for ds in selected:
        try:
            if ds.optional and not (PROCESSED_DIR / ds.csv).exists():
                previous = SITE_DATA_DIR / ds.path
                if not previous.exists():
                    print(f"  [SKIP] {ds.id}: no processed data and no previous file")
                    continue
                obj = json.loads(previous.read_text(encoding="utf-8"))
                obj["generated_at"] = generated_at  # staleness is then measured against today
                write_json(target / ds.path, obj)
                entries.append(manifest_entry(ds, obj))
                print(f"  [KEEP] {ds.id:<32} previous file kept (no processed data)  last={obj['last_observation']}")
                continue
            obj = build_dataset(ds, generated_at)
            write_json(target / ds.path, obj)
            entries.append(manifest_entry(ds, obj))
            n = sum(len(s["data"]) for s in obj["series"])
            print(f"  [OK] {ds.id:<32} {len(obj['series']):>3} series {n:>6} rows  last={obj['last_observation']}")
        except Exception as e:  # noqa: BLE001 - report every dataset
            errors.append(f"{ds.id}: {type(e).__name__}: {e}")
            print(f"  [FAIL] {ds.id}: {type(e).__name__}: {e}")

    if errors:
        print(f"\n{len(errors)} dataset(s) failed; site/data left unchanged." if not args.only else "")
        if not args.only and target.exists():
            shutil.rmtree(target)
        return 1

    if args.only:
        # Merge into existing manifest
        mpath = SITE_DATA_DIR / "manifest.json"
        existing = json.loads(mpath.read_text(encoding="utf-8"))["datasets"] if mpath.exists() else []
        by_id = {e["id"]: e for e in existing}
        by_id.update({e["id"]: e for e in entries})
        entries = [by_id[i] for i in ids if i in by_id]
    else:
        entries.sort(key=lambda e: ids.index(e["id"]))

    write_json(target / "manifest.json", {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at,
        "datasets": entries,
    })

    if not args.only:
        if SITE_DATA_DIR.exists():
            shutil.rmtree(SITE_DATA_DIR)
        target.rename(SITE_DATA_DIR)

    print(f"\nExported {len(entries)} dataset(s) to {SITE_DATA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
