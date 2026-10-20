"""Three-band equalizer built from RBJ biquad filters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np
from scipy.signal import lfilter

from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError


def _low_shelf(
    sample_rate: float,
    frequency: float,
    gain_db: float,
) -> tuple[np.ndarray, np.ndarray]:
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * frequency / sample_rate
    alpha = np.sin(w0) / (2.0 * 0.707)
    cos_w = np.cos(w0)
    root_a = np.sqrt(a)
    b0 = a * ((a + 1.0) - (a - 1.0) * cos_w + 2.0 * root_a * alpha)
    b1 = 2.0 * a * ((a - 1.0) - (a + 1.0) * cos_w)
    b2 = a * ((a + 1.0) - (a - 1.0) * cos_w - 2.0 * root_a * alpha)
    a0 = (a + 1.0) + (a - 1.0) * cos_w + 2.0 * root_a * alpha
    a1 = -2.0 * ((a - 1.0) + (a + 1.0) * cos_w)
    a2 = (a + 1.0) + (a - 1.0) * cos_w - 2.0 * root_a * alpha
    return np.array([b0, b1, b2]) / a0, np.array([a0, a1, a2]) / a0


def _peaking(sample_rate: float, frequency: float, gain_db: float) -> tuple[np.ndarray, np.ndarray]:
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * frequency / sample_rate
    alpha = np.sin(w0) / (2.0 * 0.707)
    cos_w = np.cos(w0)
    b0 = 1.0 + alpha * a
    b1 = -2.0 * cos_w
    b2 = 1.0 - alpha * a
    a0 = 1.0 + alpha / a
    a1 = -2.0 * cos_w
    a2 = 1.0 - alpha / a
    return np.array([b0, b1, b2]) / a0, np.array([a0, a1, a2]) / a0


def _high_shelf(
    sample_rate: float,
    frequency: float,
    gain_db: float,
) -> tuple[np.ndarray, np.ndarray]:
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * frequency / sample_rate
    alpha = np.sin(w0) / (2.0 * 0.707)
    cos_w = np.cos(w0)
    root_a = np.sqrt(a)
    b0 = a * ((a + 1.0) + (a - 1.0) * cos_w + 2.0 * root_a * alpha)
    b1 = -2.0 * a * ((a - 1.0) + (a + 1.0) * cos_w)
    b2 = a * ((a + 1.0) + (a - 1.0) * cos_w - 2.0 * root_a * alpha)
    a0 = (a + 1.0) - (a - 1.0) * cos_w + 2.0 * root_a * alpha
    a1 = 2.0 * ((a - 1.0) - (a + 1.0) * cos_w)
    a2 = (a + 1.0) - (a - 1.0) * cos_w - 2.0 * root_a * alpha
    return np.array([b0, b1, b2]) / a0, np.array([a0, a1, a2]) / a0


@register_effect
class EqualizerEffect(Effect):
    effect_type: ClassVar[str] = "eq"
    description: ClassVar[str] = "Three-band equalizer (low shelf, peak, high shelf)."
    streaming: ClassVar[bool] = True
    default_params: ClassVar[Mapping[str, Any]] = {
        "low_gain_db": 0.0,
        "mid_gain_db": 0.0,
        "high_gain_db": 0.0,
        "low_freq": 200.0,
        "mid_freq": 1000.0,
        "high_freq": 5000.0,
        "q": 0.707,
    }

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(params)
        for key in ("low_gain_db", "mid_gain_db", "high_gain_db"):
            if not -24.0 <= float(self.params[key]) <= 24.0:
                raise EffectError(f"'{key}' must be in [-24, 24] dB")
        for key in ("low_freq", "mid_freq", "high_freq"):
            if float(self.params[key]) <= 0.0:
                raise EffectError(f"'{key}' must be positive")
        if float(self.params["q"]) <= 0.0:
            raise EffectError("'q' must be positive")
        self._sample_rate: int | None = None
        self._stages: list[tuple[np.ndarray, np.ndarray]] = []
        self._zi: list[np.ndarray] | None = None

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        if self._sample_rate != context.sample_rate:
            self._build_stages(context.sample_rate)
            self._zi = None
        output = np.asarray(samples, dtype=np.float64)
        updated_zi: list[np.ndarray] = []
        for index, (numerator, denominator) in enumerate(self._stages):
            zi = self._zi[index] if self._zi is not None else None
            if zi is None or zi.shape[0] != samples.shape[0]:
                zi = np.zeros((samples.shape[0], 2))
            output, zi = lfilter(numerator, denominator, output, axis=1, zi=zi)
            updated_zi.append(zi)
        self._zi = updated_zi
        return output.astype(np.float32)

    def reset(self) -> None:
        self._zi = None
        self._sample_rate = None

    def _build_stages(self, sample_rate: int) -> None:
        self._sample_rate = sample_rate
        self._stages = [
            _low_shelf(
                sample_rate,
                float(self.params["low_freq"]),
                float(self.params["low_gain_db"]),
            ),
            _peaking(
                sample_rate,
                float(self.params["mid_freq"]),
                float(self.params["mid_gain_db"]),
            ),
            _high_shelf(
                sample_rate,
                float(self.params["high_freq"]),
                float(self.params["high_gain_db"]),
            ),
        ]
