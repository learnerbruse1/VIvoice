"""Linear gain with hard clipping."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np

from vivoice.core.effect import Effect, EffectContext, register_effect


@register_effect
class GainEffect(Effect):
    effect_type: ClassVar[str] = "gain"
    description: ClassVar[str] = "Apply a dB gain and hard-clip to [-1, 1]."
    streaming: ClassVar[bool] = True
    default_params: ClassVar[Mapping[str, Any]] = {"gain_db": 0.0}

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        gain_db = float(self.params["gain_db"])
        linear = 10.0 ** (gain_db / 20.0)
        return np.clip(samples * linear, -1.0, 1.0).astype(np.float32)
