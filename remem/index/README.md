# Index backend

`REMEM_INDEX=stub|gemma` selects the facade backend. Stub mode imports no GPU
libraries. Gemma loads the previously downloaded model from local cache only,
disables Hub telemetry, and uses bf16 when supported, otherwise float32.
Explicit float16 is rejected. Set configuration through `remem/config.py`'s
documented environment variables; use a separate `REMEM_DATA_DIR` per recording.

The installed API and model card were checked in the Gate 1 spike. Inference uses
`config_kwargs={"audio_config": None}`, `model_kwargs={"torch_dtype": dtype}`,
image dictionaries with `processing_kwargs={"image": {"max_soft_tokens": N}}`,
and text `prompt_name="SearchQuery"`. No remote inference is used.

`add` splits inputs at `EMBED_BATCH`, normalizes finite 768-d results in float32,
and stores 3072-byte little-endian vectors in the slice-owned `embeddings` table.
The frame store owns JPEGs and `frames` rows. `load` joins stored vectors to frame
records in `(ts, id)` order, without re-embedding. A different stored model/image
budget or an invalid vector is an error; use a fresh data directory rather than
mixing incompatible embeddings.

A single worker and GPU lock serialize encode calls. At most one running and one
queued call are admitted. Image batches have 5 s and queries 2 s, including GPU
queue wait. Timed-out queued work is cancelled; a running kernel can finish, but
its result is discarded and cannot write index state. Bad images/failed batches
are persisted as `failed` with no vector. Startup model loading is synchronous.

Retrieval computes robust z across all indexed frames. Fewer than `MIN_FRAMES`
or MAD=0 returns no candidates. Every frame at or above `Z_MIN` participates in
visit merging; consecutive candidates strictly less than `VISIT_GAP_S` apart are
one visit. The peak frame represents each visit, with ties taking the newer
frame. Return the newest `min(k, TOP_K)` visits. Raw scores are diagnostic only.
`decide` implements z-only and supplied-verdict rules. `None` verdicts means
disabled/whole-call timeout and falls back to z; `{}` means verification completed
without usable verdicts and returns None. Only the newest `VERIFY_N` candidates
are considered, and the newest positive verdict wins; its confidence sets the
band. No verifier model is loaded here. R8 model backends and recall remain deferred.

## CLI

From the repository root in PowerShell:

```powershell
$env:REMEM_INDEX='gemma'
$env:REMEM_DATA_DIR='data/replay-day1'
spikes/daniel/.venv/Scripts/python -m remem.index.cli smoke test_photos
spikes/daniel/.venv/Scripts/python -m remem.index.cli add-folder test_photos --start 15:30:00
spikes/daniel/.venv/Scripts/python -m remem.index.cli search 'a photo of keys'
```

Folder imports sort filenames, transcode photos to JPEG, and assign one second
per photo. `--start` means today's configured local time (`TZ`) or accepts an ISO
datetime for another day. Re-importing creates new frame records, so use a fresh
data directory for an independent replay.

`smoke` explicitly uses cosine ranking to inspect a tiny folder without changing
production retrieval guards. With three photos, normal `search` returns `[]`
because `MIN_FRAMES=30`. A labelled diagnostic run may set `MIN_FRAMES=3` and
`Z_MIN=0.5`; these values are not tuned thresholds for the real recording.

## Focused checks

```powershell
$env:REMEM_INDEX='stub'
New-Item -ItemType Directory -Force data | Out-Null
spikes/daniel/.venv/Scripts/python -m pytest -q spikes/daniel/test_backend.py --basetemp=data/index-test-run
python -m ruff check .
```

Use a fresh test temporary directory per run. These checks cover robust-z guards,
merge-before-limit, newest versus highest, exact gap boundaries, persistence and
reload, failure vectors, float16 rejection, bounded batches, and late GPU results.

## Decision and evaluation checks

```powershell
$env:REMEM_INDEX='stub'
spikes/daniel/.venv/Scripts/python -m pytest -q tests spikes/daniel/test_backend.py spikes/daniel/test_eval.py --basetemp=data/index-eval-check

# Real recording must already be replayed into this DATA_DIR; windows must be filled.
$env:REMEM_INDEX='gemma'
$env:REMEM_DATA_DIR='data/replay-day1'
spikes/daniel/.venv/Scripts/python eval/run_testset.py --sweep

# After applying recommended thresholds and restarting the local server:
spikes/daniel/.venv/Scripts/python eval/run_testset.py --base-url http://127.0.0.1:8000
```

The sweep embeds each find query once, writes local `eval/results/sweep.candidates.jsonl`
with every frame at z >= 1.5, and evaluates z_min=2..8 / z_act=z_min..10 in 0.25 steps.
It uses the production robust-z and visit merging functions. A true-frame retention
target of 90%, zero false-found, and zero wrong Act guide selection; if infeasible,
zero false-found takes priority and the shortfall is reported. No `.env` is changed.

`--date YYYY-MM-DD` specifies the recording's local date; otherwise it is inferred
from replay timestamps in the configured database. `HH:MM:SS-end` windows use the
last replay timestamp, or `--recording-end HH:MM:SS` / epoch seconds. Use the same
DATA_DIR as the server. Missing windows stay unscored and make latest-sighting
accuracy pending. Recall is scored separately. Errors count against never-seen
and present results; median HTTP time includes failures/timeouts, reported separately.
Review the 28 answer frames visually after the automated window check.

The summary is written to `eval/results/summary.md`; JSON details stay ignored.
Use `--summary` for diagnostic reports. An incomplete/blocked run exits 2.
