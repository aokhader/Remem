"""Evaluation correctness checks using explicit synthetic fixtures, never demo metrics."""

from datetime import date
from pathlib import Path

import numpy as np
import pytest

from eval import run_testset as runner
from remem import config
from remem.contracts import Answer, FrameRecord, Moment, SearchHit


def case(window: str = "15:30:00-end", kind: str = "find") -> runner.Case:
    return runner.Case("T01", "where are my keys", "keys", window, "act", kind)


def answer(band: str = "act", ts: float = 100) -> Answer:
    hit = SearchHit(frame_id=1, ts=ts, score=0.1, z=6, path="frames/000001.jpg",
                    visit_start=ts, visit_end=ts, n_frames=1)
    return Answer(q="where are my keys", kind="find", object="keys", band=band, message="fixture",
                  hit=hit if band in {"act", "ask"} else None, frame_url=None, ago_s=None, asked_ts=200)


def test_draft_keeps_28_present_and_8_never_seen() -> None:
    cases = runner.read_cases(runner.ROOT / "eval/test_set.csv")
    assert sum(c.kind == "find" and c.window != "NONE" for c in cases) == 28
    assert sum(c.window == "NONE" for c in cases) == 8
    assert sum(c.kind == "recall" for c in cases) == 4
    assert cases[1].object == "keys"  # keychain phrasing is left to the actual extractor/model


def test_end_and_midnight_windows() -> None:
    day = date(2026, 10, 25)
    end = runner.local_clock("16:00:00", day)
    assert runner.window_bounds(case(), day, end) == (runner.local_clock("15:30:00", day), end)
    start, end = runner.window_bounds(case("23:59:00-00:01:00"), day, None)
    assert end - start == 120
    with pytest.raises(ValueError, match="needs"):
        runner.window_bounds(case(), day, None)


@pytest.mark.parametrize("band,ts,expected", [("act", 100, True), ("ask", 100, True),
                                            ("act", 50, False), ("none", 100, False), ("error", 100, False)])
def test_present_accuracy(band: str, ts: float, expected: bool) -> None:
    assert runner.score_answer(case(), answer(band, ts), (90, 110)) is expected


def test_never_seen_error_and_pending_windows() -> None:
    never = runner.Case("T25", "where is my passport", "passport", "NONE", "none", "find")
    assert runner.score_answer(never, answer("none"), None) is True
    assert runner.score_answer(never, answer("error"), None) is False
    assert runner.score_answer(case(""), answer(), None) is None


def test_recall_is_separate() -> None:
    result = answer().model_copy(update={"kind": "recall", "moments": [
        Moment(start_ts=90, end_ts=110, frame_ids=[1, 2, 3], peak_z=5)
    ]})
    assert runner.score_answer(case(kind="recall"), result, (100, 120)) is True


def test_selection_prefers_zero_false_found_then_retention() -> None:
    def row(z_min: float, z_act: float, retention: float, false: int = 0, wrong: int = 0) -> dict:
        return dict(z_min=z_min, z_act=z_act, retention=retention, false_found=false, wrong_act=wrong)

    chosen = runner.choose_thresholds([row(2, 3, 1, false=1), row(3, 4, 0.95, wrong=1),
                                      row(3, 5, 0.95), row(4, 5, 1)])
    assert chosen["z_min"] == 3 and chosen["z_act"] == 5 and chosen["meets_retention"]
    chosen = runner.choose_thresholds([row(2, 4, 0.5), row(3, 5, 0.8)])
    assert chosen["z_min"] == 3 and not chosen["meets_retention"]
    assert runner.choose_thresholds([row(2, 4, 1, false=1)]) is None


@pytest.mark.parametrize("url", ["https://example.com", "http://example.com", "http://localhost@evil.com",
                                "http://localhost/extra", "http://localhost?redirect=evil"])
def test_only_localhost_http_is_allowed(url: str) -> None:
    with pytest.raises(ValueError, match="localhost"):
        runner.get_json(url, "/ask", 1)


def test_http_aggregation_preserves_draft_and_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [case(""), runner.Case("T25", "where is my passport", "passport", "NONE", "none", "find")]

    def response(base: str, path: str, timeout: float) -> dict:
        if path == "/status":
            return {"index": {"backend": "stub"}}
        if "passport" in path:
            raise TimeoutError("fixture timeout")
        return answer().model_dump()

    monkeypatch.setattr(runner, "get_json", response)
    result = runner.http_eval(cases, {"T01": None, "T25": None}, "http://localhost:8001", tmp_path / "answers.json")
    assert result["accuracy"] is None
    assert result["false_found"] == 1 and result["errors"] == 1
    assert result["median_s"] >= 0


def test_sweep_uses_each_query_once_and_logs_candidates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from remem.index import gemma

    monkeypatch.setattr(config, "REMEM_INDEX", "gemma")
    monkeypatch.setattr(config, "VERIFY_BACKEND", "none")
    monkeypatch.setattr(config, "MIN_FRAMES", 30)
    monkeypatch.setattr(gemma, "load", lambda: None)
    monkeypatch.setattr(gemma, "stats", lambda: type("Stats", (), {"frames_indexed": 31})())
    calls = []
    records = [FrameRecord(id=i + 1, ts=float(i), client_ts=None, path=f"frames/{i}.jpg", source="replay")
               for i in range(31)]

    def scores(text: str) -> tuple[list[FrameRecord], np.ndarray]:
        calls.append(text)
        # Clearly labelled synthetic positive versus background-only query.
        values = np.r_[np.linspace(-0.04, 0.04, 30), 0.8] if "keys" in text else np.linspace(-0.04, 0.04, 31)
        return records, values

    monkeypatch.setattr(gemma, "score_frames", scores)
    cases = [case(), runner.Case("T25", "where is my passport", "passport", "NONE", "none", "find")]
    output = tmp_path / "sweep.json"
    result = runner.sweep(cases, {"T01": (29, 31), "T25": None}, output)
    assert len(calls) == 2
    assert result["chosen"]["z_min"] == 2 and result["chosen"]["z_act"] == 2
    assert result["chosen"]["retention"] == 1
    assert '"frame_id": 31' in output.with_suffix(".candidates.jsonl").read_text()
    assert result["median_s"] is None  # in-process timing cannot become HTTP latency
