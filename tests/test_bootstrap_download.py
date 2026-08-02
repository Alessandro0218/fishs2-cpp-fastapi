from __future__ import annotations

import io
from pathlib import Path

import pytest

import run


class FakeResponse(io.BytesIO):
    def __init__(self, data: bytes, *, status: int, headers: dict[str, str]):
        super().__init__(data)
        self.status = status
        self.headers = headers

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def partial_path(destination: Path) -> Path:
    return destination.with_suffix(destination.suffix + ".part")


def test_download_resumes_an_existing_partial_file(monkeypatch, tmp_path):
    destination = tmp_path / "model.gguf"
    partial_path(destination).write_bytes(b"abc")
    requests = []

    def urlopen(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(
            b"def",
            status=206,
            headers={"Content-Length": "3", "Content-Range": "bytes 3-5/6"},
        )

    monkeypatch.setattr(run.urllib.request, "urlopen", urlopen)
    run._download_file("https://example.test/model", destination, label="model")

    assert destination.read_bytes() == b"abcdef"
    assert requests[0][0].get_header("Range") == "bytes=3-"
    assert requests[0][1] == 120


def test_download_restarts_when_server_ignores_range(monkeypatch, tmp_path):
    destination = tmp_path / "model.gguf"
    partial_path(destination).write_bytes(b"stale")
    monkeypatch.setattr(
        run.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            b"fresh",
            status=200,
            headers={"Content-Length": "5"},
        ),
    )

    run._download_file("https://example.test/model", destination, label="model")

    assert destination.read_bytes() == b"fresh"


def test_download_rejects_a_mismatched_resume_offset(monkeypatch, tmp_path):
    destination = tmp_path / "model.gguf"
    partial = partial_path(destination)
    partial.write_bytes(b"abc")
    monkeypatch.setenv("FISHS2_DOWNLOAD_ATTEMPTS", "1")
    monkeypatch.setattr(
        run.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            b"wrong",
            status=206,
            headers={"Content-Length": "5", "Content-Range": "bytes 4-8/9"},
        ),
    )

    with pytest.raises(RuntimeError, match="resumed from the wrong byte"):
        run._download_file("https://example.test/model", destination, label="model")

    assert partial.read_bytes() == b"abc"


def test_download_preserves_progress_after_bounded_failure(monkeypatch, tmp_path):
    destination = tmp_path / "model.gguf"
    partial = partial_path(destination)
    partial.write_bytes(b"partial")
    monkeypatch.setenv("FISHS2_DOWNLOAD_ATTEMPTS", "1")
    monkeypatch.setattr(
        run.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("stalled")),
    )

    with pytest.raises(RuntimeError, match="partial download remains"):
        run._download_file("https://example.test/model", destination, label="model")

    assert partial.read_bytes() == b"partial"
