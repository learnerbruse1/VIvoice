"""Formant (spectral-envelope) shifting.

Whole-signal effect: the phase vocoder infrastructure is reused for framing,
and each frame's cepstrally-smoothed spectral envelope is warped along the
frequency axis while the short-time phase (and therefore pitch) is kept.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np

from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError

_FRAME = 1024
_HOP = 256
_SMOOTH_HALF_WIDTH = 20
_ENVELOPE_GAIN_LIMIT = (0.25, 4.0)


@register_effect
class FormantShiftEffect(Effect):
    effect_type: ClassVar[str] = "formant"
    description: ClassVar[str] = "Shift spectral formants without changing pitch."
    default_params: ClassVar[Mapping[str, Any]] = {"semitones": 0.0}
    param_constraints: ClassVar[Mapping[str, Mapping[str, Any]]] = {
        "semitones": {"minimum": -12.0, "maximum": 12.0}
    }

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(params)
        semitones = float(self.params["semitones"])
        if not -12.0 <= semitones <= 12.0:
            raise EffectError("'semitones' must be in [-12, 12]")

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        semitones = float(self.params["semitones"])
        if semitones == 0.0:
            return np.array(samples, copy=True)
        factor = 2.0 ** (semitones / 12.0)
        output = np.stack(
            [_warp_channel(channel, factor) for channel in samples]
        )
        return _match_length(output, samples.shape[1])


def _warp_channel(signal: np.ndarray, factor: float) -> np.ndarray:
    length = signal.shape[0]
    if length < _FRAME + _HOP:
        return signal.copy()
    window = np.hanning(_FRAME).astype(np.float32)
    frame_count = 1 + (length - _FRAME) // _HOP
    output = np.zeros((frame_count - 1) * _HOP + _FRAME, dtype=np.float32)
    window_sum = np.zeros_like(output)

    for index in range(frame_count):
        segment = signal[index * _HOP : index * _HOP + _FRAME] * window
        spectrum = np.fft.rfft(segment)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)
        magnitude = _warp_envelope(magnitude, factor)
        reconstructed = np.fft.irfft(magnitude * np.exp(1j * phase))
        start = index * _HOP
        output[start : start + _FRAME] += reconstructed * window
        window_sum[start : start + _FRAME] += window * window
    window_sum[window_sum < 1e-6] = 1.0
    return (output / window_sum).astype(np.float32)


def _warp_envelope(magnitude: np.ndarray, factor: float) -> np.ndarray:
    epsilon = 1e-8
    log_spectrum = np.log(np.maximum(magnitude, epsilon))
    kernel = np.ones(2 * _SMOOTH_HALF_WIDTH + 1, dtype=np.float64) / (
        2 * _SMOOTH_HALF_WIDTH + 1
    )
    log_envelope = np.convolve(log_spectrum, kernel, mode="same")

    bins = np.arange(magnitude.shape[0], dtype=np.float64)
    source_bins = np.clip(bins / factor, 0.0, bins[-1])
    lower = np.floor(source_bins).astype(int)
    upper = np.minimum(lower + 1, magnitude.shape[0] - 1)
    fraction = source_bins - lower
    warped_log = log_envelope[lower] * (1.0 - fraction) + log_envelope[upper] * fraction

    ratio = np.clip(
        np.exp(warped_log - log_envelope),
        _ENVELOPE_GAIN_LIMIT[0],
        _ENVELOPE_GAIN_LIMIT[1],
    )
    return magnitude * ratio


def _match_length(samples: np.ndarray, target: int) -> np.ndarray:
    if samples.shape[1] > target:
        return samples[:, :target]
    if samples.shape[1] < target:
        return np.pad(samples, ((0, 0), (0, target - samples.shape[1])))
    return samples
