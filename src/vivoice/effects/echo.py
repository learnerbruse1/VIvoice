"""Feedback delay (comb filter) echo."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np
from scipy.signal import lfilter

from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError


@register_effect
class EchoEffect(Effect):
    effect_type: ClassVar[str] = "echo"
    description: ClassVar[str] = "Feedback delay echo."
    streaming: ClassVar[bool] = True
    block_process: ClassVar[bool] = True
    default_params: ClassVar[Mapping[str, Any]] = {
        "delay_seconds": 0.2,
        "feedback": 0.35,
        "mix": 0.5,
    }
    param_constraints: ClassVar[Mapping[str, Mapping[str, Any]]] = {
        "delay_seconds": {"minimum": 0.001, "maximum": 5.0},
        "feedback": {"minimum": 0.0, "maximum": 0.99},
        "mix": {"minimum": 0.0, "maximum": 1.0},
    }

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(params)
        self._zi: np.ndarray | None = None
        delay = float(self.params["delay_seconds"])
        feedback = float(self.params["feedback"])
        mix = float(self.params["mix"])
        if delay <= 0.0:
            raise EffectError("'delay_seconds' must be positive")
        if not 0.0 <= feedback < 1.0:
            raise EffectError("'feedback' must be in [0, 1)")
        if not 0.0 <= mix <= 1.0:
            raise EffectError("'mix' must be in [0, 1]")

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        delay = float(self.params["delay_seconds"])
        delay_samples = max(1, int(round(delay * context.sample_rate)))
        mix = float(self.params["mix"])
        feedback = float(self.params["feedback"])

        numerator = np.zeros(delay_samples + 1, dtype=np.float32)
        numerator[0] = 1.0
        numerator[delay_samples] = mix
        denominator = np.zeros(delay_samples + 1, dtype=np.float32)
        denominator[0] = 1.0
        denominator[delay_samples] = -feedback

        order = numerator.shape[0] - 1
        if self._zi is None or self._zi.shape[0] != samples.shape[0]:
            zi = np.zeros((samples.shape[0], order))
        else:
            zi = self._zi
        processed, zi = lfilter(numerator, denominator, samples, axis=1, zi=zi)
        self._zi = zi
        return processed.astype(np.float32)

    def reset(self) -> None:
        self._zi = None
