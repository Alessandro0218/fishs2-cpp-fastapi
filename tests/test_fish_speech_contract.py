import pytest
from fastapi.testclient import TestClient

from fishs2_fastapi.main import app

client = TestClient(app)


def test_speech_unsupported_format():
    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "fishs2",
            "input": "Hello",
            "voice": "default",
            "response_format": "flac",
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "unsupported_format"


def test_speech_ignores_speed_override(monkeypatch):
    captured = {}

    async def fake_generate(request, model_info=None):
        captured["speed"] = request.speed
        return b"RIFF" + (b"\x00" * 64)

    monkeypatch.setattr("fishs2_fastapi.main.engine.generate_speech_async", fake_generate)

    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "fishs2",
            "input": "Hello",
            "voice": "default",
            "speed": 1.2,
        },
    )
    assert resp.status_code == 200
    assert captured["speed"] == pytest.approx(1.2)


def test_speech_instructions_invalid_json():
    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "fishs2",
            "input": "Hello",
            "voice": "default",
            "instructions": "{not json",
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "invalid_instructions_json"


def test_speech_instructions_apply_fish_overrides(monkeypatch):
    captured = {}

    async def fake_generate(request, model_info=None):
        captured["temperature"] = request.fishs2.temperature if request.fishs2 else None
        captured["top_k"] = request.fishs2.top_k if request.fishs2 else None
        captured["control"] = request.control
        return b"RIFF" + (b"\x00" * 64)

    monkeypatch.setattr("fishs2_fastapi.main.engine.generate_speech_async", fake_generate)

    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "fishs2",
            "input": "Hello world",
            "voice": "default",
            "instructions": '{"fishs2": {"temperature": 0.6}, "top_k": 42, "control": "warm voice"}',
        },
    )

    assert resp.status_code == 200
    assert captured["temperature"] == pytest.approx(0.6)
    assert captured["top_k"] == 42
    assert captured["control"] == "warm voice"


def test_speech_unknown_model():
    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "unknown/model",
            "input": "Hello",
            "voice": "default",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "model_not_found"


def test_speech_accepts_fish_reference_field_names(monkeypatch):
    captured = {}

    async def fake_generate(request, model_info=None):
        captured["reference_audio"] = request.reference_audio
        captured["reference_text"] = request.reference_text
        return b"RIFF" + (b"\x00" * 64)

    monkeypatch.setattr("fishs2_fastapi.main.engine.generate_speech_async", fake_generate)

    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "fishs2",
            "input": "Hello",
            "voice": "default",
            "reference_audio": "E:/voices/ref.wav",
            "reference_text": "Reference transcript.",
        },
    )

    assert resp.status_code == 200
    assert captured["reference_audio"] == "E:/voices/ref.wav"
    assert captured["reference_text"] == "Reference transcript."


def test_speech_accepts_reference_aliases(monkeypatch):
    captured = {}

    async def fake_generate(request, model_info=None):
        captured["reference_audio"] = request.reference_audio
        captured["reference_text"] = request.reference_text
        return b"RIFF" + (b"\x00" * 64)

    monkeypatch.setattr("fishs2_fastapi.main.engine.generate_speech_async", fake_generate)

    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "fishs2",
            "input": "Hello",
            "voice": "default",
            "prompt_audio": "E:/voices/ref.wav",
            "ref_text": "Alias transcript.",
        },
    )

    assert resp.status_code == 200
    assert captured["reference_audio"] == "E:/voices/ref.wav"
    assert captured["reference_text"] == "Alias transcript."


def test_speech_mp3_output(monkeypatch):
    import io
    import shutil
    import wave

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(bytes(2 * 4410))
    wav_bytes = buf.getvalue()

    async def fake_generate(request, model_info=None):
        return wav_bytes

    monkeypatch.setattr("fishs2_fastapi.main.engine.generate_speech_async", fake_generate)

    resp = client.post(
        "/v1/audio/speech",
        json={
            "model": "fishs2",
            "input": "Hello",
            "voice": "default",
            "response_format": "mp3",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert resp.content[:3] == b"ID3" or resp.content[0] == 0xFF
