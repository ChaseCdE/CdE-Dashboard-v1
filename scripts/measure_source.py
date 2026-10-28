#!/usr/bin/env python3
"""
Measure one pipeline source: wall time, HTTP requests, bytes downloaded, raw bytes on
disk and peak memory, per step (fetch / process).

Instruments the HTTP layer once (requests.Session.send and, for yfinance,
curl_cffi.requests.Session.request) instead of every call site.

Usage:
    python scripts/measure_source.py ine [--steps fetch process] [--json out.json]

Bytes are the size of the decoded response body (len(response.content)); on-the-wire size
is smaller when the server compresses.
"""
import argparse
import importlib
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STATS = {"requests": 0, "bytes": 0, "hosts": Counter(), "status": Counter()}


def _count(url, status, body_len):
    from urllib.parse import urlparse
    STATS["requests"] += 1
    STATS["bytes"] += body_len
    STATS["hosts"][urlparse(str(url)).netloc] += 1
    STATS["status"][int(status)] += 1


def instrument():
    import requests
    orig_send = requests.Session.send

    def send(self, request, **kw):
        resp = orig_send(self, request, **kw)
        try:
            _count(request.url, resp.status_code, len(resp.content))
        except Exception:
            pass
        return resp
    requests.Session.send = send
    try:
        from curl_cffi import requests as cr
        orig_req = cr.Session.request

        def req(self, method, url, *a, **kw):
            resp = orig_req(self, method, url, *a, **kw)
            try:
                _count(url, resp.status_code, len(resp.content))
            except Exception:
                pass
            return resp
        cr.Session.request = req
    except ImportError:
        pass


def dir_bytes(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.exists() else 0


def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", choices=["ine", "eurostat", "bde", "yahoo"])
    ap.add_argument("--steps", nargs="+", default=["fetch", "process"])
    ap.add_argument("--json")
    args = ap.parse_args()
    instrument()
    import run_pipeline
    fetch_mod, proc_mod = run_pipeline.PIPELINE_MODULES[args.source]
    out = {"source": args.source}
    for step in args.steps:
        mod = fetch_mod if step == "fetch" else proc_mod
        STATS.update(requests=0, bytes=0, hosts=Counter(), status=Counter())
        t0 = time.time()
        ok = run_pipeline.run_step(mod, f"{step} {args.source}")
        out[step] = {
            "ok": ok, "seconds": round(time.time() - t0, 1),
            "requests": STATS["requests"], "mb_downloaded": round(STATS["bytes"] / 1e6, 2),
            "status": dict(STATS["status"]), "peak_rss_mb_cumulative": round(peak_mb(), 0),
        }
    out["raw_mb_on_disk"] = round(dir_bytes(ROOT / "data" / "raw" / args.source) / 1e6, 2)
    out["processed_mb_on_disk"] = round(dir_bytes(ROOT / "data" / "processed" / args.source) / 1e6, 2) \
        if (ROOT / "data" / "processed" / args.source).exists() else None
    print("\nMEASURE " + json.dumps(out))
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
