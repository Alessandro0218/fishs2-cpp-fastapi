from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np

from .logging_setup import APP_LOGGER_NAME
from .settings import settings

logger = logging.getLogger(APP_LOGGER_NAME)

WHISPER_SAMPLE_RATE = 16000


class TranscriptionUnavailable(RuntimeError):
    pass


class TranscriptionError(RuntimeError):
    pass


def _decode_to_pcm16k(audio_bytes: bytes) -> np.ndarray:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise TranscriptionUnavailable("ffmpeg not found on PATH: required to decode audio for transcription.")

    args = [
        ffmpeg, "-hide_banner", "-loglevel", "error",
        "-i", "pipe:0",
        "-ac", "1", "-ar", str(WHISPER_SAMPLE_RATE),
        "-f", "f32le", "pipe:1",
    ]
    proc = subprocess.run(args, input=audio_bytes, capture_output=True, check=False)
    if proc.returncode != 0 or not proc.stdout:
        detail = proc.stderr.decode(errors="replace").strip() or f"exit code {proc.returncode}"
        raise TranscriptionError(f"Could not decode audio: {detail}")
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


class WhisperTranscriber:
    def __init__(self):
        self._model: Any = None
        self._lock = Lock()

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        model_path = Path(settings.whisper_model_path)
        if not model_path.is_file():
            raise TranscriptionUnavailable(f"Whisper model not found: {model_path}")

        try:
            from pywhispercpp.model import Model
        except ImportError as exc:
            raise TranscriptionUnavailable(
                "pywhispercpp is not installed: required for audio transcription."
            ) from exc

        logger.info("Loading whisper model from %s", model_path)
        params: dict[str, Any] = {"print_progress": False, "print_realtime": False}
        if settings.whisper_n_threads:
            params["n_threads"] = settings.whisper_n_threads
        self._model = Model(str(model_path.resolve()), redirect_whispercpp_logs_to=None, **params)
        return self._model

    def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str:
        pcm = _decode_to_pcm16k(audio_bytes)
        if pcm.size == 0:
            raise TranscriptionError("Audio is empty")

        lang = (language or "").strip().lower() or "auto"
        with self._lock:
            model = self._get_model()
            segments = model.transcribe(pcm, language=lang)
        return " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()

    async def transcribe_async(self, audio_bytes: bytes, language: str | None = None) -> str:
        return await asyncio.to_thread(self.transcribe, audio_bytes, language)


transcriber = WhisperTranscriber()
