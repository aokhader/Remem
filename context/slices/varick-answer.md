# Slice — Varick: ask page, answer card, UI (+ R8)

**Mission:** turn a dictated or typed question into a card a judge reads at a glance: the right frame, how long ago, and the band **in words**.

| ID | What | Priority | Demo row |
|---|---|---|---|
| R6 | Ask page (text box + iOS dictation) + object regex | Must | 2–5 |
| R9 | Answer card: frame, "N min ago · clock", band; "I haven't seen your X" | Must | 2–4 |
| R11 | Sighting timeline (10 newest candidate visits on a time strip) | Should | 5 fallback |
| R10 | Push-to-talk, transcribed locally (PROPOSED `openai/whisper-small`) | Should | 2 (nice) |
| R14 | Read the answer aloud on the ask iPhone (`speechSynthesis`) | Could | — |
| R8 | Gemma 4 E4B double-check + spot line | Could | 2, 3 |
| — | `eval/test_set.csv` (40 queries) | — | 6 |

**Owns:** `remem/answer/` (`routes.py`, `extract.py`, `card.py`, `verify.py`, `stt.py`), `static/ask.html`, `static/card.js`, `static/card.css`, `tests/test_extract.py`, `eval/test_set.csv`, SQLite table `verdicts`, `spikes/varick/`.

**Consumes:** `index.search/decide/recall` (Daniel — stub until real) · `GET /frames/{id}.jpg` (Aziz) · `eval/ground_truth.csv` (Aziz, S1 3:45).
**Produces:** `GET /ask` (page without `q`, JSON with `q`), `GET /ask/latest`, `POST /ask/voice` · `Query`, `Answer`, `Verdict` · `verify` / `verify_many` · `renderCard(el, answer)` in `card.js` (Aziz's dashboard imports it) · `test_set.csv`.

## Stub due at gate 1 (3:15)

- `GET /ask?q=` returns `answer_act.json` (q/object/asked_ts filled); "passport" → `answer_none.json`.
- `ask.html` open on the **2nd iPhone over the tunnel**: sends a question, shows the stub card. `verify()` stub returns `None`.

## Definition of done

| Check | Row |
|---|---|
| "Where are my keys?" dictated → FOUND card with frame, "N min ago · 2:41 PM", **< 5 s** over the tunnel | 2 |
| "Where are the sunglasses?" extracts `sunglasses` (note "are the", not "my") | 3 |
| "Where is my passport?" → NOT SEEN card, **no frame** | 4 |
| "When was I at the whiteboard?" → recall route → range + strip, or the keys' R11 timeline | 5 |
| Every phrasing in `test_set.csv` extracts the right object (`test_extract.py`) | 2–5 |
| Band readable on the projector without color (word + symbol) | 1–4 |

## Extraction (R6) — PROPOSED rules

- Find: `where (is|are|'s) (my|the|your)? X`, `have you seen (my|the)? X`, `where did I (leave|put) (my|the)? X`.
- Recall: `when was I (at|by|near) (the)? X` → `Query(kind="recall")`.
- Normalize: lowercase; strip `?`, "now", "again", articles/possessives. Embed `QUERY_TEMPLATE` = `a photo of {X}` (find) or Daniel's chosen recall text.
- No match → strip question words, use what's left; empty → `band="error"`, "Ask like: where are my keys?".

## Fallbacks (stuck 20 min → take it, log it)

| Problem | Fallback |
|---|---|
| Dictation flaky | Type the question |
| R10 fails | Cut it; iOS dictation already works |
| Tunnel down | Ask from the laptop browser on `localhost:8000/ask` |
| R8 out of VRAM | `e4b-4bit` → `e2b` → `VERIFY_BACKEND=none` |
| R8 broken JSON / > 2.5 s | parse failure = not present; verify 3 newest; timeout → z-only bands |
| R14 silent on iOS | Skip; needs a user tap to start speech |

## R8 plan — only after demo rows 1–4 pass twice

Check VRAM (`nvidia-smi`) → start the ~15 GB download → backend per `architecture.md` → Verifier adapter. Prompt (spec, verbatim): *"Is {X} visible in this first-person photo? Reply JSON only: present (true/false), confidence (0–1), where (12 words max, name the surface or landmark)."* Image before text, `enable_thinking=False`, one batch for the newest `VERIFY_N`, cache in `verdicts` by (frame id, object). `decide()` (Daniel) already handles verdicts.

## You never wait for

Daniel → `REMEM_INDEX=stub` gives act/ask/none deterministically. Aziz → `ask.html?fixture=act|ask|none|recall|error`. Ground truth → draft all 40 phrasings first, windows after 3:45.

## First three tasks for Claude Code

1. **Gate 1 ask page.** "Build `static/ask.html`, `static/card.js` (`renderCard(el, answer)`, JSDoc typedefs from `context/contracts.md`) and `static/card.css` per `context/ui.md`: states idle/searching/act/ask/none/error, card layout, band word + symbol + color, 8 s `AbortController` timeout. Develop against `tests/fixtures/answer_*.json` via `?fixture=`, then wire to `GET /ask` (stub per contracts.md). Open it over the tunnel on the ask iPhone."
2. **R6 + real `/ask`.** "`remem/answer/extract.py` per my slice brief's extraction rules + `tests/test_extract.py`; then `answer.ask()`: extract → `index.search` → `index.decide` → `card.py` builds the `Answer` (copy from `context/ui.md`, `ago_s`, `timings_ms`), stores it as latest; `GET /ask/latest`. Show JSON for keys / sunglasses / passport with `REMEM_INDEX=stub`."
3. **Test set + R11.** "Write `eval/test_set.csv`: 40 rows per `context/data.md` (phrasings now, windows from `eval/ground_truth.csv` after 3:45); make `test_extract.py` cover every row. Then the R11 sighting timeline in `card.js`."

Then: tune with the team 4:45–5:15; R10/R11 at 5:15; R8 and R14 only after rows 1–4 pass twice.
