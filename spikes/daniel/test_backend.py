"""Focused correctness checks for ranking, persistence, and late GPU results."""

import sqlite3
import threading
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from remem import config
from remem.contracts import AddResult, FrameRecord
from remem.index import gemma
from remem.index.rank import rank


def records(n: int) -> list[FrameRecord]:
    return [FrameRecord(id=i + 1, ts=float(i), client_ts=None, path=f"frames/{i + 1:06d}.jpg", source="replay")
            for i in range(n)]


@pytest.fixture(autouse=True)
def settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "MIN_FRAMES", 30)
    monkeypatch.setattr(config, "Z_MIN", 3)
    monkeypatch.setattr(config, "TOP_K", 10)
    monkeypatch.setattr(config, "VISIT_GAP_S", 5)


def test_minimum_frames_and_zero_mad() -> None:
    assert rank(records(29), np.linspace(0, 1, 29)) == []
    assert rank(records(30), np.ones(30)) == []
    assert rank([], np.array([])) == []


@pytest.mark.parametrize("scores", [np.array([np.nan] * 30), np.zeros(29), np.zeros((30, 1))])
def test_invalid_scores_raise(scores: np.ndarray) -> None:
    with pytest.raises(ValueError):
        rank(records(30), scores)


def test_robust_z_matches_formula() -> None:
    values = np.r_[np.linspace(-0.04, 0.04, 30), 0.8]
    hit, = rank(records(31), values)
    expected = (0.8 - np.median(values)) / (1.4826 * np.median(abs(values - np.median(values))))
    assert hit.z == pytest.approx(expected)


def test_merge_first_preserves_newest_lower_score() -> None:
    # Twelve strong older candidates must not hide a weaker but newer visit.
    values = np.r_[np.linspace(-0.04, 0.04, 40), np.full(12, 0.9), 0.5]
    recs = records(len(values))
    recs[-1].ts = 100
    newest, older = rank(recs, values)
    assert newest.frame_id == recs[-1].id
    assert newest.score < older.score
    assert older.n_frames == 12
    assert older.visit_start == 40
    assert older.visit_end == 51


def test_strict_gap_and_peak_frame() -> None:
    values = np.r_[np.linspace(-0.04, 0.04, 40), 0.9, 0.6, 0.5]
    recs = records(len(values))
    recs[-3].ts, recs[-2].ts, recs[-1].ts = 100, 104.999, 109.999
    newest, older = rank(recs, values)
    assert newest.n_frames == 1  # exactly five seconds splits visits
    assert older.frame_id == recs[-3].id  # peak, not last frame, represents the older visit
    assert older.n_frames == 2


def test_limit_applies_to_newest_visits() -> None:
    values = np.r_[np.linspace(-0.04, 0.04, 40), np.full(12, 0.6)]
    recs = records(len(values))
    for i, rec in enumerate(recs[-12:]):
        rec.ts = 100 + i * 10
    hits = rank(recs, values, k=10)
    assert len(hits) == 10
    assert [h.ts for h in hits] == list(range(210, 110, -10))
    assert rank(recs, values, k=0) == []


@pytest.fixture
def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(gemma, "_local", threading.local())
    monkeypatch.setattr(gemma, "_records", [])
    monkeypatch.setattr(gemma, "_matrix", np.empty((0, 768), dtype=np.float32))
    monkeypatch.setattr(gemma, "_dup", 0)
    monkeypatch.setattr(gemma, "_failed", 0)
    # A test fixture for the frozen capture schema, not an alternative frame writer.
    conn = sqlite3.connect(tmp_path / "remem.db")
    conn.execute("CREATE TABLE frames (id INTEGER PRIMARY KEY, ts REAL, client_ts REAL, path TEXT, source TEXT)")
    conn.executemany("INSERT INTO frames VALUES (?, ?, NULL, ?, 'replay')",
                     [(1, 20, "frames/000001.jpg"), (2, 10, "frames/000002.jpg")])
    conn.commit()
    conn.close()
    yield tmp_path
    if hasattr(gemma._local, "conn"):
        gemma._local.conn.close()


def test_float32_little_endian_reload_without_encode(database: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vector = np.zeros(768, dtype=np.float32)
    vector[0] = 1
    gemma._persist([AddResult(frame_id=i, status="embedded", embed_ms=10) for i in (1, 2)],
                   {1: vector, 2: vector})
    raw, = gemma._conn().execute("SELECT vec FROM embeddings WHERE frame_id=1").fetchone()
    assert len(raw) == 3072
    assert raw[:4] == b"\x00\x00\x80\x3f"
    monkeypatch.setattr(gemma, "_model", SimpleNamespace(encode=lambda *a, **k: pytest.fail("must not re-embed")))
    gemma.load()
    assert [r.id for r in gemma._records] == [2, 1]
    assert gemma._matrix.dtype == np.float32
    assert np.array_equal(gemma._matrix, np.stack([vector, vector]))


def test_failed_record_has_no_vector(database: Path) -> None:
    gemma._persist([AddResult(frame_id=1, status="failed")], {})
    assert gemma.stats().frames_failed == 1
    assert gemma._conn().execute("SELECT vec FROM embeddings").fetchone() == (None,)


def test_changed_model_budget_rejected(database: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vector = np.zeros(768, dtype=np.float32)
    vector[0] = 1
    gemma._persist([AddResult(frame_id=1, status="embedded")], {1: vector})
    monkeypatch.setattr(config, "EMBED_IMAGE_TOKENS", 560)
    with pytest.raises(ValueError, match="different model/image budget"):
        gemma._rebuild()


def test_float16_rejected_before_model_import(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "EMBED_DTYPE", "float16")
    with pytest.raises(ValueError, match="Never float16"):
        gemma.load()


def test_bf16_rounding_normalized_in_float32() -> None:
    vector = np.ones(768, dtype=np.float32) * 0.036
    normalized = gemma._normalize(vector)
    assert np.linalg.norm(normalized[0]) == pytest.approx(1, abs=1e-6)
    with pytest.raises(ValueError, match="Zero"):
        gemma._normalize(np.zeros(768))


def test_batched_add_and_unreadable_frame(database: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (database / "frames").mkdir()
    Image.new("RGB", (16, 16), "white").save(database / "frames/000001.jpg")
    batches = []

    def fake_encode(inputs: list, **kwargs: dict) -> np.ndarray:
        batches.append(len(inputs))
        vector = np.zeros((len(inputs), 768), dtype=np.float32)
        vector[:, 0] = 1
        return vector

    monkeypatch.setattr(config, "EMBED_BATCH", 1)
    monkeypatch.setattr(gemma, "_model", SimpleNamespace(encode=fake_encode))
    result = gemma.add(records(2))
    assert [r.status for r in result] == ["embedded", "failed"]
    assert batches == [1]
    assert gemma.stats().frames_indexed == 1
    assert gemma.stats().frames_failed == 1


def test_late_gpu_result_cannot_persist(database: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    entered, finish, exited = threading.Event(), threading.Event(), threading.Event()

    def slow_encode(*args: list, **kwargs: dict) -> np.ndarray:
        entered.set()
        finish.wait(2)
        vector = np.zeros(768, dtype=np.float32)
        vector[0] = 1
        exited.set()
        return vector

    monkeypatch.setattr(gemma, "_model", SimpleNamespace(encode=slow_encode))
    try:
        with pytest.raises(TimeoutError):
            gemma._encode("keys", timeout=0.05)
        assert entered.is_set()
    finally:
        finish.set()
        assert exited.wait(2)
    assert gemma._conn().execute("SELECT COUNT(*) FROM embeddings").fetchone() == (0,)


def test_replay_import_persists_start_clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from remem.capture import store
    from remem.index import cli

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "_local", threading.local())
    folder = tmp_path / "source"
    folder.mkdir()
    for name in ("a.jpg", "b.jpg"):
        Image.new("RGB", (16, 16)).save(folder / name)
    monkeypatch.setattr(cli.index, "add", lambda rows: [AddResult(frame_id=r.id, status="embedded") for r in rows])
    monkeypatch.setattr(cli.index, "stats", lambda: SimpleNamespace(model_dump=lambda: {}))
    try:
        result = cli.add_folder(folder, "2026-10-25T15:30:00-07:00")
        timestamps = store._conn().execute("SELECT ts FROM frames ORDER BY id").fetchall()
        assert timestamps == [(result["start_epoch"],), (result["start_epoch"] + 1,)]
        assert result["counts"]["embedded"] == 2
        assert all((tmp_path / f"frames/{i:06d}.jpg").is_file() for i in (1, 2))
    finally:
        store._local.conn.close()


@pytest.mark.parametrize("source,ts", [("live", 123), ("replay", float("nan")), ("replay", float("inf"))])
def test_explicit_timestamp_only_for_finite_replay(source: str, ts: float) -> None:
    from remem.capture import store
    from remem.contracts import Frame

    with pytest.raises(ValueError, match="only valid for replay"):
        store.save(Frame(jpeg=b"", client_ts=None, source=source), ts=ts)
