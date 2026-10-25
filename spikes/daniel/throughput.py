"""Local throughput fixture using repeated supplied photos, not an accuracy dataset."""

import argparse
import io
import json
from pathlib import Path
from time import perf_counter

from PIL import Image, ImageOps

from remem import config, index
from remem.capture import store
from remem.contracts import Frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    photos = []
    for path in sorted(args.folder.iterdir()):
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        with Image.open(path) as image:
            buffer = io.BytesIO()
            ImageOps.exif_transpose(image).convert("RGB").save(buffer, format="JPEG", quality=90)
        photos.append(buffer.getvalue())
    if not photos or args.repeats < 1:
        parser.error("Need local photos and a positive repeat count")
    index.load()
    if store.counts()[0]:
        raise ValueError("Use a fresh REMEM_DATA_DIR for this benchmark")
    data = photos * args.repeats
    began = perf_counter()
    outcomes = []
    for offset in range(0, len(data), config.EMBED_BATCH):
        records = [store.save(Frame(jpeg=jpeg, client_ts=None, source="replay"), ts=float(offset + i))
                   for i, jpeg in enumerate(data[offset:offset + config.EMBED_BATCH])]
        outcomes.extend(index.add(records))
    elapsed = perf_counter() - began
    embedded = sum(row.status == "embedded" for row in outcomes)
    print(json.dumps({
        "fixture": f"{len(photos)} supplied photos repeated {args.repeats} times; not new observations",
        "frames": len(data), "embedded": embedded, "failed": len(data) - embedded,
        "elapsed_s": elapsed, "embedded_fps": embedded / elapsed,
        "includes": "frame saves, image decoding, batched encoding, SQLite and matrix updates; excludes model load",
        "stats": index.stats().model_dump(),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
