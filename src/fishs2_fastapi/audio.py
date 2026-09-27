from __future__ import annotations

import asyncio
import shutil
import subprocess

SUPPORTED_FORMATS = {"wav", "mp3"}

MEDIA_TYPES = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
}

_FFMPEG_ENCODE_ARGS = {
    "mp3": ["-codec:a", "libmp3lame", "-q:a", "2", "-f", "mp3"],
}


class AudioConversionError(RuntimeError):
    pass


def _encode_with_ffmpeg(wav_bytes: bytes, response_format: str) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise AudioConversionError(
            f"ffmpeg not found on PATH: required to encode '{response_format}' output."
        )

    args = [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "wav", "-i", "pipe:0"]
    args += _FFMPEG_ENCODE_ARGS[response_format]
    args.append("pipe:1")

    proc = subprocess.run(args, input=wav_bytes, capture_output=True, check=False)
    if proc.returncode != 0 or not proc.stdout:
        detail = proc.stderr.decode(errors="replace").strip() or f"exit code {proc.returncode}"
        raise AudioConversionError(f"ffmpeg failed to encode {response_format}: {detail}")
    return proc.stdout


async def convert_wav(wav_bytes: bytes, response_format: str) -> bytes:
    if response_format == "wav":
        return wav_bytes
    if response_format not in _FFMPEG_ENCODE_ARGS:
        raise AudioConversionError(f"Unsupported response_format: {response_format}")
    return await asyncio.to_thread(_encode_with_ffmpeg, wav_bytes, response_format)
