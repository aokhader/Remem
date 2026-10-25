"""Varick's dev server — the answer slice with fake frames, no camera or GPU needed.

    .venv/bin/python spikes/varick/devshim/devserver.py [--port 8000]

Uses the real remem package with REMEM_INDEX=stub, but instead of remem/app.py it
mounts only the answer router and /static, serves placeholder JPEGs at
/frames/{id}.jpg, and seeds the stub index with six fake frames (newest 10 min
ago) so keys → Act, sunglasses → Ask, passport → None. For the full app with
Aziz's ingest: REMEM_INDEX=stub uvicorn remem.app:app.
"""

import argparse
import io
import logging
import os
import sys
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]


def placeholder_jpeg(frame_id: int) -> bytes:
    img = Image.new("RGB", (640, 480), (200, 205, 210))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=56)
    except TypeError:
        font = ImageFont.load_default()
    draw.text((40, 200), f"placeholder frame {frame_id}", fill=(40, 40, 40), font=font)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    return buf.getvalue()


def build_app() -> FastAPI:
    # remem.config reads REMEM_INDEX at import, so remem is imported only after it's set.
    sys.path.insert(0, str(REPO))
    os.environ.setdefault("REMEM_INDEX", "stub")
    from remem import index
    from remem.answer.routes import router as answer_router
    from remem.contracts import FrameRecord

    app = FastAPI(title="Remem dev (answer slice)")
    app.include_router(answer_router)
    app.mount("/static", StaticFiles(directory=REPO / "static"), name="static")

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse("/ask")

    @app.get("/frames/{frame_id}.jpg")
    def frame(frame_id: int) -> Response:
        return Response(placeholder_jpeg(frame_id), media_type="image/jpeg")

    now = time.time()
    index.add([
        FrameRecord(id=i, ts=now - 3600 + i * 500, client_ts=None, path=f"frames/{i:06d}.jpg", source="replay")
        for i in range(1, 7)
    ])
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    uvicorn.run(build_app(), host=args.host, port=args.port)
