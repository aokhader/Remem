"""Aziz's endpoints: POST /frames, GET /frames/{id}.jpg, GET /status, POST + GET /replay, GET /, GET /camera,
POST + GET /memories."""

import io
import logging
import math
import time
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageOps

from remem import capture, config
from remem.capture import queue, replay, store
from remem.contracts import Frame, ReplayJob, StatusSnapshot

log = logging.getLogger(__name__)
router = APIRouter()
MAX_PHOTO_BYTES = 25_000_000  # a full-size iPhone camera-roll JPEG; we shrink it before saving
PHOTO_PX = 1280


def taken_ts(exif: Image.Exif) -> float | None:
    """EXIF DateTimeOriginal (+ OffsetTimeOriginal when the phone wrote one) → epoch seconds."""
    sub = exif.get_ifd(0x8769)  # Exif sub-IFD
    raw = sub.get(36867) or exif.get(306)  # DateTimeOriginal, else DateTime
    try:
        dt = datetime.strptime(str(raw).strip("\x00 "), "%Y:%m:%d %H:%M:%S")
        if off := sub.get(36881):
            dt = dt.replace(tzinfo=datetime.strptime(str(off).strip("\x00 "), "%z").tzinfo)
        return dt.timestamp()  # no offset → the laptop's local zone
    except ValueError:
        return None


@router.post("/frames")
def post_frame(jpeg: Annotated[bytes, Body(media_type="image/jpeg")],
               ts: float | None = None) -> dict[str, int | float]:
    # raw JPEG body + ?ts=<client epoch ms> (P7: no multipart, no python-multipart dep)
    if len(jpeg) > config.MAX_FRAME_BYTES:
        raise HTTPException(413, "frame larger than MAX_FRAME_BYTES")
    if not jpeg.startswith(b"\xff\xd8\xff"):
        raise HTTPException(400, "not a JPEG")
    t0 = time.perf_counter()
    rec = store.save(Frame(jpeg=jpeg, client_ts=None if ts is None else ts / 1000, source="live"))
    save_ms = (time.perf_counter() - t0) * 1000
    queue.put(rec)
    log.info("ingest id=%d src=live bytes=%d save_ms=%.0f queue=%d", rec.id, len(jpeg), save_ms, queue.depth())
    return {"id": rec.id, "ts": rec.ts}


@router.post("/memories")
def post_memory(photo: Annotated[bytes, Body(media_type="image/jpeg")],
                ts: float | None = None) -> dict[str, int | float]:
    """A camera-roll photo → 1280 px JPEG, indexed at the time it was taken (EXIF, else ?ts=<file ms>, else now)."""
    if len(photo) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "photo larger than MAX_PHOTO_BYTES")
    if ts is not None and not math.isfinite(ts):
        raise HTTPException(400, "ts must be finite")
    try:
        img = Image.open(io.BytesIO(photo))
        taken = taken_ts(img.getexif())
        img = ImageOps.exif_transpose(img).convert("RGB")
    except (OSError, ValueError, Image.DecompressionBombError):  # UnidentifiedImageError is an OSError
        raise HTTPException(400, "not an image we can read (HEIC: pick 'Most Compatible')") from None
    img.thumbnail((PHOTO_PX, PHOTO_PX))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    client_ts = None if ts is None else ts / 1000
    when = taken or client_ts or time.time()
    # source "replay": the frames CHECK allows only live/replay, and replay already means "explicit ts" (decisions.md)
    rec = store.save(Frame(jpeg=buf.getvalue(), client_ts=client_ts, source="replay"), ts=when)
    queue.put(rec, block=True)  # never drop a photo the user picked
    log.info("ingest id=%d src=photo bytes=%d exif=%s", rec.id, len(photo), taken is not None)
    return {"id": rec.id, "ts": rec.ts}


@router.get("/memories", include_in_schema=False)
def memories() -> FileResponse:
    return FileResponse(config.ROOT / "static/memories.html")


@router.get("/frames/{frame_id}.jpg")
def get_frame(frame_id: int) -> FileResponse:
    path = config.DATA_DIR / store.frame_path(frame_id)
    if not path.is_file():
        raise HTTPException(404, "no such frame")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/status")
def get_status() -> StatusSnapshot:
    return capture.status()


@router.post("/replay", status_code=202)
def post_replay(video: Annotated[str, Body()], start_clock: Annotated[str, Body()],
                speed: Annotated[float, Body()] = 0) -> ReplayJob:
    try:
        return replay.start(video, start_clock, speed)
    except ValueError as e:
        raise HTTPException(400, str(e)) from None
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from None


@router.get("/replay")
def get_replay() -> ReplayJob | None:
    return replay.latest()


@router.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(config.ROOT / "static/dashboard.html")


@router.get("/camera", include_in_schema=False)
def camera() -> FileResponse:
    return FileResponse(config.ROOT / "static/camera.html")
