# Progress — live status

> **Rule: edit only your own section and your own rows.** Aziz updates the Gates table. Status words: `todo` · `stub` · `wip` · `done` · `cut`. Put a time on every update (e.g. `15:40`). Sections are separate so three branches merge without conflicts.

## Gates (Aziz)

| Gate | Time | Pass when | Status | Checked |
|---|---|---|---|---|
| S0 | 2:45 (or earlier) | Skeleton on main: layout, `contracts.py`, `config.py`, every stub, fixtures, LICENSE, README skeleton | wip | 15:47 committed on main locally, every endpoint curled on stub; LICENSE + push pending |
| 1 | 3:15 | Aziz: Safari camera preview over the tunnel on venue Wi-Fi + one JPEG on disk · Daniel: one frame embedded on GPU < 0.5 s, "a photo of keys" ranks the keys photo 1st of 3 · Varick: ask page on 2nd iPhone sends a question, shows stub card from `GET /ask` · All: repo, LICENSE, README skeleton pushed, every stub live · PROPOSED items signed off | todo | |
| S1 | 3:45 | `eval/ground_truth.csv` pushed; `day.mp4` in `data/videos/` on the demo laptop | todo | |
| 2 | 4:45 | Replayed day answers "where are my keys" correctly end to end. **No → cut R10, R11, R13 + R12 except its counter** | todo | |
| — | 5:15 | z_min / z_act set from the 40-query test set | todo | |
| 3 | 6:00 | Code freeze; then backup video 6:00–6:10, submit 6:10–6:15 (closes 6:30) | todo | |

## Timeline (all PM)

| Time | Aziz | Daniel | Varick |
|---|---|---|---|
| 2:45–3:15 | S0 skeleton (≤ 15 min), camera page + tunnel spike | EG2 embed spike; query-text A/B if time | Ask page + stub card on the 2nd iPhone |
| 3:15–3:45 | **Record the demo day** (20–30 min, 8 props, ground_truth.csv) | Real index: add, z-rank, visit merge, `decide()` + tests | `extract()` regex + real `/ask` on stub index; draft `test_set.csv` |
| 3:45–4:45 | Ingest queue + replay (R5) + minimal dashboard counter | Index the day; `run_testset.py` | Answer card + bands live; fill test windows |
| 4:45–5:15 | **Everyone: 40-query test set → z_min, z_act** | runs the sweep | |
| 5:15–5:45 | R12 full dashboard; R15 only if rows 1–4 pass twice | R4 dedupe; R13 only if rows pass twice | R10, R11; R8/R14 only if rows 1–4 pass twice |
| 5:30 | **Live stream starts**; keys on camera ≥ 10 min before presenting | | |
| 5:45–6:00 | README + rehearse rows 1–6 | | |
| 6:00 / 6:10 / 6:30 | Freeze + backup video / submit / close | | |

## Kickoff checklist (from spec)

| Item | Status |
|---|---|
| Public GitHub repo, Apache-2.0 LICENSE, README model table | todo |
| `torch.cuda.is_available()` True in WSL | done (spec) |
| `torch.cuda.is_bf16_supported()` = ? → dtype | todo |
| pip install line (setup.md §1) | todo |
| `google/embeddinggemma-2` download started | todo |
| cloudflared in WSL; tunnel URL open on both iPhones over venue Wi-Fi | todo |
| One frame embed timed on GPU (< 0.5 s) | todo |
| Head strap/cap clip, power bank, Auto-Lock Never on both iPhones | todo |
| VRAM total (`nvidia-smi`) — decides R8 backend | todo |

## Requirements (each owner edits only their rows)

| ID | Requirement (short) | Owner | Priority | Status | Notes |
|---|---|---|---|---|---|
| R1 | Camera page: rear camera, POST 640 px JPEG/s over HTTPS | Aziz | Must | todo | 15:47 placeholder page only |
| R2 | Save JPEG to disk + SQLite row | Aziz | Must | wip | 15:47 `POST /frames` real, restart keeps ids; not yet over the tunnel |
| R3 | EG2 frame embed, 768-d, keeps up at 1 fps | Daniel | Must | wip | 16:01: backend implemented; 60 repeated-photo frames persisted in 7.79 s (7.70 fps), bf16; WSL/live recording validation pending |
| R4 | Skip near-duplicate frames | Daniel | Should | todo | |
| R5 | Replay MP4 at 1 fps through the same pipeline | Aziz | Must | stub | 15:47 `POST /replay` → failed "not implemented" |
| R6 | Ask page + object regex | Varick | Must | wip | 15:41 built; 61 extract tests pass; checked in browser on stub index. Not yet on the iPhone over the tunnel |
| R7 | Query embed, robust z, visits, bands | Daniel | Must | wip | 16:12: decision table and evaluator implemented; 117 combined checks pass; real-day accuracy/threshold tuning pending |
| R8 | Gemma 4 E4B double-check + spot line | Varick | Could | stub | 15:41 adapter + `none` backend only; real backends only after rows 1–4 pass twice |
| R9 | Answer card (frame, N min ago, clock, band / "I haven't seen") | Varick | Must | wip | 15:41 `/ask` → act/ask/none/error correct on stub index; card.js ready for the dashboard |
| R10 | Push-to-talk, local speech model | Varick | Should | wip | 15:50 hold-to-talk + `POST /ask/voice` built; tested with whisper-tiny on Mac CPU (~0.3 s/clip). Not yet on an iPhone or with whisper-small on the GPU |
| R11 | Sighting timeline | Varick | Should | wip | 15:41 in card.js ("Show older sightings"); needs real multi-visit hits to verify |
| R12 | Projector dashboard | Aziz | Should | stub | counter needed for row 1; 15:47 placeholder page, `/status` real |
| R13 | Moment recall | Daniel | Could | todo | cut if gate 2 fails |
| R14 | Read answer aloud | Varick | Could | todo | |
| R15 | Blur faces before save | Aziz | Could | todo | |
| R16 | Public repo, license, README model table | All | Must | todo | |

## Demo rows — must pass twice in a row (demo.md)

| Row | What | Run 1 | Run 2 | Notes |
|---|---|---|---|---|
| 1 | Frame counter climbing on projector | | | |
| 2 | "Where are my keys?" → right frame, N min ago, < 5 s | | | |
| 3 | Sunglasses moved → newest spot | | | |
| 4 | Passport → "I haven't seen your passport", no frame | | | |
| 5 | Whiteboard recall (or keys timeline) | | | |
| 6 | README model table on screen | | | |

## Test-set numbers (Daniel)

| Metric | Value | Run time |
|---|---|---|
| Latest-sighting accuracy (28 queries) | Pending: reference windows/real recording missing | 16:12 |
| False-found count (8 never-seen) | Pending: evaluate real replay, not 3-photo diagnostic | 16:12 |
| Median seconds per answer (localhost) | Pending: full replay HTTP run | 16:12 |
| Chosen z_min / z_act | 3 / 5 (placeholders) | |

## Aziz — capture, transport, ingest

- **Now:** 15:47 S0 skeleton committed on main (local), all stubs live, ruff clean
- **Next:** push S0 → LICENSE → R1 camera page over the tunnel (gate 1) → record the day + `ground_truth.csv` (S1)
- **Blocked:** LICENSE has to be added on github.com (Apache-2.0 template), not typed

## Daniel — index and retrieval

- **Gate 1 evidence:** 15:38 — Gate 1 model spike passed locally on Windows, RTX 4070 Laptop GPU (8188 MiB). `torch.cuda.is_bf16_supported() = True`; selected and actual parameter dtype `torch.bfloat16` (never float16). EG2 revision `914f7f89142e33e77833254d9c9b90c3cef7303b`; text + vision only, audio disabled; 280 image tokens; finite 768-d vectors, normalized again in float32 after bf16 rounding. Installed API signatures/source and model card checked before calls: torch 2.6.0+cu118, sentence-transformers 6.2.0, transformers 5.20.2. Offline cached model load 3.44 s. One untimed warm-up, then five synchronized single-image embeds of `closekey.jpeg`: 132.98, 129.96, 123.04, 123.50, 121.69 ms; **median 123.50 ms (< 500 ms)**, excluding load/JPEG decoding. `a photo of keys`, `prompt_name="SearchQuery"`: **closekey.jpeg #1 (0.709398), farkey.jpeg #2 (0.666007), nokey.jpeg #3 (0.563592)**. Scores are diagnostic only. Query A/B: question/photo/mean-of-three × with/without SearchQuery all rank close/far/no keys; no accuracy winner on 3 photos, retain baseline. Reproducible scripts/results summary in `spikes/daniel/`.
- **Now:** 16:01 — Step 2 complete on Windows CUDA: main skeleton/spec fixes merged; `gemma.py`, `rank.py`, `cli.py` implemented behind the existing facade. Offline text/vision model; one bounded GPU worker/lock; <= EMBED_BATCH images, 5 s image / 2 s query timeout; float32 LE SQLite vectors; restart rebuild in frame-time order without re-embedding. New spec P4 followed: merge all z-qualified candidates first, then newest 10 visits. CLI smoke median 123.26 ms; close/far/no-key ranking. `add-folder test_photos --start 15:30:00`: 3/3 embedded, 0 failed, replay timestamps 15:30:00/01/02, 0.946 s total. Fresh-process `cli search` returned close-key frame 1 at 15:30:00 with score 0.709327, z 0.674491, band ask, using explicit small-fixture overrides MIN_FRAMES=3/Z_MIN=0.5; production MIN_FRAMES=30/Z_MIN=3 correctly returns none on 3 photos. Throughput fixture: supplied 3 photos repeated 20 times (not new observations), 60/60 embedded, 0 failed, 7.791 s including saves/decoding/SQLite/matrix updates excluding load = 7.70 fps. 19 focused tests and ruff pass; stub imports no torch/ST; stub app POST /frames and GET /status return 200, passport query none. Details in `remem/index/README.md` and `spikes/daniel/step2-results.md`.
- **Step 3:** 16:12 — `decide.py` implements z-only/newest-wins plus supplied-verdict confidence rows, VERIFY_N, negative/missing verdicts, and None timeout fallback; 20 table/boundary tests. `eval/run_testset.py` defaults to bounded localhost-only HTTP GET /ask, scores find/never-seen/recall separately, counts errors, preserves missing windows, supports local date and HH:MM:SS-end. `--sweep` caches find-query scores, logs every frame z >= 1.5, shares production robust-z/merge logic, sweeps 0.25 grid with zero false-found/zero wrong Act/90% retention rules and reports infeasibility. 117 combined checks and ruff pass. Actual localhost:8001 diagnostic completed all 40 draft requests with zero errors on 3-photo database; final metrics not claimed from that guard-only run. `eval/results/summary.md` contains pending final metrics and diagnostic context.
- **Next:** 16:12 — Replay real recording; Varick fills expected windows from ground_truth.csv; run sweep, apply selected Z_MIN/Z_ACT, restart and run HTTP evaluation, then visually inspect 28 returned frames. R4 remains a later Should; R13 remains gated.
- **Blocked:** 16:12 — No decision/eval code blocker. Final 3 README numbers and calibrated thresholds await real recording/reference windows (28 present and 4 recall windows blank on main). WSL validation pending. Before any real R8 activation, Varick's `_verdicts()` must preserve completed empty mappings (`{}`) instead of converting them to None (timeout/no-verifier fallback); answer files were not modified in this step.

## Varick — ask page, answer card, UI

- **Now:** 15:58 merged S0 into `varick-routing`; slice runs inside the real `remem.app` (stub index): `POST /frames` → `/ask` FOUND with that frame, voice works, ruff + 61 tests pass. Devshim copies removed. 15:50 R10 push-to-talk built (`remem/answer/stt.py`, `POST /ask/voice`, mic button). 15:41 slice built on branch `varick-answer`: `remem/answer/` (extract, pipeline, card, verify, routes), `static/ask.html` + `card.js` + `card.css`, `tests/test_extract.py`, draft `eval/test_set.csv`. Runs today via `spikes/varick/devshim/devserver.py` (stub index, placeholder frames).
- **Next:** PR `varick-routing` → main · open `/ask` on the ask iPhone over the tunnel (gate 1 check, incl. holding the mic) · fill `test_set.csv` windows from `ground_truth.csv` (new `HH:MM:SS-end` format) · R14/R8 only after rows 1–4 pass twice.
- **Blocked:** Daniel's `remem/index/gemma.py` — `config.py` defaults to `REMEM_INDEX=gemma`, so the app won't import until it lands; off-GPU use `REMEM_INDEX=stub`. `ground_truth.csv` (S1) for test windows.
