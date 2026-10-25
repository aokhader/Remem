# Evaluation results

Run: 2026-10-25T16:12:44-07:00
Dataset: `C:\Users\danie\Documents\1_Projects\Remem\eval\test_set.csv` (40 queries); recording date: 2026-10-25; TZ: America/Los_Angeles.
Mode: in-process sweep. Backend: gemma.

| README metric | Measured value |
|---|---|
| Latest-sighting accuracy (28 present queries) | Pending — not measured |
| False-found count (8 never-seen queries) | Pending — not measured |
| Median seconds per answer (localhost, excludes tunnel) | Pending — requires HTTP run |

Blocked: Sweep needs filled present windows and never-seen queries; draft windows are blank

Current thresholds: Z_MIN=3.0, Z_ACT=5.0 (not evidence of tuning).
Present scored: not an HTTP run; request/answer errors: not an HTTP run.
Recall: 0 correct / 0 scored, separately.
Accuracy uses visit-window overlap. Visually review all 28 returned frames: an in-window frame
that does not show the object is still wrong. Timing includes transport failures/timeouts;
those are counted as errors and never-seen errors count as false-found.
Details (local, ignored): `none`.

## Implementation verification (not final README numbers)

- 117 checks pass: 20 decision-table cases, 61 extraction checks, 19 backend checks,
  and 17 evaluator checks. Ruff and Git diff checks pass.
- Real localhost:8001 HTTP diagnostic ran all 40 draft queries against the cached
  Gemma backend and existing three-photo database: zero request/answer errors.
  Eight never-seen queries returned none; median request time was 0.031681 s.
  **These are diagnostic observations only:** MIN_FRAMES=30 blocked find retrieval
  on three frames, so no query embedding was performed. They are not demo accuracy,
  false-found, or latency claims for the recorded day.
- Full synthetic sweep regression covers query caching, z >= 1.5 candidate logging,
  production visit merging, and threshold selection. Synthetic values are test
  fixtures, not recorded observations or final thresholds.
- Final metrics require the real replayed recording, filled present/recall windows,
  a completed sweep, and a fresh HTTP run against that database. Z_MIN=3/Z_ACT=5
  remain placeholders; no .env or dataset windows were changed.

Commands and input descriptions: `remem/index/README.md` and `context/data.md`.
The optional R8 decision path has pure fixture tests; no R8 model was loaded.
