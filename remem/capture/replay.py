"""R5 replay: decode data/videos/<video> at FPS with the ffmpeg CLI and feed every frame through the same ingest.

ffmpeg over a pipe instead of torchcodec (decisions.md): capture needs no torch, and ffmpeg applies the iPhone
rotation flag. Blocking put, so zero drops; frame k gets ts = start_clock + k / FPS (P10).
"""

import logging
import subprocess
import threading
import time
from collections.abc import Iterator
from datetime import datetime
from datetime import time as dtime
from pathlib import Path
from typing import IO
from zoneinfo import ZoneInfo

from remem import config
from remem.capture import queue, store
from remem.contracts import Frame, ReplayJob

FPS = 3  # decisions.md 16:40; camera.html is on a 5 fps trial (17:47), recorded days stay at 3
log = logging.getLogger(__name__)
_latest: ReplayJob | None = None
_lock = threading.Lock()


def videos_dir() -> Path:
    return config.DATA_DIR.parent / "videos"  # sibling of live/ and replay-day1/ (data.md → on-disk layout)


def _epoch(clock: str) -> float:
    # shortcut: assumes the recording was made today in TZ; add a date to ReplayJob if an older day is replayed
    tz = ZoneInfo(config.TZ)
    return datetime.combine(datetime.now(tz).date(), dtime.fromisoformat(clock), tzinfo=tz).timestamp()


def _seconds(path: Path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         check=False, capture_output=True, text=True)  # a bad file shows up as unparsable stdout
    try:
        return round(float(out.stdout) * FPS)
    except ValueError:
        raise ValueError(f"not a readable video: {path.name}") from None


def _jpegs(stream: IO[bytes]) -> Iterator[bytes]:
    """Split ffmpeg's MJPEG pipe on the EOI marker (FF D9 can't occur inside the scan: 0xFF data bytes are stuffed)."""
    buf = b""
    for chunk in iter(lambda: stream.read(1 << 16), b""):
        buf += chunk
        while (end := buf.find(b"\xff\xd9")) >= 0:
            yield buf[: end + 2]
            buf = buf[end + 2:]


def _run(job: ReplayJob, path: Path, t0: float) -> None:
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-an", "-vf", f"fps={FPS},scale=640:-2",
           "-f", "image2pipe", "-c:v", "mjpeg", "-q:v", "4", "-"]
    wall0 = time.monotonic()
    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
            for jpeg in _jpegs(p.stdout):
                if job.speed > 0:  # 1 = real time (demo fallback); 0 = as fast as the index keeps up
                    time.sleep(max(0.0, wall0 + job.frames_done / FPS / job.speed - time.monotonic()))
                rec = store.save(Frame(jpeg=jpeg, client_ts=None, source="replay"), ts=t0 + job.frames_done / FPS)
                queue.put(rec, block=True)
                job.frames_done += 1
            err = p.stderr.read().decode(errors="replace").strip()
        if p.returncode:
            raise RuntimeError(f"ffmpeg exit {p.returncode}: {err[-300:]}")
        job.frames_total, job.state = job.frames_done, "done"
        log.info("replay %d done: %d frames from %s", job.id, job.frames_done, path.name)
    except Exception as e:  # surface on /status + dashboard instead of a silently dead thread
        log.exception("replay %d failed after %d frames", job.id, job.frames_done)
        job.state, job.error = "failed", str(e)


def start(video: str, start_clock: str, speed: float) -> ReplayJob:
    """Start a replay thread. ValueError = bad request (400); RuntimeError = one is already running (409)."""
    global _latest
    path = videos_dir() / video
    if Path(video).name != video or not path.is_file():
        raise ValueError(f"no such video under {videos_dir()}: {video!r}")
    if speed < 0:
        raise ValueError("speed must be >= 0")
    t0, total = _epoch(start_clock), _seconds(path)  # both raise ValueError on bad input
    with _lock:
        if _latest is not None and _latest.state in ("queued", "running"):
            raise RuntimeError(f"replay {_latest.id} is still running")
        _latest = ReplayJob(id=_latest.id + 1 if _latest else 1, video=video, start_clock=start_clock, speed=speed,
                            state="running", frames_total=total, frames_done=0)
        threading.Thread(target=_run, args=(_latest, path, t0), name="replay", daemon=True).start()
    return _latest


def latest() -> ReplayJob | None:
    return _latest
