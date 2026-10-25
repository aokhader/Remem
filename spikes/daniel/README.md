# Daniel Gate 1 spike

Measured 2026-10-25 at 15:38 America/Los_Angeles. Spike passed;
this does not certify sustained ingest or the entire team's Gate 1.

## Verified API

Checked the [Google model card](https://huggingface.co/google/embeddinggemma-2)
and installed signatures/source before the model calls:

- `SentenceTransformer(..., config_kwargs={"audio_config": None}, model_kwargs={"torch_dtype": dtype})`
- `encode({"image": PIL_image}, processing_kwargs={"image": {"max_soft_tokens": 280}})`
- Text query uses `prompt_name="SearchQuery"`; images use no prefix.
- `normalize_embeddings=True`; validate finite 768-d outputs and normalize again
  in float32 because bf16 normalization can differ from unit norm by > 0.001.

Installed: torch 2.6.0+cu118, sentence-transformers 6.2.0,
transformers 5.20.2, huggingface-hub 2.3.0. Verified `BaseModel.__init__`,
`SentenceTransformer.encode`, `Transformer.preprocess`, and the Gemma4 image
processor's `max_soft_tokens`. Model revision:
`914f7f89142e33e77833254d9c9b90c3cef7303b` (existing local cache).

## Results

- NVIDIA GeForce RTX 4070 Laptop GPU, 8188 MiB, Windows native CUDA.
- `torch.cuda.is_bf16_supported() = True`; selected/actual parameters: bfloat16.
- Model load: 3.44 s; audio encoder disabled; 280 image tokens.
- Warm single-image samples: 132.98, 129.96, 123.04, 123.50, 121.69 ms.
- **Median: 123.50 ms**, one untimed warm-up, CUDA synchronization at boundaries.
  Includes encode/float32 validation, excludes load and JPEG decoding. Original
  supplied 768×1024 photos, no manual resize. No throughput inference from this test.

`a photo of keys` with SearchQuery:

| Rank | Local photo | Cosine (diagnostic only) |
|---|---|---|
| 1 | closekey.jpeg | 0.709398 |
| 2 | farkey.jpeg | 0.666007 |
| 3 | nokey.jpeg | 0.563592 |

Both first photos contain keys; the third contains no keys. This is not a
three-class or robust-z evaluation. No raw-score cutoff is used.

## Query A/B

All six variants ranked close/far/no keys. Scores below follow that order.
Mean-of-three averages normalized embeddings and normalizes the mean.

| Text | SearchQuery | Close | Far | No keys |
|---|---|---|---|---|
| where are my keys? | yes | 0.697945 | 0.693844 | 0.571912 |
| where are my keys? | no | 0.691801 | 0.688493 | 0.571646 |
| a photo of keys | yes | 0.709398 | 0.666007 | 0.563592 |
| a photo of keys | no | 0.694054 | 0.652759 | 0.552707 |
| mean of three | yes | 0.751725 | 0.707238 | 0.601541 |
| mean of three | no | 0.729682 | 0.684702 | 0.568587 |

Three phrasings: `a photo of keys`, `a set of keys`, `keys on a surface`.
No accuracy winner on this tiny set; keep the existing photo + SearchQuery baseline.

## Reproduce

Run from the repository root in PowerShell using the approved spike venv:

```powershell
spikes/daniel/.venv/Scripts/python spikes/daniel/preflight.py
spikes/daniel/.venv/Scripts/python -u spikes/daniel/gate1.py test_photos --keys closekey.jpeg --ab
```

Review preflight output before model calls. The venv inherits existing CUDA
torch via `--system-site-packages`; new packages were installed only in the venv.
Inference enforces offline Hub mode and disables telemetry. Model files must
already be cached. `.local.json` outputs, venv, and photos are not committed.
All photo processing and inference ran on this laptop.
