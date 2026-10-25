"""GET /ask pipeline: extract → index.search → [verify, R8] → index.decide → card.

Never raises: every failure becomes an Answer with band "error". The whole call
is capped at ASK_TIMEOUT_S; a verify timeout falls back to the z-only bands.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

from remem import config, index
from remem.answer.card import ASK_HINT, error_answer, find_answer, recall_answer
from remem.answer.extract import extract
from remem.answer.verify import get_verifier
from remem.contracts import Answer, SearchHit, Verdict

log = logging.getLogger("remem.answer")

# GPU calls can't be cancelled, so a timed-out call finishes in its thread and is discarded.
_ask_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ask")
_verify_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="verify")

_latest: Answer | None = None
_latest_lock = threading.Lock()


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)


def _verdicts(hits: list[SearchHit], obj: str, timings: dict[str, float]) -> dict[int, Verdict] | None:
    verifier = get_verifier()
    if verifier.name == "none" or not hits:
        return None
    newest = hits[: config.VERIFY_N]
    paths = [str(Path(config.REMEM_DATA_DIR) / h.path) for h in newest]
    start = time.perf_counter()
    try:
        results = _verify_pool.submit(verifier.verify_many, paths, obj).result(
            timeout=config.VERIFY_TIMEOUT_S
        )
    except FutureTimeout:
        log.warning("verify timeout after %.1f s; using z-only bands", config.VERIFY_TIMEOUT_S)
        return None
    finally:
        timings["verify"] = _ms(start)
    verdicts = {h.frame_id: v for h, v in zip(newest, results, strict=False) if v is not None}
    return verdicts or None


def _answer(q: str, asked_ts: float) -> Answer:
    timings: dict[str, float] = {}
    start = time.perf_counter()

    step = time.perf_counter()
    query = extract(q)
    timings["extract"] = _ms(step)
    if query is None:
        timings["total"] = _ms(start)
        return error_answer(q, asked_ts, "no object", timings, message=ASK_HINT)

    if query.kind == "recall":
        step = time.perf_counter()
        moments = index.recall(query.text)
        timings["search"] = _ms(step)
        timings["total"] = _ms(start)
        return recall_answer(q, query, moments, asked_ts, timings)

    step = time.perf_counter()
    # Contract says newest first; sorting again is free and keeps newest-wins safe.
    hits = sorted(index.search(query.text, k=config.TOP_K), key=lambda h: h.ts, reverse=True)
    timings["search"] = _ms(step)

    verdicts = _verdicts(hits, query.object, timings)

    step = time.perf_counter()
    decision = index.decide(hits, verdicts)
    timings["decide"] = _ms(step)
    timings["total"] = _ms(start)
    return find_answer(q, query, decision, hits, asked_ts, timings)


def ask(q: str) -> Answer:
    asked_ts = time.time()
    start = time.perf_counter()
    try:
        answer = _ask_pool.submit(_answer, q, asked_ts).result(timeout=config.ASK_TIMEOUT_S)
    except FutureTimeout:
        answer = error_answer(q, asked_ts, "timeout", {"total": _ms(start)})
    except Exception as exc:
        log.exception("ask failed q=%r", q)
        answer = error_answer(q, asked_ts, type(exc).__name__, {"total": _ms(start)})

    global _latest
    with _latest_lock:
        _latest = answer
    z = f"{answer.hit.z:.1f}" if answer.hit else "-"
    stages = " ".join(f"{k}_ms={v:g}" for k, v in answer.timings_ms.items())
    log.info('ask q="%s" obj=%s band=%s z=%s %s', q, answer.object or "-", answer.band, z, stages)
    return answer


def latest() -> Answer | None:
    with _latest_lock:
        return _latest
