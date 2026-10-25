"""Varick's endpoints. S0 stubs: GET /ask, GET /ask/latest, POST /ask/voice."""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from remem import answer, config
from remem.contracts import Answer

router = APIRouter()


@router.get("/ask", response_model=None)
def get_ask(q: str | None = None) -> Answer | FileResponse:
    if q is None:  # no q → the ask page; with q → Answer JSON (P8)
        return FileResponse(config.ROOT / "static/ask.html")
    return answer.ask(q)


@router.get("/ask/latest")
def get_latest() -> Answer | None:
    return answer.latest()


@router.post("/ask/voice")
def post_voice() -> dict[str, str]:
    return {"text": ""}  # R10 stub: no transcription yet
