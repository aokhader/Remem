"""R8 verifier (Varick, Could). S0 stub: no verdict, so decide() uses the z-only bands."""

from remem.contracts import Verdict


def verify(frame_path: str, obj: str) -> Verdict | None:
    return None


def verify_many(frame_paths: list[str], obj: str) -> list[Verdict | None]:
    return [None] * len(frame_paths)
