# Decisions — time · decision · why · who

> Append-only. Log new decisions in **your own section** at the bottom (separate sections = no merge conflicts). After gate 1, any change to `contracts.md` needs the owner's OK and a line here. Don't reopen a decision in "Already decided" without the whole team.

## Already decided (kickoff — don't reopen)

| Time | Decision | Why | Who |
|---|---|---|---|
| kickoff | Name: **Remem** | — | Team |
| kickoff | Demo laptop: Windows + WSL2, NVIDIA GPU, CUDA visible in WSL | The GPU we have | Team |
| kickoff | Python, FastAPI + uvicorn; JPEGs on disk + SQLite rows + one in-RAM NumPy matrix; **no vector DB** | Team knows Python; 3 h at 1 fps ≈ 10,800 × 768 floats ≈ 33 MB → brute force takes ms | Team |
| kickoff | Static HTML/JS served by FastAPI, no build step, poll every 1 s | Quick tunnels don't support Server-Sent Events | Team |
| kickoff | cloudflared quick tunnel inside WSL next to uvicorn | Camera needs HTTPS; outbound tunnel skips venue client isolation + WSL inbound NAT | Team |
| kickoff | All models free from Hugging Face. **No Google Cloud / Vertex AI** (no billing account), no paid APIs | Cost + nothing leaves the laptop | Team |
| kickoff | Core model **EmbeddingGemma 2** (`google/embeddinggemma-2`) via sentence-transformers, `config_kwargs={"audio_config": None}`; bfloat16 if `is_bf16_supported()` else float32, **never float16**; 768-d normalized; images `{"image": ...}`, no prefix | Open (Apache 2.0), text + images in one space; float16 gives NaN/worse vectors silently | Team |
| kickoff | **Gemma 4 is a nice-to-have** (R8, Could): `google/gemma-4-E4B-it` via transformers on GPU, image before text, `enable_thinking=False`, JSON-only, 4-bit if VRAM short; ~15 GB download only if R8 is attempted | Prize may need it; core works without it; no Google Cloud because there is no billing account | Team |
| kickoff | Camera iPhone on the forehead, Safari, rear camera, 640 px JPEG every 1000 ms; ask iPhone on `/ask` with iOS dictation; laptop dashboard on projector | No app install; honest glasses stand-in | Team |
| kickoff | **Retrieval ranks, deterministic code decides** | Predictable on stage | Team |
| kickoff | **Never a raw cosine cutoff**; robust z-score within each query | Image-to-text scores aren't calibrated | Team |
| kickoff | **The answer is the newest candidate**, not the highest score | The user wants the last sighting | Team |
| kickoff | Bands without R8: Act z ≥ z_act (5), Ask z_min ≤ z < z_act (z_min 3), None if no candidate. With R8: newest frame Gemma says present wins; conf ≥ 0.8 Act, 0.5–0.8 Ask | Spec decision rule | Team |
| kickoff | All cutoffs set from the 40-query test set at 4:45–5:15 | Placeholders until measured | Team |
| kickoff | Nothing leaves the laptop; no audio is recorded | Bystander privacy | Team |
| kickoff | Owners: Aziz R1 R2 R5 R12 R15 · Daniel R3 R4 R7 R13 · Varick R6 R9 R10 R11 R14 (+R8) · All R16 | Three parallel slices | Team |
| kickoff | Interface names fixed: `POST /frames`, `index.search(text, k)`, `verify(frame_path, object)` (stub = no verdict), `GET /ask?q=` | Stub-first integration | Team |
| kickoff | Public GitHub repo, Apache-2.0; README names every model + license + role, "Built with Claude Code", 3 test-set numbers | Submission rules / Open-Source theme | Team |
| kickoff | Gate 2 go/no-go: if the replayed day fails "where are my keys" at 4:45, cut R10–R13. Coulds (incl. R8) only after rows 1–4 pass twice. Freeze 6:00 | Protect the Musts | Team |
| kickoff | Cue cards are a next step; `demo.md` keeps the judge instructions, design TODO | Time | Team |

## Needs sign-off at gate 1 (3:15 PM)

Each PROPOSED item below is a concrete choice where the spec is silent. Owner says OK or edits it, then moves the line to "Already decided".

| # | PROPOSED | Where | Sign-off |
|---|---|---|---|
| P1 | Aziz ships the S0 skeleton and owns `app.py`, `config.py`, `pyproject.toml`; `contracts.py` frozen at gate 1 | architecture.md | All |
| P2 | Repo layout + module names (`remem/capture`, `remem/index`, `remem/answer`, `static/`, `eval/`, `spikes/<name>/`) | architecture.md | All |
| P3 | `index.search` returns **merged visits, newest first**, `SearchHit` fields as written | contracts.md | Daniel, Varick |
| P4 | Retrieval order: all frames with z ≥ z_min → merge into visits → keep the 10 newest visits (spec updated 15:39; top-10-frames-first let a long older visit hide the newest) | spec.md, architecture.md | Daniel |
| P5 | `decide(hits, verdicts)` lives in Daniel's slice and implements the R8 branch too; Varick only produces Verdicts | contracts.md | Daniel, Varick |
| P6 | `verify_many(frame_paths, obj)` batch form next to the spec's `verify(frame_path, object)` | contracts.md | Varick |
| P7 | `POST /frames` = raw JPEG body + `?ts=<ms>` (no multipart, no python-multipart dep) | contracts.md | Aziz |
| P8 | `GET /ask` without `q` serves `ask.html`; with `q` returns JSON (spec uses `/ask` for both) | contracts.md | Varick |
| P9 | Extra endpoints: `GET /`, `GET /camera`, `GET /replay`, `GET /ask/latest`, `POST /ask/voice` | contracts.md | Aziz, Varick |
| P10 | Canonical `ts` = server receive time; `ago_s` computed server-side; replay `ts` = `start_clock` + video offset; replay `speed` 0 (fast, blocking) or 1 (real time) | contracts.md | Aziz, Daniel |
| P11 | Stub return values (deterministic: passport → none, sunglasses → ask, else act) | contracts.md | All |
| P12 | `MIN_FRAMES=30` and MAD = 0 → no candidates; verify timeout → z-only bands | architecture.md | Daniel, Varick |
| P13 | Latency budget table; freshness ≤ 3 s; ask-page timeout 8 s; stalled after 3 s | architecture.md, ui.md | All |
| P14 | Band words FOUND / MAYBE / NOT SEEN / ERROR + symbols + colors `#1B7F3B #B26A00 #4A4A4A #B3261E`; JPEG quality 0.7; "N min ago" rules | ui.md | Varick, Aziz |
| P15 | SQLite schema: one table per owner (`frames`, `embeddings`, `verdicts`), float32 BLOB vectors, reload matrix on start | data.md | All |
| P16 | `ground_truth.csv` extra columns `kind`, `end_clock_time`; 4 recall landmarks; never-seen list; test-set ID layout; tie-break "never-seen → None wins" | data.md | Aziz, Varick, Daniel |
| P17 | Varick writes `test_set.csv`; Daniel owns `run_testset.py`; Aziz owns `ground_truth.csv` | data.md | All |
| P18 | Recording: strip audio on import (`ffmpeg -an`); move file via a Mac (AirDrop can't reach Windows) | data.md | Aziz |
| P19 | `.env` names/defaults incl. `EMBED_IMAGE_TOKENS=280`, `EMBED_BATCH=8`, `INGEST_QUEUE_MAX=8`, `DEDUPE_COS=0.98`, `TZ=America/Los_Angeles`; `config.py` parses `.env` itself | setup.md | All |
| P20 | `apt install ffmpeg` (torchcodec + audio strip); `ruff`, `pytest` dev deps | setup.md | Aziz |
| P21 | R10 speech model `openai/whisper-small` via transformers; R15 face blur with OpenCV Haar cascade (new dep) | setup.md, slices | Varick, Aziz |
| P22 | R8 fallback backend id `google/gemma-4-E2B-it` (verify on HF) | architecture.md | Varick |
| P23 | Timeouts per call; branch names `aziz/capture`, `daniel/index`, `varick/answer` | code-standards.md | All |
| P24 | A minimal dashboard counter (part of R12) is pulled into Aziz's pre-gate-2 work because row 1 needs it | progress.md | Aziz |
| P25 | Roles: Aziz wearer, Varick asker, Daniel presenter; backup-video filming plan; tag `v1-demo` at freeze | demo.md | All |
| P26 | R6 extraction patterns incl. "where are the X" and recall routing "when was I at X"; `ask.html?fixture=` dev flag | slices/varick-answer.md, ui.md | Varick |
| P27 | R13 recall: merge gap 20 s, stretches ≥ 10 s, 3–5 evenly spaced frames | slices/daniel-index.md | Daniel |

## Log — Aziz

| Time | Decision | Why | Who |
|---|---|---|---|
| 15:39 | spec.md consistency pass: wrote P4, P6, P8, P10, P12, P16, P18, P20, P24, P26 into the spec; find-query windows now run from the last placement/move to `end`; recall band = Act if any stretch, else None; privacy line = "stored and searched only on this laptop". Owners still sign off their P items at gate 1 | Spec contradicted itself and the context folder; frames do leave via the answer card and Cloudflare's edge | Aziz |
| 15:47 | ruff `I001` ignored for `remem/contracts.py` only | Keeps it a verbatim copy of contracts.md (no blank line between imports) | Aziz |
| 15:47 | `config.py` defaults = `.env.example` values, so `REMEM_INDEX` defaults to `gemma`; off-GPU dev sets `REMEM_INDEX=stub` | One source of defaults | Aziz |
| 15:47 | `/status` counters come from SQLite on every poll (`COUNT`, `SUM(dropped)`, last row), no in-memory counters | Restarts keep the counter; no extra state | Aziz |
| 15:47 | Placeholder `static/camera.html`, `dashboard.html`, `ask.html` at S0 | `GET /`, `/camera`, `/ask` return 200 before the real pages land | Aziz |
| 15:47 | Fixture values not given in contracts.md were filled in: recall Moment 14:47:00–14:49:30 PDT, `frame_ids` 1172/1222/1272/1322, `peak_z` 5.0; error fixture reuses the none fixture's passport question | Illustrative only, consistent with the act fixture's 2:41 PM clock | Aziz |
| 16:02 | Demo laptop runs uvicorn + cloudflared in WSL but from the Windows checkout: `cd /mnt/d/Documents/GitHub/Remem && REMEM_DATA_DIR=$HOME/remem-data/live ~/.venvs/remem/bin/uvicorn remem.app:app --host 127.0.0.1 --port 8000 --workers 1`; venv + HF cache in `~`; cloudflared binary in `~/.local/bin` (no sudo) | One checkout for editing; Linux CUDA wheels + ffmpeg already in WSL; DATA_DIR must be on the Linux side (SQLite WAL is unreliable on `/mnt/d`) | Aziz |
| 16:02 | Camera frames are portrait 640×853 (3:4), ~65 KB | Phone held upright on the forehead; 640 px is the width as specified. Daniel: no resize assumptions | Aziz |

## Log — Daniel

| Time | Decision | Why | Who |
|---|---|---|---|
| 15:38 | Run Gate 1 spike in isolated Windows venv reusing CUDA torch; retain 280 image tokens and `a photo of {X}` + SearchQuery | User approved spike dependencies; neither WSL distribution has model packages. GPU bf16 works; median 123.50 ms, keys #1. All six A/B variants tie on ranking; defer query changes until larger evaluation. Re-normalize vectors in float32 after bf16 rounding. | Daniel |
| 16:01 | P4: follow revised spec: merge every z-qualified candidate before retaining the newest 10 visits | Prevent a long older visit hiding a newer visit; covered by regression check. Keep MIN_FRAMES/MAD guards and default thresholds. | Daniel |
| 16:01 | User-approved cross-slice edit: optional keyword-only `ts` on `capture.store.save`, allowed only for finite replay timestamps | CLI `add-folder --start` needs persistent replay time; live frames still use server receive time. All frame-table writes stay in capture store. Config and contracts unchanged. | Daniel |
| 16:01 | Model inference offline from cache; bounded single GPU worker; 5 s image and 2 s query deadlines, discard late results | Keep questions responsive without unbounded queued kernels or late index writes. Startup load synchronous. Stored model/image budget mismatches fail loudly. | Daniel |
| 16:01 | Use MIN_FRAMES=3/Z_MIN=0.5 only for labelled three-photo CLI diagnostic; retain production defaults 30/3 | Three photos cannot validate calibrated retrieval; default guard returns none. 60-frame throughput fixture repeats supplied photos and is not an accuracy dataset. | Daniel |
| 16:12 | `decide` distinguishes None (disabled/whole-call timeout → z-only) from {} (completed verification without positives → None); newest present verdict wins and its confidence alone sets band | Preserve newest-wins rather than falling back to an older more-confident frame. A newest positive below CONF_ASK returns None. Pure decision tests only; R8 models remain gated. Varick's adapter currently collapses {} to None and needs correction before real R8 activation. | Daniel |
| 16:12 | Sweep uses production score/robust-z/visit functions; one query encode per find row, candidates z >= 1.5 logged locally; search grid 0.25, zero false-found first | Avoid calibration drift, reject infeasible thresholds honestly, and never use in-process timing as HTTP latency. No config or .env edits. | Daniel |
| 16:12 | Keep all 3 final README numbers pending; isolate 40-request localhost smoke on the 3-photo database as diagnostic only | Draft has 28 present + 4 recall windows blank and no real recording; MIN_FRAMES suppresses search on 3 photos. No invented ground truth or demo accuracy claims. | Daniel |

| 16:42 | R4 compares normalized image cosine to the last kept vector with inclusive DEDUPE_COS; persist dup_of with no vector, serialize add calls, restore anchor from stored matrix | Prevent gradual drift through discarded frames and keep behavior consistent across batches/restarts. Older backfills are retained instead of matched to future captures. | Daniel |
| 16:42 | R4 preserves all frame timestamps/JPEGs and keeps first-frame age during a stationary run; calibrate on a fresh deduplicated replay | Frame-table writes belong to capture; changing a timestamp without changing its JPEG would misstate the shown frame's capture time. MIN_FRAMES counts kept vectors. Final metrics remain pending real recording/reference windows. | Daniel |

## Log — Varick

| Time | Decision | Why | Who |
|---|---|---|---|
| 15:41 | Slice branch is `varick-answer` (code-standards.md says `varick/answer`) | Branch already created on GitHub with that name | Varick |
| 15:41 | Build against a dev shim in `spikes/varick/devshim/` (contracts verbatim, config subset, index stub, dev server); delete it once S0 is on main | S0 skeleton not on main yet; shim keeps every edit inside my slice | Varick |
| 15:41 | Code reads `remem.config` as module constants named like the env vars (`config.Z_ACT`, `config.TOP_K`, `config.QUERY_TEMPLATE`, `config.TZ`…) — **needs Aziz's OK** | contracts.md doesn't define the config API | Varick |
| 15:41 | Added `remem/answer/pipeline.py` (`ask`, `latest`) and `static/dev-fixtures.js` (contract fixtures + an extra `timeline` fixture) | Keep routes thin; R11 needs a multi-sighting fixture | Varick |
| 15:41 | `timings_ms` reports `search` (embed + rank together) instead of separate `embed`/`rank` | Split happens inside Daniel's `search()`; his logs have the breakdown | Varick |
| 15:41 | Unparseable question → `band="error"`, message "Ask like: where are my keys?", `error="no object"`; recall with no moments → none, "I haven't seen you at the {X}." | Copy missing from ui.md | Varick |
| 15:41 | Recall query text uses `QUERY_TEMPLATE` too ("a photo of whiteboard") until Daniel picks a recall phrasing | R13 text not specified | Varick |
| 15:41 | `test_set.csv` T34–T36 objects and T38–T40 landmarks are guesses; windows blank until `ground_truth.csv` | Recording not logged yet | Varick |
| 15:41 | Logging setup (`logging.basicConfig`) belongs in `app.py`; the `ask …` timing line only prints once that's configured | app.py is Aziz's | Varick |
| 15:50 | R10 decodes with the ffmpeg CLI over pipes (no temp file) and runs `STT_MODEL` through the transformers ASR pipeline, English forced, **float32 pinned** (transformers 5 defaults to `dtype="auto"`) | Audio never touches disk; predictable precision; no new dependency (ffmpeg is P20) | Varick |
| 15:50 | Speech model warms in the background when `/ask` (the page) is opened; a clip sent before it's loaded gets `504` and the page says "type your question" | No app.py change needed; first load takes seconds (32 s incl. download for whisper-tiny on Mac CPU) | Varick |
| 15:50 | Clips quieter than RMS 0.003 or shorter than 0.25 s are rejected (`422`) instead of transcribed | Whisper invents "Thank you." on silence | Varick |
| 15:50 | Added a `listening` state to the ask page (R10) | ui.md listed none for push-to-talk | Varick |
| 15:50 | Contract change (my endpoint): `POST /ask/voice` now lists its error codes 400/413/422/503/504; added an R10 smoke row to setup.md | Clients need to tell "type instead" from "try again" | Varick |
| 15:58 | Merged S0 into `varick-routing`; my real `remem/answer/*` and `static/ask.html` replace the S0 placeholders; devshim copies of contracts/config/index deleted (devserver now uses the real package with `REMEM_INDEX=stub`) | S0 landed; one copy of each shared file | Varick |
| 15:58 | Config API confirmed by S0: module constants. Only change needed: `config.DATA_DIR` (absolute Path) instead of `REMEM_DATA_DIR` | Matches Aziz's config.py | Varick |
| 15:58 | `remem.answer` loads `ask`/`latest` lazily (module `__getattr__`) | `config.py` defaults to `REMEM_INDEX=gemma`, which doesn't exist yet; `test_extract.py` shouldn't need any index backend | Varick |

## Log — Team (gate decisions, cuts, cutoffs)

| Time | Decision | Why | Who |
|---|---|---|---|
