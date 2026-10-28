"""
Shared HTTP layer for the fetchers.

- One pooled `requests.Session` per source (connection reuse, keep-alive).
- Retries with exponential backoff on connection errors and on 429 / 500 / 502 / 503 / 504,
  honouring `Retry-After`.
- A default timeout on every request (connect 10 s, read 60 s), so a hung server cannot
  block the pipeline.
- `map_bounded`: run a function over many items with a small, bounded number of worker
  threads (polite concurrency per host) and collect results or exceptions per item.

Retry exhaustion raises, as before; callers decide whether that is fatal (they log it, so
run_pipeline.py reports the source as not refreshed, audit H1).
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (10, 60)  # (connect, read) seconds
RETRY_STATUS = (429, 500, 502, 503, 504)


class Session(requests.Session):
    """requests.Session with a default timeout."""

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        super().__init__()
        self._default_timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self._default_timeout)
        return super().request(method, url, **kwargs)


def make_session(
    user_agent: str = "CdE-Dashboard/1.0",
    headers: Optional[dict] = None,
    retries: int = 3,
    backoff: float = 1.0,
    pool_size: int = 8,
    timeout=DEFAULT_TIMEOUT,
    methods: Tuple[str, ...] = ("GET", "HEAD"),
) -> Session:
    """
    Session with pooled connections and retry/backoff.

    `backoff` is urllib3's backoff_factor: sleeps backoff * 2**(n-1) seconds between retries
    (1 s, 2 s, 4 s with the defaults), or the server's Retry-After when it sends one.
    """
    session = Session(timeout=timeout)
    retry = Retry(
        total=retries, connect=retries, read=retries, status=retries,
        backoff_factor=backoff, status_forcelist=RETRY_STATUS,
        allowed_methods=frozenset(methods), respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_size, pool_maxsize=pool_size)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": user_agent})
    if headers:
        session.headers.update(headers)
    return session


class CircuitBreaker:
    """
    Stop hammering a host that is down.

    After `threshold` consecutive failures (with no success in between) every further call
    to `check()` raises, so an outage costs seconds instead of (requests x retries x backoff).
    """

    def __init__(self, threshold: int = 8):
        self.threshold = threshold
        self._fails = 0
        self._lock = threading.Lock()

    def check(self) -> None:
        if self._fails >= self.threshold:
            raise ConnectionError(f"skipped: {self._fails} consecutive requests failed, host assumed down")

    def success(self) -> None:
        with self._lock:
            self._fails = 0

    def failure(self) -> None:
        with self._lock:
            self._fails += 1


def map_bounded(fn: Callable, items: Iterable, max_workers: int = 4) -> List[Tuple[object, Optional[BaseException]]]:
    """
    Apply `fn` to every item with at most `max_workers` threads.

    Returns a list, in the order of `items`, of (result, None) or (None, exception).
    Exceptions never escape, so one failing item does not hide the others.
    """
    items = list(items)

    def call(item):
        try:
            return fn(item), None
        except Exception as exc:  # noqa: BLE001 - reported per item by the caller
            return None, exc

    if max_workers <= 1 or len(items) <= 1:
        return [call(i) for i in items]
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(call, items))
