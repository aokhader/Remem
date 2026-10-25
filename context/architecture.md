# Architecture — layout, owners, data path, rules, failures

Owner: Aziz (structure). Every slice reads this. Formulas/rules come from `spec.md` → Data and decision rules.

## Diagrams (rebuilt from the kickoff message; the spec's embedded diagrams don't export)

```
CAPTURE                                         ┃ LAPTOP = TRUST BOUNDARY (WSL2 + NVIDIA GPU)
Camera iPhone (forehead, Safari, rear camera)   ┃
  POST /frames, 1 JPEG/s, HTTPS ─ cloudflared ─▶┃ Ingest (FastAPI) ─▶ Frame store (JPEG on disk + SQLite row)
                                                ┃   ─▶ EmbeddingGemma 2 image embed (GPU) ─▶ Frame matrix (NumPy, RAM)
Replay (R5): day.mp4 at 1 fps ─────────────────▶┃ Ingest      (bypass: no phone, no tunnel)
ASK                                             ┃
Ask iPhone (Safari /ask) ─ GET /ask?q= ─ tunnel▶┃ Question → object (regex) → EG2 text embed "a photo of {X}", SearchQuery
                                                ┃ → Rank: cos vs every frame, robust z, z ≥ z_min, merge < 5 s, 10 newest visits
                                                ┃ → Decide: newest candidate; its z → Act / Ask / None
                                                ┃ ⇢ [R8, dashed] Gemma 4 E4B: 5 newest, one GPU batch → present/confidence/where
Ask iPhone ◀──────── Answer card ─── tunnel ────┃◀ Answer card ─▶ Dashboard (localhost, projector)
```
Only JPEGs in and answer cards out cross the tunnel. No vector, no frame store, no matrix ever leaves. The tunnel's HTTPS ends at Cloudflare's edge, so say "stored and searched only on this laptop", never "no frame left it".

## Repo layout and file ownership (one owner per file — this is what makes the slices parallel)

```
Remem/
├── CLAUDE.md, README.md          All; README has one section per owner, Aziz owns its structure (R16)
├── LICENSE (Apache-2.0), pyproject.toml, .env.example, .gitignore, .gitattributes   Aziz (skeleton)
├── context/                      docs; progress.md + decisions.md have one section per person
├── remem/
│   ├── app.py                    Aziz   FastAPI app, lifespan (index.load, worker start), routers, /static
│   ├── config.py                 Aziz   every env var in setup.md, all defined at skeleton time
│   ├── contracts.py              FROZEN at gate 1, verbatim from contracts.md
│   ├── capture/                  Aziz   R1 R2 R5 R12 R15: routes.py store.py queue.py replay.py blur.py
│   ├── index/                    Daniel R3 R4 R7 R13: __init__.py (facade) stub.py gemma.py rank.py decide.py dedupe.py recall.py cli.py
│   └── answer/                   Varick R6 R9 R10 R11 R14 (+R8): routes.py extract.py card.py verify.py stt.py
├── static/  camera.html dashboard.html (Aziz) · ask.html card.js card.css (Varick; dashboard imports card.js)
├── eval/    ground_truth.csv (Aziz) · test_set.csv (Varick) · run_testset.py + results/summary.md (Daniel)
├── tests/   fixtures/*.json (from contracts.md, frozen) · test_decide.py (Daniel) · test_extract.py (Varick)
├── spikes/<name>/                each person's scratch scripts; nobody else edits
└── data/                         gitignored. One DATA_DIR per run: data/live/, data/replay-day1/, data/videos/
```
**Shared files** (`app.py`, `config.py`, `contracts.py`, `pyproject.toml`): change only through the owner + a line in `decisions.md`.

## Parallel plan — only 3 sync points; everything else runs on stubs and fixtures

| Sync | When | What | Who waits |
|---|---|---|---|
| S0 skeleton | 2:45 (or before) | Aziz pushes layout + `contracts.py` + `config.py` + every stub + fixtures (task 1 in his brief) | Nobody: Daniel spikes in `spikes/daniel/`, Varick builds `ask.html` on fixtures |
| S1 data | 3:45 | Aziz pushes `eval/ground_truth.csv`; copies `day.mp4` to `data/videos/` on the demo laptop | Varick fills test windows; Daniel indexes frames |
| S2 gate 2 | 4:45 | Merge all slices on main, replay the day, ask "where are my keys" | Everyone, by design |

| You need | From | Until it lands, use |
|---|---|---|
| Real search hits (Varick) | Daniel | `REMEM_INDEX=stub` — deterministic hits (contracts.md → Stubs) |
| Answers to render (Varick, Aziz's dashboard) | Varick `/ask` | `tests/fixtures/answer_*.json`; `ask.html?fixture=act` |
| Frames to index (Daniel) | Aziz ingest/replay | `ffmpeg -i day.mp4 -vf fps=1` → `python -m remem.index.cli add-folder` |
| `index.add` (Aziz's worker) | Daniel | stub index: accepts everything, remembers records |
| Card renderer (Aziz's dashboard) | Varick `card.js` | `<pre>` of the Answer JSON |
| GPU (Aziz/Varick on their own laptops) | demo laptop | stub mode: `REMEM_INDEX=stub`, `VERIFY_BACKEND=none`, no torch import |
| Test-set windows (Daniel's runner) | Varick `test_set.csv` | the 6 sample rows in spec.md |

## Process model

- **One uvicorn process, `--workers 1`** (model + matrix live in RAM), inside WSL next to cloudflared.
- Threads: event loop (HTTP) · **ingest worker** (Aziz) pops ≤ `EMBED_BATCH` records → `index.add()` · **replay thread** (Aziz) while a job runs · `/ask` handlers are sync `def` → FastAPI threadpool.
- **Ingest queue** = `collections.deque(maxlen=INGEST_QUEUE_MAX)`. Live frames append; when full the **oldest** queued frame falls out and is marked `dropped` (JPEG + row kept, never embedded). The newest is never dropped. Replay uses a blocking put instead (no drops).
- **GPU lock:** the index holds one lock around `encode`. A question's text embed waits at most one image batch. R8 has its own model and lock.

## Path of one frame (R1 → R2 → R3)

1. `camera.html`: `<video>` → canvas 640 px wide → JPEG blob → `POST /frames?ts=<ms>`; max 1 request in flight. *[phone]*
2. HTTPS → Cloudflare edge → quick tunnel (outbound from WSL) → `localhost:8000`. *[JPEG only]*
3. **═ trust boundary ═** `capture.store.save()`: (R15 blur if on) → `DATA_DIR/frames/{id:06d}.jpg` → `frames` row; `ts` = server receive time.
4. `queue.put(FrameRecord)`; worker → `index.add([...])` → image embed → R4 dup check → matrix row + `embeddings` row.
5. Dashboard polls `GET /status` every 1 s: counter, last frame, ingest lag, backlog.

## Path of one question (R6 → R7 → [R8] → R9)

1. `ask.html` text box (iOS dictation works) → `GET /ask?q=where are my keys`. *[phone]* → tunnel *[question text only]*
2. **═ trust boundary ═** `answer.extract()` → `Query(kind="find", object="keys", text="a photo of keys")`.
3. `index.search(text, k=10)` → `SearchHit`s: z ≥ z_min, merged into visits, **newest first**.
4. [R8 on] `verify_many(newest VERIFY_N paths, object)` → `Verdict`s (cached by (frame id, object)).
5. `index.decide(hits, verdicts)` → `Decision(band, hit, verdict)`.
6. `answer.card` → `Answer` JSON, stored as latest → back through the tunnel; phone loads `GET /frames/{id}.jpg`.

## State machines

| Ask page (R6/R9) | → | on |
|---|---|---|
| idle | searching | submit non-empty text |
| searching | act / ask / none | 200 with that `band` |
| searching | error | timeout 8 s (PROPOSED), non-200, network error, or `band="error"` |
| act / ask / none / error | searching | new submit or Retry |

| Ingest, per frame (R2/R3/R4) | Ingest, source (dashboard) |
|---|---|
| received → saved → queued → `embedded` / `dup` (R4) / `dropped` (queue full) / `failed` (encode error or timeout) | `idle` (no frame yet) → `streaming` (last frame < 3 s ago) ⇄ `stalled` (≥ 3 s, PROPOSED) · `replaying` while a ReplayJob runs |

## Retrieval (R7) — never a raw cosine cutoff

```
s_i = cos(e_q, f_i)  (= dot product; both are normalized, 768-d)
z_i = (s_i − median(s)) / (1.4826 · MAD(s)),   MAD(s) = median(|s_i − median(s)|)
C   = { i : z_i ≥ z_min }     z_min = 3 to start
visits: sort C by ts; consecutive frames < 5 s apart → one visit, keep the higher-scoring frame
return the 10 newest visits (merge first: the 10 best frames can all sit in one older visit)
query text: "a photo of {X}" with prompt_name="SearchQuery"; images: {"image": ...}, no prefix
```
PROPOSED edge cases: fewer than `MIN_FRAMES` (30) embedded → return `[]` · MAD = 0 → return `[]`.

## Decision rule (R7; Daniel's `decide()`, pure function)

| Mode | Winner | Act | Ask | None |
|---|---|---|---|---|
| z only (MVP) | newest visit in C | z ≥ z_act (5) | z_min ≤ z < z_act | C empty |
| R8 on | newest frame with `present=true` among the newest `VERIFY_N` | confidence ≥ 0.8 | 0.5 ≤ conf < 0.8 | none present, or all < 0.5 |

R8 details: a JSON parse failure = not present (spec). PROPOSED: if the whole verify call times out, fall back to the z-only row.

## Verifier adapter (Varick, R8 — Could)

```python
class Verifier(Protocol):
    name: str                                   # VERIFY_BACKEND value
    def load(self) -> None: ...                 # no-op for "none"
    def verify_many(self, frame_paths: list[str], obj: str) -> list[Verdict | None]: ...
def verify(frame_path: str, obj: str) -> Verdict | None   # spec name; = verify_many([frame_path], obj)[0]
```
| Backend | Model | Memory (spec, approx.) | When |
|---|---|---|---|
| `none` (default) | — | 0 | Always until rows 1–4 pass twice |
| `e4b-bf16` | `google/gemma-4-E4B-it` | ~15 GB + EG2 ~1.5 GB | VRAM allows |
| `e4b-4bit` | same, bitsandbytes 4-bit | ~5 GB | VRAM short |
| `e2b` | Gemma 4 E2B (PROPOSED; `google/gemma-4-E2B-it` exists on HF, Apache-2.0) | smaller | still short |

Image before text; `enable_thinking=False`; JSON-only reply; one batch for the newest `VERIFY_N` (5; 3 if slow).

## Outputs

`Answer` JSON (ask page + `GET /ask/latest` for the dashboard) · frame JPEGs · `StatusSnapshot` · per-stage timing logs (`embed_ms rank_ms verify_ms total_ms`) · `eval/results/` + README's 3 numbers.

## Latency budget — PROPOSED (whole answer < 5 s, row 2)

| Stage | Budget | | Stage | Budget |
|---|---|---|---|---|
| Phone → laptop (tunnel) | 800 ms | | Decide + card | 10 ms |
| Extract | 5 ms | | [R8] verify 5 frames, one batch | 2,500 ms (hard timeout) |
| Text embed (GPU, incl. lock wait) | 600 ms | | Laptop → phone + frame JPEG | 800 ms |
| Rank over ≤ 10,800 × 768 | 50 ms | | **Total** | ~2.3 s without R8, ~4.8 s with |

Freshness (row 3): frame seen → searchable ≤ 3 s (1 s capture + upload + ≤ 1 batch).

## Failure table

| Dependency | Detect / timeout | Fallback | Owner |
|---|---|---|---|
| Quick tunnel | camera POST fails ×3 or > 3 s; dashboard `stalled` | `--protocol http2` → iPhone Personal Hotspot uplink → replay mode | Aziz |
| Safari camera | `navigator.mediaDevices` undefined (HTTP) or permission denied | Always the HTTPS tunnel URL; record in Camera app (Most Compatible) → AirDrop → replay | Aziz |
| Safari backgrounded / locked | ingest lag ≥ 3 s on dashboard | Auto-Lock Never, Safari in front; tap page to restart stream | Aziz |
| Embed speed (R3) | `embed_ms` p50 > 1,000 or backlog growing | image budget 70 tokens; embed every 2nd frame; R4 dedupe | Daniel |
| Small objects don't rank | keys below z_min on test set | bright keychain; 560-token image budget; lower z_min | Daniel |
| GPU memory (R8) | OOM on load or `nvidia-smi` | e4b-4bit → e2b → `VERIFY_BACKEND=none` | Varick |
| R8 JSON parse / latency | parse error; verify > 2.5 s | parse error = not present; verify 3 newest; timeout → z-only bands | Varick |
| Server crash mid-demo | `/status` unreachable | restart uvicorn; index reloads from `embeddings` table (no re-embed); phones reload same tunnel URL | Aziz |

## Stub-first plan

1. **S0:** skeleton ships every stub from `contracts.md` → Stubs; `uvicorn` boots with `REMEM_INDEX=stub VERIFY_BACKEND=none` on any laptop, no GPU.
2. **Gate 1:** each slice's spike works behind its stub's interface; stubs still selectable by env var.
3. **3:15–4:45:** real implementations replace stubs inside each owner's files only. Contracts frozen.
4. **Gate 2:** demo laptop runs `REMEM_INDEX=gemma`; stub stays for off-GPU dev and tests.
