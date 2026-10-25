"""Varick's dev server — runs the answer slice before Aziz's S0 skeleton lands.

    .venv/bin/python spikes/varick/devshim/devserver.py [--port 8000]

Stands in for remem/app.py: mounts the answer router and /static, serves
placeholder JPEGs at /frames/{id}.jpg, and seeds the stub index with six fake
frames (newest 10 min ago) so keys → Act, sunglasses → Ask, passport → None.
"""

import argparse
import io
import logging
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(Path(__file__).resolve().parent)]

import uvicorn  # noqa: E402
from fastapi import FastAPI, Response  # noqa: E402
from fastapi.responses import RedirectResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from remem import index  # noqa: E402
from remem.answer.routes import router as answer_router  # noqa: E402
from remem.contracts import FrameRecord  # noqa: E402

app = FastAPI(title="Remem dev (answer slice)")
app.include_router(answer_router)
app.mount("/static", StaticFiles(directory=REPO / "static"), name="static")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse("/ask")


@app.get("/frames/{frame_id}.jpg")
def frame(frame_id: int) -> Response:
    img = Image.new("RGB", (640, 480), (200, 205, 210))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=56)
    except TypeError:
        font = ImageFont.load_default()
    draw.text((40, 200), f"placeholder frame {frame_id}", fill=(40, 40, 40), font=font)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    return Response(buf.getvalue(), media_type="image/jpeg")


def seed() -> None:
    now = time.time()
    index.add([
        FrameRecord(id=i, ts=now - 3600 + i * 500, client_ts=None,
                    path=f"frames/{i:06d}.jpg", source="replay")
        for i in range(1, 7)
    ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    seed()
    uvicorn.run(app, host=args.host, port=args.port)
