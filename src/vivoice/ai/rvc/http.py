"""HTTP client for a VIvoice-compatible voice-conversion server.

The server side can be the reference ``scripts/rvc_server.py`` (run inside the
upstream RVC environment) or any implementation of
``docs/RVC_SERVER_PROTOCOL.md``. This adapter keeps the network boundary inside
the engine layer, exactly like the in-process adapter.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np
import soundfile as sf

from vivoice.ai.adapter import VoiceConversionAdapter, register_adapter
from vivoice.core.errors import ConversionError
from vivoice.models.model import VoiceModel

DEFAULT_ENDPOINT = "http://127.0.0.1:7865"
DEFAULT_TIMEOUT = 300.0


@register_adapter
class RvcHttpAdapter(VoiceConversionAdapter):
    engine: ClassVar[str] = "rvc-http"
    sample_rate: ClassVar[int] = 40_000

    def convert(
        self,
        audio_mono: np.ndarray,
        voice_model: VoiceModel,
        params: Mapping[str, Any],
    ) -> np.ndarray:
        endpoint = str(params.get("endpoint", DEFAULT_ENDPOINT)).rstrip("/")
        timeout = float(params.get("timeout", DEFAULT_TIMEOUT))

        payload = io.BytesIO()
        sf.write(payload, audio_mono, self.sample_rate, format="WAV", subtype="FLOAT")
        request = urllib.request.Request(
            f"{endpoint}/convert",
            data=payload.getvalue(),
            method="POST",
            headers={
                "Content-Type": "audio/wav",
                "X-Voice-Model": urllib.parse.quote(voice_model.name),
                "X-Model-Path": urllib.parse.quote(
                    str(voice_model.checkpoint), safe="/\\:"
                ),
                "X-Index": urllib.parse.quote(
                    str(voice_model.index), safe="/\\:"
                )
                if voice_model.index
                else "",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            raise ConversionError(
                f"Voice-conversion server error ({exc.code}): {_error_message(exc)}"
            ) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise ConversionError(
                f"Cannot reach voice-conversion server '{endpoint}': {exc}"
            ) from exc

        try:
            converted, sample_rate = sf.read(
                io.BytesIO(body), dtype="float32", always_2d=False
            )
        except Exception as exc:
            raise ConversionError("The server returned data that is not WAV audio") from exc
        result = np.asarray(converted, dtype=np.float32).reshape(-1)
        if int(sample_rate) != self.sample_rate:
            from scipy.signal import resample_poly

            result = resample_poly(
                result, up=self.sample_rate, down=int(sample_rate)
            ).astype(np.float32)
        return result


def _error_message(exc: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(exc.read().decode("utf-8"))
        if isinstance(body, dict) and body.get("error"):
            return str(body["error"])
    except Exception:
        pass
    return exc.reason
