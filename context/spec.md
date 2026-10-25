# Remem — Hack Day build spec

Oct 25, 2026 · @Aziz

## Overview

**Remem** answers "Where are my keys?" with the last frame your glasses saw them in. An iPhone worn on the forehead stands in for Meta glasses and sends one frame per second to a laptop. A second iPhone asks the questions and shows the answers. EmbeddingGemma 2 embeds every frame on the laptop. A spoken or typed question is embedded into the same vector space, and the newest matching frame comes back with its timestamp and how long ago it was seen.

The MVP is the lost-item lookup. The stretch goal is moment recall ("when was I at the whiteboard?"), which reuses the same index.

**The problem.** A Shane Co. survey of 2,000+ people in April 2023 found 35% of Americans have been late for work or school because they were hunting for a lost item, and per-state search time ranges from 9 h 45 min a year (Maryland) to 30 h 17 min (Oklahoma). Keys rank second only to phones as the item people most dread losing (41%). [source](https://shaneco.com/theloupe/articles-and-news/stuff-each-state-loses-the-most)

**Why a phone is an honest stand-in.** Meta's Wearables Device Access Toolkit lets a phone app pull a video stream from Ray-Ban Meta glasses at up to 720p and 30 fps over Bluetooth, and it is in public developer preview. So the production path is glasses → phone → our pipeline; the hack replaces only the first arrow. [UploadVR](https://www.uploadvr.com/meta-wearables-device-access-toolkit-public-preview/), [Meta FAQ](https://developers.meta.com/wearables/faq)

| Who | What they do | Sees a screen? |
| --- | --- | --- |
| Wearer | Wears the camera iPhone on the forehead and moves around normally | No; that phone only streams |
| Asker | Asks "where is my X?" on the second iPhone, by dictation or typing | Yes, the answer card (on real glasses the answer would be spoken) |
| Bystanders | Appear in frames without asking to | No, which is why frames are stored only on the laptop |
| Judges | Hide an object during the demo, then ask for it | Yes, the ask iPhone and the projected dashboard |

**Themes hit.** Best Open-Source AI Project: the core is EmbeddingGemma 2 (740M params, 440M as we load it without the audio encoder; Apache 2.0), well under the 10B small-model line. Best Use of Gemma 4: EmbeddingGemma 2 is built on Gemma 4, so ask DS3 whether it counts on its own; if not, the prize needs the optional Gemma 4 E4B check (R8). [Gemma challenge](https://hacktoberfest-handbook.mlh.com/hack-days-partner-modules/partner-challenge-google-gemma), [model card](https://huggingface.co/google/embeddinggemma-2)

## Goals and non-goals

At 6:30 PM judges should see five things work live, with nothing faked.

**Goals**

1. The phone streams 1 frame per second to the laptop, and a frame counter on the dashboard climbs.
2. "Where are my keys?" returns the newest frame that shows the keys and how long ago it was seen, in under 5 seconds.
3. Moving an object during the demo changes the answer within about 10 seconds.
4. Asking for something never seen returns "I haven't seen your X" instead of a wrong frame.
5. Every frame is stored, embedded and checked only on the laptop; the only frame that goes out is the answer, to the ask iPhone. The public repo's README names every model, its license, and what it does.

Stretch: "When was I at the whiteboard?" returns a time range and a strip of frames.

**Non-goals**

- Real Meta glasses. The phone is the stand-in; the toolkit is the path after the hack.
- All-day battery, storage tiering, or deleting old footage.
- Accounts, auth, or more than one wearer.
- Recording conversation audio. The mic is used only for push-to-talk questions.
- Training or fine-tuning any model.
- Cloud storage of frames.

## Demo script = acceptance test

The build is done when these six rows pass twice in a row on venue Wi-Fi (row 5 is skipped if R11 and R13 are both cut). Total: 3 minutes. Judges play two roles; cue cards are a next step.

From 5:30 PM the wearer streams live and moves around normally, and sets the keys on a table on camera at least 10 minutes before presenting.

| # | Time | Who | What happens | Passes when |
| --- | --- | --- | --- | --- |
| 1 | 0:00–0:20 | Presenter | Pitch in two lines. Point to the camera iPhone on the wearer's forehead and to the ask iPhone. | Live frame counter is climbing on the projected dashboard |
| 2 | 0:20–0:50 | Asker | On the ask iPhone, dictate or type: "Where are my keys?" | Top result is a frame with the keys, shows "N min ago" and the clock time; under 5 s |
| 3 | 0:50–1:30 | Judge A ("Put these sunglasses somewhere the wearer will walk past. Don't say where.") | Wearer walks past once. Judge A asks on the ask iPhone: "Where are the sunglasses?" | Newest frame shows the judge's chosen spot, not an earlier one. **Live change row.** |
| 4 | 1:30–1:55 | Judge B ("Ask for something nobody brought, e.g. a passport.") | "Where is my passport?" on the ask iPhone | Card says "I haven't seen your passport" and shows no frame. **Failure-path row.** |
| 5 | 1:55–2:30 | Asker | Stretch: "When was I at the whiteboard?" If the stretch is cut, show the keys' sighting timeline instead. | A time range and a strip of 3–5 frames appear |
| 6 | 2:30–3:00 | Presenter | Show the README model table. Say: "Your whole day was stored and searched only on this laptop. Next step is Meta's glasses toolkit." | README with models and licenses is on screen |

**Backup video.** Record rows 1–6 at 6:00 PM, right after the code freeze. If live Wi-Fi or the phone fails, play it and say it is a recording. The same video goes in the submission: source code is required, video is encouraged.

## Functional requirements

Eight Musts, plus the frame counter from R12 that row 1 needs, carry demo rows 1–4 and 6 with EmbeddingGemma 2 alone; four Shoulds add voice, dedupe, the timeline and the rest of the dashboard. Could items, including the Gemma 4 check (R8), start only after rows 1–4 pass twice.

| ID | Stage | Requirement | Priority |
| --- | --- | --- | --- |
| R1 | Capture | Camera iPhone on the forehead runs a web page over HTTPS that opens the rear camera and POSTs one JPEG per second (640 px wide) with its timestamp | Must |
| R2 | Ingest | Server saves each frame to disk and a row in SQLite (id, server receive time, path) | Must |
| R3 | Index | Embed each frame with EmbeddingGemma 2 (text + vision only, 768 dims, normalized), keep up at 1 frame per second, and save each vector in SQLite so a restart reloads instead of re-embedding | Must |
| R4 | Index | Skip a frame whose embedding is near-identical to the last kept one (wearer standing still) | Should |
| R5 | Index | Replay mode: feed a recorded MP4 through the same pipeline, 1 frame per second of video, as fast as the index keeps up (real time only as a demo fallback); each frame's time = recording start time + its offset in the video | Must |
| R6 | Query | Ask page on the second iPhone: text box (dictation works); pull the object out with a few regexes ("where is / are my / the X", "have you seen my X", "where did I leave my X"; "when was I at the X" goes to recall) | Must |
| R7 | Retrieve | Embed the query, score every frame, keep the frames that stand out from the rest, merge them into visits, and pick the answer band from the newest visit's z (rules in Data) | Must |
| R8 | Verify | Nice-to-have: Gemma 4 E4B double-checks the 5 newest candidates and names the spot; code still makes the call | Could |
| R9 | Answer | Answer card on the ask iPhone: frame, "N min ago" and clock time, band; Gemma 4's one-line spot when R8 is on; or "I haven't seen your X" | Must |
| R10 | Query | Push-to-talk question, transcribed locally with an open speech model | Should |
| R11 | Answer | Sighting timeline: the object's 10 newest candidate sightings on a time strip | Should |
| R12 | Ops | Laptop dashboard for the projector: frame counter, last frame, ingest lag, and the latest answer card (the counter is built before gate 2: row 1 needs it) | Should |
| R13 | Recall | Moment recall: free-form query returns time ranges of matching stretches | Could |
| R14 | Answer | Read the answer aloud on the ask iPhone | Could |
| R15 | Privacy | Blur faces before a frame is saved | Could |
| R16 | Ship | Public repo, open-source license, README naming each model, its license, and what it does | Must |

## High-level overview

&#91;embedded content: Remem architecture · capture, index, query, verify\]

The same EmbeddingGemma 2 model turns frames and questions into vectors in one space, so a typed "keys" can be compared straight against a photo. The dashed Gemma 4 box is the optional R8 check; without it, the z-score bands decide alone. Frames are stored and searched only on the laptop either way.

## Tech stack

One Python server on one laptop does everything; the phone runs a single web page. Every external piece has a fallback that keeps the demo alive.

| Layer | Choice | Why | Fallback |
| --- | --- | --- | --- |
| Capture | One HTML page in Safari on the camera iPhone, worn on the forehead with the rear camera facing forward: `getUserMedia({video: {facingMode: "environment"}})`, draw to canvas, POST a JPEG every 1000 ms | No app install; Safari allows the camera on HTTPS pages | Record in the iPhone Camera app (Formats: Most Compatible, for H.264), copy it to the laptop by USB (AirDrop can't reach Windows), strip the audio, run replay mode (R5) |
| Transport | `cloudflared tunnel --url http://localhost:8000` (quick tunnel, no account), run inside WSL next to the server | Camera access only works on HTTPS or localhost; the tunnel is outbound, so it skips venue client isolation and WSL's inbound NAT | Retry with `--protocol http2`; iPhone Personal Hotspot as the laptop's uplink; replay mode if both fail |
| Server | FastAPI + uvicorn in WSL; JPEGs on disk; SQLite rows; one in-memory NumPy matrix | Team knows Python. 3 hours at 1 fps is 10,800 × 768 floats (about 33 MB), so brute-force cosine takes milliseconds; no vector DB needed | None needed |
| Embedding (core) | EmbeddingGemma 2 (`google/embeddinggemma-2`) from Hugging Face via sentence-transformers, `config_kwargs={"audio_config": None}` (loads 440M of the 740M params: no audio encoder), on the NVIDIA GPU through CUDA in WSL; bfloat16 if supported, else float32 | Open (Apache 2.0), free, text and images in one 768-d space, built to run on laptops | Image budget 70 tokens; embed every 2nd frame |
| Verify (R8, nice-to-have) | Gemma 4 E4B (`google/gemma-4-E4B-it`) from Hugging Face via transformers on the laptop GPU; image before text, `enable_thinking=False`, JSON out; 4-bit if VRAM is short. Free, no billing | Adds the spot line and a second check | Leave it off: the z-score bands decide alone |
| Voice | iPhone keyboard dictation into the ask page's text box (zero code); push-to-talk with a local open speech model is R10 | Dictation is free and already works | Type the question |
| Ask page + dashboard | Ask page on the second iPhone (same tunnel URL: `GET /ask` serves the page, `GET /ask?q=` returns the answer as JSON) and a laptop dashboard for the projector; both static HTML/JS served by FastAPI, polling every 1 s | No build step. Quick tunnels do not support Server-Sent Events, so poll | Dashboard on localhost; ask from the laptop's browser |

**Gotchas from the docs**

- Never run EmbeddingGemma 2 in float16: it returns NaN or silently worse vectors, with no error. Use bfloat16 when `torch.cuda.is_bf16_supported()` is True, else float32. [model card](https://huggingface.co/google/embeddinggemma-2)
- Images go in as `model.encode({"image": path_or_PIL})` with no prefix; queries use `prompt_name="SearchQuery"`. Image detail is `processing_kwargs={"image": {"max_soft_tokens": 70 | 140 | 280 | 560 | 1120}}`. [multimodal guide](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers)
- Image-to-text scores are not calibrated: in Google's own example an unrelated painting scored 0.585 against the Golden Gate photo. Rank within one query; never hard-code a raw score cutoff. [multimodal guide](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers)
- If R8 is built: Gemma 4 E4B on Hugging Face is `google/gemma-4-E4B-it`. Put the image before the text in the message content, and pass `enable_thinking=False` to the chat template so the reply is only the JSON. [Gemma 4 cheat sheet](https://cheatsheets.zip/gemma4)
- If R8 is built: approximate weight memory for E4B is 15 GB in BF16, 7.5 GB in 8-bit, 5 GB in 4-bit, before KV cache; EmbeddingGemma 2 adds roughly 1.5 GB. Check real use with `nvidia-smi`. [Gemma 4 cheat sheet](https://cheatsheets.zip/gemma4)
- Quick tunnels have no uptime guarantee, cap at 200 in-flight requests, and get a new hostname on every restart. [Cloudflare](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)
- The tunnel's HTTPS ends at Cloudflare's edge, so incoming JPEGs and outgoing answers pass through Cloudflare, and the answer frame goes out to the ask iPhone. On stage, say frames are "stored and searched only on this laptop", never "no frame left it".
- WSL may run in UTC. Convert clock times (`ground_truth.csv`, the replay start time) with an explicit `America/Los_Angeles` zone.
- `navigator.mediaDevices` is undefined on plain HTTP, so the page fails silently on a LAN IP. [MDN](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
- iPhone specifics, from experience and to verify at gate 1: the `<video>` preview needs `playsinline` and `muted`, and Safari stops the camera when the screen locks or the tab leaves the foreground.

**Kickoff checklist**

- [ ] Public GitHub repo with an Apache-2.0 LICENSE and a README model table (source code is required in the submission)
- [x] Inside WSL, `torch.cuda.is_available()` returns True on the NVIDIA GPU
- [ ] Note whether `torch.cuda.is_bf16_supported()` is True (bfloat16 vs float32 for EmbeddingGemma 2)
- [ ] `sudo apt install ffmpeg` (torchcodec needs it; it also strips audio from the recorded day), then `pip install -U sentence-transformers transformers accelerate pillow torchcodec fastapi uvicorn numpy`
- [ ] Start the `google/embeddinggemma-2` download now (740M params, about 1.5 GB in BF16; not gated, so no login)
- [ ] Install `cloudflared` inside WSL; open the tunnel URL in Safari on both iPhones over venue Wi-Fi: camera preview on one, ask page on the other
- [ ] Time one frame embed on the GPU (gate 1 target: under 0.5 s)
- [ ] Head strap or cap clip for the camera iPhone (rear camera facing forward), power bank, Auto-Lock set to Never on both iPhones
- [ ] Only if R8 is attempted after gate 2: check VRAM with `nvidia-smi`, `pip install bitsandbytes`, download `google/gemma-4-E4B-it` (about 15 GB in BF16)

## Data and decision rules

EmbeddingGemma 2 ranks frames and plain code makes the call; Gemma 4 can optionally double-check the newest few (R8). Cutoffs come from a 40-query test set run on a recorded "day", so every run repeats exactly.

**The recorded day.** By 3:45 PM, record about 10 minutes with Ray-Ban Meta glasses at the venue. The glasses cap each clip at 3 minutes, so the day is at least 4 back-to-back clips; replay each one with its own start time. Place 8 props on camera and log the recording's start time, each placement and each move in `ground_truth.csv` (object, spot, clock time). Use distinct props: keys on a bright keychain, sunglasses, water bottle, wallet, earbuds case, charger, notebook, mug. Move three of them once mid-recording. For the recall queries, linger at least a minute at 4 landmarks (one is the whiteboard) and log each stretch's start and end time. The glasses record sound, so strip it on the laptop before anything else. Replay mode (R5) feeds these MP4s through the same pipeline once; the vectors are saved, so every test run after that reuses them.

**Retrieval rule (R7).** For a query about object X, score every frame, then standardize scores within that query, because raw image-to-text scores are not calibrated.

```latex
s_i = \cos(e_q, f_i), \qquad z_i = \frac{s_i - \operatorname{median}(s)}{1.4826 \cdot \operatorname{MAD}(s)}
```

```latex
C = \{\, i : z_i \ge z_{\min} \,\}, \quad z_{\min} = 3 \text{ to start}
```

Collapse candidates less than 5 s apart into one visit, keeping the higher score. Keep the 10 newest visits for the timeline (R11). Merge before cutting to 10: the 10 best frames can all come from one long older visit and hide the newest sighting. If MAD(s) = 0 or fewer than 30 frames are indexed, return no candidates. Query text is `a photo of {X}` with `prompt_name="SearchQuery"`.

**Decision rule (R7, no Gemma needed).** Take the newest candidate visit in C; its z picks the band. The answer is the **newest** candidate, not the highest-scoring one, because the user wants the last sighting.

**Optional Gemma 4 check (R8, nice-to-have).** If R8 ships, send the 5 newest candidates to Gemma 4 E4B in one batch on the GPU. Prompt: "Is {X} visible in this first-person photo? Reply JSON only: present (true/false), confidence (0–1), where (12 words max, name the surface or landmark)." The answer becomes the newest frame with present = true; its confidence sets the band, and "where" fills the spot line on the card.

| Band | Rule (MVP, z only) | With Gemma 4 (R8) | What the card says |
| --- | --- | --- | --- |
| Act | Newest candidate has z ≥ z\_act (start at 5) | Confidence 0.8 or higher | "Your keys: seen 12 min ago (2:41 PM)." + frame; with R8 it adds "on the gray table by the laptop" |
| Ask | Newest candidate has z\_min ≤ z < z\_act | Confidence 0.5 to 0.8 | "Might be these. Seen 12 min ago." + frame + Show older sightings |
| None | No candidate with z ≥ z\_min | No frame present, or all below 0.5 | "I haven't seen your X." No frame |

Recall answers (R13) are Act when at least one stretch is found, else None.

z\_min = 3, z\_act = 5 and the 0.8 / 0.5 confidence cutoffs are placeholders. Expect z\_min to rise: with ~600 frames, even pure noise puts a few frames above z = 3. Set them at 4:45–5:15 PM from the test set: the lowest z\_act with zero wrong frames in Act, and the z\_min that keeps the true frame in C for at least 90% of present queries while every never-seen query lands in None.

**Test set: 40 scripted queries.** 24 present (8 props × 3 phrasings, IDs in the prop order above), 8 never-seen (passport, umbrella, cat…), 4 asked after a move (the 3 moved props, one asked twice), 4 moment-recall. All run after the whole day has replayed. A present answer is right when its frame is from the object's latest spot: after its last placement or move (−10 s), because any later sighting of that spot is right too. A recall answer is right when a returned stretch overlaps the logged one. Never-seen expects NONE.

```csv
id,query,expected_object,expected_window,expected_band
T01,where are my keys,keys,14:41:00-end,act
T02,have you seen my keychain,keys,14:41:00-end,act
T04,where did I leave my sunglasses,sunglasses,14:52:20-end,act
T25,where is my passport,passport,NONE,none
T33,where is my water bottle now,water bottle,14:58:05-end,act
T37,when was I at the whiteboard,whiteboard,14:47:00-14:49:30,act
```

Report three numbers on the README: latest-sighting accuracy on present queries, false-found count on never-seen queries (target 0), and median seconds per answer.

## Team split and timeline

Three slices meet at gate 2 (4:45 PM), when a typed question returns the right frame on the replayed day. Each slice ships a stub behind its interface by gate 1 so integration starts early.

| Person | Slice | Requirements | Spike due at gate 1 (3:15 PM) |
| --- | --- | --- | --- |
| Aziz | Capture, transport, ingest | R1, R2, R5, R12, R15 | iPhone Safari camera preview over the tunnel on venue Wi-Fi; one JPEG lands on disk |
| Daniel | Index and retrieval | R3, R4, R7, R13 | One frame embedded and timed on the GPU; "a photo of keys" ranks the keys photo first among 3 test photos. Nice-to-have: A/B the query text (whole question vs `a photo of {X}`, with vs without the `SearchQuery` prefix, one phrasing vs the average of three) and keep whichever ranks the keys photo highest |
| Varick | Ask page, answer card, UI | R6, R9, R10, R11, R14; R8 as a nice-to-have | The ask page on the second iPhone sends a question and shows a stub answer card from `GET /ask` |
| All | Ship | R16 | Repo, LICENSE and README skeleton pushed |

Stub interfaces: `POST /frames` (Aziz; raw JPEG body with the phone time in `?ts=`, so no python-multipart), `index.search(text, k)` returning up to k visits, newest first, each with frame id, time, score and z (Daniel), `verify(frame_path, object)` returning present, confidence and where, plus `verify_many(frame_paths, object)` for R8's one-batch check (Varick; R8 nice-to-have, stubs return no verdict), `GET /ask?q=` (Varick).

&#91;embedded content: build plan · 2:45 to 6:30 PM, 3 lanes, 3 gates\]

Gate 2 is the go/no-go: if the replayed day does not answer "where are my keys" correctly by 4:45 PM, cut R10, R11, R13 and all of R12 except the frame counter, and spend the time on cutoffs and the backup video. Coulds, including the Gemma 4 check (R8), start only after demo rows 1–4 pass twice. Code freezes at 6:00 PM; after that, only the backup video and the submission.

## Risks and fallbacks

The two risks most likely to sink the demo are venue networking and small objects not ranking; both have a fallback that is built by gate 2 (4:45 PM).

| Risk | Fallback | Owner |
| --- | --- | --- |
| Venue Wi-Fi blocks or slows the tunnel | Retry with `cloudflared tunnel --protocol http2`; then iPhone Personal Hotspot as the laptop's uplink; then replay the recorded video | Aziz |
| Phone page opened over plain HTTP, camera silently unavailable | Always use the HTTPS tunnel URL; check the Safari preview at gate 1 | Aziz |
| Safari stops the camera when the iPhone locks or the tab goes to the background | Auto-Lock set to Never, Safari kept in front; the dashboard's ingest lag shows a stall within seconds | Aziz |
| Forehead mount slips, tilts down, or blurs frames on head turns | Head strap plus tape; wearer turns slowly in the demo; check the dashboard's last frame before presenting | Aziz |
| Tunnel and server end up on different sides of WSL | Run cloudflared and uvicorn both inside WSL | Aziz |
| Small items (keys) never stand out (z below z\_min) | Bright keychain; try a 560-token image budget; lower z\_min | Daniel |
| Without Gemma 4, a look-alike object answers "where are my keys" | Set z\_act from the test set so look-alikes land in Ask, not Act; never-seen queries must land in None | Daniel |
| If R8 is built: Gemma 4 E4B and EmbeddingGemma 2 don't fit in VRAM | Load E4B in 4-bit, or E2B; or leave R8 off | Varick |
| If R8 is built: verify blows the 5 s answer budget or returns broken JSON | Verify the 3 newest only; `enable_thinking=False`; a parse failure counts as "not present"; or leave R8 off | Varick |
| Integration slips | Every slice ships a stub behind its endpoint by gate 1: fake frames, fake scores, canned answer | All |
| Wrong frame on stage | Newest-candidate rule plus the Ask band; rehearse rows 2–4 twice; backup video ready | Daniel |
| A judge asks who is liable for filming bystanders | Frames are stored and searched only on the laptop; no audio is kept; face blur (R15) and auto-delete are the next steps | Presenter |
| A wrong number on stage | Quote only the sourced numbers in this doc, and name the source: "Shane Co. survey, 2023" | Presenter |
| Camera iPhone overheats or dies after 3 hours of streaming | 640 px frames; power bank in a pocket with the cable run to the head mount | Aziz |
| Model download crawls on venue Wi-Fi | Start EmbeddingGemma 2 now; Gemma 4 E4B (about 15 GB) only if R8 is attempted | All |

## Open questions

- [ ] Who wears the camera iPhone, who holds the ask iPhone, and who presents?
- [ ] Does EmbeddingGemma 2 alone count for Best Use of Gemma 4? It is built on Gemma 4. If not, that prize depends on the optional R8 check. Ask DS3.
- [ ] If R8 is attempted: how much VRAM does the GPU have? It decides Gemma 4 E4B in BF16 or 4-bit.
- [ ] Where do we submit (platform or form)? Find it before 5:45 PM.
- [ ] Does Daniel build on the demo laptop, since it has the only GPU?
- [x] Checked on Hugging Face (Oct 25): `google/embeddinggemma-2`, `google/gemma-4-E4B-it`, `google/gemma-4-E2B-it` and `openai/whisper-small` are all Apache-2.0 and not gated, so no login is needed.

## Sources

- [Shane Co. lost-items survey (April 2023)](https://shaneco.com/theloupe/articles-and-news/stuff-each-state-loses-the-most)
- [EmbeddingGemma 2 model card](https://huggingface.co/google/embeddinggemma-2)
- [Multimodal embeddings with EmbeddingGemma 2](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers)
- [EmbeddingGemma 2 explainer (eesel)](https://www.eesel.ai/blog/embeddinggemma-2)
- [Gemma 4 cheat sheet (community; memory figures approximate)](https://cheatsheets.zip/gemma4)
- [MLH Google Gemma challenge](https://hacktoberfest-handbook.mlh.com/hack-days-partner-modules/partner-challenge-google-gemma)
- [Meta Wearables Device Access Toolkit FAQ](https://developers.meta.com/wearables/faq)
- [UploadVR on the toolkit's public preview](https://www.uploadvr.com/meta-wearables-device-access-toolkit-public-preview/)
- [MDN: getUserMedia()](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)
