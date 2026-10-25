# AI workflow — rules for every Claude Code session on Remem

Three people run Claude Code in parallel on three slices. These rules keep the sessions from colliding.

## Session start (every time, including after `/clear`)

1. Read `CLAUDE.md`, `context/slices/<you>.md`, `context/contracts.md`, and **your** section of `context/progress.md`.
2. `git pull --rebase origin main` on your slice branch.
3. Name **the one task** for this session in one line: requirement ID + demo row + done-when. Example: "R7 robust z ranking — row 2 — done when `cli search 'a photo of keys'` ranks the keys frame first on the replayed day."

## Stay in your slice

- Edit only files your slice owns (`architecture.md` → Repo layout and file ownership).
- If the task needs another slice's file, a shared file (`app.py`, `config.py`, `contracts.py`, `pyproject.toml`) or a contract change: **stop and say so.** Write the request in `progress.md` → your Blocked line and tell the owner. Don't "just fix it".
- Missing piece from another slice? Use its stub or fixture (`architecture.md` → Parallel plan). Never wait idle.

## The loop

1. **Plan briefly** — ≤ 5 bullets, files named.
2. **Build the smallest working version** behind the contract.
3. **Run it** — the slice's smoke check (`setup.md` §8) or the relevant test. Show the actual output.
4. **Commit** — `[slice] verb: what` on your slice branch. Merge to main only if main still runs.

## Model calls — EmbeddingGemma 2 and Gemma 4 are new

- Before writing any model call, check it against the current model card or the installed package (`python -c "import sentence_transformers, inspect; ..."`, `pip show`, the package source). Don't trust memory.
- Calls to verify: `SentenceTransformer(..., config_kwargs={"audio_config": None})`, `encode({"image": ...})`, `prompt_name="SearchQuery"`, `processing_kwargs={"image": {"max_soft_tokens": N}}`; for R8 the chat template with image-before-text and `enable_thinking=False`.
- dtype: bfloat16 if `torch.cuda.is_bf16_supported()`, else float32. **Never float16** — it fails silently (NaN or worse vectors).

## Never

- Send a frame, vector or question off the laptop (no cloud API, no paid API, no telemetry, no CDN).
- Print or log tokens/secrets; commit `.env`, weights, frames, videos, `*.db`.
- Invent data: no made-up test results, ground-truth times, latency numbers or licenses. Unknown → say unknown.
- Use a raw cosine cutoff, or pick the highest score instead of the newest candidate.
- Start a Could (R8, R13, R14, R15) before demo rows 1–4 pass twice.

## Stuck 20 minutes → take the fallback

Take the fallback listed in your slice brief (or `architecture.md` → Failure table), log it in `decisions.md` → your section ("15:52 · switched to embed-every-2nd-frame · embed 900 ms · Daniel"), and move on.

## Session end

1. Update your section of `progress.md`: **Now / Next / Blocked**, plus your R-rows' status.
2. Log decisions in your section of `decisions.md`: time · decision · why · who.
3. Commit, push your branch, merge to main if smoke checks pass.
4. `/clear`.

## Ask the human before

- Deleting any file · adding a dependency · any destructive git command (`reset --hard`, `push --force`, branch delete, `clean -fd`) · touching another slice's files.

## After the 6:00 PM freeze (gate 3)

No code changes except **demo-breaking** fixes, each logged in `decisions.md` and announced to the team. 6:00–6:10 backup video, 6:10–6:15 submit.

## Parallel sessions on one laptop

If two people's Claude Code sessions share the demo laptop: separate clones (`~/remem-aziz`, `~/remem-daniel`), separate venvs share one `HF_HOME`; only one uvicorn on port 8000 (the integration clone on main). Test your branch on another port (`--port 8001`) with its own `REMEM_DATA_DIR`.
