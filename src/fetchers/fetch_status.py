"""
Run-local record of fetch failures (audit H1).

Fetchers fall back to the previous download when a request fails or returns nothing,
so the site keeps working, but that must never look like a successful refresh.
run_pipeline.py records every failure the fetchers log (via a logging handler) in
data/.fetch_failures.jsonl, resets the file at the start of a run, and reports it in the
summary and exit code.
A file is used (not a module-level list) because fetchers are imported under two
package paths ("fetchers." and "src.fetchers.").
"""

import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / ".fetch_failures.jsonl"


def reset() -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text("", encoding="utf-8")


def record(source: str, target: str, reason: str) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "source": source, "target": str(target), "reason": reason,
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }, ensure_ascii=False) + "\n")


def read() -> list:
    if not STATUS_FILE.exists():
        return []
    return [json.loads(l) for l in STATUS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
