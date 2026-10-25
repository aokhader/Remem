"""Local HTTP evaluation (default), or an in-process robust-z threshold sweep."""

import argparse
import csv
import json
import math
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from statistics import median
from time import perf_counter
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from zoneinfo import ZoneInfo

# Support the documented `python eval/run_testset.py` invocation without installation.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from remem import config  # noqa: E402
from remem.answer.extract import extract  # noqa: E402
from remem.contracts import Answer  # noqa: E402


@dataclass(frozen=True)
class Case:
    id: str
    query: str
    object: str
    window: str
    band: str
    kind: str


def read_cases(path: Path) -> list[Case]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "query", "expected_object", "expected_window", "expected_band"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Test set requires columns {sorted(required)}")
        cases = []
        for row in reader:
            query = extract(row["query"])
            if query is None:
                raise ValueError(f"{row['id']}: question has no extracted object")
            band = row["expected_band"].strip()
            window = row["expected_window"].strip()
            if band not in {"act", "ask", "none"} or (window.upper() == "NONE") != (band == "none"):
                raise ValueError(f"{row['id']}: expected band/window mismatch")
            cases.append(Case(row["id"].strip(), row["query"], row["expected_object"].strip(), window, band, query.kind))
    if not cases or len({c.id for c in cases}) != len(cases):
        raise ValueError("Test set is empty or contains duplicate IDs")
    return cases


def local_clock(value: str, day: date) -> float:
    return datetime.combine(day, time.fromisoformat(value), tzinfo=ZoneInfo(config.TZ)).timestamp()


def window_bounds(case: Case, day: date, recording_end: float | None) -> tuple[float, float] | None:
    if not case.window or case.window.upper() == "NONE":
        return None
    start_text, end_text = case.window.split("-", 1)
    start = local_clock(start_text, day)
    if end_text.lower() == "end":
        if recording_end is None:
            raise ValueError(f"{case.id}: '-end' needs --recording-end or indexed frame timestamps")
        end = recording_end
    else:
        end = local_clock(end_text, day)
        if end < start:  # recording crosses local midnight
            end = local_clock(end_text, day + timedelta(days=1))
    if end < start:
        raise ValueError(f"{case.id}: expected window starts after recording end")
    return start, end


def overlaps(start: float, end: float, expected: tuple[float, float]) -> bool:
    return start <= expected[1] and end >= expected[0]


def score_answer(case: Case, answer: Answer, expected: tuple[float, float] | None) -> bool | None:
    if case.window.upper() == "NONE":
        return answer.band == "none"  # errors count as false-found per spec's band != none
    if expected is None:
        return None
    if answer.kind != case.kind:
        return False
    if case.kind == "recall":
        return answer.band == "act" and any(overlaps(m.start_ts, m.end_ts, expected) for m in answer.moments)
    return answer.band in {"act", "ask"} and answer.hit is not None and overlaps(
        answer.hit.visit_start, answer.hit.visit_end, expected
    )


def recording_context(day_arg: str | None, end_arg: str | None) -> tuple[date, float | None]:
    db = config.DATA_DIR / "remem.db"
    last = None
    if db.is_file():
        with sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True) as conn:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE name='frames'").fetchone():
                last = conn.execute("SELECT MAX(ts) FROM frames WHERE source='replay'").fetchone()[0]
    zone = ZoneInfo(config.TZ)
    day = date.fromisoformat(day_arg) if day_arg else (
        datetime.fromtimestamp(last, zone).date() if last is not None else datetime.now(zone).date()
    )
    if end_arg:
        try:
            last = float(end_arg)
        except ValueError:
            last = local_clock(end_arg, day)
        if not math.isfinite(last):
            raise ValueError("Recording end must be finite")
    return day, last


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: object, code: int, msg: str,
                         headers: object, newurl: str) -> None:
        raise ValueError("Local evaluation does not follow redirects")


def get_json(base_url: str, path: str, timeout: float) -> dict:
    parsed = urlsplit(base_url)
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
        raise ValueError("Evaluation requires a plain HTTP localhost URL")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(Request(base_url.rstrip("/") + path), timeout=timeout) as response:
        return json.load(response)


def http_eval(cases: list[Case], expected: dict[str, tuple[float, float] | None],
              base_url: str, output: Path) -> dict:
    status = get_json(base_url, "/status", config.ASK_TIMEOUT_S + 1)
    rows = []
    for case in cases:
        started = perf_counter()
        try:
            data = get_json(base_url, "/ask?" + urlencode({"q": case.query}), config.ASK_TIMEOUT_S + 1)
            answer = Answer.model_validate(data)
            if answer.q != case.query:
                raise ValueError("Response question differs from request")
            row = {"id": case.id, "answer": answer.model_dump(), "correct": score_answer(case, answer, expected[case.id])}
        except Exception as exc:
            row = {"id": case.id, "error": f"{type(exc).__name__}: {exc}",
                   "correct": None if not case.window else False}
        row["elapsed_s"] = perf_counter() - started
        rows.append(row)
        print(f"{case.id}: correct={row['correct']} {row['elapsed_s']:.3f}s", flush=True)
    output.write_text(json.dumps({"server_status": status, "rows": rows}, indent=2), encoding="utf-8")
    by_id = {row["id"]: row for row in rows}
    present = [c for c in cases if c.kind == "find" and c.window.upper() != "NONE"]
    never = [c for c in cases if c.window.upper() == "NONE"]
    recall = [c for c in cases if c.kind == "recall"]
    complete = all(by_id[c.id]["correct"] is not None for c in present)
    return {
        "mode": "HTTP localhost (excludes tunnel)", "server_backend": status.get("index", {}).get("backend"),
        "frames_indexed": status.get("index", {}).get("frames_indexed"),
        "accuracy": sum(by_id[c.id]["correct"] is True for c in present) / len(present) if present and complete else None,
        "present_n": len(present), "present_scored": sum(by_id[c.id]["correct"] is not None for c in present),
        "false_found": sum(by_id[c.id]["correct"] is not True for c in never), "never_n": len(never),
        "median_s": median(row["elapsed_s"] for row in rows),
        "errors": sum("error" in r or r.get("answer", {}).get("band") == "error" for r in rows),
        "recall_correct": sum(by_id[c.id]["correct"] is True for c in recall),
        "recall_scored": sum(by_id[c.id]["correct"] is not None for c in recall),
        "detail": str(output),
    }


def choose_thresholds(grid: list[dict]) -> dict | None:
    safe = [row for row in grid if row["false_found"] == 0 and row["wrong_act"] == 0]
    feasible = [row for row in safe if row["retention"] >= 0.9]
    if feasible:
        return {**min(feasible, key=lambda r: (r["z_min"], r["z_act"])), "meets_retention": True}
    if safe:
        return {**min(safe, key=lambda r: (-r["retention"], r["z_min"], r["z_act"])), "meets_retention": False}
    return None


def sweep(cases: list[Case], expected: dict[str, tuple[float, float] | None], output: Path) -> dict:
    from remem.index import gemma
    from remem.index.rank import rank, robust_z

    find = [c for c in cases if c.kind == "find"]
    present = [c for c in find if c.window.upper() != "NONE"]
    never = [c for c in find if c.window.upper() == "NONE"]
    if config.REMEM_INDEX != "gemma" or config.VERIFY_BACKEND != "none":
        raise ValueError("Sweep requires REMEM_INDEX=gemma and VERIFY_BACKEND=none")
    if not present or not never or any(expected[c.id] is None for c in present):
        raise ValueError("Sweep needs filled present windows and never-seen queries; draft windows are blank")
    gemma.load()
    if gemma.stats().frames_indexed < config.MIN_FRAMES:
        raise ValueError(f"Sweep needs at least MIN_FRAMES={config.MIN_FRAMES} indexed frames")
    cached = {}
    log_path = output.with_suffix(".candidates.jsonl")
    with log_path.open("w", encoding="utf-8") as handle:
        for case in find:
            query = extract(case.query)
            records, scores = gemma.score_frames(query.text)
            z = robust_z(scores)
            cached[case.id] = (records, scores, z)
            candidates = [] if z is None else [
                {"frame_id": r.id, "ts": r.ts, "path": r.path, "score": float(scores[i]), "z": float(z[i])}
                for i, r in enumerate(records) if z[i] >= 1.5
            ]
            handle.write(json.dumps({"id": case.id, "query": case.query, "candidates": candidates}) + "\n")
    grid = []
    for step in range(8, 33):  # 2 through 8 inclusive in quarters
        z_min = step / 4
        visits, retained = {}, 0
        for case in find:
            records, scores, z = cached[case.id]
            visits[case.id] = rank(records, scores, config.TOP_K, z_min=z_min)
            bounds = expected[case.id]
            if bounds is not None and z is not None:
                retained += any(z[i] >= z_min and bounds[0] <= r.ts <= bounds[1] for i, r in enumerate(records))
        false_found = sum(bool(visits[c.id]) for c in never)
        for act_step in range(step, 41):  # z_min through 10 inclusive
            z_act = act_step / 4
            wrong_act, correct = 0, 0
            for case in find:
                hit = visits[case.id][0] if visits[case.id] else None
                bounds = expected[case.id]
                right = hit is not None and bounds is not None and overlaps(hit.visit_start, hit.visit_end, bounds)
                correct += bool(right)
                wrong_act += bool(hit is not None and hit.z >= z_act and not right)
            grid.append({"z_min": z_min, "z_act": z_act, "retention": retained / len(present),
                         "false_found": false_found, "wrong_act": wrong_act,
                         "accuracy": correct / len(present)})
    chosen = choose_thresholds(grid)
    output.write_text(json.dumps({"chosen": chosen, "grid": grid, "candidate_log": str(log_path)}, indent=2),
                      encoding="utf-8")
    return {"mode": "in-process sweep (not HTTP latency)", "chosen": chosen, "accuracy": None,
            "false_found": None, "median_s": None, "present_n": len(present), "never_n": len(never),
            "detail": str(output), "candidate_log": str(log_path)}


def write_summary(path: Path, result: dict, cases: list[Case], dataset: Path, day: date) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    accuracy = result.get("accuracy")
    false_found = result.get("false_found")
    latency = result.get("median_s")
    lines = ["# Evaluation results", "", f"Run: {datetime.now(ZoneInfo(config.TZ)).isoformat(timespec='seconds')}",
             f"Dataset: `{dataset}` ({len(cases)} queries); recording date: {day}; TZ: {config.TZ}.",
             f"Mode: {result['mode']}. Backend: {result.get('server_backend', config.REMEM_INDEX)}.", "",
             "| README metric | Measured value |", "|---|---|",
             f"| Latest-sighting accuracy ({result.get('present_n', 28)} present queries) | "
             + (f"{accuracy:.1%}" if accuracy is not None else "Pending — not measured") + " |",
             f"| False-found count ({result.get('never_n', 8)} never-seen queries) | "
             + (str(false_found) if false_found is not None else "Pending — not measured") + " |",
             "| Median seconds per answer (localhost, excludes tunnel) | "
             + (f"{latency:.4f} s" if latency is not None else "Pending — requires HTTP run") + " |", ""]
    if result.get("blocked"):
        lines += [f"Blocked: {result['blocked']}", ""]
    if result.get("server_backend") == "stub":
        lines += ["**Stub run: these are integration diagnostics, not model accuracy or demo numbers.**", ""]
    if accuracy is None and not result.get("blocked"):
        lines += ["**Incomplete ground truth: available counts/timing are diagnostic, not final README numbers.**", ""]
    if result.get("frames_indexed") is not None and result["frames_indexed"] < config.MIN_FRAMES:
        lines += [f"**Only {result['frames_indexed']} frames indexed; MIN_FRAMES={config.MIN_FRAMES}. "
                  "Find queries return no candidates before model query encoding.**", ""]
    if "chosen" in result:
        lines += ["Sweep recommendation: `" + json.dumps(result["chosen"]) + "`.",
                  "No environment files were changed. If retention is infeasible, never-seen → None takes priority.", ""]
    lines += [f"Current thresholds: Z_MIN={config.Z_MIN}, Z_ACT={config.Z_ACT} (not evidence of tuning).",
              f"Present scored: {result.get('present_scored', 'not an HTTP run')}; "
              f"request/answer errors: {result.get('errors', 'not an HTTP run')}.",
              f"Recall: {result.get('recall_correct', 0)} correct / {result.get('recall_scored', 0)} scored, separately.",
              "Accuracy uses visit-window overlap. Visually review all 28 returned frames: an in-window frame",
              "that does not show the object is still wrong. Timing includes transport failures/timeouts;",
              "those are counted as errors and never-seen errors count as false-found.",
              f"Details (local, ignored): `{result.get('detail', 'none')}`.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", action="store_true")
    parser.add_argument("--test-set", type=Path, default=ROOT / "eval/test_set.csv")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--date", help="Recording local date YYYY-MM-DD; inferred from replay DB if omitted")
    parser.add_argument("--recording-end", help="Local HH:MM:SS or epoch seconds; otherwise max replay ts in DATA_DIR")
    parser.add_argument("--summary", type=Path, default=ROOT / "eval/results/summary.md")
    args = parser.parse_args()
    cases = read_cases(args.test_set)
    day, recording_end = recording_context(args.date, args.recording_end)
    expected = {case.id: window_bounds(case, day, recording_end) for case in cases}
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    output = args.summary.parent / ("sweep.json" if args.sweep else "answers.json")
    try:
        result = sweep(cases, expected, output) if args.sweep else http_eval(cases, expected, args.base_url, output)
    except (ValueError, OSError, RuntimeError) as exc:
        result = {"mode": "in-process sweep" if args.sweep else "HTTP localhost", "blocked": str(exc),
                  "accuracy": None, "false_found": None, "median_s": None,
                  "present_n": sum(c.kind == "find" and c.window.upper() != "NONE" for c in cases),
                  "never_n": sum(c.window.upper() == "NONE" for c in cases)}
    write_summary(args.summary, result, cases, args.test_set, day)
    print(json.dumps(result, indent=2))
    incomplete = (args.sweep and result.get("chosen") is None) or (not args.sweep and result.get("accuracy") is None)
    return 2 if result.get("blocked") or incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
