"""R10 — push-to-talk: transcribe one short clip on the laptop. Audio lives only in memory.

Decode: the ffmpeg CLI over pipes (clip on stdin → 16 kHz mono float32 on stdout), no temp files.
Model: STT_MODEL (openai/whisper-small) through the transformers ASR pipeline, on the GPU if present.
torch/transformers are imported only in load(), so stub-mode laptops run without them.
"""

import logging
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from remem import config

log = logging.getLogger("remem.answer")

SAMPLE_RATE = 16_000
MAX_SECONDS = 15
TIMEOUT_S = 4.0  # context/code-standards.md → R10 transcription
SILENCE_RMS = 0.003  # whisper invents "Thank you." on silence; don't send it a near-silent clip

_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="stt")
_load_lock = threading.Lock()
_asr = None
_load_error: str | None = None


class SttError(Exception):
    """A clip couldn't be transcribed; `status` is the HTTP code for POST /ask/voice."""

    def __init__(self, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.status = status


def load() -> None:
    """Load the ASR model once (takes seconds). Safe to call from several threads."""
    global _asr, _load_error
    with _load_lock:
        if _asr is not None or _load_error is not None:
            return
        start = time.perf_counter()
        try:
            import torch
            from transformers import pipeline

            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            # transformers 5 defaults to dtype="auto" (the checkpoint's); pin float32 so it's predictable.
            _asr = pipeline("automatic-speech-recognition", model=config.STT_MODEL, device=device,
                            dtype=torch.float32)
        # stub mode (no torch), download/disk errors, CUDA OOM, bad STT_MODEL
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            _load_error = f"{type(exc).__name__}: {exc}"
            log.warning("stt unavailable model=%s: %s", config.STT_MODEL, _load_error)
            return
        log.info("stt loaded model=%s device=%s load_ms=%.0f", config.STT_MODEL, device,
                 (time.perf_counter() - start) * 1000)


def warm() -> None:
    """Start load() in the background so the first question doesn't pay for it."""
    if _asr is None and _load_error is None:
        _pool.submit(load)


def _decode(audio: bytes):
    import numpy as np

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SttError("ffmpeg not installed (context/setup.md §1)", status=503)
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-t", str(MAX_SECONDS),
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1"],
        input=audio, capture_output=True, timeout=TIMEOUT_S, check=False,
    )
    if proc.returncode != 0:
        last_line = (proc.stderr.decode(errors="replace").strip().splitlines() or ["?"])[-1]
        raise SttError(f"can't decode audio: {last_line[:200]}")
    samples = np.frombuffer(proc.stdout, dtype=np.float32)
    if samples.size < SAMPLE_RATE // 4:
        raise SttError("clip too short")
    if float(np.sqrt(np.mean(samples**2))) < SILENCE_RMS:
        raise SttError("only silence")
    return samples


def _transcribe(audio: bytes) -> str:
    start = time.perf_counter()
    samples = _decode(audio)
    decode_ms = (time.perf_counter() - start) * 1000
    load()
    if _asr is None:
        raise SttError(f"speech model unavailable: {_load_error}", status=503)
    out = _asr(
        {"raw": samples, "sampling_rate": SAMPLE_RATE},
        generate_kwargs={"language": "english", "task": "transcribe"},
    )
    text = out["text"].strip()
    log.info('stt text="%s" audio_s=%.1f decode_ms=%.0f total_ms=%.0f', text, samples.size / SAMPLE_RATE,
             decode_ms, (time.perf_counter() - start) * 1000)
    return text


def transcribe(audio: bytes) -> str:
    """Clip bytes (Safari audio/mp4, Chrome audio/webm, wav…) → text. Raises SttError."""
    try:
        return _pool.submit(_transcribe, audio).result(timeout=TIMEOUT_S)
    except FutureTimeout as exc:
        raise SttError("transcription timed out", status=504) from exc
    except subprocess.TimeoutExpired as exc:
        raise SttError("decoding timed out", status=504) from exc
