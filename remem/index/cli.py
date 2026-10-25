"""Local smoke, folder import, and retrieval: python -m remem.index.cli --help."""

import argparse
import io
import json
import logging
from datetime import datetime, time
from pathlib import Path
from time import perf_counter
from zoneinfo import ZoneInfo

from PIL import Image, ImageOps

from remem import config, index
from remem.contracts import Frame


def _photos(folder: Path) -> list[Path]:
    paths = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    if not paths:
        raise ValueError(f"No photos in {folder}")
    return paths


def _start(value: str) -> float:
    """HH:MM:SS means today in configured TZ; ISO datetimes can name a date."""
    zone = ZoneInfo(config.TZ)
    try:
        clock = time.fromisoformat(value)
    except ValueError:
        stamp = datetime.fromisoformat(value)
        return (stamp if stamp.tzinfo else stamp.replace(tzinfo=zone)).timestamp()
    return datetime.combine(datetime.now(zone).date(), clock, tzinfo=zone).timestamp()


def add_folder(folder: Path, start: str) -> dict:
    # Capture owns creation of JPEGs and frame rows, including replay timestamps.
    from remem.capture import store

    paths, began = _photos(folder), _start(start)
    counts = {"embedded": 0, "dup": 0, "failed": 0}
    wall_start = perf_counter()
    for offset in range(0, len(paths), config.EMBED_BATCH):
        records = []
        for i, path in enumerate(paths[offset:offset + config.EMBED_BATCH], start=offset):
            with Image.open(path) as photo:
                buffer = io.BytesIO()
                ImageOps.exif_transpose(photo).convert("RGB").save(buffer, format="JPEG", quality=90)
            record = store.save(Frame(jpeg=buffer.getvalue(), client_ts=None, source="replay"), ts=began + i)
            records.append(record)
        for result in index.add(records):
            counts[result.status] += 1
    elapsed = perf_counter() - wall_start
    return {
        "files": [path.name for path in paths], "start_epoch": began,
        "cadence_s": 1, "counts": counts, "elapsed_s": elapsed,
        "embedded_fps": counts["embedded"] / elapsed,
        "stats": index.stats().model_dump(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    smoke = commands.add_parser("smoke", help="warm image timing and cosine ranking (diagnostic)")
    smoke.add_argument("folder", type=Path)
    add = commands.add_parser("add-folder", help="import sorted photos at 1 fps into configured DATA_DIR")
    add.add_argument("folder", type=Path)
    add.add_argument("--start", required=True, help="HH:MM:SS today in TZ, or ISO datetime")
    search = commands.add_parser("search", help="search persisted embeddings with production guards")
    search.add_argument("text")
    search.add_argument("-k", type=int, default=config.TOP_K)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    index.load()
    if args.command == "smoke":
        if config.REMEM_INDEX != "gemma":
            parser.error("smoke requires REMEM_INDEX=gemma")
        from remem.index.gemma import smoke as run_smoke
        result = run_smoke(_photos(args.folder))
    elif args.command == "add-folder":
        result = add_folder(args.folder, args.start)
    else:
        hits = index.search(args.text, k=args.k)
        result = {
            "hits": [hit.model_dump() for hit in hits],
            "decision": index.decide(hits).model_dump(), "stats": index.stats().model_dump(),
            "guards": {"MIN_FRAMES": config.MIN_FRAMES, "Z_MIN": config.Z_MIN, "Z_ACT": config.Z_ACT},
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
