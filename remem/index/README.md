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
`decide` retains the skeleton's z-only rule; R8 and recall remain deferred.

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
