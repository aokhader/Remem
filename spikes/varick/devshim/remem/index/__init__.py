"""DEV SHIM for Daniel's remem.index — the stub exactly as context/contracts.md specifies.

Deterministic: no records or "passport" → []; "sunglasses" → newest record at
z 4.0 (Ask); anything else → newest at z 6.0 (Act) plus oldest at z 3.5.
Delete this shim once S0 is on main.
"""

from remem import config
from remem.contracts import (
    AddResult,
    Decision,
    FrameRecord,
    IndexStats,
    Moment,
    SearchHit,
    Verdict,
)

_records: list[FrameRecord] = []


def load() -> None:
    pass


def add(records: list[FrameRecord]) -> list[AddResult]:
    _records.extend(records)
    return [AddResult(frame_id=r.id, status="embedded", embed_ms=0.0) for r in records]


def _hit(r: FrameRecord, z: float, score: float) -> SearchHit:
    return SearchHit(
        frame_id=r.id, ts=r.ts, score=score, z=z, path=r.path,
        visit_start=r.ts, visit_end=r.ts, n_frames=1,
    )


def search(text: str, k: int = 10) -> list[SearchHit]:
    if not _records or "passport" in text:
        return []
    newest = max(_records, key=lambda r: r.ts)
    if "sunglasses" in text:
        return [_hit(newest, 4.0, 0.30)]
    hits = [_hit(newest, 6.0, 0.35)]
    if len(_records) >= 2:
        hits.append(_hit(min(_records, key=lambda r: r.ts), 3.5, 0.29))
    return hits[:k]


def decide(hits: list[SearchHit], verdicts: dict[int, Verdict] | None = None) -> Decision:
    if not hits:
        return Decision(band="none", hit=None)
    newest = hits[0]
    return Decision(band="act" if newest.z >= config.Z_ACT else "ask", hit=newest)


def recall(text: str) -> list[Moment]:
    return []


def stats() -> IndexStats:
    return IndexStats(
        backend="stub", dtype="stub", frames_indexed=len(_records), frames_dup=0,
        frames_failed=0, last_indexed_ts=max((r.ts for r in _records), default=None),
        embed_ms_p50=None,
    )
