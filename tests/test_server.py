from __future__ import annotations

import io
import json
import sys
import threading
import types
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import numpy as np
import pytest
import soundfile as sf

from vivoice.server import _Handler, convert_audio, converter_ready


def _start() -> tuple[ThreadingHTTPServer, str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def test_health_reports_engine_and_readiness() -> None:
    httpd, url = _start()
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=5) as response:
            payload = json.loads(response.read())
        assert payload == {"engine": "rvc", "ready": converter_ready()}
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_convert_audio_uses_hub_engine(tmp_path, monkeypatch) -> None:
    pytest.importorskip("torch")
    module = types.ModuleType("huggingface_hub_rvc")

    class FakePipeline:
        last_instance: FakePipeline | None = None

        def __init__(self) -> None:
            self.kwargs: dict = {}
            FakePipeline.last_instance = self

        @classmethod
        def from_pretrained(cls, directory, **kwargs) -> FakePipeline:
            instance = cls()
            instance.directory = directory
            return instance

        def convert_file(self, source, output, **kwargs) -> None:
            self.kwargs.update(kwargs)
            data, sample_rate = sf.read(str(source), dtype="float32")
            sf.write(str(output), data * 0.5, 40_000, format="WAV", subtype="FLOAT")

    module.RVCPipeline = FakePipeline
    monkeypatch.setitem(sys.modules, "huggingface_hub_rvc", module)
    checkpoint = tmp_path / "model.pth"
    checkpoint.write_bytes(b"checkpoint")
    index = tmp_path / "model.index"
    index.write_bytes(b"index")
    buffer = io.BytesIO()
    sf.write(
        buffer,
        np.ones(8_000, np.float32) * 0.2,
        40_000,
        format="WAV",
        subtype="FLOAT",
    )

    output = convert_audio(buffer.getvalue(), str(checkpoint), str(index), "cpu")
    assert output.shape == (8_000,)
    assert np.allclose(output, 0.1, atol=1e-5)
    instance = FakePipeline.last_instance
    assert instance is not None
    assert instance.kwargs["audio_mode"] == "vocal_only"
    assert instance.kwargs["device"] == "cpu"
    assert instance.kwargs["output_sample_rate"] == 40_000


def test_handler_unquotes_encoded_paths(monkeypatch) -> None:
    captured: dict = {}

    def fake_convert(body, model_path, index_path, device):
        captured.update(model=model_path, index=index_path)
        return np.zeros(16, np.float32)

    monkeypatch.setattr("vivoice.server.convert_audio", fake_convert)
    httpd, url = _start()
    try:
        buffer = io.BytesIO()
        sf.write(buffer, np.zeros(16, np.float32), 40_000, format="WAV")
        request = urllib.request.Request(
            f"{url}/convert",
            data=buffer.getvalue(),
            method="POST",
            headers={
                "Content-Type": "audio/wav",
                "X-Model-Path": urllib.parse.quote("E:\\角色\\模型.pth", safe="/\\:"),
                "X-Index": urllib.parse.quote("E:\\角色\\索引.index", safe="/\\:"),
            },
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.status == 200
        assert captured["model"] == "E:\\角色\\模型.pth"
        assert captured["index"] == "E:\\角色\\索引.index"
    finally:
        httpd.shutdown()
        httpd.server_close()
