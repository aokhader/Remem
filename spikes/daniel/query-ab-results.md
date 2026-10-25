# Bare keys vs photo query — 2026-10-25

Same original local photos, same image vectors, bfloat16, 280 image tokens,
normalized float32 comparisons; `prompt_name="SearchQuery"` for both queries.

| Photo | `keys` | `a photo of keys` |
|---|---|---|
| closekey.jpeg | 0.742602 | 0.709398 |
| farkey.jpeg | 0.705263 | 0.666007 |
| nokey.jpeg | 0.622002 | 0.563592 |

Both rank close keys, distant keys, no keys. Bare `keys` increases every score,
including the negative. The weaker positive minus negative gap is 0.083261 for
`keys` vs 0.102415 for `a photo of keys`. Thus bare `keys` does not improve ranking
or separation on this small fixture; no general accuracy conclusion follows.
Production template and thresholds are unchanged. No raw cosine cutoff is used.

Reproduce from repository root:

```powershell
$env:REMEM_INDEX='gemma'
$env:REMEM_DATA_DIR='data/step2-smoke'
spikes/daniel/.venv/Scripts/python -m spikes.daniel.query_ab
```
