# Contracts — every shape, function, endpoint and stub between slices

> **Rule: after gate 1 (3:15 PM) this file is frozen.** A change needs the owning slice's OK **and** a line in `decisions.md`. Adding an optional field with a default is still a change. `remem/contracts.py` is a verbatim copy of the pydantic block below.

Conventions: times are **epoch seconds (float, UTC)**; the browser renders clock time in its own local zone. Frame `path` is relative to `DATA_DIR` (`frames/000123.jpg`). JSON is snake_case. `score` is raw cosine for display/debug only — **never a cutoff**.

## Data shapes — pydantic v2 (`remem/contracts.py`)

```python
from typing import Literal
from pydantic import BaseModel, Field

Band = Literal["act", "ask", "none", "error"]
Source = Literal["live", "replay"]

class Frame(BaseModel):          # into ingest (POST /frames or replay) — Aziz internal
    jpeg: bytes
    client_ts: float | None      # phone clock; None for replay
    source: Source

class FrameRecord(BaseModel):    # Aziz → Daniel via index.add(); row in `frames`
    id: int
    ts: float                    # server receive time; replay: start_clock + video offset
    client_ts: float | None
    path: str                    # "frames/000123.jpg"
    source: Source

class AddResult(BaseModel):      # Daniel → Aziz
    frame_id: int
    status: Literal["embedded", "dup", "failed"]
    dup_of: int | None = None    # R4: id of the kept frame it matched
    embed_ms: float | None = None

class SearchHit(BaseModel):      # Daniel → Varick; ONE merged visit (candidates < 5 s apart)
    frame_id: int                # highest-scoring frame of the visit
    ts: float                    # that frame's ts
    score: float                 # raw cosine — display only
    z: float                     # robust z within this query
    path: str
    visit_start: float
    visit_end: float
    n_frames: int

class Verdict(BaseModel):        # Varick (R8) → Daniel's decide()
    present: bool
    confidence: float = Field(ge=0, le=1)
    where: str = ""              # ≤ 12 words: surface or landmark
    backend: str                 # VERIFY_BACKEND value
    ms: float

class Decision(BaseModel):       # Daniel decide() → Varick
    band: Literal["act", "ask", "none"]
    hit: SearchHit | None        # None iff band == "none"
    verdict: Verdict | None = None

class Query(BaseModel):          # Varick extract()
    kind: Literal["find", "recall"]
    object: str                  # "keys", "whiteboard"
    text: str                    # what gets embedded: "a photo of keys"

class Moment(BaseModel):         # Daniel recall() (R13)
    start_ts: float
    end_ts: float
    frame_ids: list[int]         # 3–5 for the strip, in time order
    peak_z: float

class Answer(BaseModel):         # Varick → ask page, dashboard, eval runner
    q: str
    kind: Literal["find", "recall"]
    object: str
    band: Band
    message: str                 # card headline in words (ui.md → Card copy)
    hit: SearchHit | None
    frame_url: str | None        # "/frames/123.jpg"
    ago_s: float | None          # asked_ts − hit.ts (server clock; phone clock never used)
    spot: str | None = None      # R8 "where"
    sightings: list[SearchHit] = []   # R11 timeline, newest first
    moments: list[Moment] = []        # R13
    asked_ts: float
    timings_ms: dict[str, float] = {} # extract, embed, rank, verify, decide, total
    error: str | None = None

class IndexStats(BaseModel):     # Daniel → Aziz's /status
    backend: Literal["stub", "gemma"]
    dtype: str                   # "bfloat16" | "float32" | "stub"
    frames_indexed: int
    frames_dup: int
    frames_failed: int
    last_indexed_ts: float | None
    embed_ms_p50: float | None

class ReplayJob(BaseModel):      # Aziz (R5)
    id: int
    video: str                   # file name under data/videos/
    start_clock: str             # "HH:MM:SS" local time the recording started
    speed: float                 # 0 = as fast as the index keeps up (tests); 1 = real time (demo fallback)
    state: Literal["queued", "running", "done", "failed"]
    frames_total: int | None
    frames_done: int
    error: str | None = None

class StatusSnapshot(BaseModel): # Aziz GET /status (dashboard, R12)
    now: float
    mode: Literal["idle", "streaming", "stalled", "replaying"]
    frames_received: int
    frames_dropped: int
    last_frame_id: int | None
    last_frame_ts: float | None
    ingest_lag_s: float | None   # now − last_frame_ts; ≥ 3 → "stalled"
    queue_depth: int
    index: IndexStats
    replay: ReplayJob | None
```

## JSDoc mirror (`static/card.js` top; static pages have no build step)

```js
/** @typedef {"act"|"ask"|"none"|"error"} Band */
/** @typedef {{frame_id:number, ts:number, score:number, z:number, path:string, visit_start:number, visit_end:number, n_frames:number}} SearchHit */
/** @typedef {{start_ts:number, end_ts:number, frame_ids:number[], peak_z:number}} Moment */
/** @typedef {{q:string, kind:"find"|"recall", object:string, band:Band, message:string, hit:?SearchHit, frame_url:?string, ago_s:?number, spot:?string, sightings:SearchHit[], moments:Moment[], asked_ts:number, timings_ms:Object<string,number>, error:?string}} Answer */
/** @typedef {{backend:"stub"|"gemma", dtype:string, frames_indexed:number, frames_dup:number, frames_failed:number, last_indexed_ts:?number, embed_ms_p50:?number}} IndexStats */
/** @typedef {{id:number, video:string, start_clock:string, speed:number, state:"queued"|"running"|"done"|"failed", frames_total:?number, frames_done:number, error:?string}} ReplayJob */
/** @typedef {{now:number, mode:"idle"|"streaming"|"stalled"|"replaying", frames_received:number, frames_dropped:number, last_frame_id:?number, last_frame_ts:?number, ingest_lag_s:?number, queue_depth:number, index:IndexStats, replay:?ReplayJob}} StatusSnapshot */
```

## Functions each slice exposes — and exactly what the stub returns

| Owner | Function | Real behavior | Stub returns (S0 skeleton) |
|---|---|---|---|
| Daniel | `index.load() -> None` | Load EG2 (bf16/fp32), rebuild matrix from `embeddings` table | no-op |
| Daniel | `index.add(records: list[FrameRecord]) -> list[AddResult]` | Embed batch, R4 dup check, append to matrix + table | remembers records; each `AddResult(status="embedded", embed_ms=0.0)` |
| Daniel | `index.search(text: str, k: int = 10) -> list[SearchHit]` | Rank per architecture.md; ≤ k visits, z ≥ z_min, **newest first** | no records or "passport" in text → `[]`; "sunglasses" → newest record, z 4.0, score 0.30 (Ask); else newest record z 6.0, score 0.35 + oldest record z 3.5, score 0.29 (if ≥ 2). Visit = the one frame |
| Daniel | `index.decide(hits, verdicts: dict[int, Verdict] \| None = None) -> Decision` | Decision table in architecture.md (`verdicts` keyed by frame_id) | the real z-only rule (it's 10 lines) |
| Daniel | `index.recall(text: str) -> list[Moment]` | R13 stretches | `[]` |
| Daniel | `index.stats() -> IndexStats` | live counters | `backend="stub"`, `dtype="stub"`, counts of remembered records |
| Aziz | `capture.start_worker() / stop_worker()` | ingest worker thread | starts/stops a thread that calls `index.add` |
| Aziz | `capture.status() -> StatusSnapshot` | live counters | real counters (they're trivial) |
| Varick | `answer.extract(q: str) -> Query \| None` | regex set (R6) | `where (is\|are) my (.+?)\??$` → find; else `None` |
| Varick | `answer.ask(q: str) -> Answer` | extract → search → [verify] → decide → card | `answer_act.json` with `q`, `object`, `asked_ts` filled; "passport" → `answer_none.json` |
| Varick | `answer.latest() -> Answer \| None` | last Answer served | last stub Answer |
| Varick | `verify(frame_path: str, obj: str) -> Verdict \| None` | R8 via backend | `None` (no verdict) |
| Varick | `verify_many(frame_paths: list[str], obj: str) -> list[Verdict \| None]` (PROPOSED, the batch form) | one GPU batch | `[None] * len(frame_paths)` |

## HTTP endpoints

| Method + path | Owner | Request | Response |
|---|---|---|---|
| `POST /frames` | Aziz | **PROPOSED:** raw JPEG body, `Content-Type: image/jpeg`, query `?ts=<client epoch ms>` (no multipart → no python-multipart dep) | `200 {"id": int, "ts": float}` · `400` not a JPEG · `413` > 2 MB |
| `GET /frames/{id}.jpg` | Aziz | — | `image/jpeg` · `404` |
| `GET /status` | Aziz | — | `StatusSnapshot` |
| `POST /replay` | Aziz | `{"video": "day.mp4", "start_clock": "14:32:10", "speed": 0}` | `202 ReplayJob` · `409` if one is running |
| `GET /replay` | Aziz, PROPOSED | — | `ReplayJob \| null` (latest) |
| `GET /` | Aziz, PROPOSED | — | `dashboard.html` (open on localhost for the projector) |
| `GET /camera` | Aziz, PROPOSED | — | `camera.html` |
| `GET /ask` | Varick | **PROPOSED:** no `q` → `ask.html`; with `q` → JSON | `Answer`. Always `200`; internal failure → `band="error"`, `error` set |
| `GET /ask/latest` | Varick, PROPOSED | — | `Answer \| null` (dashboard card, R12) |
| `POST /ask/voice` | Varick, PROPOSED (R10) | audio body (Safari MediaRecorder `audio/mp4`) | `{"text": str}` — audio kept in memory only, never written |
| `GET /static/*` | Aziz (mount) | — | files in `static/` |

## Fixtures (`tests/fixtures/`, copied at S0, frozen)

`answer_act.json`:
```json
{"q": "Where are my keys?", "kind": "find", "object": "keys", "band": "act",
 "message": "Your keys: seen 12 min ago (2:41 PM).",
 "hit": {"frame_id": 812, "ts": 1792964460.0, "score": 0.35, "z": 6.2, "path": "frames/000812.jpg",
         "visit_start": 1792964458.0, "visit_end": 1792964463.0, "n_frames": 4},
 "frame_url": "/frames/812.jpg", "ago_s": 720.0, "spot": null,
 "sightings": [{"frame_id": 812, "ts": 1792964460.0, "score": 0.35, "z": 6.2, "path": "frames/000812.jpg",
                "visit_start": 1792964458.0, "visit_end": 1792964463.0, "n_frames": 4}],
 "moments": [], "asked_ts": 1792965180.0,
 "timings_ms": {"extract": 1, "embed": 80, "rank": 12, "verify": 0, "decide": 0, "total": 95}, "error": null}
```
- `answer_ask.json` = act with `band "ask"`, `z 4.1`, `message "Might be these. Seen 12 min ago."`
- `answer_none.json`: `{"q": "Where is my passport?", "kind": "find", "object": "passport", "band": "none", "message": "I haven't seen your passport.", "hit": null, "frame_url": null, "ago_s": null, "spot": null, "sightings": [], "moments": [], "asked_ts": 1792965180.0, "timings_ms": {"total": 90}, "error": null}`
- `answer_recall.json` = none-shaped with `kind "recall"`, `object "whiteboard"`, `band "act"`, `message "You were at the whiteboard 2:47–2:49 PM."`, one Moment with 4 `frame_ids`.
- `answer_error.json` = none-shaped with `band "error"`, `message "Something went wrong. Try again."`, `error "timeout"`.
