"""Capture slice (Aziz): R1 R2 R5 R12 R15. Facade: start_worker / stop_worker / status."""

import time

from remem import config, index
from remem.capture import queue, replay, store
from remem.capture.queue import start_worker, stop_worker
from remem.contracts import StatusSnapshot


def status() -> StatusSnapshot:
    now = time.time()
    received, dropped, last_id, last_ts = store.counts()
    lag = None if last_ts is None else now - last_ts
    job = replay.latest()
    if job is not None and job.state in ("queued", "running"):
        mode = "replaying"
    elif lag is None:
        mode = "idle"
    else:
        mode = "stalled" if lag >= config.STALL_S else "streaming"
    return StatusSnapshot(now=now, mode=mode, frames_received=received, frames_dropped=dropped,
                          last_frame_id=last_id, last_frame_ts=last_ts, ingest_lag_s=lag,
                          queue_depth=queue.depth(), index=index.stats(), replay=job)


__all__ = ["start_worker", "status", "stop_worker"]
