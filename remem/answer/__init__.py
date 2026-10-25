"""Answer facade (Varick). S0 stub: canned fixture Answers (contracts.md → Functions)."""

import time

from remem import config
from remem.answer.extract import extract
from remem.contracts import Answer

_latest: Answer | None = None


def ask(q: str) -> Answer:
    global _latest
    query = extract(q)
    name = "none" if "passport" in q.lower() else "act"
    canned = Answer.model_validate_json((config.ROOT / f"tests/fixtures/answer_{name}.json").read_text("utf-8"))
    _latest = canned.model_copy(
        update={"q": q, "object": query.object if query else canned.object, "asked_ts": time.time()})
    return _latest


def latest() -> Answer | None:
    return _latest


__all__ = ["ask", "extract", "latest"]
