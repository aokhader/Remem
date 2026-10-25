"""HTTP for the answer slice. Aziz's app.py includes `router`.

GET  /ask          → ask.html (the ask iPhone opens this); also warms the speech model
GET  /ask?q=...    → Answer JSON (always 200; failures are band "error")
GET  /ask/latest   → last Answer or null (dashboard card, R12)
POST /ask/voice    → {"text": str} from a push-to-talk clip (R10); the audio is never saved
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from remem import config
from remem.answer import pipeline, stt
from remem.contracts import Answer

log = logging.getLogger("remem.answer")

MAX_AUDIO_BYTES = 2_000_000  # ~15 s of Safari AAC is far below this

router = APIRouter()


@router.get("/ask", response_model=None)
def ask(q: str | None = None) -> FileResponse | Answer:
    if q is None:
        stt.warm()
        return FileResponse(config.ROOT / "static/ask.html", headers={"Cache-Control": "no-store"})
    return pipeline.ask(q)


@router.get("/ask/latest")
def ask_latest() -> Answer | None:
    return pipeline.latest()


@router.post("/ask/voice")
async def ask_voice(request: Request) -> dict[str, str]:
    audio = await request.body()
    if not audio:
        raise HTTPException(400, "empty audio")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "audio too large")
    try:
        text = await run_in_threadpool(stt.transcribe, audio)
    except stt.SttError as exc:
        log.info("stt failed: %s", exc)
        raise HTTPException(exc.status, str(exc)) from exc
    return {"text": text}
