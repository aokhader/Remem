"""Stub index (contracts.md → Functions): remembers every record, deterministic hits, no torch."""

import threading

from remem.contracts import AddResult, FrameRecord, IndexStats, Moment, SearchHit

_records: list[FrameRecord] = []
_lock = threading.Lock()


def load() -> None:
    pass


def add(records: list[FrameRecord]) -> list[AddResult]:
    with _lock:
        _records.extend(records)
    return [AddResult(frame_id=r.id, status="embedded", embed_ms=0.0) for r in records]


def _hit(r: FrameRecord, z: float, score: float) -> SearchHit:
    return SearchHit(frame_id=r.id, ts=r.ts, score=score, z=z, path=r.path,
                     visit_start=r.ts, visit_end=r.ts, n_frames=1)


def search(text: str, k: int = 10) -> list[SearchHit]:
    with _lock:
        recs = sorted(_records, key=lambda r: r.ts)
    if not recs or "passport" in text:
        return []
    if "sunglasses" in text:
        return [_hit(recs[-1], 4.0, 0.30)]
    hits = [_hit(recs[-1], 6.0, 0.35)]
    if len(recs) >= 2:
        hits.append(_hit(recs[0], 3.5, 0.29))
    return hits[:k]


def recall(text: str) -> list[Moment]:
    return []


def stats() -> IndexStats:
    with _lock:
        n = len(_records)
        last = max((r.ts for r in _records), default=None)
    return IndexStats(backend="stub", dtype="stub", frames_indexed=n, frames_dup=0, frames_failed=0,
                      last_indexed_ts=last, embed_ms_p50=0.0 if n else None)
