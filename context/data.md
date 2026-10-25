# Data — recorded day, test set, tuning, SQLite, disk layout

File owners: `eval/ground_truth.csv` Aziz · `eval/test_set.csv` Varick · `eval/run_testset.py` + `eval/results/summary.md` Daniel. Each SQLite table is created by its owner's code (`CREATE TABLE IF NOT EXISTS` at startup) — no shared migration file.

## The recorded day (Aziz, 3:15–3:45; spec → Data and decision rules)

- **~10 min from Ray-Ban Meta glasses**, worn normally, at the venue (decision 16:25). The glasses cap each clip at **3 min** (default 60 s: raise it in the Meta AI app's camera settings), so the day is **≥ 4 back-to-back clips** → `data/videos/day-1.mp4` … `day-N.mp4`, ~600 frames in total. Keep the gaps between clips short; nothing is seen in a gap.
- Quality doesn't need a setting: replay scales every frame to 640 px wide and ffmpeg decodes H.264 or HEVC, whatever resolution the glasses use.
- Each clip is replayed on its own, oldest first, with **its own** `start_clock`, so frame times stay true across the gaps. Read each clip's start from its metadata (`ffprobe … format_tags=creation_time`); if that tag is missing, use the capture time shown in the Meta AI app.
- 8 distinct props, each placed on camera and logged: **keys (bright keychain), sunglasses, water bottle, wallet, earbuds case, charger, notebook, mug**.
- Move **three** of them once mid-recording; log the new spot and time.
- Linger ≥ 1 min at 4 landmarks (one is the whiteboard) for the 4 recall queries (R13); log start + end. (PROPOSED)
- The wearer logs clock times on their phone (the glasses do the recording). Missed times are recovered from timestamped contact sheets of the clips.
- **No audio** (decision): the glasses record sound, so strip it on import — `ffmpeg -i <clip> -an -c:v copy data/videos/day-N.mp4`, then delete the original.
- Getting the clips to the Windows demo laptop: import them from the glasses in the Meta AI app (they land in the phone's camera roll), then AirDrop to a teammate's Mac → USB stick / LAN copy, or USB cable + Windows Photos import. **Never through a messaging app**: it downscales and strips the capture time. (PROPOSED)
- Push `eval/ground_truth.csv` by **3:45** (sync point S1).

## `eval/ground_truth.csv` — spec fields + PROPOSED extras

| Column | Spec? | Example | Notes |
|---|---|---|---|
| `object` | spec | `keys` | lowercase, same words as `expected_object` |
| `spot` | spec | `gray table by the laptop` | ≤ 12 words |
| `clock_time` | spec | `14:41:10` | local time (America/Los_Angeles), HH:MM:SS |
| `kind` | PROPOSED | `start` / `place` / `move` / `stretch` | `start` row = when recording began (replay `start_clock`) |
| `end_clock_time` | PROPOSED | `14:49:30` | only for `stretch` rows |

```csv
object,spot,clock_time,kind,end_clock_time
_recording,,14:32:10,start,
keys,gray table by the laptop,14:41:10,place,
water bottle,window ledge,14:44:00,place,
whiteboard,whiteboard by the door,14:47:00,stretch,14:49:30
water bottle,chair next to the projector,14:58:15,move,
```

## `eval/test_set.csv` — 40 scripted queries (spec schema)

`id,query,expected_object,expected_window,expected_band` — window, local time: `HH:MM:SS-end` for find queries (from the object's last placement/move −10 s to the end of the recording, because any later sighting of that spot is right too), `HH:MM:SS-HH:MM:SS` for recall stretches, or `NONE`.

| IDs | Count | Kind | Expected |
|---|---|---|---|
| T01–T24 | 24 | present: 8 props × 3 phrasings, 3 consecutive IDs per prop in the prop order above | window of the object's **last** placement/move; band `act` |
| T25–T32 | 8 | never-seen: passport, umbrella, cat + 5 more not at the venue (PROPOSED: guitar, tennis racket, frying pan, skateboard, teddy bear) | `NONE`, band `none` |
| T33–T36 | 4 | asked after a move ("…now"); 3 moved props + 1 second phrasing | new spot's window, `act` |
| T37–T40 | 4 | moment recall ("when was I at …") | stretch window, `act` |

- All 40 run **after the whole day has replayed**, so a moved prop's present queries also expect its newest spot.
- Phrasings must exercise R6's regex: "where are my X", "where is my X", "have you seen my X", "where did I leave my X", "where's my X", "when was I at the X".
- Varick drafts all 40 rows with windows blank by 3:45, fills windows from `ground_truth.csv` right after S1.
- Spec sample rows:
```csv
T01,where are my keys,keys,14:41:00-end,act
T04,where did I leave my sunglasses,sunglasses,14:52:20-end,act
T25,where is my passport,passport,NONE,none
T33,where is my water bottle now,water bottle,14:58:05-end,act
T37,when was I at the whiteboard,whiteboard,14:47:00-14:49:30,act
```

## Setting z_min and z_act (everyone, 4:45–5:15; Daniel runs the script)

1. Replay `day-1.mp4` … `day-N.mp4` once into `data/replay-day1/` (`speed: 0`, one job per clip, oldest first, each with its own `start_clock`). Embeddings persist, so restarts reload without re-embedding.
2. `python eval/run_testset.py --sweep` (in-process): for every query, log all frames with z ≥ 1.5, then sweep `z_min ∈ [2, 8]` and `z_act ∈ [z_min, 10]` in 0.25 steps.
3. Pick, per spec:
   - **z_act** = the lowest value with **zero wrong frames in Act** (wrong = newest visit doesn't overlap the expected window).
   - **z_min** = keeps the true frame in C for **≥ 90% of present queries** while **every never-seen query lands in None**.
   - If both can't hold, never-seen → None wins (false-found target is 0). Log it in `decisions.md`. (PROPOSED tie-break)
   - Expect z_min to rise: with ~600 frames, even pure noise puts a few frames above z = 3.
4. Write `Z_MIN`, `Z_ACT` to `.env`, restart, run `python eval/run_testset.py` end to end over HTTP on localhost. Look at the 28 answer frames once: a frame inside the window that doesn't show the object is still wrong.
5. Same for `CONF_ACT`/`CONF_ASK` (0.8/0.5) only if R8 ships.

**README numbers** (Daniel writes `eval/results/summary.md`; R16):

| Metric | Definition |
|---|---|
| Latest-sighting accuracy | Of T01–T24 + T33–T36 (28): band ∈ {act, ask} and the hit's visit overlaps `expected_window` |
| False-found count | Of T25–T32 (8): band ≠ `none`. Target 0 |
| Median seconds per answer | Median wall time of `GET /ask` from the runner on localhost (say "localhost, excludes tunnel" in README) |

Recall queries (T37–T40) are scored separately: any `moments[]` overlapping the window.

## SQLite (`DATA_DIR/remem.db`, WAL mode) — PROPOSED

```sql
-- Aziz (R2, R15)
CREATE TABLE IF NOT EXISTS frames (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ts        REAL NOT NULL,          -- epoch s UTC; server receive time (replay: start_clock + offset)
  client_ts REAL,                   -- phone clock; NULL for replay
  path      TEXT NOT NULL,          -- frames/000123.jpg (relative to DATA_DIR)
  source    TEXT NOT NULL CHECK (source IN ('live','replay')),
  dropped   INTEGER NOT NULL DEFAULT 0,  -- fell out of the ingest queue; never embedded
  blurred   INTEGER NOT NULL DEFAULT 0   -- R15
);
CREATE INDEX IF NOT EXISTS frames_ts ON frames(ts);
-- Daniel (R3, R4)
CREATE TABLE IF NOT EXISTS embeddings (
  frame_id     INTEGER PRIMARY KEY REFERENCES frames(id),
  status       TEXT NOT NULL CHECK (status IN ('embedded','dup','failed')),
  dup_of       INTEGER,             -- R4: kept frame it matched
  vec          BLOB,                -- 768 × float32 LE, L2-normalized; NULL unless embedded
  model        TEXT NOT NULL,       -- google/embeddinggemma-2
  image_tokens INTEGER,             -- max_soft_tokens used
  embed_ms     REAL
);
-- Varick (R8 verdict cache, keyed by (frame id, object))
CREATE TABLE IF NOT EXISTS verdicts (
  frame_id   INTEGER NOT NULL REFERENCES frames(id),
  object     TEXT NOT NULL,         -- lowercase, trimmed
  present    INTEGER NOT NULL,
  confidence REAL NOT NULL,
  where_     TEXT,
  backend    TEXT NOT NULL,
  ms         REAL,
  PRIMARY KEY (frame_id, object)
);
```
Rules: each owner writes only its own table; one connection per thread; vectors are cast to float32 before saving even when the model runs in bfloat16. The in-RAM matrix = `embeddings.status='embedded'` ordered by `frames.ts` (ids array, ts array, N × 768 float32).

## On-disk layout (`data/` is gitignored)

```
data/
├── videos/day-N.mp4        recorded day (Ray-Ban Meta clips), audio stripped (never committed)
├── live/                   DATA_DIR for the live demo (from 5:30 PM)
│   ├── remem.db (+ -wal, -shm)
│   └── frames/000001.jpg … one 640 px JPEG per frame (~50 KB each, estimate)
└── replay-day1/            DATA_DIR for test runs — same layout
```
Never mix live and replay frames in one DATA_DIR (newest-wins would compare across days). Switch with `REMEM_DATA_DIR` and restart.
