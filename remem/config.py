"""Every env var from context/setup.md §5, read once at import. Nothing else reads os.environ."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    # tiny .env parser instead of python-dotenv: KEY=value lines, '#' comments; real env vars win
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.split(" #", 1)[0].strip().strip("\"'")
        if sep and key and not key.startswith("#") and value:
            os.environ.setdefault(key, value)


_load_dotenv(ROOT / ".env")
_env = os.environ.get

# server (Aziz)
DATA_DIR = ROOT / _env("REMEM_DATA_DIR", "data/live")
PORT = int(_env("REMEM_PORT", "8000"))
TZ = _env("TZ", "America/Los_Angeles")
INGEST_QUEUE_MAX = int(_env("INGEST_QUEUE_MAX", "8"))
MAX_FRAME_BYTES = int(_env("MAX_FRAME_BYTES", "2000000"))
STALL_S = float(_env("STALL_S", "3"))
FACE_BLUR = _env("FACE_BLUR", "0") == "1"

# index (Daniel)
REMEM_INDEX = _env("REMEM_INDEX", "gemma")
EMBED_MODEL = _env("EMBED_MODEL", "google/embeddinggemma-2")
EMBED_DTYPE = _env("EMBED_DTYPE", "auto")
EMBED_IMAGE_TOKENS = int(_env("EMBED_IMAGE_TOKENS", "280"))
EMBED_BATCH = int(_env("EMBED_BATCH", "8"))
QUERY_TEMPLATE = _env("QUERY_TEMPLATE", "a photo of {X}")
Z_MIN = float(_env("Z_MIN", "3"))
Z_ACT = float(_env("Z_ACT", "5"))
TOP_K = int(_env("TOP_K", "10"))
VISIT_GAP_S = float(_env("VISIT_GAP_S", "5"))
MIN_FRAMES = int(_env("MIN_FRAMES", "30"))
DEDUPE_COS = float(_env("DEDUPE_COS", "0.98"))

# answer (Varick)
ASK_TIMEOUT_S = float(_env("ASK_TIMEOUT_S", "5"))
VERIFY_BACKEND = _env("VERIFY_BACKEND", "none")
VERIFY_MODEL = _env("VERIFY_MODEL", "google/gemma-4-E4B-it")
VERIFY_N = int(_env("VERIFY_N", "5"))
VERIFY_TIMEOUT_S = float(_env("VERIFY_TIMEOUT_S", "2.5"))
CONF_ACT = float(_env("CONF_ACT", "0.8"))
CONF_ASK = float(_env("CONF_ASK", "0.5"))
STT_MODEL = _env("STT_MODEL", "openai/whisper-small")

# Hugging Face: huggingface_hub reads these from os.environ itself. Never log HF_TOKEN.
HF_HOME = _env("HF_HOME")
HF_TOKEN = _env("HF_TOKEN")

if REMEM_INDEX not in ("stub", "gemma"):
    raise ValueError(f"REMEM_INDEX={REMEM_INDEX!r}: use stub or gemma")
if EMBED_DTYPE not in ("auto", "bfloat16", "float32"):
    raise ValueError(f"EMBED_DTYPE={EMBED_DTYPE!r}: use auto, bfloat16 or float32 (never float16)")
