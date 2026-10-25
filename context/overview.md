# Overview — what Remem is and who it's for

Source: `spec.md` → Overview, Goals and non-goals, Demo script. This file adds user flows and a glossary.

## The problem (quote only these numbers on stage; name the source)

| Fact | Source |
|---|---|
| 35% of Americans have been late for work or school because they were hunting for a lost item | Shane Co. survey, 2,000+ people, April 2023 |
| Per-state search time ranges from 9 h 45 min/yr (Maryland) to 30 h 17 min/yr (Oklahoma) | same |
| Keys rank second only to phones as the item people most dread losing (41%) | same |

Link: https://shaneco.com/theloupe/articles-and-news/stuff-each-state-loses-the-most

**Why a phone is an honest stand-in:** Meta's Wearables Device Access Toolkit (public developer preview) lets a phone app pull up to 720p/30 fps from Ray-Ban Meta glasses over Bluetooth. Production path = glasses → phone → our pipeline; the hack replaces only the first arrow.

## Users and roles

| Role | Does | Sees a screen? |
|---|---|---|
| Wearer | Wears the camera iPhone on the forehead (rear camera forward), moves normally | No — that phone only streams |
| Asker | Asks "where is my X?" on the ask iPhone by dictation or typing | Yes — the answer card |
| Bystanders | Appear in frames without asking | No — which is why frames are stored only on the laptop |
| Judges | Judge A hides sunglasses (row 3); Judge B asks for a passport (row 4) | Ask iPhone + projected dashboard |

## Goals (each maps to a demo row)

| # | Goal | Demo row | Reqs |
|---|---|---|---|
| G1 | Phone streams 1 frame/s; dashboard frame counter climbs | 1 | R1, R2, R12 (counter) |
| G2 | "Where are my keys?" → newest frame with keys + "N min ago" in < 5 s | 2 | R3, R6, R7, R9 |
| G3 | Moving an object changes the answer within ~10 s | 3 | R3, R7 |
| G4 | Never-seen object → "I haven't seen your X", no frame | 4 | R7, R9 |
| G5 | Everything stored/embedded/checked on the laptop; README names every model + license | 6 | R16 |
| Stretch | "When was I at the whiteboard?" → time range + 3–5 frame strip | 5 | R13 (fallback R11) |

## Non-goals

- Real Meta glasses · all-day battery, storage tiering, deleting old footage · accounts/auth/multiple wearers
- Recording conversation audio (mic only for push-to-talk questions, R10; audio never saved)
- Training or fine-tuning any model · cloud storage of frames

## Prize themes

| Theme | Our claim | Status |
|---|---|---|
| Best Open-Source AI Project | Core is EmbeddingGemma 2 (Apache 2.0), well under the 10B small-model line | Claim |
| Best Use of Gemma 4 | EmbeddingGemma 2 is built on Gemma 4 | **Pending DS3's answer.** If no, the prize needs R8 (Gemma 4 E4B) |

## User flows

### F1 — Lost item found (rows 2, 3)
1. Wearer walks by the keys; camera page POSTs 1 JPEG/s (R1).
2. Ingest saves JPEG + SQLite row (R2) and queues it; the index embeds it (R3).
3. Asker types/dictates "Where are my keys?" on `/ask` (R6).
4. Server extracts `keys`, embeds "a photo of keys" with `prompt_name="SearchQuery"`.
5. Rank: cosine vs every frame → robust z → keep z ≥ z_min → merge visits < 5 s apart (R7).
6. Decide: newest visit; z ≥ z_act → Act, else Ask (R7).
7. Card: frame + "12 min ago · 2:41 PM" + band in words (R9); dashboard shows the same card (R12).

### F2 — Never-seen item, failure path (row 4)
1. Judge B asks "Where is my passport?"
2. Extraction gives `passport`; rank finds no frame with z ≥ z_min.
3. Decide → None. Card: "I haven't seen your passport." **No frame shown.** No guess, ever.

### F3 — Object moved mid-demo, live change (row 3)
1. Judge A places sunglasses somewhere the wearer will walk past; says nothing.
2. Wearer walks past once (2–5 frames of the new spot).
3. Within ~10 s those frames are embedded (ingest lag + embed backlog on dashboard).
4. Judge A asks; the newest candidate visit is the new spot → card shows it, not the older spot.

### F4 — Moment recall, stretch (row 5)
1. Asker: "When was I at the whiteboard?" → extraction routes to recall (R6 regex `when was I at X`).
2. Index returns stretches of consecutive matching frames (R13).
3. Card shows a time range ("2:47–2:49 PM") and a strip of 3–5 frames.
4. If R13 is cut: show the keys' sighting timeline instead (R11).

### F5 — Reset between demo runs
1. Sunglasses go back in a bag, off camera. Keys stay on the table, on camera.
2. Do **not** wipe the index — newest-wins makes the next run correct, and the keys need ≥10 min of history.
3. Reload `/ask` (back to idle). Check dashboard: counter climbing, ingest lag < 3 s.
4. Full checklist: `demo.md` → Reset procedure.

## Glossary

| Term | Meaning |
|---|---|
| Frame | One 640 px JPEG from the camera iPhone (or replay), with a server timestamp; a row in `frames` |
| Candidate | A frame with z ≥ z_min for a query |
| Sighting / visit | Candidates < 5 s apart merged into one visit; keeps the higher score. A sighting = one visit |
| z-score | z_i = (s_i − median(s)) / (1.4826 · MAD(s)) over all frames' cosine scores s for one query |
| z_min | Lowest z that counts as a candidate. Starts at 3; set from the test set 4:45–5:15 |
| z_act | z at/above which the newest candidate is Act. Starts at 5; set from the test set |
| Band | Act ("Your keys: seen…"), Ask ("Might be these…"), None ("I haven't seen your X") |
| Replay mode | R5: feeds a recorded MP4 at 1 frame per second of video straight into ingest, skipping phone + tunnel |
| Stub | A slice's placeholder that returns exactly what `contracts.md` says, so others build against it |
