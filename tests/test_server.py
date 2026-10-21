from __future__ import annotations

import io
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import numpy as np
import pytest
import soundfile as sf

from vivoice.server import _Handler


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
        assert payload == {"engine": "rvc", "ready": False}
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_convert_returns_501_until_wired() -> None:
    httpd, url = _start()
    try:
        buffer = io.BytesIO()
        sf.write(buffer, np.zeros(64, np.float32), 40_000, format="WAV")
        request = urllib.request.Request(
            f"{url}/convert",
            data=buffer.getvalue(),
            method="POST",
            headers={"Content-Type": "audio/wav"},
        )
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(request, timeout=5)
        payload = json.loads(excinfo.value.read())
        assert "not wired" in payload["error"]
    finally:
        httpd.shutdown()
        httpd.server_close()
