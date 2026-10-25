"""Run the draft over actual localhost HTTP on an explicitly tiny diagnostic DB."""

import threading
import time
from pathlib import Path

import uvicorn

from eval import run_testset
from remem import config


def main() -> None:
    # Environment is configured by the caller; no new config variables are introduced.
    if config.DATA_DIR.name != "step2-folder":
        raise ValueError("Use only the known three-photo data/step2-folder fixture")
    server = uvicorn.Server(uvicorn.Config("remem.app:app", host="127.0.0.1", port=8001, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 90
        while not server.started:
            if not thread.is_alive() or time.monotonic() >= deadline:
                raise RuntimeError("Diagnostic server did not start")
            time.sleep(0.2)
        cases = run_testset.read_cases(Path("eval/test_set.csv"))
        day, _ = run_testset.recording_context(None, None)
        expected = {case.id: None for case in cases}  # draft windows really are blank
        output = Path("eval/results/http-diagnostic.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        result = run_testset.http_eval(cases, expected, "http://127.0.0.1:8001", output)
        result["blocked"] = "DIAGNOSTIC ONLY: 3 photos, production MIN_FRAMES=30, and draft ground-truth windows"
        run_testset.write_summary(Path("eval/results/http-diagnostic.md"), result, cases,
                                 Path("eval/test_set.csv"), day)
        print(result, flush=True)
    finally:
        server.should_exit = True
        thread.join(timeout=10)


if __name__ == "__main__":
    main()
