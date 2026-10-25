# Progress — live status

> **Rule: edit only your own section and your own rows.** Aziz updates the Gates table. Status words: `todo` · `stub` · `wip` · `done` · `cut`. Put a time on every update (e.g. `15:40`). Sections are separate so three branches merge without conflicts.

## Gates (Aziz)

| Gate | Time | Pass when | Status | Checked |
|---|---|---|---|---|
| S0 | 2:45 (or earlier) | Skeleton on main: layout, `contracts.py`, `config.py`, every stub, fixtures, LICENSE, README skeleton | wip | 15:47 every endpoint curled on stub; pushed to main; LICENSE still missing |
| 1 | 3:15 | Aziz: Safari camera preview over the tunnel on venue Wi-Fi + one JPEG on disk · Daniel: one frame embedded on GPU < 0.5 s, "a photo of keys" ranks the keys photo 1st of 3 · Varick: ask page on 2nd iPhone sends a question, shows stub card from `GET /ask` · All: repo, LICENSE, README skeleton pushed, every stub live · PROPOSED items signed off | wip | 16:02 Aziz part passed: camera iPhone → tunnel → frames on disk (29 frames, lag 0.1 s) |
| S1 | 3:45 | `eval/ground_truth.csv` pushed; `day.mp4` in `data/videos/` on the demo laptop | wip | 16:20 only a 4.5 s wallet test clip (`wallet.mp4`, 4 frames): replays fine, ground truth v0 written; the 20–30 min day with 8 props is not recorded |
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
| cloudflared in WSL; tunnel URL open on both iPhones over venue Wi-Fi | wip 16:02: cloudflared 2026.10.3 in WSL `~/.local/bin`; camera iPhone streaming; ask iPhone not tried |
| One frame embed timed on GPU (< 0.5 s) | todo |
| Head strap/cap clip, power bank, Auto-Lock Never on both iPhones | todo |
| VRAM total (`nvidia-smi`) — decides R8 backend | done 15:55: RTX 2000 Ada Laptop, 8 GB (E4B bf16 won't fit; 4-bit ≈ 5 GB + EG2 ≈ 1.5 GB is tight) |

## Requirements (each owner edits only their rows)

| ID | Requirement (short) | Owner | Priority | Status | Notes |
|---|---|---|---|---|---|
| R1 | Camera page: rear camera, POST 640 px JPEG/s over HTTPS | Aziz | Must | done | 16:02 iPhone over tunnel: 1.00 s median gap, 640×853 portrait, ~65 KB; leaving Safari pauses frames (20 s gap) and they resume on return with no tap; screen lock unverified |
| R2 | Save JPEG to disk + SQLite row | Aziz | Must | done | 16:02 tunnel frames in `~/remem-data/spike`; restart keeps ids |
| R3 | EG2 frame embed, 768-d, keeps up at 1 fps | Daniel | Must | todo | |
| R4 | Skip near-duplicate frames | Daniel | Should | todo | |
| R5 | Replay MP4 at 1 fps through the same pipeline | Aziz | Must | done | 16:16 ffmpeg pipe, blocking put: synthetic 20 s rotated 1080p video → 20/20 frames, 0 dropped (queue max 2), ts 1 s apart from `start_clock`, 640×1138 portrait; 400 bad input, 409 while running. Real `day.mp4` not run yet |
| R6 | Ask page + object regex | Varick | Must | wip | 15:41 built; 61 extract tests pass; checked in browser on stub index. Not yet on the iPhone over the tunnel |
| R7 | Query embed, robust z, visits, bands | Daniel | Must | todo | |
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
| Latest-sighting accuracy (28 queries) | | |
| False-found count (8 never-seen) | | |
| Median seconds per answer (localhost) | | |
| Chosen z_min / z_act | 3 / 5 (placeholders) | |

## Aziz — capture, transport, ingest

- **Now:** 16:20 R5 replay done + row-1 dashboard (`aziz/capture`). Real iPhone clip (`wallet.mp4`, 4.5 s) replays upright with 0 drops; `ground_truth.csv` v0 covers that clip only
- **Next:** record the 20–30 min day (8 props, 3 moves, 4 landmarks), send the original file (AirDrop/USB, not a messaging app) so the start time comes from metadata → contact sheets → full `ground_truth.csv` → replay into `replay-day1` for gate 2
- **Blocked:** full recorded day (gate 2 needs keys on video; z tuning needs ≥ 30 frames). LICENSE has to be added on github.com (Apache-2.0 template), not typed

## Daniel — index and retrieval

- **Now:**
- **Next:** EG2 embed spike (gate 1)
- **Blocked:**

## Varick — ask page, answer card, UI

- **Now:** 15:58 merged S0 into `varick-routing`; slice runs inside the real `remem.app` (stub index): `POST /frames` → `/ask` FOUND with that frame, voice works, ruff + 61 tests pass. Devshim copies removed. 15:50 R10 push-to-talk built (`remem/answer/stt.py`, `POST /ask/voice`, mic button). 15:41 slice built on branch `varick-answer`: `remem/answer/` (extract, pipeline, card, verify, routes), `static/ask.html` + `card.js` + `card.css`, `tests/test_extract.py`, draft `eval/test_set.csv`. Runs today via `spikes/varick/devshim/devserver.py` (stub index, placeholder frames).
- **Next:** PR `varick-routing` → main · open `/ask` on the ask iPhone over the tunnel (gate 1 check, incl. holding the mic) · fill `test_set.csv` windows from `ground_truth.csv` (new `HH:MM:SS-end` format) · R14/R8 only after rows 1–4 pass twice.
- **Blocked:** Daniel's `remem/index/gemma.py` — `config.py` defaults to `REMEM_INDEX=gemma`, so the app won't import until it lands; off-GPU use `REMEM_INDEX=stub`. `ground_truth.csv` (S1) for test windows.
