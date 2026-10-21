"""Voice conversion as an effect, bridging the core to the AI adapter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np
from scipy.signal import resample_poly

from vivoice.ai.adapter import get_adapter
from vivoice.ai.device import resolve_device
from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError
from vivoice.models.registry import ModelRegistry


@register_effect
class VoiceConversionEffect(Effect):
    effect_type: ClassVar[str] = "voice-conversion"
    description: ClassVar[str] = "Change speaker identity through an AI adapter."
    required_params: ClassVar[tuple[str, ...]] = ("model",)
    default_params: ClassVar[Mapping[str, Any]] = {
        "engine": "rvc",
        "device": "auto",
        "endpoint": "http://127.0.0.1:7865",
        "timeout": 300.0,
    }
    param_constraints: ClassVar[Mapping[str, Mapping[str, Any]]] = {
        "engine": {"enum": ["rvc", "rvc-hub", "rvc-http"]},
        "device": {"enum": ["auto", "cpu", "cuda", "mps"]},
        "timeout": {"minimum": 1.0, "maximum": 3600.0},
    }

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        engine = str(self.params["engine"])
        device = resolve_device(str(self.params["device"]))
        adapter = get_adapter(engine, device=device)

        try:
            model = ModelRegistry().get(str(self.params["model"]))
        except Exception as exc:
            raise EffectError(str(exc)) from exc

        mono = samples.mean(axis=0).astype(np.float32)
        if context.sample_rate != adapter.sample_rate:
            engine_audio = resample_poly(
                mono, up=adapter.sample_rate, down=context.sample_rate
            ).astype(np.float32)
        else:
            engine_audio = mono

        converted = adapter.convert(engine_audio, voice_model=model, params=dict(self.params))
        if context.sample_rate != adapter.sample_rate:
            converted = resample_poly(
                converted, up=context.sample_rate, down=adapter.sample_rate
            ).astype(np.float32)
        converted = _match_length(converted, samples.shape[1])
        return np.tile(converted, (samples.shape[0], 1))


def _match_length(signal: np.ndarray, target: int) -> np.ndarray:
    if signal.shape[0] > target:
        return signal[:target]
    if signal.shape[0] < target:
        return np.pad(signal, (0, target - signal.shape[0]))
    return signal
