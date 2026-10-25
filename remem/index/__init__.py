"""Index facade (Daniel). REMEM_INDEX picks the backend; torch loads only when gemma is picked."""

import importlib

from remem import config
from remem.index.decide import decide

_backend = importlib.import_module(f"remem.index.{config.REMEM_INDEX}")
load = _backend.load
add = _backend.add
search = _backend.search
recall = _backend.recall
stats = _backend.stats

__all__ = ["add", "decide", "load", "recall", "search", "stats"]
