"""Reference server implementing the VIvoice voice-conversion protocol.

Run it inside the environment where the RVC engine is available:

    uv sync --extra ai
    python scripts/fetch_rvc.py
    vivoice serve --host 127.0.0.1 --port 7865

Endpoints (see docs/RVC_SERVER_PROTOCOL.md):

- ``GET /health`` — engine name and readiness as JSON
- ``POST /convert`` — WAV bytes in, WAV bytes out; ``X-Model-Path`` and
  ``X-Index`` headers select the voice model
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import tempfile
import urllib.parse
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import find_spec
from pathlib import Path

import numpy as np
import soundfile as sf

ENGINE_NAME = "rvc"
SAMPLE_RATE = 40_000
MAX_BODY_BYTES = 128 * 1024 * 1024

def converter_ready() -> bool:
    """The conversion endpoint is usable when the rvc-hub engine is installed."""
    return find_spec("huggingface_hub_rvc") is not None


def convert_audio(
    wav_bytes: bytes,
    model_path: str,
    index_path: str,
    device: str,
) -> np.ndarray:
    """Convert one WAV payload to float32 mono audio at 40 kHz."""
    if not model_path or not Path(model_path).is_file():
        raise RuntimeError(f"RVC model file not found: {model_path or '(missing)'}")
    if index_path and not Path(index_path).is_file():
        raise RuntimeError(f"RVC index file not found: {index_path}")
    try:
        from huggingface_hub_rvc import RVCPipeline
    except ImportError as exc:
        raise RuntimeError(
            "huggingface-hub-rvc is not installed; run: uv sync --extra ai"
        ) from exc

    audio, sample_rate = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    with tempfile.TemporaryDirectory(prefix="vivoice-server-") as temporary:
        root = Path(temporary)
        input_path = root / "input.wav"
        output_path = root / "output.wav"
        sf.write(str(input_path), np.asarray(audio, dtype=np.float32), int(sample_rate))
        model_directory = root / "model"
        model_directory.mkdir()
        shutil.copy2(model_path, model_directory / "model.pth")
        if index_path:
            shutil.copy2(index_path, model_directory / "model.index")

        from vivoice.ai.rvc.hub import _soundfile_torchaudio_backend

        with _soundfile_torchaudio_backend():
            pipeline = RVCPipeline.from_pretrained(model_directory)
            pipeline.convert_file(
                input_path,
                output_path,
                audio_mode="vocal_only",
                device=device,
                f0_method="rmvpe",
                retrieval_strength=0.75,
                output_sample_rate=SAMPLE_RATE,
            )
        converted, _output_rate = sf.read(
            str(output_path), dtype="float32", always_2d=False
        )
    return np.asarray(converted, dtype=np.float32).reshape(-1)


class _Handler(BaseHTTPRequestHandler):
    server_version = "VIvoice/0.3"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self._json(404, {"error": "not found"})
            return
        self._json(200, {"engine": ENGINE_NAME, "ready": converter_ready()})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/convert":
            self._json(404, {"error": "not found"})
            return
        length = self.headers.get("Content-Length")
        if length is None:
            self._json(411, {"error": "Content-Length header is required"})
            return
        if int(length) > MAX_BODY_BYTES:
            self._json(413, {"error": "payload too large"})
            return
        body = self.rfile.read(int(length))
        try:
            converted = convert_audio(
                body,
                urllib.parse.unquote(self.headers.get("X-Model-Path", "")),
                urllib.parse.unquote(self.headers.get("X-Index", "")),
                "cpu",
            )
        except Exception as exc:  # noqa: BLE001 - boundary reports JSON, never a crash
            self._json(500, {"error": f"conversion failed: {exc}"})
            return
        output = io.BytesIO()
        sf.write(
            output,
            np.asarray(converted, dtype=np.float32).reshape(-1),
            SAMPLE_RATE,
            format="WAV",
            subtype="FLOAT",
        )
        payload = output.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Keep server logs concise."""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the VIvoice conversion server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7865)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    print(f"VIvoice conversion server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
