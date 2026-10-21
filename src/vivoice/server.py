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
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import soundfile as sf

ENGINE_NAME = "rvc"
SAMPLE_RATE = 40_000
MAX_BODY_BYTES = 128 * 1024 * 1024

# Flip to True once ``convert_audio`` is wired to the vendored engine.
CONVERTER_READY = False


def convert_audio(
    wav_bytes: bytes,
    model_path: str,
    index_path: str,
    device: str,
) -> np.ndarray:
    """Convert one WAV payload to float32 mono audio at 40 kHz.

    This is the single integration point for the vendored RVC engine; the
    exact upstream calls are described in docs/AI_HANDBOOK.md section 4.
    """
    raise NotImplementedError(
        "The RVC engine is not wired into this server yet; "
        "see docs/AI_HANDBOOK.md section 4."
    )


class _Handler(BaseHTTPRequestHandler):
    server_version = "VIvoice/0.3"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self._json(404, {"error": "not found"})
            return
        self._json(200, {"engine": ENGINE_NAME, "ready": CONVERTER_READY})

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
                self.headers.get("X-Model-Path", ""),
                self.headers.get("X-Index", ""),
                "cpu",
            )
        except NotImplementedError as exc:
            self._json(501, {"error": str(exc)})
            return
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
