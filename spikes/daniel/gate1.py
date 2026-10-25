"""Local Gate 1 spike; run preflight.py and review its output first."""

import argparse
import json
import os
from pathlib import Path
from statistics import median
from time import perf_counter

# Model artifacts may be downloaded separately; inference must remain offline.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["DO_NOT_TRACK"] = "1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photos", type=Path, nargs="?", help="folder with exactly 3 photos")
    parser.add_argument("--keys", help="filename of the known keys photo")
    parser.add_argument("--tokens", type=int, choices=(70, 140, 280, 560, 1120), default=280)
    parser.add_argument("--ab", action="store_true")
    args = parser.parse_args()

    import numpy as np
    import torch
    from PIL import Image, ImageOps
    from sentence_transformers import SentenceTransformer

    bf16 = torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if bf16 else torch.float32
    print(f"torch.cuda.is_bf16_supported() = {bf16}", flush=True)
    print(f"dtype used = {dtype}", flush=True)
    if not torch.cuda.is_available():
        raise RuntimeError("Gate 1 requires a CUDA GPU")
    report = {
        "bf16_supported": bf16, "dtype": str(dtype),
        "gpu": torch.cuda.get_device_name(), "image_tokens": args.tokens,
        "warm_embed_ms": None, "keys_rank": None, "gate_pass": False,
    }
    start = perf_counter()
    model = SentenceTransformer(
        "google/embeddinggemma-2", device="cuda", local_files_only=True,
        config_kwargs={"audio_config": None}, model_kwargs={"torch_dtype": dtype},
    )
    torch.cuda.synchronize()
    report["load_s"] = perf_counter() - start
    parameter_dtypes = sorted({str(p.dtype) for p in model.parameters()})
    report["parameter_dtypes"] = parameter_dtypes
    if "torch.float16" in parameter_dtypes:
        raise RuntimeError("float16 parameters are forbidden")

    def checked(vector: np.ndarray) -> np.ndarray:
        vector = np.asarray(vector, dtype=np.float32)
        if vector.shape != (768,) or not np.isfinite(vector).all():
            raise RuntimeError(f"Invalid embedding: shape={vector.shape}")
        norm = float(np.linalg.norm(vector))
        if not 0.98 <= norm <= 1.02:
            raise RuntimeError(f"Embedding is not approximately normalized: {norm}")
        # BF16 normalization rounds; normalize again in the stored float32 dtype.
        return vector / norm

    if args.photos:
        paths = sorted(p for p in args.photos.iterdir() if p.suffix.lower() in {
            ".jpg", ".jpeg", ".png", ".webp"
        })
        if len(paths) != 3 or args.keys not in {p.name for p in paths}:
            parser.error("Supply exactly 3 photos and --keys with the known keys filename")
        images = []
        for path in paths:
            with Image.open(path) as photo:
                images.append(ImageOps.exif_transpose(photo).convert("RGB"))

        def embed_image(image: Image.Image) -> np.ndarray:
            return checked(model.encode(
                {"image": image}, normalize_embeddings=True, prompt="",
                show_progress_bar=False,
                processing_kwargs={"image": {"max_soft_tokens": args.tokens}},
            ))

        embed_image(images[0])  # untimed warm-up
        elapsed = []
        for _ in range(5):
            torch.cuda.synchronize()
            start = perf_counter()
            embed_image(images[0])
            torch.cuda.synchronize()
            elapsed.append((perf_counter() - start) * 1000)
        report["warm_embed_ms"] = median(elapsed)
        report["warm_samples_ms"] = elapsed
        matrix = np.stack([embed_image(image) for image in images])

        def query(text: str, use_prompt: bool = True) -> np.ndarray:
            prompt = {"prompt_name": "SearchQuery"} if use_prompt else {"prompt": ""}
            return checked(model.encode(
                text, normalize_embeddings=True, show_progress_bar=False, **prompt
            ))

        def rank(vector: np.ndarray) -> list[dict]:
            scores = matrix @ vector
            return [{"photo": paths[i].name, "cosine": float(scores[i])}
                    for i in np.argsort(-scores, kind="stable")]

        ranking = rank(query("a photo of keys"))
        report["ranking"] = ranking
        report["keys_rank"] = next(
            i + 1 for i, row in enumerate(ranking) if row["photo"] == args.keys
        )
        report["gate_pass"] = report["warm_embed_ms"] < 500 and report["keys_rank"] == 1
        if args.ab:
            variants = {}
            for name, texts in {
                "question": ["where are my keys?"],
                "photo": ["a photo of keys"],
                "mean_three": ["a photo of keys", "a set of keys", "keys on a surface"],
            }.items():
                for use_prompt in (True, False):
                    vector = np.mean([query(text, use_prompt) for text in texts], axis=0)
                    vector /= np.linalg.norm(vector)
                    variants[f"{name}/SearchQuery={use_prompt}"] = rank(vector)
            report["ab"] = variants
    else:
        report["blocked"] = "Three local test photos, including known keys photo, are required"

    output = json.dumps(report, indent=2)
    Path(__file__).with_name("result.local.json").write_text(output, encoding="utf-8")
    print(output, flush=True)


if __name__ == "__main__":
    main()
