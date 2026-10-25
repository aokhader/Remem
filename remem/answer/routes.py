"""HTTP for the answer slice. Aziz's app.py includes `router`.

GET /ask          → ask.html (the ask iPhone opens this)
GET /ask?q=...    → Answer JSON (always 200; failures are band "error")
GET /ask/latest   → last Answer or null (dashboard card, R12)
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from remem.answer import pipeline
from remem.contracts import Answer

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

router = APIRouter()


@router.get("/ask", response_model=None)
def ask(q: str | None = None) -> FileResponse | Answer:
    if q is None:
        return FileResponse(STATIC_DIR / "ask.html", headers={"Cache-Control": "no-store"})
    return pipeline.ask(q)


@router.get("/ask/latest")
def ask_latest() -> Answer | None:
    return pipeline.latest()
