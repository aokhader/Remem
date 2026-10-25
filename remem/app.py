"""Remem server: one process, --workers 1 (the model and the frame matrix live in RAM)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from remem import capture, config, index
from remem.answer.routes import router as answer_router
from remem.capture.routes import router as capture_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    index.load()
    capture.start_worker()
    yield
    capture.stop_worker()


app = FastAPI(title="Remem", lifespan=lifespan)
app.include_router(capture_router)
app.include_router(answer_router)
app.mount("/static", StaticFiles(directory=config.ROOT / "static"), name="static")
