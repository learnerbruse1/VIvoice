"""Robot voice via ring modulation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np

from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError


@register_effect
class RobotEffect(Effect):
    effect_type: ClassVar[str] = "robot"
    description: ClassVar[str] = "Ring-modulation robot voice with dry/wet mix."
    default_params: ClassVar[Mapping[str, Any]] = {"frequency": 90.0, "mix": 1.0}

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(params)
        frequency = float(self.params["frequency"])
        mix = float(self.params["mix"])
        if frequency <= 0.0:
            raise EffectError("'frequency' must be positive")
        if not 0.0 <= mix <= 1.0:
            raise EffectError("'mix' must be in [0, 1]")

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        time = np.arange(samples.shape[1], dtype=np.float32) / context.sample_rate
        frequency = float(self.params["frequency"])
        carrier = np.sin(2.0 * np.pi * frequency * time).astype(np.float32)
        mix = float(self.params["mix"])
        wet = samples * carrier
        return (samples * (1.0 - mix) + wet * mix).astype(np.float32)
