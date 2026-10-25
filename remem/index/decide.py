"""Pure band selection from the decision table; no model or verifier calls."""

from remem import config
from remem.contracts import Decision, SearchHit, Verdict


def decide(hits: list[SearchHit], verdicts: dict[int, Verdict] | None = None) -> Decision:
    candidates = [h for h in hits if h.z >= config.Z_MIN]
    if not candidates:
        return Decision(band="none", hit=None)
    candidates.sort(key=lambda h: (h.ts, h.frame_id), reverse=True)
    if verdicts is not None:
        # None means verifier disabled/whole-call timeout. An empty mapping means
        # verification completed without a positive verdict (e.g. parse failures).
        for hit in candidates[:config.VERIFY_N]:
            verdict = verdicts.get(hit.frame_id)
            if verdict is not None and verdict.present:
                if verdict.confidence < config.CONF_ASK:
                    return Decision(band="none", hit=None)
                band = "act" if verdict.confidence >= config.CONF_ACT else "ask"
                return Decision(band=band, hit=hit, verdict=verdict)
        return Decision(band="none", hit=None)
    newest = candidates[0]  # newest candidate wins, not the highest score
    return Decision(band="act" if newest.z >= config.Z_ACT else "ask", hit=newest)
