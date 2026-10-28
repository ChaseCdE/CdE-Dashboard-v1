#!/usr/bin/env python3
"""
Regression oracle for site/data (independent of src/).

    python scripts/audit/check_all.py              # all checks, needs network
    python scripts/audit/check_all.py --offline    # only check_transforms (no network)
    python scripts/audit/check_all.py --coverage   # also print a per-dataset coverage table (markdown)

Exit code 1 if any check FAILs. WARN does not fail the run.
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, manifest  # noqa: E402

import check_bde  # noqa: E402
import check_cross  # noqa: E402
import check_eurostat  # noqa: E402
import check_ine  # noqa: E402
import check_transforms  # noqa: E402
import check_yahoo  # noqa: E402

ORDER = {"FAIL": 3, "WARN": 2, "PASS": 1, "SKIP": 0}


def coverage(rep: Report) -> str:
    ids = [e["id"] for e in manifest()["datasets"]]
    cols = ["identity", "values", "transform", "cross", "dating", "meta"]
    out = ["| Dataset | " + " | ".join(cols) + " | Result |", "|---|" + "---|" * (len(cols) + 1)]
    for i in ids:
        rows = [r for r in rep.rows if r.ds == i]
        cells = []
        for c in cols:
            st = [r.status for r in rows if r.check == c]
            cells.append(max(st, key=lambda s: ORDER[s]) if st else "-")
        worst = max((r.status for r in rows), key=lambda s: ORDER[s], default="NOT CHECKED")
        out.append(f"| {i} | " + " | ".join(cells) + f" | {worst} |")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    args = ap.parse_args(argv)
    rep = Report()
    mods = [check_transforms] if args.offline else [check_ine, check_eurostat, check_bde, check_yahoo, check_cross, check_transforms]
    for m in mods:
        try:
            m.run(rep)
        except Exception as e:  # noqa: BLE001 - a module that cannot run is a failure, not a pass
            rep.add(m.__name__, "error", "FAIL", f"{type(e).__name__}: {e}")
            traceback.print_exc()
    rows = sorted(rep.rows, key=lambda r: -ORDER[r.status])
    rep.rows = rows
    rep.print()
    if args.coverage:
        print()
        print(coverage(rep))
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
