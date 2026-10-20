"""Noise gate with smooth attack/release envelope."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np

from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError


@register_effect
class NoiseGateEffect(Effect):
    effect_type: ClassVar[str] = "noise-gate"
    description: ClassVar[str] = "Attenuate signals below a threshold."
    streaming: ClassVar[bool] = True
    default_params: ClassVar[Mapping[str, Any]] = {
        "threshold_db": -40.0,
        "attack_ms": 5.0,
        "release_ms": 100.0,
        "floor_db": -80.0,
    }

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(params)
        if not -90.0 <= float(self.params["threshold_db"]) <= 0.0:
            raise EffectError("'threshold_db' must be in [-90, 0]")
        if float(self.params["floor_db"]) >= float(self.params["threshold_db"]):
            raise EffectError("'floor_db' must be below 'threshold_db'")
        if float(self.params["attack_ms"]) <= 0.0 or float(self.params["release_ms"]) <= 0.0:
            raise EffectError("'attack_ms' and 'release_ms' must be positive")
        self._envelope: np.ndarray | None = None

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        threshold = 10.0 ** (float(self.params["threshold_db"]) / 20.0)
        floor = 10.0 ** (float(self.params["floor_db"]) / 20.0)
        attack_ms = float(self.params["attack_ms"]) / 1000.0
        release_ms = float(self.params["release_ms"]) / 1000.0
        attack = float(np.exp(-1.0 / (attack_ms * context.sample_rate)))
        release = float(np.exp(-1.0 / (release_ms * context.sample_rate)))

        if self._envelope is None or self._envelope.shape[0] != samples.shape[0]:
            self._envelope = np.zeros(samples.shape[0], dtype=np.float32)
        output = np.empty_like(samples)
        for channel in range(samples.shape[0]):
            envelope = self._envelope[channel]
            for frame in range(samples.shape[1]):
                value = samples[channel, frame]
                magnitude = abs(float(value))
                coefficient = attack if magnitude > envelope else release
                envelope = coefficient * envelope + (1.0 - coefficient) * magnitude
                output[channel, frame] = value * (1.0 if envelope > threshold else floor)
            self._envelope[channel] = envelope
        return output

    def reset(self) -> None:
        self._envelope = None
