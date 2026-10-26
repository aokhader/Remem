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

TODO

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
