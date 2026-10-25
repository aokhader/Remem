# Step 2 verification — 2026-10-25, 16:01 PDT

R3/R7 backend implemented on `daniel-index`, with the skeleton and corrected spec
merged from main. No dependencies added in this step. Runtime is the Gate 1
Windows CUDA venv, RTX 4070 Laptop GPU, bf16, 280 image tokens.

## Results

| Check | Observed |
|---|---|
| CLI smoke warm single-image median (5) | 123.26 ms |
| Smoke ranking | closekey.jpeg → farkey.jpeg → nokey.jpeg |
| Folder import at `--start 15:30:00` | 3 embedded, 0 failed, 0.946 s |
| Persisted replay times | 15:30:00, 15:30:01, 15:30:02 PDT |
| Restart with default production guards | 3 vectors reloaded; no candidates, band none (MIN_FRAMES=30) |
| Fresh-process search with labelled MIN_FRAMES=3/Z_MIN=0.5 | frame 1, close keys, 15:30:00; score 0.709327; z 0.674491; band ask |
| Throughput fixture | 60/60 embedded, 0 failed, 7.791 s = 7.70 fps |
| Focused tests | 19 passed |
| Ruff and Git diff checks | passed |
| Stub import | neither torch nor sentence-transformers imported |
| Stub app | POST /frames 200; GET /status 200; passport query none |

The throughput fixture repeats the three supplied images 20 times. It includes
frame saves, JPEG decoding, encoding in batches of at most 8, embedding commits,
and matrix updates; model load is excluded. It is not a recorded day or evidence
of retrieval accuracy. WSL/live-stream validation and real-day threshold tuning
remain pending. No demo rows or team gates are marked passed from this fixture.

The normal three-photo search correctly returns no candidates. The diagnostic
overrides are explicit, local process settings, not new defaults. Raw cosine
scores are never used as a production cutoff.

## Reproduce (PowerShell, repository root)

Use a fresh ignored data directory for each independent import/benchmark.

```powershell
$env:REMEM_INDEX='gemma'
$env:REMEM_DATA_DIR='data/step2-folder'
spikes/daniel/.venv/Scripts/python -m remem.index.cli smoke test_photos
spikes/daniel/.venv/Scripts/python -m remem.index.cli add-folder test_photos --start 15:30:00
spikes/daniel/.venv/Scripts/python -m remem.index.cli search 'a photo of keys'

# Diagnostic only, for the three-photo fixture:
$env:MIN_FRAMES='3'
$env:Z_MIN='0.5'
spikes/daniel/.venv/Scripts/python -m remem.index.cli search 'a photo of keys'

# Separate repeated-photo throughput fixture; does not evaluate search:
$env:REMEM_DATA_DIR='data/step2-throughput'
spikes/daniel/.venv/Scripts/python -m spikes.daniel.throughput test_photos

# Focused checks:
$env:REMEM_INDEX='stub'
New-Item -ItemType Directory -Force data | Out-Null
spikes/daniel/.venv/Scripts/python -m pytest -q spikes/daniel/test_backend.py --basetemp=data/index-check-run
python -m ruff check .
```

App smoke required running outside the sandbox: the sandbox blocked Windows'
event-loop socket pair before app startup. Outside it, frame/status/ask requests
passed. The initial pytest temporary-directory failure was resolved using a
workspace temporary directory. No application fix was needed for either issue.

Cross-slice change approved by the user: `capture.store.save(frame, *, ts=None)`
now supports a finite explicit replay timestamp. Live ingestion retains receive
time, and all frame-table writes remain in capture code. The shared config and
contracts are unchanged. Decision-rule expansion/eval (Step 3), R4 dedupe and
R13 recall remain deferred.
