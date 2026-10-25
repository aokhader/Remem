"""Compare bare-object and photo query text on the supplied three-photo fixture."""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from remem import config
from remem.index import gemma


def main() -> None:
    paths = sorted(Path("test_photos").glob("*.jpeg"))
    if {p.name for p in paths} != {"closekey.jpeg", "farkey.jpeg", "nokey.jpeg"}:
        raise ValueError("Expected the three original local test photos")
    images = []
    for path in paths:
        with Image.open(path) as photo:
            images.append({"image": ImageOps.exif_transpose(photo).convert("RGB")})
    gemma.load()
    matrix = gemma._encode(
        images, timeout=5, batch_size=1, prompt="",
        processing_kwargs={"image": {"max_soft_tokens": config.EMBED_IMAGE_TOKENS}},
    )
    results = {}
    for text in ("keys", "a photo of keys"):
        query = gemma._encode(text, timeout=2, prompt_name="SearchQuery")[0]
        scores = matrix @ query
        results[text] = {
            "ranking": [{"photo": paths[i].name, "cosine": float(scores[i])}
                        for i in np.argsort(-scores, kind="stable")],
            "weakest_positive_minus_negative": float(min(scores[0], scores[1]) - scores[2]),
        }
    report = {"dtype": gemma.stats().dtype, "image_tokens": config.EMBED_IMAGE_TOKENS,
              "prompt_name": "SearchQuery", "queries": results,
              "note": "Diagnostic relative scores; no production query template or thresholds changed"}
    output = json.dumps(report, indent=2)
    Path(__file__).with_name("query-ab.local.json").write_text(output, encoding="utf-8")
    print(output, flush=True)


if __name__ == "__main__":
    main()
