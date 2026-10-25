"""Varick's slice: ask page, object extraction, answer card (R6 R9 R10 R11) + R8 verifier adapter.

The HTTP router lives in remem.answer.routes so importing this package needs no FastAPI.
ask/latest load the pipeline (and with it the index backend) on first use, so code that
only needs extract() — like tests/test_extract.py — runs whatever REMEM_INDEX says.
"""

from remem.answer.extract import extract
from remem.answer.verify import verify, verify_many

__all__ = ["ask", "extract", "latest", "verify", "verify_many"]


def __getattr__(name: str):
    if name in ("ask", "latest"):
        from remem.answer import pipeline

        return getattr(pipeline, name)
    raise AttributeError(f"module 'remem.answer' has no attribute {name!r}")
