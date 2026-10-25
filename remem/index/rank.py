"""Robust query-relative scores, merged visits, and newest-first retrieval."""

import numpy as np

from remem import config
from remem.contracts import FrameRecord, SearchHit


def robust_z(scores: np.ndarray) -> np.ndarray | None:
    """Return robust query-relative z, or None when MAD is zero."""
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 1 or not np.isfinite(scores).all():
        raise ValueError("Scores must be a finite vector")
    if not len(scores):
        return None
    center = np.median(scores)
    mad = np.median(np.abs(scores - center))
    if mad == 0:
        return None
    return (scores - center) / (1.4826 * mad)


def rank(records: list[FrameRecord], scores: np.ndarray, k: int = 10, *,
         z_min: float | None = None) -> list[SearchHit]:
    """Merge every qualifying frame before limiting the number of newest visits."""
    scores = np.asarray(scores, dtype=np.float64)
    if scores.shape != (len(records),) or not np.isfinite(scores).all():
        raise ValueError("Scores must be a finite vector aligned with frame records")
    if len(records) < config.MIN_FRAMES or not records or k <= 0:
        return []
    z = robust_z(scores)
    if z is None:
        return []
    candidates = sorted(
        (int(i) for i in np.flatnonzero(z >= (config.Z_MIN if z_min is None else z_min))),
        key=lambda i: (records[i].ts, records[i].id),
    )
    visits: list[list[int]] = []
    for i in candidates:
        if not visits or records[i].ts - records[visits[-1][-1]].ts >= config.VISIT_GAP_S:
            visits.append([i])
        else:
            visits[-1].append(i)
    hits = []
    for visit in visits:
        # A tied peak uses the newer frame; visit bounds still cover all candidates.
        peak = max(visit, key=lambda i: (scores[i], records[i].ts, records[i].id))
        record = records[peak]
        hits.append(SearchHit(
            frame_id=record.id, ts=record.ts, path=record.path,
            score=float(scores[peak]), z=float(z[peak]),
            visit_start=records[visit[0]].ts, visit_end=records[visit[-1]].ts,
            n_frames=len(visit),
        ))
    return sorted(hits, key=lambda h: (h.visit_end, h.ts, h.frame_id), reverse=True)[:k]
