"""R8 verifier adapter (Could). Only the "none" backend exists until demo rows 1–4 pass twice.

Backends planned in context/architecture.md → Verifier adapter: e4b-bf16, e4b-4bit, e2b.
A backend returns one Verdict per frame, or None for "no verdict".
"""

import logging
from typing import Protocol

from remem import config
from remem.contracts import Verdict

log = logging.getLogger("remem.answer")


class Verifier(Protocol):
    name: str

    def load(self) -> None: ...

    def verify_many(self, frame_paths: list[str], obj: str) -> list[Verdict | None]: ...


class NoneVerifier:
    """Default: no verdicts, so decide() uses the z-only bands."""

    name = "none"

    def load(self) -> None:
        pass

    def verify_many(self, frame_paths: list[str], obj: str) -> list[Verdict | None]:
        return [None] * len(frame_paths)


_verifier: Verifier | None = None


def get_verifier() -> Verifier:
    global _verifier
    if _verifier is None:
        if config.VERIFY_BACKEND != "none":
            log.warning("VERIFY_BACKEND=%s is not built yet (R8); using none", config.VERIFY_BACKEND)
        _verifier = NoneVerifier()
        _verifier.load()
    return _verifier


def verify(frame_path: str, obj: str) -> Verdict | None:
    return get_verifier().verify_many([frame_path], obj)[0]


def verify_many(frame_paths: list[str], obj: str) -> list[Verdict | None]:
    return get_verifier().verify_many(frame_paths, obj)
