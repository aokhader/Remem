# Demo — script = acceptance test, roles, reset, backup video, submission

**Done = rows 1–6 pass twice in a row on venue Wi-Fi.** Total 3 min. From 5:30 PM the wearer streams live and moves normally; **keys go on a table, on camera, at least 10 min before presenting.**

## Roles — PROPOSED (open question in the spec)

| Role | Who (PROPOSED) | Why | Holds |
|---|---|---|---|
| Wearer | Aziz | Owns the camera page + mount; can spot a stall | Camera iPhone on forehead, power bank in pocket |
| Asker | Varick | Owns the ask page + card | Ask iPhone |
| Presenter | Daniel | Can answer retrieval / z-score / "why not just a threshold" questions | Laptop + projector |

## The 6 rows (spec)

| # | Time | Who | What happens | Passes when | Reqs |
|---|---|---|---|---|---|
| 1 | 0:00–0:20 | Presenter | Pitch in two lines. Point to the camera iPhone on the wearer's forehead and to the ask iPhone. | Live frame counter is climbing on the projected dashboard | R1 R2 R12 |
| 2 | 0:20–0:50 | Asker | Dictate or type "Where are my keys?" | Top result is a frame with the keys, shows "N min ago" and the clock time; **under 5 s** | R3 R6 R7 R9 |
| 3 | 0:50–1:30 | Judge A | Hides sunglasses where the wearer will walk past; wearer walks past once; Judge A asks "Where are the sunglasses?" | Newest frame shows the judge's chosen spot, not an earlier one (**live change**) | R3 R7 R9 |
| 4 | 1:30–1:55 | Judge B | "Where is my passport?" | Card says "I haven't seen your passport" and shows **no frame** (**failure path**) | R7 R9 |
| 5 | 1:55–2:30 | Asker | Stretch: "When was I at the whiteboard?" (if cut: keys' sighting timeline) | A time range and a strip of 3–5 frames appear | R13 / R11 |
| 6 | 2:30–3:00 | Presenter | Show README model table. Say: "Your whole day was stored and searched only on this laptop. Next step is Meta's glasses toolkit." | README with models and licenses is on screen | R16 |

Row 3 note: "Where are the sunglasses?" uses "are the", not "my" — R6's regex must accept it.

## Judge instructions (cue-card design: **TODO** — next step)

| Card | Text (from spec) |
|---|---|
| Judge A (row 3) | "Put these sunglasses somewhere the wearer will walk past. Don't say where." Then: "Now ask the phone: Where are the sunglasses?" |
| Judge B (row 4) | "Ask for something nobody brought, e.g. a passport." → "Where is my passport?" |

## Pre-show checklist (5:30 PM → presenting)

- [ ] cloudflared URL open on both iPhones; dashboard on projector at `http://localhost:8000/`
- [ ] Both iPhones: Auto-Lock Never, Low Power off, Safari in front, power bank connected to camera iPhone
- [ ] `REMEM_DATA_DIR=data/live`, `REMEM_INDEX=gemma`, `Z_MIN`/`Z_ACT` = tuned values in `.env`
- [ ] Keys on the table on camera ≥ 10 min before; dashboard last frame shows a level, sharp view
- [ ] Ask "where are my keys" once privately → Act with the right frame
- [ ] README on GitHub open in a browser tab (row 6); backup video file ready to play

## Reset procedure between runs

1. Sunglasses back in a bag, **off camera**. Keys stay on the table, on camera.
2. Don't wipe the index or restart anything that works (newest-wins makes run 2 correct).
3. Reload `/ask` on the ask iPhone (idle state). Dashboard: counter climbing, mode LIVE, ingest lag < 3 s.
4. Wearer resumes normal movement; wait ≥ 30 s before row 1.
5. If something broke: restart uvicorn only (index reloads from disk); never cloudflared unless dead (new URL → reopen both phones).

## Backup video (6:00–6:10, right after the freeze)

Record rows 1–6 in one take. If live Wi-Fi or a phone fails on stage, play it and **say it's a recording**. Same video goes in the submission.

| Shot | Row | Capture with | Shows |
|---|---|---|---|
| 1 | 1 | Phone video (PROPOSED: a 4th phone/laptop webcam) | Wearer with forehead iPhone + projected dashboard counter climbing |
| 2 | 2 | iOS screen recording on the ask iPhone | Dictating "Where are my keys?" → Act card, "N min ago · clock" |
| 3 | 3 | Phone video + ask iPhone screen recording | Sunglasses placed, wearer walks past, ask → new spot |
| 4 | 4 | ask iPhone screen recording | Passport → "I haven't seen your passport", no frame |
| 5 | 5 | ask iPhone screen recording | Recall range + strip (or keys' timeline) |
| 6 | 6 | Laptop screen recording | README model table + "stored and searched only on this laptop" |

Who films: PROPOSED — Presenter films shots 1 and 3 on their own phone; Asker screen-records on the ask iPhone.

## Submission checklist

| Time | Item | Owner |
|---|---|---|
| 5:45 | README final: pitch, how to run, **model table** (every model, license, what it does), "Built with Claude Code", 3 test-set numbers (`data.md`) | All (sections per owner) |
| 5:45 | Repo public; Apache-2.0 `LICENSE` at root; no `.env`, weights, frames, videos, `*.db` committed | Aziz |
| **6:00** | **Code freeze (gate 3).** Tag `v1-demo` (PROPOSED) | Aziz |
| 6:00–6:10 | Backup video recorded (above) | All |
| 6:10–6:15 | Submit: repo URL + video (source code required, video encouraged). **Target 6:15** | Aziz |
| 6:30 | Submissions close | — |

Submission platform/form isn't named in the spec — find it before 5:45 (open question).
