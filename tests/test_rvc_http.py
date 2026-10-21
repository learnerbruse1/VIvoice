from __future__ import annotations

import io
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pytest
import soundfile as sf

from vivoice.ai.device import Device
from vivoice.ai.rvc.http import RvcHttpAdapter
from vivoice.core import ConversionError
from vivoice.models.model import VoiceModel


def _server(handler_class: type[BaseHTTPRequestHandler]) -> tuple[ThreadingHTTPServer, str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def _wav_bytes(samples: np.ndarray, sample_rate: int = 40_000) -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV", subtype="FLOAT")
    return buffer.getvalue()


def test_http_adapter_roundtrip(tmp_path) -> None:
    response = _wav_bytes(np.zeros(4_000, dtype=np.float32))
    received: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            received["body"] = self.rfile.read(length)
            received["model"] = self.headers.get("X-Model-Path")
            received["index"] = self.headers.get("X-Index")
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, format: str, *args: object) -> None:
            pass

    httpd, url = _server(Handler)
    try:
        model = VoiceModel("alice", tmp_path, tmp_path / "model.pth", None, "test")
        output = RvcHttpAdapter(Device.CPU).convert(
            np.zeros(4_000, dtype=np.float32),
            model,
            {"endpoint": url, "timeout": 5.0},
        )
        assert output.shape == (4_000,)
        assert received["model"].endswith("model.pth")
        assert received["index"] == ""
        assert len(received["body"]) > 44  # a WAV header at least
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_http_adapter_maps_server_error(tmp_path) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            self.rfile.read(int(self.headers["Content-Length"]))
            body = json.dumps({"error": "engine exploded"}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    httpd, url = _server(Handler)
    try:
        model = VoiceModel("alice", tmp_path, tmp_path / "model.pth", None, "test")
        with pytest.raises(ConversionError, match="engine exploded"):
            RvcHttpAdapter(Device.CPU).convert(
                np.zeros(64, np.float32), model, {"endpoint": url}
            )
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_http_adapter_reports_unreachable_server(tmp_path) -> None:
    model = VoiceModel("alice", tmp_path, tmp_path / "model.pth", None, "test")
    with pytest.raises(ConversionError, match="Cannot reach"):
        RvcHttpAdapter(Device.CPU).convert(
            np.zeros(64, np.float32),
            model,
            {"endpoint": "http://127.0.0.1:1", "timeout": 1.0},
        )


def test_http_adapter_encodes_non_ascii_headers(tmp_path) -> None:
    response = _wav_bytes(np.zeros(64, dtype=np.float32))
    received: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            self.rfile.read(int(self.headers["Content-Length"]))
            received["name"] = self.headers.get("X-Voice-Model")
            received["model"] = self.headers.get("X-Model-Path")
            received["index"] = self.headers.get("X-Index")
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, format: str, *args: object) -> None:
            pass

    httpd, url = _server(Handler)
    try:
        directory = tmp_path / "角色"
        checkpoint = directory / "模型.pth"
        index = directory / "索引.index"
        model = VoiceModel("懒羊羊", directory, checkpoint, index, "test")
        RvcHttpAdapter(Device.CPU).convert(
            np.zeros(64, np.float32), model, {"endpoint": url}
        )
        assert received["name"] == urllib.parse.quote("懒羊羊")
        assert urllib.parse.unquote(received["model"]) == str(checkpoint)
        assert urllib.parse.unquote(received["index"]) == str(index)
    finally:
        httpd.shutdown()
        httpd.server_close()
