# Code standards — enough to keep three parallel slices mergeable

## Python

| Rule | Detail |
|---|---|
| Version | Python 3.11+ (`X \| None`, `Literal`, pydantic v2) |
| Types | Type hints on every function signature; shapes come from `remem/contracts.py`, never redefined locally |
| Lint | `ruff check .` clean before every merge to main (config in `pyproject.toml`, owned by Aziz) |
| Config | Read env vars only through `remem/config.py`; every var is listed in `setup.md` → .env.example. No literals for cutoffs (Z_MIN, Z_ACT, CONF_*) in code |
| Secrets | No tokens in code, logs, commits or Claude transcripts. `.env` is gitignored. Never print `HF_TOKEN` |
| Heavy imports | `torch`, `sentence_transformers`, `transformers`, `bitsandbytes` imported **only** inside `remem/index/gemma.py` and R8/R10 backends — stub mode must run without them |
| FastAPI | Route handlers that touch the GPU or SQLite are sync `def` (threadpool), not `async def`. One process, `--workers 1` |
| SQLite | WAL mode; one connection per thread; each owner writes only its own table (`data.md`) |
| Errors | Never crash the request: `/ask` returns `band="error"` with a short `error`; ingest marks the frame `failed` and moves on |

## Timeouts — on every model call and every HTTP call

| Call | Timeout (PROPOSED) | On timeout |
|---|---|---|
| Image embed batch (ingest worker) | 5 s | mark batch `failed`, keep going |
| Text embed (`/ask`) | 2 s | `band="error"` |
| Whole `/ask` | `ASK_TIMEOUT_S` = 5 s | `band="error"` |
| R8 `verify_many` | `VERIFY_TIMEOUT_S` = 2.5 s | fall back to z-only bands |
| R10 transcription | 4 s | keep text box; "Type your question" |
| Browser `fetch` (ask page) | 8 s, `AbortController` | error state |
| Browser `fetch` (camera POST) | 3 s | count as a failure → stalled after 3 |

GPU calls can't be cancelled mid-kernel: run them in a worker thread, `wait_for` the result, and let a late result be discarded.

## Logging — per-stage timing, one line per event

```
ask q="where are my keys" obj=keys band=act z=6.2 extract_ms=1 embed_ms=82 rank_ms=11 verify_ms=0 total_ms=97
ingest id=812 src=live bytes=48211 save_ms=3 queue=2
embed batch=8 embed_ms=410 dup=1 failed=0
```
`logging` module, INFO level, no frame bytes, no vectors, no tokens. `timings_ms` in every Answer mirrors the `ask` line.

## Tests — only the ones that matter today

| Test | Owner | Why |
|---|---|---|
| `tests/test_decide.py` — table of hits/verdicts → band (act, ask, none, newest-not-highest wins, R8 present/confidence rows, verify timeout → z rule) | Daniel | The decision rule is what judges see; it's pure and cheap to test |
| `eval/run_testset.py` — retrieval on the 40-query test set | Daniel | Sets z_min/z_act; produces the README numbers |
| `tests/test_extract.py` — every phrasing in `test_set.csv` → right object | Varick | One wrong regex = wrong answer on stage |
No UI tests, no ingest tests — smoke checks in `setup.md` cover them.

## JS / HTML

Plain ES modules, no build step, no CDN. `card.js` exports `renderCard(el, answer)` (Varick); dashboard imports it. Use the JSDoc typedefs from `contracts.md`. Every `fetch` has an `AbortController` timeout.

## Git

| Rule | Detail |
|---|---|
| `main` always runs | Merge only after your smoke checks pass on main + your branch |
| Branch per slice | `aziz/capture`, `daniel/index`, `varick/answer` (short-lived topic branches off them are fine) |
| Commits | `[slice] verb: what` — e.g. `[index] add: robust z-score ranking`, `[capture] fix: drop oldest not newest` |
| Merge | `git pull --rebase origin main` on your branch, smoke check, then fast-forward/merge to main, push |
| Never | force-push main · commit `.env`, model weights, `data/`, frames, videos, `*.db` · edit another slice's files |
| Ask first | deleting files, adding a dependency (`pyproject.toml` is Aziz's), any destructive git command |

`.gitignore` (S0): `.env`, `.venv/`, `data/`, `*.db*`, `*.mp4`, `*.mov`, `*.MOV`, `*.jpg` outside `static/`, `eval/results/*` except `summary.md`, `__pycache__/`, HF caches.

## WSL notes

- Clone under `~` (Linux filesystem), **not** `/mnt/c/...` — 10× slower I/O and CRLF trouble.
- `.gitattributes`: `* text=auto eol=lf` (S0) so Windows editors don't break shell scripts.
- Keep `HF_HOME` on the Linux filesystem (`~/.cache/huggingface`).
- uvicorn **and** cloudflared both run inside WSL (the tunnel is outbound, so WSL's inbound NAT doesn't matter).
- `TZ=America/Los_Angeles` in `.env` — WSL clocks often default to UTC.
