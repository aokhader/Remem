# Setup — install, run, tunnel, phones, smoke checks

Demo laptop = Windows + WSL2 + NVIDIA GPU (CUDA visible in WSL — confirmed). Everything below runs **inside WSL** unless it says Windows or iPhone.

## 1. WSL + GPU (demo laptop)

```bash
nvidia-smi                                  # GPU listed, note total VRAM (decides R8 backend)
cd ~ && git clone <repo-url> remem && cd remem   # Linux filesystem, NOT /mnt/c (slow + CRLF trouble)
sudo apt-get install -y ffmpeg python3-venv     # PROPOSED: ffmpeg needed by torchcodec (replay) + audio strip
python3 -m venv .venv && source .venv/bin/activate
pip install -U sentence-transformers transformers accelerate pillow torchcodec fastapi uvicorn numpy   # spec line
pip install ruff pytest                         # dev tools (code-standards.md)
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.is_bf16_supported())"
```
Write the `is_bf16_supported()` result in `progress.md` → kickoff. True → bfloat16, False → float32. **Never float16.**

## 2. Download EmbeddingGemma 2 (start now — venue Wi-Fi is slow)

```bash
export HF_HOME=~/.cache/huggingface        # keep the cache on the Linux filesystem
python -c "from huggingface_hub import snapshot_download; snapshot_download('google/embeddinggemma-2')"
```
Not gated as of Oct 25, so no login. If it ever asks for one: accept the terms on the model page, then `HF_TOKEN` in `.env` (never commit, never print).
Load with `SentenceTransformer("google/embeddinggemma-2", config_kwargs={"audio_config": None}, model_kwargs={"torch_dtype": ...})` — **check the exact kwargs against the model card / installed sentence-transformers before writing the call.**

## 3. Only if R8 is attempted (after demo rows 1–4 pass twice)

```bash
nvidia-smi                                 # free VRAM: BF16 E4B ≈ 15 GB, 8-bit ≈ 7.5 GB, 4-bit ≈ 5 GB (+ EG2 ≈ 1.5 GB)
pip install bitsandbytes                   # only for e4b-4bit
python -c "from huggingface_hub import snapshot_download; snapshot_download('google/gemma-4-E4B-it')"   # ~15 GB
```

## 4. Off-GPU dev (Aziz, Varick on their own laptops, incl. macOS) — stub mode

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U fastapi uvicorn numpy pillow ruff pytest
REMEM_INDEX=stub VERIFY_BACKEND=none uvicorn remem.app:app --port 8000 --workers 1
```
Works because torch/sentence-transformers are imported **only** inside `remem/index/gemma.py` and the R8 backends.

## 5. `.env.example` — PROPOSED names (all defined in `remem/config.py` at S0; a new var = contract change)

```bash
# server (Aziz)
REMEM_DATA_DIR=data/live          # data/replay-day1 for test runs
REMEM_PORT=8000
TZ=America/Los_Angeles            # ground_truth.csv is local time; convert with zoneinfo.ZoneInfo(TZ), not the process zone (WSL may run in UTC)
INGEST_QUEUE_MAX=8                # drop-oldest deque
MAX_FRAME_BYTES=2000000
STALL_S=3
FACE_BLUR=0                       # R15
# index (Daniel)
REMEM_INDEX=gemma                 # stub | gemma
EMBED_MODEL=google/embeddinggemma-2
EMBED_DTYPE=auto                  # auto | bfloat16 | float32 — float16 raises at startup
EMBED_IMAGE_TOKENS=280            # 70 | 140 | 280 | 560 | 1120 (Daniel sets at gate 1)
EMBED_BATCH=8
QUERY_TEMPLATE=a photo of {X}
Z_MIN=3
Z_ACT=5
TOP_K=10
VISIT_GAP_S=5
MIN_FRAMES=30
DEDUPE_COS=0.98                   # R4
# answer (Varick)
ASK_TIMEOUT_S=5
VERIFY_BACKEND=none               # none | e4b-bf16 | e4b-4bit | e2b
VERIFY_MODEL=google/gemma-4-E4B-it
VERIFY_N=5
VERIFY_TIMEOUT_S=2.5
CONF_ACT=0.8
CONF_ASK=0.5
STT_MODEL=openai/whisper-small    # R10 (PROPOSED model; Apache-2.0 on HF)
# Hugging Face
HF_HOME=/home/<you>/.cache/huggingface
HF_TOKEN=                         # only if required; never commit
```
`config.py` loads `.env` itself (≈10 lines, no python-dotenv dependency) — PROPOSED.

## 6. Run (two WSL terminals)

```bash
# terminal 1 — server
source .venv/bin/activate && uvicorn remem.app:app --host 127.0.0.1 --port 8000 --workers 1
# terminal 2 — tunnel (install once: download cloudflared-linux-amd64.deb from github.com/cloudflare/cloudflared/releases, sudo dpkg -i)
cloudflared tunnel --url http://localhost:8000          # prints https://<random>.trycloudflare.com
cloudflared tunnel --protocol http2 --url http://localhost:8000   # fallback if venue Wi-Fi blocks QUIC
```
- **Camera iPhone:** Safari → `https://<random>.trycloudflare.com/camera` → tap Start → allow camera.
- **Ask iPhone:** Safari → `https://<random>.trycloudflare.com/ask`.
- **Projector:** Windows browser → `http://localhost:8000/` (WSL2 forwards localhost; else use `hostname -I` IP from WSL).
- The hostname changes on every cloudflared restart → reopen both URLs. **Don't restart cloudflared after 5:30 PM** unless it's dead.
- Both iPhones: Auto-Lock **Never**, Low Power Mode off, Safari in front.

## 7. Fallback recording (Camera app)

iPhone Settings → Camera → Formats → **Most Compatible** (H.264). Record, get the file to the demo laptop (`data.md` → recorded day), strip audio, then:
```bash
curl -s -X POST localhost:8000/replay -H 'Content-Type: application/json' -d '{"video":"day.mp4","start_clock":"14:32:10","speed":0}'
```

## 8. Smoke checks (each < 1 min; run before every merge to main)

| Slice | Command | Pass |
|---|---|---|
| Aziz | `curl -s -X POST --data-binary @t.jpg -H 'Content-Type: image/jpeg' "localhost:8000/frames?ts=$(date +%s000)"` | `{"id": …, "ts": …}` and `data/live/frames/000001.jpg` exists |
| Aziz | `curl -s localhost:8000/status` | valid StatusSnapshot; `frames_received` climbs while the camera page runs |
| Daniel | `python -m remem.index.cli smoke spikes/daniel/photos/` | prints dtype (bfloat16/float32), embed ms < 500, keys photo ranked 1st for "a photo of keys" |
| Daniel | `pytest -q tests/test_decide.py` | all band cases pass |
| Varick | `curl -s "localhost:8000/ask?q=where%20are%20my%20keys"` | Answer JSON, `band` act (stub) |
| Varick | `curl -s "localhost:8000/ask?q=where%20is%20my%20passport"` | `band` none, `hit` null |
| Varick | `/ask` on the ask iPhone over the tunnel | card renders, word + color |
| Varick (R10) | open `/ask` once (warms the speech model, first load downloads `openai/whisper-small` ≈ 1 GB), then `curl -s -X POST --data-binary @clip.m4a localhost:8000/ask/voice` | `{"text": "Where are my keys?"}`; needs `ffmpeg` on PATH |
| All | `ruff check . && pytest -q` | clean |
