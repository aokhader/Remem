"""Memories: camera-roll photos are dated from EXIF and stored like any other frame."""

import io
import os
from datetime import UTC, datetime, timedelta, timezone

os.environ.setdefault("REMEM_INDEX", "stub")

import pytest
from fastapi import HTTPException
from PIL import Image

from remem import config
from remem.capture import queue
from remem.capture.routes import post_memory, taken_ts


def _photo(taken: str | None = None, offset: str | None = None, fmt: str = "JPEG") -> bytes:
    exif = Image.Exif()
    if taken:
        exif[0x8769] = {36867: taken, **({36881: offset} if offset else {})}
    buf = io.BytesIO()
    Image.new("RGB", (3000, 2000), "red").save(buf, fmt, exif=exif)
    return buf.getvalue()


def _exif(data: bytes) -> Image.Exif:
    return Image.open(io.BytesIO(data)).getexif()


def test_taken_ts_uses_offset_when_present() -> None:
    want = datetime(2026, 10, 20, 9, 30, tzinfo=timezone(timedelta(hours=-7))).timestamp()
    assert taken_ts(_exif(_photo("2026:10:20 09:30:00", "-07:00"))) == want


def test_taken_ts_without_offset_is_local_and_missing_is_none() -> None:
    assert taken_ts(_exif(_photo("2026:10:20 09:30:00"))) == datetime(2026, 10, 20, 9, 30).timestamp()
    assert taken_ts(_exif(_photo())) is None


def test_post_memory(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)  # no worker runs: the queue just holds the records
    out = post_memory(_photo("2026:10:20 09:30:00", "-07:00"), ts=1_700_000_000_000)
    assert out["ts"] == datetime(2026, 10, 20, 16, 30, tzinfo=UTC).timestamp()
    saved = Image.open(tmp_path / f"frames/{out['id']:06d}.jpg")
    assert saved.format == "JPEG" and max(saved.size) == 1280
    # no EXIF (a PNG screenshot) → the file time from ?ts=
    assert post_memory(_photo(fmt="PNG"), ts=1_700_000_000_000)["ts"] == 1_700_000_000
    for bad, ts in ((b"not an image", None), (_photo(), float("nan"))):
        with pytest.raises(HTTPException) as e:
            post_memory(bad, ts=ts)
        assert e.value.status_code == 400
    queue._q.clear()
