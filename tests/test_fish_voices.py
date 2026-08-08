from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from fishs2_fastapi.main import app
from fishs2_fastapi.settings import settings
from fishs2_fastapi.voices import VoiceStore

client = TestClient(app)


def test_list_voices_aliases_match():
    primary = client.get("/v1/audio/voices")
    assert primary.status_code == 200
    assert primary.json()["object"] == "list"

    alias = client.get("/v1/voices")
    assert alias.status_code == 200
    assert alias.json() == primary.json()

    legacy = client.get("/v1/files")
    assert legacy.status_code == 200
    assert legacy.json() == primary.json()


def test_create_and_delete_voice_with_files_field():
    voice_id = f"fish-voice-{uuid4().hex}"
    payload = b"RIFF\x00\x00\x00\x00WAVE" + (b"\x00" * 512)

    created = client.post(
        "/v1/audio/voices",
        files={"files": ("sample.wav", payload, "audio/wav")},
        data={"voice_id": voice_id, "prompt_text": "sample transcript"},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["id"] == voice_id
    assert body["sample_count"] == 1

    listed = client.get("/v1/audio/voices")
    assert listed.status_code == 200
    ids = [item["voice_id"] for item in listed.json()["data"]]
    assert voice_id in ids

    deleted = client.delete(f"/v1/audio/voices/{voice_id}")
    assert deleted.status_code == 200


def test_voice_store_rejects_paths_outside_voice_root(tmp_path, monkeypatch):
    voice_root = tmp_path / "voices"
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(settings, "voices_dir", voice_root)

    store = VoiceStore()
    with pytest.raises(ValueError, match="Invalid voice ID"):
        store.delete("../outside")

    assert marker.read_text(encoding="utf-8") == "keep"
