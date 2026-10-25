# Progress — live status

> **Rule: edit only your own section and your own rows.** Aziz updates the Gates table. Status words: `todo` · `stub` · `wip` · `done` · `cut`. Put a time on every update (e.g. `15:40`). Sections are separate so three branches merge without conflicts.

## Gates (Aziz)

| Gate | Time | Pass when | Status | Checked |
|---|---|---|---|---|
| S0 | 2:45 (or earlier) | Skeleton on main: layout, `contracts.py`, `config.py`, every stub, fixtures, LICENSE, README skeleton | todo | |
| 1 | 3:15 | Aziz: Safari camera preview over the tunnel on venue Wi-Fi + one JPEG on disk · Daniel: one frame embedded on GPU < 0.5 s, "a photo of keys" ranks the keys photo 1st of 3 · Varick: ask page on 2nd iPhone sends a question, shows stub card from `GET /ask` · All: repo, LICENSE, README skeleton pushed, every stub live · PROPOSED items signed off | todo | |
| S1 | 3:45 | `eval/ground_truth.csv` pushed; `day.mp4` in `data/videos/` on the demo laptop | todo | |
| 2 | 4:45 | Replayed day answers "where are my keys" correctly end to end. **No → cut R10–R13** | todo | |
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
| R1 | Camera page: rear camera, POST 640 px JPEG/s over HTTPS | Aziz | Must | todo | |
| R2 | Save JPEG to disk + SQLite row | Aziz | Must | todo | |
| R3 | EG2 frame embed, 768-d, keeps up at 1 fps | Daniel | Must | todo | |
| R4 | Skip near-duplicate frames | Daniel | Should | todo | |
| R5 | Replay MP4 at 1 fps through the same pipeline | Aziz | Must | todo | |
| R6 | Ask page + object regex | Varick | Must | wip | 15:41 built; 61 extract tests pass; checked in browser on stub index. Not yet on the iPhone over the tunnel |
| R7 | Query embed, robust z, top 10, bands | Daniel | Must | todo | |
| R8 | Gemma 4 E4B double-check + spot line | Varick | Could | stub | 15:41 adapter + `none` backend only; real backends only after rows 1–4 pass twice |
| R9 | Answer card (frame, N min ago, clock, band / "I haven't seen") | Varick | Must | wip | 15:41 `/ask` → act/ask/none/error correct on stub index; card.js ready for the dashboard |
| R10 | Push-to-talk, local speech model | Varick | Should | wip | 15:50 hold-to-talk + `POST /ask/voice` built; tested with whisper-tiny on Mac CPU (~0.3 s/clip). Not yet on an iPhone or with whisper-small on the GPU |
| R11 | Sighting timeline | Varick | Should | wip | 15:41 in card.js ("Show older sightings"); needs real multi-visit hits to verify |
| R12 | Projector dashboard | Aziz | Should | todo | counter needed for row 1 |
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

- **Now:**
- **Next:** S0 skeleton → camera page over tunnel (gate 1)
- **Blocked:**

## Daniel — index and retrieval

- **Now:**
- **Next:** EG2 embed spike (gate 1)
- **Blocked:**

## Varick — ask page, answer card, UI

- **Now:** 15:50 R10 push-to-talk built (`remem/answer/stt.py`, `POST /ask/voice`, mic button). 15:41 slice built on branch `varick-answer`: `remem/answer/` (extract, pipeline, card, verify, routes), `static/ask.html` + `card.js` + `card.css`, `tests/test_extract.py`, draft `eval/test_set.csv`. Runs today via `spikes/varick/devshim/devserver.py` (stub index, placeholder frames).
- **Next:** open `/ask` on the ask iPhone over the tunnel (gate 1 check, incl. holding the mic) · rebase onto main once S0 lands, delete the devshim · fill `test_set.csv` windows from `ground_truth.csv` · R14/R8 only after rows 1–4 pass twice.
- **Blocked:** S0 skeleton not on main (no `remem/contracts.py`, `config.py`, `app.py`, index stub) — Aziz. Need Aziz's OK that `remem.config` exposes module constants named like the env vars (`config.Z_ACT`, `config.QUERY_TEMPLATE`…). `ground_truth.csv` (S1) for test windows.
