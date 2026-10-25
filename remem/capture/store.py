"""Frame store (R2): JPEG on disk + a `frames` row in DATA_DIR/remem.db (schema: context/data.md)."""

import math
import sqlite3
import threading
import time

from remem import config
from remem.contracts import Frame, FrameRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS frames (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ts        REAL NOT NULL,
  client_ts REAL,
  path      TEXT NOT NULL,
  source    TEXT NOT NULL CHECK (source IN ('live','replay')),
  dropped   INTEGER NOT NULL DEFAULT 0,
  blurred   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS frames_ts ON frames(ts);
"""
_local = threading.local()


def _conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):  # one connection per thread (code-standards.md)
        (config.DATA_DIR / "frames").mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(config.DATA_DIR / "remem.db")
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.executescript(_SCHEMA)
    return _local.conn


def frame_path(frame_id: int) -> str:
    return f"frames/{frame_id:06d}.jpg"


def save(frame: Frame, *, ts: float | None = None) -> FrameRecord:
    """Use receive time for live frames, or an explicit recording timestamp for replay."""
    if ts is not None and (frame.source != "replay" or not math.isfinite(ts)):
        raise ValueError("An explicit finite timestamp is only valid for replay frames")
    conn, ts = _conn(), time.time() if ts is None else ts
    with conn:  # one transaction: a failed JPEG write leaves no row
        fid = conn.execute("INSERT INTO frames (ts, client_ts, path, source) VALUES (?, ?, '', ?)",
                           (ts, frame.client_ts, frame.source)).lastrowid
        (config.DATA_DIR / frame_path(fid)).write_bytes(frame.jpeg)
        conn.execute("UPDATE frames SET path = ? WHERE id = ?", (frame_path(fid), fid))
    return FrameRecord(id=fid, ts=ts, client_ts=frame.client_ts, path=frame_path(fid), source=frame.source)


def mark_dropped(frame_id: int) -> None:
    with _conn() as conn:
        conn.execute("UPDATE frames SET dropped = 1 WHERE id = ?", (frame_id,))


def counts() -> tuple[int, int, int | None, float | None]:
    """frames_received, frames_dropped, last_frame_id, last_frame_ts — read from SQLite so restarts keep them."""
    conn = _conn()
    received, dropped = conn.execute("SELECT COUNT(*), COALESCE(SUM(dropped), 0) FROM frames").fetchone()
    last_id, last_ts = conn.execute("SELECT id, ts FROM frames ORDER BY id DESC LIMIT 1").fetchone() or (None, None)
    return received, dropped, last_id, last_ts
