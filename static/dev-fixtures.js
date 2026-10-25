// Dev-only canned Answers for /ask?fixture=<name>. Owner: Varick.
// act/ask/none/recall/error mirror context/contracts.md → Fixtures; timeline is extra (R11 with 4 sightings).

const keysHit = {
  frame_id: 812, ts: 1792964460.0, score: 0.35, z: 6.2, path: "frames/000812.jpg",
  visit_start: 1792964458.0, visit_end: 1792964463.0, n_frames: 4,
};

const base = {
  spot: null, sightings: [], moments: [], asked_ts: 1792965180.0, error: null,
};

const sighting = (frame_id, ts, z) => ({
  frame_id, ts, score: 0.3, z, path: `frames/${String(frame_id).padStart(6, "0")}.jpg`,
  visit_start: ts - 2, visit_end: ts + 3, n_frames: 3,
});

export const FIXTURES = {
  act: {
    ...base, q: "Where are my keys?", kind: "find", object: "keys", band: "act",
    message: "Your keys: seen 12 min ago (2:41 PM).", hit: keysHit, frame_url: "/frames/812.jpg",
    ago_s: 720.0, sightings: [keysHit],
    timings_ms: { extract: 1, embed: 80, rank: 12, verify: 0, decide: 0, total: 95 },
  },
  ask: {
    ...base, q: "Where are my keys?", kind: "find", object: "keys", band: "ask",
    message: "Might be these. Seen 12 min ago.", hit: { ...keysHit, z: 4.1 }, frame_url: "/frames/812.jpg",
    ago_s: 720.0, sightings: [{ ...keysHit, z: 4.1 }],
    timings_ms: { extract: 1, embed: 80, rank: 12, verify: 0, decide: 0, total: 95 },
  },
  none: {
    ...base, q: "Where is my passport?", kind: "find", object: "passport", band: "none",
    message: "I haven't seen your passport.", hit: null, frame_url: null, ago_s: null,
    timings_ms: { total: 90 },
  },
  recall: {
    ...base, q: "When was I at the whiteboard?", kind: "recall", object: "whiteboard", band: "act",
    message: "You were at the whiteboard 2:47–2:49 PM.", hit: null, frame_url: null, ago_s: 210.0,
    moments: [{ start_ts: 1792964820.0, end_ts: 1792964970.0, frame_ids: [700, 730, 760, 790], peak_z: 5.8 }],
    timings_ms: { total: 90 },
  },
  error: {
    ...base, q: "Where are my keys?", kind: "find", object: "", band: "error",
    message: "Something went wrong. Try again.", hit: null, frame_url: null, ago_s: null,
    timings_ms: { total: 5000 }, error: "timeout",
  },
  timeline: {
    ...base, q: "Where are my keys?", kind: "find", object: "keys", band: "act",
    message: "Your keys: seen 12 min ago (2:41 PM).", hit: keysHit, frame_url: "/frames/812.jpg", ago_s: 720.0,
    sightings: [keysHit, sighting(560, 1792963200.0, 5.1), sighting(320, 1792962000.0, 3.9), sighting(90, 1792960800.0, 3.4)],
    timings_ms: { total: 95 },
  },
};
