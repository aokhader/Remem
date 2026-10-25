# Verbatim copy of context/contracts.md → Data shapes. Frozen at gate 1: change only via the owner + decisions.md.
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
