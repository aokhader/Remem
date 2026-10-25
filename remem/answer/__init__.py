"""Varick's slice: ask page, object extraction, answer card (R6 R9 R11) + R8 verifier adapter.

The HTTP router lives in remem.answer.routes so importing this package needs no FastAPI.
"""

from remem.answer.extract import extract
from remem.answer.pipeline import ask, latest
from remem.answer.verify import verify, verify_many

__all__ = ["ask", "extract", "latest", "verify", "verify_many"]
