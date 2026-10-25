"""Offline GPU duplicate/reload diagnostic on supplied photos, not accuracy data."""

import json
from pathlib import Path
from time import perf_counter

from remem import config, index
from remem.capture import store
from remem.contracts import Frame


def main() -> None:
    if (config.DATA_DIR / "remem.db").exists():
        raise ValueError("Use a fresh REMEM_DATA_DIR")
    index.load()
    photos = Path("test_photos")
    inputs = [photos / "closekey.jpeg"] * 3 + [photos / "nokey.jpeg"] * 2
    records = [store.save(Frame(jpeg=path.read_bytes(), client_ts=None, source="replay"), ts=float(i))
               for i, path in enumerate(inputs)]
    began = perf_counter()
    results = index.add(records[:3]) + index.add(records[3:])
    elapsed = perf_counter() - began
    expected = ["embedded", "dup", "dup", "embedded", "dup"]
    assert [r.status for r in results] == expected
    assert [r.dup_of for r in results] == [None, 1, 1, None, 4]
    before = index.stats().model_dump()
    index.load()
    after = index.stats().model_dump()
    assert before == after
    assert after["frames_indexed"] == 2 and after["frames_dup"] == 3 and after["frames_failed"] == 0
    print(json.dumps({"fixture": "5 frames from 2 supplied photos; diagnostic only",
                      "results": [r.model_dump() for r in results], "elapsed_s": elapsed,
                      "processed_fps": len(records) / elapsed, "reload_stats": after}, indent=2))


if __name__ == "__main__":
    main()
