"""Decision rule (architecture.md → Decision rule). S0: the z-only row; the R8 verdict row is Daniel's."""

from remem import config
from remem.contracts import Decision, SearchHit, Verdict


def decide(hits: list[SearchHit], verdicts: dict[int, Verdict] | None = None) -> Decision:
    candidates = [h for h in hits if h.z >= config.Z_MIN]
    if not candidates:
        return Decision(band="none", hit=None)
    newest = max(candidates, key=lambda h: h.ts)  # newest candidate wins, not the highest score
    return Decision(band="act" if newest.z >= config.Z_ACT else "ask", hit=newest)
