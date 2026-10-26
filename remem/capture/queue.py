"""Ingest queue + worker thread (architecture.md → Process model).

When the queue is full, the OLDEST queued frame falls out (marked dropped; JPEG + row kept, never
embedded). The newest frame is never dropped. The worker hands up to EMBED_BATCH records to index.add.
"""

import logging
import threading
from collections import deque

from remem import config, index
from remem.capture import store
from remem.contracts import FrameRecord

log = logging.getLogger(__name__)
_q: deque[FrameRecord] = deque()
_cv = threading.Condition()
_stop = threading.Event()
_worker: threading.Thread | None = None


def put(rec: FrameRecord, block: bool = False) -> None:
    """Live: drop the oldest queued frame when full. Replay (block=True): wait for room, never drop."""
    with _cv:
        if block:
            _cv.wait_for(lambda: len(_q) < config.INGEST_QUEUE_MAX)
        elif len(_q) >= config.INGEST_QUEUE_MAX:
            store.mark_dropped(_q.popleft().id)
        _q.append(rec)
        _cv.notify_all()  # all: the worker and a blocked replay put share this condition


def depth() -> int:
    return len(_q)


def _run() -> None:
    while not _stop.is_set():
        with _cv:
            _cv.wait_for(lambda: _q or _stop.is_set())
            batch = [_q.popleft() for _ in range(min(len(_q), config.EMBED_BATCH))]
            _cv.notify_all()  # wake a replay put waiting for room
        if batch:
            try:
                index.add(batch)
            except Exception:  # ingest never dies; the index marks its own failures
                log.exception("index.add failed for ids %d..%d", batch[0].id, batch[-1].id)


def start_worker() -> None:
    global _worker
    _stop.clear()
    _worker = threading.Thread(target=_run, name="ingest", daemon=True)
    _worker.start()


def stop_worker() -> None:
    _stop.set()
    with _cv:
        _cv.notify_all()
    if _worker is not None:
        _worker.join(timeout=5)
