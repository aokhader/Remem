// Answer card renderer (R9) with the sighting timeline (R11) and recall strip (R13).
// Owner: Varick. Used by /ask and Aziz's dashboard:
//   <link rel="stylesheet" href="/static/card.css">
//   import { renderCard } from "/static/card.js";  renderCard(el, answer);
// Scale the whole card with font-size on its container (em-based). No build step, no CDN.

/** @typedef {"act"|"ask"|"none"|"error"} Band */
/** @typedef {{frame_id:number, ts:number, score:number, z:number, path:string, visit_start:number, visit_end:number, n_frames:number}} SearchHit */
/** @typedef {{start_ts:number, end_ts:number, frame_ids:number[], peak_z:number}} Moment */
/** @typedef {{q:string, kind:"find"|"recall", object:string, band:Band, message:string, hit:?SearchHit, frame_url:?string, ago_s:?number, spot:?string, sightings:SearchHit[], moments:Moment[], asked_ts:number, timings_ms:Object<string,number>, error:?string}} Answer */

// Never color alone: every band has a word and a symbol too (context/ui.md).
const BANDS = {
  act: { word: "FOUND", symbol: "✓" },
  ask: { word: "MAYBE", symbol: "?" },
  none: { word: "NOT SEEN", symbol: "✕" },
  error: { word: "ERROR", symbol: "!" },
};

/** "just now" · "12 min ago" · "1 h 5 min ago" — same rules as remem/answer/card.py. */
export function formatAgo(seconds) {
  const minutes = Math.floor(Math.max(seconds ?? 0, 0) / 60);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  return `${Math.floor(minutes / 60)} h ${minutes % 60} min ago`;
}

/** Epoch seconds → "2:41 PM" in the viewer's local time. */
export function formatClock(ts) {
  return new Date(ts * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

const frameUrl = (id) => `/frames/${id}.jpg`;

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  node.append(...children.filter((c) => c != null));
  return node;
}

function frameImg(src, alt, cls) {
  const img = el("img", { class: cls, src, alt, decoding: "async" });
  img.addEventListener("error", () => img.replaceWith(el("div", { class: `${cls} remem-missing` }, "frame unavailable")), { once: true });
  return img;
}

/** R11: every candidate visit as a tick on one strip, plus tappable thumbnails (newest first). */
function sightingTimeline(answer) {
  const hits = answer.sightings;
  const t0 = Math.min(...hits.map((h) => h.visit_start));
  const t1 = Math.max(answer.asked_ts, ...hits.map((h) => h.visit_end));
  const span = Math.max(t1 - t0, 1);

  const thumbs = el("ol", { class: "remem-thumbs" });
  const strip = el("div", { class: "remem-timeline__strip", role: "list" });
  hits.forEach((hit, i) => {
    const label = `${formatClock(hit.ts)} · ${formatAgo(answer.asked_ts - hit.ts)}`;
    const thumb = el("li", { class: "remem-thumb", id: `remem-sighting-${hit.frame_id}` },
      frameImg(frameUrl(hit.frame_id), `${answer.object} at ${formatClock(hit.ts)}`, "remem-thumb__img"),
      el("span", { class: "remem-thumb__label" }, i === 0 ? `Newest · ${label}` : label));
    thumbs.append(thumb);
    strip.append(el("button", {
      class: i === 0 ? "remem-tick remem-tick--newest" : "remem-tick",
      style: `left:${((hit.ts - t0) / span) * 100}%`,
      type: "button",
      role: "listitem",
      "aria-label": label,
      onclick: () => {
        thumbs.querySelectorAll(".remem-thumb--selected").forEach((t) => t.classList.remove("remem-thumb--selected"));
        thumb.classList.add("remem-thumb--selected");
        thumb.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      },
    }));
  });

  return el("details", { class: "remem-card__more" },
    el("summary", {}, `Show older sightings (${hits.length - 1})`),
    el("div", { class: "remem-timeline" },
      strip,
      el("div", { class: "remem-timeline__axis" },
        el("span", {}, formatClock(t0)), el("span", {}, "now"))),
    thumbs);
}

/** R13: newest stretch as a strip of 3–5 frames; older stretches listed as text. */
function recallStrip(answer) {
  const [newest, ...older] = answer.moments;
  const strip = el("div", { class: "remem-strip" },
    ...newest.frame_ids.map((id) => frameImg(frameUrl(id), `${answer.object}, frame ${id}`, "remem-strip__img")));
  const also = older.length
    ? el("p", { class: "remem-card__meta" },
      `Also: ${older.map((m) => `${formatClock(m.start_ts)}–${formatClock(m.end_ts)}`).join(", ")}`)
    : null;
  return [strip, el("p", { class: "remem-card__meta" }, formatAgo(answer.ago_s)), also];
}

/** Build the card element for one Answer. */
export function buildCard(answer) {
  const band = BANDS[answer.band] ?? BANDS.error;
  const card = el("article", { class: "remem-card", "data-band": answer.band },
    el("header", { class: "remem-card__band" },
      el("span", { class: "remem-card__symbol", "aria-hidden": "true" }, band.symbol),
      el("span", {}, band.word)),
    el("p", { class: "remem-card__message" }, answer.message));

  if (answer.kind === "recall" && answer.moments?.length) {
    card.append(...recallStrip(answer).filter(Boolean));
  } else if (answer.hit && answer.frame_url && (answer.band === "act" || answer.band === "ask")) {
    card.append(
      frameImg(answer.frame_url, `Newest frame showing ${answer.object}`, "remem-card__frame"),
      el("p", { class: "remem-card__meta" }, `${formatAgo(answer.ago_s)} · ${formatClock(answer.hit.ts)}`));
    if (answer.spot) card.append(el("p", { class: "remem-card__spot" }, `\u{1F4CD} ${answer.spot}`));
    if (answer.sightings?.length > 1) card.append(sightingTimeline(answer));
  }
  return card;
}

/** Replace el's contents with the card for answer. */
export function renderCard(container, answer) {
  container.replaceChildren(buildCard(answer));
}
