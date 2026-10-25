"""R5 replay. S0 stub: every job fails with "not implemented" until the 1 fps decoder lands."""

from remem.contracts import ReplayJob

_latest: ReplayJob | None = None


def start(video: str, start_clock: str, speed: float) -> ReplayJob:
    global _latest
    _latest = ReplayJob(id=_latest.id + 1 if _latest else 1, video=video, start_clock=start_clock, speed=speed,
                        state="failed", frames_total=None, frames_done=0, error="not implemented")
    return _latest


def latest() -> ReplayJob | None:
    return _latest
