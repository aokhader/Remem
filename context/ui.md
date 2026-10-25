# UI — ask page, answer card, camera page, dashboard

Owners: ask page + answer card + `card.js`/`card.css` = Varick (R6, R9, R10, R11, R14). Camera page + dashboard = Aziz (R1, R12). Shapes: `contracts.md`.

## Rules for every page

- **Never color alone.** Every band has a word + a symbol + a color. Projector and colorblind judges must read it.
- Static HTML/JS served by FastAPI, no build step, no framework, no CDN (venue Wi-Fi; nothing leaves the laptop).
- Poll every 1 s where live data is needed (quick tunnels don't support Server-Sent Events).
- Times: show "N min ago · 2:41 PM". `ago_s` comes from the server; clock time = `new Date(ts*1000).toLocaleTimeString([], {hour:"numeric", minute:"2-digit"})`.
- Dev without a server: `ask.html?fixture=act|ask|none|recall|error` loads `tests/fixtures/answer_<x>.json` (PROPOSED; served via `/static` copy or a dev route — Varick decides).

## Band styling — PROPOSED colors

| Band | Word on card | Symbol | Color (bg / text) |
|---|---|---|---|
| act | **FOUND** | ✓ | `#1B7F3B` / white |
| ask | **MAYBE** | ? | `#B26A00` / white |
| none | **NOT SEEN** | ✕ | `#4A4A4A` / white |
| error | **ERROR** | ! | `#B3261E` / white |

## Ask page (`/ask`, Varick) — states

| State | Shows | Leaves when |
|---|---|---|
| idle | Text box (placeholder "Where are my keys?"), Ask button, hint "tap 🎤 on the keyboard to dictate" | submit non-empty |
| searching | Button disabled, "Looking…" + spinner; question echoed | response or 8 s timeout (PROPOSED) |
| act | Answer card, FOUND | new question |
| ask | Answer card, MAYBE + "Show older sightings" (expands R11 timeline) | new question |
| none | Answer card, NOT SEEN, **no frame, no image box** | new question |
| error | ERROR + "Try again" button; keep the typed question | Retry / new question |
| listening (R10) | Mic button turns red and pulses; "Listening… release to ask" | release → searching ("Transcribing…"), then asks the transcript like typed text. Tap < 0.35 s, mic blocked, or nothing heard → back to the previous state with a hint |

Input: `<input type="text" enterkeyhint="search" autocomplete="off">`; Enter submits. Keep the last question in the box after answering. R10 push-to-talk button sits between the box and Ask (hold to record, max 15 s, release to send to `POST /ask/voice`, fills the box, then submits). Hidden when the browser lacks `MediaRecorder`; the mic stream stops the moment the finger lifts.

## Answer card layout (R9) — same renderer on ask page and dashboard (`card.js`)

```
┌──────────────────────────────────────┐
│ ✓ FOUND                              │  band word + symbol + color (top bar)
│ Your keys: seen 12 min ago (2:41 PM) │  `message` (largest text)
│ ┌──────────────────────────────────┐ │
│ │        frame  /frames/812.jpg    │ │  full card width, 4:3; omitted for none/error
│ └──────────────────────────────────┘ │
│ 12 min ago · 2:41 PM                 │  from ago_s + hit.ts
│ 📍 on the gray table by the laptop   │  spot line — only when R8 on and spot != null
│ ▸ Show older sightings (3)           │  ask band always; act band optional (R11)
│ [Read aloud]                         │  R14 (speechSynthesis on-device)
└──────────────────────────────────────┘
```

### Card copy (from spec; `{X}` = `object`)

| Band | `message` |
|---|---|
| act | `Your {X}: seen {N} min ago ({clock}).` (R8 adds the spot line, e.g. "on the gray table by the laptop") |
| ask | `Might be these. Seen {N} min ago.` + frame + Show older sightings |
| none | `I haven't seen your {X}.` — no frame |
| recall (R13) | `You were at the {X} {start}–{end}.` + strip of 3–5 frames |
| error | `Something went wrong. Try again.` |

"N min ago" rules (PROPOSED): < 60 s → "just now"; < 60 min → "N min ago"; else "N h M min ago".

### Sighting timeline (R11) and recall strip (R13)
- Timeline: horizontal strip from first frame to now; one tick per `sightings[]` visit; newest tick labelled; tap a tick → thumbnail + clock time. Row 5 fallback when R13 is cut.
- Recall: time range text + 3–5 thumbnails (`/frames/{id}.jpg`) in time order.

### Read aloud (R14)
`speechSynthesis.speak(new SpeechSynthesisUtterance(answer.message))` — runs on the phone, nothing extra leaves the laptop. Only on a user tap (iOS needs a gesture).

## Camera page (`/camera`, Aziz, R1) — states

| State | Shows (wearer never looks; text is for setup/debug) | Leaves when |
|---|---|---|
| permission | "Tap to start camera" button (iOS needs a gesture) | permission granted → streaming; denied → error text "Allow camera in Safari settings" |
| streaming | Small preview, sent-frame counter, last POST ms, green dot + "LIVE" | 3 POST failures in a row or no ack > 3 s → stalled |
| stalled | Red dot + "STALLED — check Wi-Fi/tunnel", retry every 2 s | next 200 → streaming |

Capture: `getUserMedia({video:{facingMode:"environment"}, audio:false})` → canvas 640 px wide → `toBlob("image/jpeg", 0.7)` (quality PROPOSED) every 1000 ms; skip a tick if the previous POST is still in flight. Optional Wake Lock API (`navigator.wakeLock.request("screen")`) where supported; Auto-Lock Never is the real fix.

## Dashboard (`/`, Aziz, R12) — projector

| Panel | Source | Notes |
|---|---|---|
| Frame counter | `status.frames_received` (+ indexed) | Huge digits; must visibly climb (row 1) |
| Last frame | `/frames/{last_frame_id}.jpg` | Refresh each poll; shows mount tilt/blur before presenting |
| Ingest lag | `status.ingest_lag_s` + mode word | "LIVE 0.8 s" / "STALLED 7 s" (word + color) |
| Backlog | `queue_depth`, `frames_dropped`, `embed_ms_p50` | small text |
| Latest answer card | `GET /ask/latest` → `card.js` | same card as the phone; `<pre>` JSON until card.js lands |
| Replay | `status.replay` | progress bar only when replaying |

Projector readability: dark text on white or white on near-black, min 28 px body, 96 px counter, 1080p layout without scrolling, no thin fonts, no info in color alone.

## iPhone notes (verify at gate 1)

- `<video autoplay playsinline muted>` or the preview won't play inline.
- Open **only** the `https://….trycloudflare.com` URL — on plain HTTP `navigator.mediaDevices` is undefined and the page fails silently.
- Safari stops the camera when the screen locks or the tab leaves the foreground: Settings → Display & Brightness → Auto-Lock → **Never** on both iPhones; keep Safari in front; no other tabs.
- Low Power Mode off; brightness can be minimum on the camera iPhone (saves heat).
- Add `<meta name="viewport" content="width=device-width, initial-scale=1">`; inputs ≥ 16 px font so iOS doesn't zoom on focus.
