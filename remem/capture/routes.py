"""Aziz's endpoints: POST /frames, GET /frames/{id}.jpg, GET /status, POST + GET /replay, GET /, GET /camera."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse

from remem import capture, config
from remem.capture import queue, replay, store
from remem.contracts import Frame, ReplayJob, StatusSnapshot

log = logging.getLogger(__name__)
router = APIRouter()


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
    return replay.start(video, start_clock, speed)


@router.get("/replay")
def get_replay() -> ReplayJob | None:
    return replay.latest()


@router.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(config.ROOT / "static/dashboard.html")


@router.get("/camera", include_in_schema=False)
def camera() -> FileResponse:
    return FileResponse(config.ROOT / "static/camera.html")
