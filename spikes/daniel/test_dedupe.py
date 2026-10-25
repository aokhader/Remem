"""R4 persistence and last-kept semantics, using controlled normalized vectors."""

import sqlite3
import threading
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from remem import config
from remem.contracts import FrameRecord
from remem.index import gemma


def direction(angle: float) -> np.ndarray:
    vector = np.zeros(768, dtype=np.float32)
    vector[:2] = np.cos(angle), np.sin(angle)
    return vector


@pytest.fixture
def backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[FrameRecord]:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DEDUPE_COS", 0.98)
    monkeypatch.setattr(config, "EMBED_BATCH", 8)
    monkeypatch.setattr(gemma, "_local", threading.local())
    monkeypatch.setattr(gemma, "_records", [])
    monkeypatch.setattr(gemma, "_matrix", np.empty((0, 768), dtype=np.float32))
    monkeypatch.setattr(gemma, "_dup", 0)
    monkeypatch.setattr(gemma, "_failed", 0)
    monkeypatch.setattr(gemma, "_model", object())
    records = [FrameRecord(id=i, ts=float(i), client_ts=None,
                           path=f"frames/{i:06d}.jpg", source="replay") for i in range(1, 6)]
    (tmp_path / "frames").mkdir()
    with sqlite3.connect(tmp_path / "remem.db") as conn:
        conn.execute("CREATE TABLE frames (id INTEGER PRIMARY KEY, ts REAL, client_ts REAL, path TEXT, source TEXT)")
        for rec in records:
            conn.execute("INSERT INTO frames VALUES (?, ?, NULL, ?, ?)", (rec.id, rec.ts, rec.path, rec.source))
            Image.new("RGB", (16, 16), "white").save(tmp_path / rec.path)
    yield records
    if hasattr(gemma._local, "conn"):
        gemma._local.conn.close()


def test_drift_compares_last_kept_and_persists(backend: list[FrameRecord], monkeypatch: pytest.MonkeyPatch) -> None:
    # Adjacent steps are duplicates, but step 3 differs enough from the kept step 1.
    vectors = np.stack([direction(0), direction(0.15), direction(0.30), direction(0.30)])
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: vectors)
    results = gemma.add(backend[:4])
    assert [r.status for r in results] == ["embedded", "dup", "embedded", "dup"]
    assert [r.dup_of for r in results] == [None, 1, None, 3]
    assert gemma._conn().execute(
        "SELECT frame_id, dup_of, vec FROM embeddings WHERE status='dup' ORDER BY frame_id"
    ).fetchall() == [(2, 1, None), (4, 3, None)]
    assert [r.id for r in gemma._records] == [1, 3]
    assert gemma.stats().frames_dup == 2
    # Simulated restart: no encode, same matrix, counters and last-kept anchor.
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: pytest.fail("restart must not encode"))
    gemma.load()
    assert [r.id for r in gemma._records] == [1, 3]
    assert gemma.stats().frames_dup == 2
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: np.stack([direction(0.30)]))
    result, = gemma.add(backend[4:])
    assert (result.status, result.dup_of) == ("dup", 3)
    assert gemma._conn().execute("SELECT ts FROM frames ORDER BY id").fetchall() == [
        (1.0,), (2.0,), (3.0,), (4.0,), (5.0,)
    ]


def test_duplicate_across_batches_and_calls(backend: list[FrameRecord], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "EMBED_BATCH", 1)
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: np.stack([direction(0)]))
    assert [r.status for r in gemma.add(backend[:2])] == ["embedded", "dup"]
    assert gemma.add(backend[2:3])[0].dup_of == 1
    assert gemma.stats().frames_indexed == 1


def test_threshold_is_inclusive(backend: list[FrameRecord], monkeypatch: pytest.MonkeyPatch) -> None:
    vectors = np.stack([direction(0), direction(0.2)])
    monkeypatch.setattr(config, "DEDUPE_COS", float(vectors[0] @ vectors[1]))
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: vectors)
    assert gemma.add(backend[:2])[1].status == "dup"


def test_failed_encode_does_not_replace_anchor(backend: list[FrameRecord], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: np.stack([direction(0)]))
    gemma.add(backend[:1])

    def fail(*args: object, **kwargs: object) -> np.ndarray:
        raise TimeoutError("fixture")

    monkeypatch.setattr(gemma, "_encode", fail)
    assert gemma.add(backend[1:2])[0].status == "failed"
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: np.stack([direction(0)]))
    assert gemma.add(backend[2:3])[0].dup_of == 1
    assert gemma.stats().frames_failed == 1


def test_backfill_never_matches_future_frame(backend: list[FrameRecord], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gemma, "_encode", lambda *a, **k: np.stack([direction(0)]))
    gemma.add(backend[2:3])
    assert gemma.add(backend[:1])[0].status == "embedded"
    assert gemma.add(backend[3:4])[0].dup_of == 3


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 1.01, -1.01])
def test_invalid_threshold_rejected(value: float, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "DEDUPE_COS", value)
    monkeypatch.setattr(gemma, "_model", SimpleNamespace())
    with pytest.raises(ValueError, match="DEDUPE_COS"):
        gemma.load()
