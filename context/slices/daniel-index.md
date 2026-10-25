# Slice — Daniel: index and retrieval

**Mission:** turn every frame into a vector and every question into the **newest** frame that stands out — with the band set by code, never by a raw score.

| ID | What | Priority | Demo row |
|---|---|---|---|
| R3 | EmbeddingGemma 2 frame embed (text + vision, 768-d, normalized), keeps up at 1 fps | Must | 2–4 |
| R7 | Query embed, robust z, z ≥ z_min, 5 s visit merge, 10 newest visits, newest-wins `decide()` | Must | 2–4 |
| R4 | Skip a frame near-identical to the last kept one | Should | 1 (backlog) |
| R13 | Moment recall: time ranges of matching stretches | Could | 5 |
| — | `run_testset.py`, z_min/z_act sweep, README's 3 numbers | — | 6 |

**Owns:** `remem/index/` (all files), `tests/test_decide.py`, `eval/run_testset.py`, `eval/results/summary.md`, SQLite table `embeddings`, `spikes/daniel/`.

**Consumes:** `FrameRecord`s via `index.add` (Aziz) · `dict[frame_id, Verdict]` (Varick, R8 only) · `eval/test_set.csv` (Varick) · `eval/ground_truth.csv` + `day.mp4` (Aziz, S1 3:45).
**Produces:** `index.load/add/search/decide/recall/stats` → `AddResult`, `SearchHit`, `Decision`, `Moment`, `IndexStats` (contracts.md) · tuned `Z_MIN`/`Z_ACT` · README numbers.

## Stub due at gate 1 (3:15)

- `remem/index/stub.py` deterministic per contracts.md (passport → `[]`, sunglasses → z 4.0, else z 6.0); `decide()` = real z-only rule.
- Spike numbers in `progress.md`: `is_bf16_supported()`, dtype used, warm embed ms for one frame (**< 0.5 s**), keys photo ranked **1st of 3** for "a photo of keys".
- Nice-to-have A/B (keep the winner): whole question vs `a photo of {X}` · with vs without `prompt_name="SearchQuery"` · one phrasing vs mean of three.

## Definition of done

| Check | Row |
|---|---|
| `REMEM_INDEX=gemma` embeds ≥ 1 frame/s sustained; dtype logged; float16 **raises** at load | 1–3 |
| Replayed day: "a photo of keys" → newest visit overlaps the keys' ground-truth window | gate 2, 2 |
| "a photo of passport" → `[]` → None | 4 |
| Moved prop → newest visit is the new spot | 3 |
| `test_decide.py` passes: act/ask/none, newest-not-highest, R8 rows, verify-timeout fallback | 2–4 |
| `run_testset.py` prints accuracy, false-found, median s; z_min/z_act chosen by 5:15 | 6 |
| Restart reloads the matrix from `embeddings` (no re-embed) | all |

## Retrieval notes

- Formula, guards (MIN_FRAMES, MAD = 0) and decision table: `architecture.md`. Sign-off P4 (spec now merges first, then keeps the 10 newest visits) is your call.
- One GPU lock around `encode`; batches ≤ `EMBED_BATCH` so a question waits ≤ one batch.
- Store vectors as float32 LE BLOBs; matrix ordered by `frames.ts`.
- R4: cosine to the last kept frame ≥ `DEDUPE_COS` (0.98) → `AddResult(status="dup", dup_of=…)`; consider refreshing the kept frame's `ts` so "N min ago" stays honest (your call, log it).
- R13: same scores, larger gap (PROPOSED 20 s), return stretches ≥ 10 s with 3–5 evenly spaced frame ids.

## Fallbacks (stuck 20 min → take it, log it)

| Problem | Fallback |
|---|---|
| Embed > 0.5 s / backlog grows | `EMBED_IMAGE_TOKENS=70`; embed every 2nd frame; R4 dedupe |
| Keys never reach z_min | 560-token image budget; bright keychain; lower z_min; best A/B query text |
| Look-alike answers "keys" | raise z_act so it lands in Ask |
| Never-seen lands in Ask | raise z_min (never-seen → None wins) |
| bf16 load error | float32 (never float16) |
| No frames from Aziz yet | `ffmpeg -i day.mp4 -vf fps=1 dir/%05d.jpg` → `cli add-folder dir --start HH:MM:SS` |

## You never wait for

Aziz → index a folder of JPEGs yourself. Varick → test `decide()` with fake Verdicts; use the spec's 6 sample test rows until `test_set.csv` lands.

## First three tasks for Claude Code

1. **Gate 1 spike.** "In `spikes/daniel/`: load `google/embeddinggemma-2` per `context/setup.md` §2 — first check the exact sentence-transformers kwargs against the installed package and the model card. Print `torch.cuda.is_bf16_supported()` and the dtype used (never float16). Time one warm image embed (median of 5). Rank 3 test photos for `a photo of keys` with `prompt_name="SearchQuery"`. If time, run the query-text A/B. Write the numbers into my section of `context/progress.md`."
2. **R3 + R7 backend.** "Build `remem/index/gemma.py` (load, batched encode under a lock, float32 vectors into the `embeddings` table per `context/data.md`, matrix rebuild on load), `rank.py` (robust z, top-k, 5 s visit merge, MIN_FRAMES/MAD guards, newest first), `cli.py` (`smoke`, `add-folder --start`, `search`). `REMEM_INDEX` picks stub/gemma. Show `cli search 'a photo of keys'` on a frame folder."
3. **decide + eval.** "`decide.py` exactly per the decision table in `context/architecture.md`; table-driven `tests/test_decide.py`. Then `eval/run_testset.py`: `--sweep` in-process (log z ≥ 1.5, sweep z_min/z_act per `context/data.md`), default end-to-end over `GET /ask` on localhost; write `eval/results/summary.md` with the 3 README numbers."

Then: tune with the team 4:45–5:15, R4 at 5:15, R13 only after rows 1–4 pass twice.
