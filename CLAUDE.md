# Remem — Claude Code project memory

**Pitch.** Remem answers "Where are my keys?" with the last frame your glasses saw them in: a forehead-worn iPhone streams 3 frames/s to a laptop, where EmbeddingGemma 2 indexes every frame. A second iPhone asks the question and gets back the newest matching frame, "N min ago" and the clock time, with every frame stored and searched only on the laptop.

Hack Day: Sun Oct 25 2026, DS3 @ UC San Diego. Team: Aziz (capture), Daniel (index), Varick (answer).

## Hard rules (never break these)

1. **Frames are stored and searched only on the laptop.** Only JPEGs in and answer cards out cross the tunnel. No cloud APIs, no Google Cloud/Vertex, no paid APIs, no audio saved.
2. **Never float16** for EmbeddingGemma 2. bfloat16 if `torch.cuda.is_bf16_supported()`, else float32.
3. **No raw score cutoffs.** Image-to-text cosine isn't calibrated; only the robust z-score within one query.
4. **Newest candidate wins**, not the highest score.
5. **Retrieval ranks, code decides.** Bands come from `decide()`, never from a model's free text.
6. **Stay in your slice.** Edit only files your slice owns (see `context/architecture.md` → File ownership). Need another slice's file or a contract change? Stop and say so.
7. **R8 (Gemma 4) and every Could start only after demo rows 1–4 pass twice.**
8. Don't invent data, numbers, or API calls. EmbeddingGemma 2 / Gemma 4 are new: check the model card or installed package first.

## Gates

| Gate | Time | Pass when |
|---|---|---|
| 1 | 3:15 PM | Every slice's spike done + stub live; repo, LICENSE, README skeleton pushed; PROPOSED items signed off |
| 2 | 4:45 PM | Replayed day answers "where are my keys" correctly end to end. **Go/no-go:** if not, cut R10, R11, R13 and R12 except its frame counter |
| 3 | 6:00 PM | Code freeze. Only demo-breaking fixes after this. Submit by 6:15, closes 6:30 |

## Map of context/ — read only what you need

| File | Read when |
|---|---|
| `context/slices/<you>.md` | **Every session start.** Your mission, files, tasks, fallbacks |
| `context/contracts.md` | **Every session start.** Data shapes, function signatures, endpoints, stub returns |
| `context/progress.md` | Every session start/end. Gates, R1–R16 status, your Now/Next/Blocked |
| `context/architecture.md` | Repo layout + file owners, process model, retrieval formula, failure table, parallel plan, diagrams |
| `context/ui.md` | Building any page: ask, camera, dashboard, answer card |
| `context/data.md` | SQLite schema, frame layout, ground_truth.csv, 40-query test set, tuning z_min/z_act |
| `context/setup.md` | Installing, running uvicorn + cloudflared, .env vars, per-slice smoke checks |
| `context/code-standards.md` | Before writing code or committing |
| `context/ai-workflow.md` | How a Claude Code session runs here (start, loop, stuck, end) |
| `context/demo.md` | Demo rows 1–6, roles, reset, backup video, submission checklist |
| `context/decisions.md` | Before changing anything already decided; log new decisions here |
| `context/overview.md` | Problem, users, goals/non-goals, user flows, glossary |
| `context/spec.md` | Source of truth (verbatim spec). Wins over every other file on conflicts |

## Session start

1. Read this file, `context/slices/<you>.md`, `context/contracts.md`, your section of `context/progress.md`.
2. Name the **one** task for this session (a requirement ID + demo row).
3. Plan in ≤5 bullets, build the smallest working version, run it, show the output, commit.

## Session end

1. Update your section of `context/progress.md` (Now / Next / Blocked) and your R-rows.
2. Log any decision in your section of `context/decisions.md` (time · decision · why · who).
3. Commit on your slice branch as `[slice] verb: what`, merge to main only if main still runs. Then `/clear`.
