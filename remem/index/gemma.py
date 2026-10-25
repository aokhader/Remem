"""Local EG2 backend: serialized GPU calls and durable float32 embeddings."""

import logging
import os
import sqlite3
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Any

import numpy as np
from PIL import Image, ImageOps

from remem import config
from remem.contracts import AddResult, FrameRecord, IndexStats, Moment, SearchHit
from remem.index.rank import rank

_log = logging.getLogger(__name__)
_local = threading.local()
_gpu_lock = threading.Lock()
_state_lock = threading.RLock()
_load_lock = threading.Lock()
_add_lock = threading.Lock()
_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="remem-embed")
# At most one running call and one queued call. Timed-out kernels retain their slot
# until completion; no unbounded GPU queue or late writes to SQLite/the matrix.
_slots = threading.BoundedSemaphore(2)
_model: Any = None
_dtype = "unloaded"
_records: list[FrameRecord] = []
_matrix = np.empty((0, 768), dtype=np.float32)
_samples: deque[float] = deque(maxlen=256)
_dup = 0
_failed = 0

_SCHEMA = """
CREATE TABLE IF NOT EXISTS embeddings (
  frame_id INTEGER PRIMARY KEY REFERENCES frames(id),
  status TEXT NOT NULL CHECK (status IN ('embedded','dup','failed')),
  dup_of INTEGER,
  vec BLOB,
  model TEXT NOT NULL,
  image_tokens INTEGER,
  embed_ms REAL
);
"""


def _conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(config.DATA_DIR / "remem.db", timeout=5)
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
        _local.conn.executescript(_SCHEMA)
    return _local.conn


def _normalize(vectors: Any) -> np.ndarray:
    array = np.asarray(vectors, dtype=np.float32)
    if array.ndim == 1:
        array = array[None, :]
    if array.ndim != 2 or array.shape[1] != 768 or not np.isfinite(array).all():
        raise ValueError("Expected finite 768-dimensional embeddings")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if np.any(norms == 0) or not np.isfinite(norms).all():
        raise ValueError("Zero or invalid embedding norm")
    return array / norms


def _rebuild() -> None:
    """Caller holds state lock; never re-embed persisted records."""
    global _records, _matrix, _dup, _failed
    conn = _conn()
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='frames'").fetchone():
        _records, _matrix = [], np.empty((0, 768), dtype=np.float32)
        _dup = _failed = 0
        return
    rows = conn.execute("""
        SELECT f.id, f.ts, f.client_ts, f.path, f.source, e.vec, e.model, e.image_tokens
        FROM embeddings e JOIN frames f ON f.id=e.frame_id
        WHERE e.status='embedded' ORDER BY f.ts, f.id
    """).fetchall()
    records, vectors = [], []
    for fid, ts, client_ts, path, source, blob, model, tokens in rows:
        if model != config.EMBED_MODEL or tokens != config.EMBED_IMAGE_TOKENS:
            raise ValueError("Stored embeddings use a different model/image budget; use a fresh DATA_DIR")
        if blob is None or len(blob) != 768 * 4:
            raise ValueError(f"Invalid stored embedding for frame {fid}")
        vector = np.frombuffer(blob, dtype="<f4").copy()
        if not np.isfinite(vector).all() or not np.isclose(np.linalg.norm(vector), 1, atol=1e-4):
            raise ValueError(f"Invalid stored embedding norm for frame {fid}")
        records.append(FrameRecord(id=fid, ts=ts, client_ts=client_ts, path=path, source=source))
        vectors.append(vector)
    _records = records
    _matrix = np.stack(vectors) if vectors else np.empty((0, 768), dtype=np.float32)
    counts = dict(conn.execute("SELECT status, COUNT(*) FROM embeddings GROUP BY status"))
    _dup, _failed = counts.get("dup", 0), counts.get("failed", 0)


def load() -> None:
    global _model, _dtype
    if config.EMBED_DTYPE not in ("auto", "bfloat16", "float32"):
        raise ValueError("Never float16: use auto, bfloat16, or float32")
    if config.EMBED_BATCH < 1:
        raise ValueError("EMBED_BATCH must be positive")
    if not np.isfinite(config.DEDUPE_COS) or not -1 <= config.DEDUPE_COS <= 1:
        raise ValueError("DEDUPE_COS must be finite and between -1 and 1")
    with _load_lock:
        if _model is None:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
            os.environ["DO_NOT_TRACK"] = "1"
            import torch
            from sentence_transformers import SentenceTransformer

            supported = torch.cuda.is_bf16_supported()
            _dtype = config.EMBED_DTYPE
            if _dtype == "auto":
                _dtype = "bfloat16" if supported else "float32"
            if _dtype == "bfloat16" and not supported:
                raise ValueError("bfloat16 requested but not supported; select float32")
            dtype = torch.bfloat16 if _dtype == "bfloat16" else torch.float32
            _log.info("embed bf16_supported=%s dtype=%s", supported, _dtype)
            model = SentenceTransformer(
                config.EMBED_MODEL, device="cuda" if torch.cuda.is_available() else "cpu",
                local_files_only=True, config_kwargs={"audio_config": None},
                model_kwargs={"torch_dtype": dtype},
            )
            if any(parameter.dtype == torch.float16 for parameter in model.parameters()):
                raise ValueError("float16 parameters are forbidden")
            _model = model
        with _state_lock:
            _rebuild()
    _log.info("index loaded frames=%d dtype=%s", len(_records), _dtype)


def _encode(inputs: Any, timeout: float, **kwargs: Any) -> np.ndarray:
    """Timeout includes admission, queue wait, preprocessing, GPU, and conversion."""
    if _model is None:
        raise RuntimeError("Call index.load() before embedding")
    started = perf_counter()
    if not _slots.acquire(timeout=timeout):
        raise TimeoutError("GPU busy")

    def run() -> np.ndarray:
        with _gpu_lock:
            return _normalize(_model.encode(
                inputs, normalize_embeddings=True, show_progress_bar=False, **kwargs
            ))

    try:
        future = _worker.submit(run)
    except BaseException:
        _slots.release()
        raise
    future.add_done_callback(lambda _: _slots.release())
    try:
        return future.result(timeout=max(0, timeout - (perf_counter() - started)))
    except TimeoutError:
        future.cancel()  # running kernels finish, but their result has no state-writing callback
        raise


def _persist(results: list[AddResult], vectors: dict[int, np.ndarray]) -> None:
    with _state_lock:
        with _conn() as conn:
            conn.executemany("""
                INSERT INTO embeddings (frame_id, status, dup_of, vec, model, image_tokens, embed_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(frame_id) DO UPDATE SET status=excluded.status, dup_of=excluded.dup_of,
                    vec=excluded.vec, model=excluded.model, image_tokens=excluded.image_tokens,
                    embed_ms=excluded.embed_ms
            """, [(
                r.frame_id, r.status, r.dup_of,
                vectors[r.frame_id].astype("<f4").tobytes() if r.frame_id in vectors else None,
                config.EMBED_MODEL, config.EMBED_IMAGE_TOKENS, r.embed_ms,
            ) for r in results])
        _rebuild()


def add(records: list[FrameRecord]) -> list[AddResult]:
    # Keep comparison + persistence ordered across concurrent ingest callers.
    with _add_lock:
        return _add(records)


def _deduplicate(
    records: list[FrameRecord], results: list[AddResult], vectors: dict[int, np.ndarray],
) -> None:
    """Compare with the last kept frame, never a discarded intermediate frame.

    Older/backfilled records are retained rather than matched to a future frame.
    Capture timestamps and JPEGs remain owned by the frame store.
    Caller holds the state lock through persistence.
    """
    last = _records[-1] if _records else None
    vector = _matrix[-1] if _records else None
    by_id = {result.frame_id: result for result in results}
    for record in sorted(records, key=lambda row: (row.ts, row.id)):
        if record.id not in vectors:
            continue
        current = vectors[record.id]
        newer = last is None or (record.ts, record.id) > (last.ts, last.id)
        if newer and vector is not None and float(current @ vector) >= config.DEDUPE_COS:
            result = by_id[record.id]
            result.status, result.dup_of = "dup", last.id
            del vectors[record.id]
        elif newer:
            last, vector = record, current


def _add(records: list[FrameRecord]) -> list[AddResult]:
    if _model is None:
        raise RuntimeError("Call index.load() before add()")
    results = []
    for offset in range(0, len(records), config.EMBED_BATCH):
        batch = records[offset:offset + config.EMBED_BATCH]
        images, valid, batch_results = [], [], []
        for record in batch:
            try:
                path = (config.DATA_DIR / record.path).resolve()
                if not path.is_relative_to(config.DATA_DIR.resolve()):
                    raise ValueError("Frame path must stay inside DATA_DIR")
                with Image.open(path) as image:
                    images.append({"image": ImageOps.exif_transpose(image).convert("RGB")})
                valid.append(record)
            except (OSError, ValueError):
                _log.exception("embed unreadable frame_id=%d", record.id)
                batch_results.append(AddResult(frame_id=record.id, status="failed"))
        vectors = {}
        if valid:
            started = perf_counter()
            try:
                encoded = _encode(
                    images, timeout=5.0, batch_size=config.EMBED_BATCH, prompt="",
                    processing_kwargs={"image": {"max_soft_tokens": config.EMBED_IMAGE_TOKENS}},
                )
                if len(encoded) != len(valid):
                    raise ValueError("Unexpected embedding batch length")
                elapsed_ms = (perf_counter() - started) * 1000
                per_frame = elapsed_ms / len(valid)
                batch_results.extend(AddResult(frame_id=r.id, status="embedded", embed_ms=per_frame) for r in valid)
                vectors = {r.id: vector for r, vector in zip(valid, encoded, strict=True)}
                with _state_lock:
                    _samples.append(per_frame)
            except Exception:
                _log.exception("embed batch=%d failed", len(valid))
                batch_results.extend(AddResult(frame_id=r.id, status="failed") for r in valid)
        with _state_lock:
            _deduplicate(batch, batch_results, vectors)
            _persist(batch_results, vectors)
        _log.info("embed batch=%d embed_ms=%.2f dup=%d failed=%d", len(batch),
                  sum(r.embed_ms or 0 for r in batch_results),
                  sum(r.status == "dup" for r in batch_results),
                  sum(r.status == "failed" for r in batch_results))
        by_id = {r.frame_id: r for r in batch_results}
        results.extend(by_id[r.id] for r in batch)
    return results


def score_frames(text: str) -> tuple[list[FrameRecord], np.ndarray]:
    """Local evaluator snapshot: same query encode and scores as search, no cutoff."""
    with _state_lock:
        records, matrix = _records, _matrix
    if not records:
        return records, np.array([], dtype=np.float32)
    query = _encode(text, timeout=2.0, prompt_name="SearchQuery")[0]
    return records, matrix @ query


def search(text: str, k: int = 10) -> list[SearchHit]:
    with _state_lock:
        records = _records
    if len(records) < config.MIN_FRAMES or not records or k <= 0:
        return []
    started = perf_counter()
    records, scores = score_frames(text)
    embedded = perf_counter()
    hits = rank(records, scores, min(k, config.TOP_K))
    _log.info("search embed_ms=%.2f rank_ms=%.2f hits=%d", (embedded - started) * 1000,
              (perf_counter() - embedded) * 1000, len(hits))
    return hits


def recall(text: str) -> list[Moment]:
    return []  # R13 remains gated behind demo rows 1–4.


def stats() -> IndexStats:
    with _state_lock:
        return IndexStats(
            backend="gemma", dtype=_dtype, frames_indexed=len(_records), frames_dup=_dup, frames_failed=_failed,
            last_indexed_ts=_records[-1].ts if _records else None,
            embed_ms_p50=median(_samples) if _samples else None,
        )


def smoke(paths: list[Path]) -> dict[str, Any]:
    """Small-folder GPU diagnostic; bypasses retrieval guards without persisting data."""
    images = []
    for path in paths:
        with Image.open(path) as image:
            images.append({"image": ImageOps.exif_transpose(image).convert("RGB")})
    kwargs = {
        "prompt": "", "batch_size": 1,
        "processing_kwargs": {"image": {"max_soft_tokens": config.EMBED_IMAGE_TOKENS}},
    }
    _encode(images[0], timeout=5.0, **kwargs)
    samples = []
    for _ in range(5):
        started = perf_counter()
        _encode(images[0], timeout=5.0, **kwargs)
        samples.append((perf_counter() - started) * 1000)
    matrix = _encode(images, timeout=5.0, **kwargs)
    query = _encode("a photo of keys", timeout=2.0, prompt_name="SearchQuery")[0]
    scores = matrix @ query
    return {
        "dtype": _dtype, "image_tokens": config.EMBED_IMAGE_TOKENS,
        "warm_embed_ms_median": median(samples), "warm_samples_ms": samples,
        "ranking": [{"photo": paths[i].name, "cosine": float(scores[i])}
                    for i in np.argsort(-scores, kind="stable")],
        "note": "Diagnostic cosine ranking only; production search retains MIN_FRAMES/MAD/z guards",
    }
