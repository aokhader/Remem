"""R9 — build the Answer the card renders. Copy comes from context/ui.md → Card copy."""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from remem import config
from remem.contracts import Answer, Decision, Moment, Query, SearchHit

ASK_HINT = "Ask like: where are my keys?"


def _tz() -> ZoneInfo | None:
    try:
        return ZoneInfo(config.TZ)
    except (ZoneInfoNotFoundError, ValueError):
        return None  # fall back to the process's local zone


def format_ago(seconds: float) -> str:
    """< 60 s → "just now"; < 60 min → "N min ago"; else "N h M min ago"."""
    minutes = int(max(seconds, 0) // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min ago"


def format_clock(ts: float) -> str:
    """Epoch seconds → "2:41 PM" in the venue's time zone."""
    return datetime.fromtimestamp(ts, _tz()).strftime("%I:%M %p").lstrip("0")


def format_range(start_ts: float, end_ts: float) -> str:
    """"2:47–2:49 PM", or "11:58 AM–12:03 PM" when the half of the day changes."""
    start, end = format_clock(start_ts), format_clock(end_ts)
    if start.split()[1] == end.split()[1]:
        start = start.split()[0]
    return f"{start}–{end}"


def find_answer(
    q: str, query: Query, decision: Decision, sightings: list[SearchHit],
    asked_ts: float, timings_ms: dict[str, float],
) -> Answer:
    hit = decision.hit
    if decision.band == "none" or hit is None:
        return Answer(
            q=q, kind="find", object=query.object, band="none",
            message=f"I haven't seen your {query.object}.", hit=None, frame_url=None,
            ago_s=None, asked_ts=asked_ts, timings_ms=timings_ms,
        )
    ago_s = max(asked_ts - hit.ts, 0.0)
    if decision.band == "act":
        message = f"Your {query.object}: seen {format_ago(ago_s)} ({format_clock(hit.ts)})."
    else:
        message = f"Might be these. Seen {format_ago(ago_s)}."
    return Answer(
        q=q, kind="find", object=query.object, band=decision.band, message=message,
        hit=hit, frame_url=f"/frames/{hit.frame_id}.jpg", ago_s=ago_s,
        spot=(decision.verdict.where or None) if decision.verdict else None,
        sightings=sightings, asked_ts=asked_ts, timings_ms=timings_ms,
    )


def recall_answer(
    q: str, query: Query, moments: list[Moment], asked_ts: float, timings_ms: dict[str, float],
) -> Answer:
    moments = sorted(moments, key=lambda m: m.start_ts, reverse=True)
    if not moments:
        return Answer(
            q=q, kind="recall", object=query.object, band="none",
            message=f"I haven't seen you at the {query.object}.", hit=None, frame_url=None,
            ago_s=None, asked_ts=asked_ts, timings_ms=timings_ms,
        )
    newest = moments[0]
    return Answer(
        q=q, kind="recall", object=query.object, band="act",
        message=f"You were at the {query.object} {format_range(newest.start_ts, newest.end_ts)}.",
        hit=None, frame_url=None, ago_s=max(asked_ts - newest.end_ts, 0.0),
        moments=moments, asked_ts=asked_ts, timings_ms=timings_ms,
    )


def error_answer(
    q: str, asked_ts: float, error: str, timings_ms: dict[str, float],
    message: str = "Something went wrong. Try again.", query: Query | None = None,
) -> Answer:
    return Answer(
        q=q, kind=query.kind if query else "find", object=query.object if query else "",
        band="error", message=message, hit=None, frame_url=None, ago_s=None,
        asked_ts=asked_ts, timings_ms=timings_ms, error=error,
    )
