"""Decision-table boundaries, newest-wins, verifier rejection and timeout fallback."""

import pytest

from remem import config
from remem.contracts import SearchHit, Verdict
from remem.index.decide import decide


def hit(fid: int = 1, z: float = 6, ts: float = 10) -> SearchHit:
    return SearchHit(frame_id=fid, ts=ts, score=0.3, z=z, path=f"frames/{fid:06d}.jpg",
                     visit_start=ts, visit_end=ts, n_frames=1)


def verdict(conf: float, present: bool = True) -> Verdict:
    return Verdict(present=present, confidence=conf, backend="fixture", ms=1)


@pytest.fixture(autouse=True)
def thresholds(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in {"Z_MIN": 3, "Z_ACT": 5, "CONF_ACT": 0.8, "CONF_ASK": 0.5, "VERIFY_N": 5}.items():
        monkeypatch.setattr(config, key, value)


@pytest.mark.parametrize("hits,verdicts,band,fid", [
    ([], None, "none", None),
    ([hit(z=2.999)], None, "none", None),
    ([hit(z=3)], None, "ask", 1),
    ([hit(z=4.999)], None, "ask", 1),
    ([hit(z=5)], None, "act", 1),
    ([hit(1, 9, 10), hit(2, 3, 20)], None, "ask", 2),
    ([hit(1, 9, 10), hit(2, 2, 20)], None, "act", 1),
    ([hit()], {}, "none", None),
    ([hit()], {1: verdict(0.99, False)}, "none", None),
    ([hit()], {1: verdict(0.499)}, "none", None),
    ([hit()], {1: verdict(0.5)}, "ask", 1),
    ([hit()], {1: verdict(0.799)}, "ask", 1),
    ([hit(z=3)], {1: verdict(0.8)}, "act", 1),
    ([hit()], {99: verdict(1)}, "none", None),
    ([hit(1, 9, 10), hit(2, 3, 20)], {1: verdict(0.99), 2: verdict(0.6)}, "ask", 2),
    ([hit(1, 9, 10), hit(2, 3, 20)], {1: verdict(0.8), 2: verdict(0.9, False)}, "act", 1),
    ([hit(1, 9, 10), hit(2, 3, 20)], {1: verdict(1), 2: verdict(0.2)}, "none", None),
    ([hit()], None, "act", 1),  # whole verifier timeout passes None, retaining z-only behavior
], ids=["empty", "below-z-min", "at-z-min", "below-z-act", "at-z-act", "newest-not-highest",
        "reject-subthreshold", "parse-failures", "negative", "below-confidence", "at-ask", "below-act",
        "at-act", "unrelated-verdict", "newest-not-most-confident", "skip-negative", "newest-weak", "timeout"])
def test_decision_table(hits: list[SearchHit], verdicts: dict[int, Verdict] | None,
                        band: str, fid: int | None) -> None:
    result = decide(hits, verdicts)
    assert result.band == band
    assert (result.hit.frame_id if result.hit else None) == fid
    assert (result.hit is None) == (band == "none")
    if band != "none" and verdicts is not None:
        assert result.verdict == verdicts[fid]


def test_verifier_only_considers_newest_n(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "VERIFY_N", 1)
    assert decide([hit(1, ts=10), hit(2, ts=20)], {1: verdict(1)}).band == "none"


def test_thresholds_come_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "Z_ACT", 7)
    monkeypatch.setattr(config, "CONF_ACT", 0.95)
    assert decide([hit(z=6)]).band == "ask"
    assert decide([hit()], {1: verdict(0.9)}).band == "ask"
