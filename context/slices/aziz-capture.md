# Slice — Aziz: capture, transport, ingest

**Mission:** get 3 frames/s from the forehead iPhone (or the recorded day) onto the laptop's disk and into the index, and show the room it's working.

| ID | What | Priority | Demo row |
|---|---|---|---|
| R1 | Camera page: rear camera, 640 px JPEG POST every 333 ms (3 fps) over HTTPS | Must | 1 |
| R2 | Save JPEG to disk + `frames` row | Must | 1–4 |
| R5 | Replay MP4 at 3 fps through the same ingest | Must | gate 2, test set, fallback |
| R12 | Projector dashboard (counter, last frame, ingest lag, latest card) | Should — **counter needed for row 1** | 1 |
| R15 | Blur faces before save (PROPOSED: OpenCV Haar cascade, new dep → ask) | Could | — |
| — | S0 skeleton · `ground_truth.csv` + recorded day · gates table · submission | — | 6 |

**Owns:** `remem/app.py`, `remem/config.py`, `remem/contracts.py` (until frozen), `remem/capture/`, `static/camera.html`, `static/dashboard.html`, `eval/ground_truth.csv`, `pyproject.toml`, `LICENSE`, `.env.example`, `.gitignore`, `.gitattributes`, `tests/fixtures/` (S0 copy), README structure, `spikes/aziz/`, SQLite table `frames`.

**Consumes:** `index.load/add/stats` (Daniel — stub until real) · `GET /ask/latest` + `static/card.js` (Varick) for the dashboard card.
**Produces:** `POST /frames`, `GET /frames/{id}.jpg`, `GET /status`, `POST`/`GET /replay`, `GET /`, `GET /camera` · `FrameRecord`s into `index.add` · `StatusSnapshot`, `ReplayJob` · `ground_truth.csv` + `data/videos/day.mp4` (S1, 3:45).

## Stub due at gate 1 (3:15)

- S0 skeleton on main with **every** slice's stub (contracts.md → Functions), fixtures, LICENSE, README skeleton.
- `POST /frames` real: JPEG lands in `DATA_DIR/frames/`, row in `frames`. `GET /status` real counters. `POST /replay` → `ReplayJob(state="failed", error="not implemented")`.
- Spike: Safari camera preview on the camera iPhone **over the tunnel on venue Wi-Fi**, one JPEG on disk.

## Definition of done

| Check | Row |
|---|---|
| Camera iPhone streams over the tunnel; dashboard counter climbs; ingest lag < 3 s | 1 |
| `POST /replay` of `day.mp4` → every second of video saved + handed to `index.add`, zero drops (blocking put) | gate 2 |
| Live queue drops the **oldest** queued frame, never the newest; `frames_dropped` visible | 2, 3 |
| Frame captured → handed to `index.add` in ≤ 3 s | 3 |
| uvicorn restart keeps frames and ids; phones keep working on the same tunnel URL | all |

## Fallbacks (stuck 20 min → take it, log it)

| Problem | Fallback |
|---|---|
| Tunnel blocked/slow | `--protocol http2` → iPhone Personal Hotspot as laptop uplink → replay `day.mp4` at `speed: 1` |
| Safari camera won't start | HTTPS URL only; else Camera app recording (Most Compatible) → replay |
| Safari stops on lock/background | Auto-Lock Never, Safari in front; dashboard shows stall within 3 s |
| torchcodec decode fails | `ffmpeg -i day.mp4 -vf fps=1 out/%05d.jpg` → feed the folder through the same `ingest()` |
| Mount slips / blur | Head strap + tape; wearer turns slowly; check the last-frame panel before presenting |
| Phone overheats / dies | 640 px frames; power bank in pocket, cable to the mount |
| Blur (R15) too slow | `FACE_BLUR=0` |

## You never wait for

Daniel → stub index accepts and remembers every frame. Varick → dashboard shows the Answer as `<pre>` JSON until `card.js` lands.

## First three tasks for Claude Code

1. **S0 skeleton (≤ 15 min).** "Create the repo layout in `context/architecture.md` exactly. `remem/contracts.py` = the pydantic block in `context/contracts.md`, verbatim. `remem/config.py` = every var in `context/setup.md` §5 with a ~10-line `.env` loader. Stubs in `remem/index/`, `remem/answer/`, `remem/capture/` returning exactly what `contracts.md` → Functions says; `REMEM_INDEX` selects stub/gemma with lazy imports. `tests/fixtures/*.json` from contracts.md → Fixtures. `app.py`: lifespan (`index.load`, `capture.start_worker`), routers, `/static` mount. `.gitignore`/`.gitattributes` per code-standards.md, `pyproject.toml` with ruff, README skeleton (pitch, run, model table, test-set numbers, Built with Claude Code). LICENSE: use GitHub's Apache-2.0 template, don't type it. Run `REMEM_INDEX=stub uvicorn remem.app:app` and curl every endpoint in contracts.md; commit `[capture] add: skeleton with all stubs` to main."
2. **R1 + R2.** "Build `static/camera.html` (states in `context/ui.md`) and the real `POST /frames` + `store.py` per `contracts.md` and the `frames` schema in `context/data.md`. Run cloudflared, open `/camera` on the camera iPhone, show the preview, `ls data/live/frames`, and `/status` climbing."
3. **Queue + R5 + row-1 dashboard.** "`queue.py`: drop-oldest `deque(maxlen=INGEST_QUEUE_MAX)` + worker thread calling `index.add` in batches of `EMBED_BATCH`. `replay.py`: decode `data/videos/day.mp4` at 1 fps (torchcodec), blocking put, `ts = start_clock + offset`; `POST`/`GET /replay`. Minimal `dashboard.html`: counter, last frame, ingest lag. Test: replay into `data/replay-day1` with the stub index and show `/status`."

Then: record the day 3:15–3:45 (`data.md` → recorded day), push `ground_truth.csv` (S1), full R12 after gate 2, R15 only after rows 1–4 pass twice.
