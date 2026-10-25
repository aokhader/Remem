"""Inspect the installed API before running the Gate 1 model calls."""

import inspect
import json
from importlib.metadata import version
from pathlib import Path


def main() -> None:
    import torch
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.sentence_transformer.modules import Transformer

    report = {
        "versions": {name: version(name) for name in (
            "torch", "sentence-transformers", "transformers", "huggingface-hub"
        )},
        "cuda_available": torch.cuda.is_available(),
        "bf16_supported": torch.cuda.is_bf16_supported(),
        "selected_dtype": str(
            torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float32
        ),
        "constructor": str(inspect.signature(SentenceTransformer.__init__)),
        "encode": str(inspect.signature(SentenceTransformer.encode)),
        "transformer_preprocess": inspect.getsource(Transformer.preprocess),
    }
    text = json.dumps(report, indent=2)
    Path(__file__).with_name("preflight.local.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
