# Progress — live status

> **Rule: edit only your own section and your own rows.** Aziz updates the Gates table. Status words: `todo` · `stub` · `wip` · `done` · `cut`. Put a time on every update (e.g. `15:40`). Sections are separate so three branches merge without conflicts.

## Gates (Aziz)

| Gate | Time | Pass when | Status | Checked |
|---|---|---|---|---|
| S0 | 2:45 (or earlier) | Skeleton on main: layout, `contracts.py`, `config.py`, every stub, fixtures, LICENSE, README skeleton | wip | 15:47 every endpoint curled on stub; pushed to main; LICENSE still missing |
| 1 | 3:15 | Aziz: Safari camera preview over the tunnel on venue Wi-Fi + one JPEG on disk · Daniel: one frame embedded on GPU < 0.5 s, "a photo of keys" ranks the keys photo 1st of 3 · Varick: ask page on 2nd iPhone sends a question, shows stub card from `GET /ask` · All: repo, LICENSE, README skeleton pushed, every stub live · PROPOSED items signed off | wip | 16:02 Aziz part passed: camera iPhone → tunnel → frames on disk (29 frames, lag 0.1 s) |
| S1 | 3:45 | `eval/ground_truth.csv` pushed; `day.mp4` in `data/videos/` on the demo laptop | wip | 17:05 `daily.mp4` (2:21, 832×464, walk across campus) + `whiteboard.mp4` (0:14) in `data/videos/`; `ground_truth.csv` logs wallet + backpack, door ×2, footbridge, coffee kiosk, lab, whiteboard. **No keys or other props on camera** → "where are my keys" can't be checked on replay. 16:20 only a 4.5 s wallet test clip |
| 2 | 4:45 | Replayed day answers "where are my keys" correctly end to end. **No → cut R10, R11, R13 + R12 except its counter** | todo | |
| — | 5:15 | z_min / z_act set from the 40-query test set | todo | |
| 3 | 6:00 | Code freeze; then backup video 6:00–6:10, submit 6:10–6:15 (closes 6:30) | todo | |

## Timeline (all PM)

| Time | Aziz | Daniel | Varick |
|---|---|---|---|
| 2:45–3:15 | S0 skeleton (≤ 15 min), camera page + tunnel spike | EG2 embed spike; query-text A/B if time | Ask page + stub card on the 2nd iPhone |
| 3:15–3:45 | **Record the demo day** (10 min at 720p, 8 props, ground_truth.csv) | Real index: add, z-rank, visit merge, `decide()` + tests | `extract()` regex + real `/ask` on stub index; draft `test_set.csv` |
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
| cloudflared in WSL; tunnel URL open on both iPhones over venue Wi-Fi | wip 16:02: cloudflared 2026.10.3 in WSL `~/.local/bin`; camera iPhone streaming; ask iPhone not tried |
| One frame embed timed on GPU (< 0.5 s) | todo |
| Head strap/cap clip, power bank, Auto-Lock Never on both iPhones | todo |
| VRAM total (`nvidia-smi`) — decides R8 backend | done 15:55: RTX 2000 Ada Laptop, 8 GB (E4B bf16 won't fit; 4-bit ≈ 5 GB + EG2 ≈ 1.5 GB is tight) |

## Requirements (each owner edits only their rows)

| ID | Requirement (short) | Owner | Priority | Status | Notes |
|---|---|---|---|---|---|
| R1 | Camera page: rear camera, POST 640 px JPEG 3×/s over HTTPS | Aziz | Must | wip | 16:40 switched to 3 fps (333 ms tick); not re-checked on the iPhone over the tunnel yet: one POST in flight, so round trips > 333 ms lower the rate. 16:02 at 1 fps, iPhone over tunnel: 1.00 s median gap, 640×853 portrait, ~65 KB; leaving Safari pauses frames (20 s gap) and they resume on return with no tap; screen lock unverified |
| R2 | Save JPEG to disk + SQLite row | Aziz | Must | done | 16:02 tunnel frames in `~/remem-data/spike`; restart keeps ids |
| R3 | EG2 frame embed, 768-d, keeps up at 1 fps | Daniel | Must | wip | 16:01: backend implemented; 60 repeated-photo frames persisted in 7.79 s (7.70 fps), bf16; WSL/live recording validation pending |
| R4 | Skip near-duplicate frames | Daniel | Should | done | 16:44: inclusive last-kept cosine dedupe; persistent dup_of/no vector; restart restores anchor. 126 checks + ruff pass; offline bf16 GPU fixture: 2 kept / 3 dup / 0 failed, 2.67 s for 5 frames (diagnostic only) |
| R5 | Replay MP4 at 3 fps through the same pipeline | Aziz | Must | done | 16:40 now 3 fps: synthetic 20 s video → 60/60 frames, 0.333 s apart, 0 dropped. 16:16 ffmpeg pipe, blocking put: synthetic 20 s rotated 1080p video → 20/20 frames, 0 dropped (queue max 2), ts 1 s apart from `start_clock`, 640×1138 portrait; 400 bad input, 409 while running. Real `day.mp4` not run yet |
| R6 | Ask page + object regex | Varick | Must | wip | 15:41 built; 61 extract tests pass; checked in browser on stub index. Not yet on the iPhone over the tunnel |
| R7 | Query embed, robust z, visits, bands | Daniel | Must | wip | 16:12: decision table and evaluator implemented; 117 combined checks pass; real-day accuracy/threshold tuning pending |
| R8 | Gemma 4 E4B double-check + spot line | Varick | Could | stub | 15:41 adapter + `none` backend only; real backends only after rows 1–4 pass twice |
| R9 | Answer card (frame, N min ago, clock, band / "I haven't seen") | Varick | Must | wip | 15:41 `/ask` → act/ask/none/error correct on stub index; card.js ready for the dashboard |
| R10 | Push-to-talk, local speech model | Varick | Should | wip | 15:50 hold-to-talk + `POST /ask/voice` built; tested with whisper-tiny on Mac CPU (~0.3 s/clip). Not yet on an iPhone or with whisper-small on the GPU |
| R11 | Sighting timeline | Varick | Should | wip | 15:41 in card.js ("Show older sightings"); needs real multi-visit hits to verify |
| R12 | Projector dashboard | Aziz | Should | wip | 16:16 counter + indexed, LIVE/STALLED/REPLAYING word + lag, last frame, queue/dropped/embed p50, replay progress bar, latest answer card (card.js); checked in browser during a replay. Not yet on the projector at 1080p |
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

- **Now:** 17:05 merged main (R4) into `aziz/capture` and pushed; stub smoke after merge OK (frames → index → keys act, passport none). `ground_truth.csv` logged from contact sheets of `daily.mp4` (start 16:30:00) + `whiteboard.mp4` (16:35:00); clocks chosen, files carry no creation time. Demo laptop has no torch/sentence-transformers/EG2 weights anywhere yet
- **Next:** WSL clone `~/remem` (branch `aziz/capture` until it's on main) + model libs in `~/.venvs/remem` + EG2 download → replay wallet.mov, daily.mp4, whiteboard.mp4 in that order into `data/replay-day1` → ask wallet/backpack/passport → PR `aziz/capture` → main (main still has the R5 stub)
- **Blocked:** keys on video for gate 2's exact query (record a ~30 s 720p clip of keys on a table, or rely on the live stream from 5:30). LICENSE has to be added on github.com (Apache-2.0 template), not typed

## Daniel — index and retrieval

- **Gate 1 evidence:** 15:38 — Gate 1 model spike passed locally on Windows, RTX 4070 Laptop GPU (8188 MiB). `torch.cuda.is_bf16_supported() = True`; selected and actual parameter dtype `torch.bfloat16` (never float16). EG2 revision `914f7f89142e33e77833254d9c9b90c3cef7303b`; text + vision only, audio disabled; 280 image tokens; finite 768-d vectors, normalized again in float32 after bf16 rounding. Installed API signatures/source and model card checked before calls: torch 2.6.0+cu118, sentence-transformers 6.2.0, transformers 5.20.2. Offline cached model load 3.44 s. One untimed warm-up, then five synchronized single-image embeds of `closekey.jpeg`: 132.98, 129.96, 123.04, 123.50, 121.69 ms; **median 123.50 ms (< 500 ms)**, excluding load/JPEG decoding. `a photo of keys`, `prompt_name="SearchQuery"`: **closekey.jpeg #1 (0.709398), farkey.jpeg #2 (0.666007), nokey.jpeg #3 (0.563592)**. Scores are diagnostic only. Query A/B: question/photo/mean-of-three × with/without SearchQuery all rank close/far/no keys; no accuracy winner on 3 photos, retain baseline. Reproducible scripts/results summary in `spikes/daniel/`.
- **Now:** 16:01 — Step 2 complete on Windows CUDA: main skeleton/spec fixes merged; `gemma.py`, `rank.py`, `cli.py` implemented behind the existing facade. Offline text/vision model; one bounded GPU worker/lock; <= EMBED_BATCH images, 5 s image / 2 s query timeout; float32 LE SQLite vectors; restart rebuild in frame-time order without re-embedding. New spec P4 followed: merge all z-qualified candidates first, then newest 10 visits. CLI smoke median 123.26 ms; close/far/no-key ranking. `add-folder test_photos --start 15:30:00`: 3/3 embedded, 0 failed, replay timestamps 15:30:00/01/02, 0.946 s total. Fresh-process `cli search` returned close-key frame 1 at 15:30:00 with score 0.709327, z 0.674491, band ask, using explicit small-fixture overrides MIN_FRAMES=3/Z_MIN=0.5; production MIN_FRAMES=30/Z_MIN=3 correctly returns none on 3 photos. Throughput fixture: supplied 3 photos repeated 20 times (not new observations), 60/60 embedded, 0 failed, 7.791 s including saves/decoding/SQLite/matrix updates excluding load = 7.70 fps. 19 focused tests and ruff pass; stub imports no torch/ST; stub app POST /frames and GET /status return 200, passport query none. Details in `remem/index/README.md` and `spikes/daniel/step2-results.md`.
- **Step 3:** 16:12 — `decide.py` implements z-only/newest-wins plus supplied-verdict confidence rows, VERIFY_N, negative/missing verdicts, and None timeout fallback; 20 table/boundary tests. `eval/run_testset.py` defaults to bounded localhost-only HTTP GET /ask, scores find/never-seen/recall separately, counts errors, preserves missing windows, supports local date and HH:MM:SS-end. `--sweep` caches find-query scores, logs every frame z >= 1.5, shares production robust-z/merge logic, sweeps 0.25 grid with zero false-found/zero wrong Act/90% retention rules and reports infeasibility. 117 combined checks and ruff pass. Actual localhost:8001 diagnostic completed all 40 draft requests with zero errors on 3-photo database; final metrics not claimed from that guard-only run. `eval/results/summary.md` contains pending final metrics and diagnostic context.
- **Integration:** 16:19 — Merged origin/main capture updates; resolved progress conflict by keeping Aziz's completed R1/R2 rows and Daniel's R3 evidence. Incoming camera implementation retained unchanged. 117 tests and ruff pass. Local stub integration: camera route 200, POST frame and exact JPEG retrieval 200, ingest worker indexed the saved frame, keys answer selected it, passport returned none. No new iPhone/tunnel or live GPU validation claimed.
- **Query A/B:** Bare `keys` tested against `a photo of keys` on original 3 photos, same SearchQuery/bf16/280-token image vectors. Both rank close/far/no keys. Bare scores 0.742602/0.705263/0.622002; photo scores 0.709398/0.666007/0.563592. Weaker-positive/background gap 0.083261 vs 0.102415; no benefit from bare keys on this fixture. Template unchanged; see `spikes/daniel/query-ab-results.md`.
- **R4:** 16:44 — Complete: last-kept normalized cosine >= DEDUPE_COS skips vector retention and persists dup_of. Duplicate/failed frames never advance the anchor; cross-batch/call and restart behavior covered, add calls serialized. Older backfills are retained. Capture timestamps/JPEGs unchanged; stationary runs retain first-kept frame age. 126 checks and ruff pass. Offline Windows CUDA/bf16 diagnostic on 5 frames from 2 supplied photos: embedded/dup/dup/embedded/dup, 2 kept / 3 dup / 0 failed, 2.669 s including decoding/encoding/persistence excluding model load (1.873 processed fps, not a sustained benchmark). Reload preserved counts and matrix. `spikes/daniel/r4_smoke.py` reproduces it with a fresh DATA_DIR. Throughput script now counts duplicates separately from failures.
- **Next:** 16:44 — Replay real recording into a fresh DATA_DIR with R4 active; Varick fills expected windows from ground_truth.csv; run sweep, apply selected Z_MIN/Z_ACT, restart and run HTTP evaluation, then visually inspect 28 returned frames. MIN_FRAMES counts kept vectors; R13 remains gated.
- **Blocked:** 16:44 — Final 3 README numbers and calibrated thresholds await real recording/reference windows (ground_truth.csv/day.mp4 absent locally; 28 present and 4 recall windows blank). WSL validation pending. Before any real R8 activation, Varick's `_verdicts()` must preserve completed empty mappings (`{}`) instead of converting them to None (timeout/no-verifier fallback); answer files were not modified in this step.

## Varick — ask page, answer card, UI

- **Now:** 15:58 merged S0 into `varick-routing`; slice runs inside the real `remem.app` (stub index): `POST /frames` → `/ask` FOUND with that frame, voice works, ruff + 61 tests pass. Devshim copies removed. 15:50 R10 push-to-talk built (`remem/answer/stt.py`, `POST /ask/voice`, mic button). 15:41 slice built on branch `varick-answer`: `remem/answer/` (extract, pipeline, card, verify, routes), `static/ask.html` + `card.js` + `card.css`, `tests/test_extract.py`, draft `eval/test_set.csv`. Runs today via `spikes/varick/devshim/devserver.py` (stub index, placeholder frames).
- **Next:** PR `varick-routing` → main · open `/ask` on the ask iPhone over the tunnel (gate 1 check, incl. holding the mic) · fill `test_set.csv` windows from `ground_truth.csv` (new `HH:MM:SS-end` format) · R14/R8 only after rows 1–4 pass twice.
- **Blocked:** Daniel's `remem/index/gemma.py` — `config.py` defaults to `REMEM_INDEX=gemma`, so the app won't import until it lands; off-GPU use `REMEM_INDEX=stub`. `ground_truth.csv` (S1) for test windows.
