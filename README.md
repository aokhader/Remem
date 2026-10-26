# Remem

**"Where are my keys?"** Remem answers with the last frame your glasses saw them in. A forehead-worn iPhone streams 3 frames/s to a laptop, where EmbeddingGemma 2 indexes every frame. A second iPhone asks the question and gets back the newest matching frame, "N min ago" and the clock time, with every frame stored and searched only on the laptop.

Built at DS3 Hack Day, UC San Diego, Oct 25 2026 by Aziz (capture), Daniel (index) and Varick (answer).

## Run

Stub mode (any laptop, no GPU):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U fastapi uvicorn numpy pillow ruff pytest
REMEM_INDEX=stub VERIFY_BACKEND=none uvicorn remem.app:app --port 8000 --workers 1
```

Demo laptop (WSL2 + NVIDIA GPU), the cloudflared tunnel and the phones: [context/setup.md](context/setup.md).

| URL | What |
|---|---|
| `http://localhost:8000/` | Dashboard (projector) |
| `https://<tunnel>/camera` | Camera page (forehead iPhone) |
| `https://<tunnel>/ask` | Ask page (second iPhone) |
| `https://<tunnel>/memories` | Add camera-roll photos so `/ask` searches them too |

## State (Oct 25, 6:30 PM)

Working end to end on the demo laptop: live iPhone camera → tunnel → laptop, replay of recorded MP4s, EmbeddingGemma 2 indexing with near-duplicate skip, the ask page with act / ask / none answer cards and top-5 match thumbnails, the projector dashboard, and memories (checked on an iPhone).

Not done yet: z_min / z_act tuned from the 40-query test set (numbers below are blank), the Gemma 4 double-check (R8, `VERIFY_BACKEND=none` only), moment recall (R13), read-aloud (R14), face blur (R15). Cards for photos older than a day read "N h ago" with no date.

## Models

| Model | License | What it does | Used in |
|---|---|---|---|
| [EmbeddingGemma 2](https://huggingface.co/google/embeddinggemma-2) (`google/embeddinggemma-2`) | Apache 2.0 | Embeds every frame and every question into one 768-d space | R3, R7 (core) |
| Gemma 4 E4B (`google/gemma-4-E4B-it`) | TBD (check model card) | Optional double-check of the newest candidates + spot line | R8, only if shipped |
| Whisper small (`openai/whisper-small`) | Apache 2.0 | Push-to-talk transcription on the laptop | R10, only if shipped |

## Test-set numbers

40 scripted queries on the recorded day; filled from `eval/results/summary.md`.

| Metric | Value |
|---|---|
| Latest-sighting accuracy (28 present queries) | — |
| False-found count (8 never-seen queries, target 0) | — |
| Median seconds per answer (localhost, excludes tunnel) | — |

## Capture, transport, ingest (Aziz)

Three ways frames get in, all into the same JPEG-on-disk + SQLite store and one ingest queue that feeds the index:

- **Live** (`/camera` → `POST /frames`): the rear camera sends a 640 px JPEG 5 times a second (trial; spec says 3), one request in flight. Stamped with the laptop's receive time. When the queue is full the oldest queued frame is dropped and counted, never the newest.
- **Replay** (`POST /replay`): ffmpeg pulls 3 frames/s from an MP4 in `data/videos/`, stamped from the recording's start clock. Never drops.
- **Memories** (`/memories` → `POST /memories`): pick photos from the iPhone's library. Each photo is shrunk to 1280 px and dated by its EXIF capture time (else the file time), so "where are my keys" can answer with a photo from last week. Newest still wins: a live sighting beats an older photo.

`GET /status` feeds the dashboard counters (received, dropped, queue depth, ingest lag → LIVE / STALLED / REPLAYING).

## Index and retrieval (Daniel)

TODO

## Ask page and answer card (Varick)

TODO

## Privacy

Every frame is stored and searched only on this laptop: no vector, frame store or index ever leaves it. Only JPEGs in and answer cards out cross the cloudflared tunnel, whose HTTPS ends at Cloudflare's edge. No cloud APIs, no audio recorded.

## Built with Claude Code

Remem was built with [Claude Code](https://claude.com/claude-code).

## License

Apache-2.0, see [LICENSE](LICENSE).
