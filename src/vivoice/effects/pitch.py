"""Pitch shift with a NumPy phase vocoder.

This is a compact, deterministic implementation good enough for v0. It is the
first candidate for a quality upgrade (see docs/ROADMAP.md, v0.3).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np
from scipy.signal import resample_poly

from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError


def _phase_vocoder_stretch(
    signal: np.ndarray,
    rate: float,
    frame: int = 1024,
    hop: int = 256,
) -> np.ndarray:
    """Time-stretch a 1-D signal by ``rate`` without changing pitch."""
    if rate == 1.0:
        return signal.copy()
    length = signal.shape[0]
    if length < frame + hop:
        return signal.copy()

    window = np.hanning(frame).astype(np.float32)
    frame_count = 1 + (length - frame) // hop
    bins = frame // 2 + 1

    spectrum = np.zeros((bins, frame_count), dtype=np.complex64)
    for index in range(frame_count):
        segment = signal[index * hop : index * hop + frame] * window
        spectrum[:, index] = np.fft.rfft(segment)

    phase = np.angle(spectrum)
    output_hop = max(1, int(round(hop * rate)))

    # Track how the input phase deviates from a bin-centered sine over the
    # analysis hop, then re-apply that deviation on top of the advance implied
    # by the synthesis hop. This keeps pitch constant while changing duration.
    analysis_advance = 2.0 * np.pi * np.arange(bins) * hop / frame
    synthesis_advance = 2.0 * np.pi * np.arange(bins) * output_hop / frame
    output_phase = np.zeros_like(phase)
    output_phase[:, 0] = phase[:, 0]
    for index in range(1, frame_count):
        delta = phase[:, index] - phase[:, index - 1] - analysis_advance
        delta = np.mod(delta + np.pi, 2.0 * np.pi) - np.pi
        output_phase[:, index] = output_phase[:, index - 1] + synthesis_advance + delta

    output_length = (frame_count - 1) * output_hop + frame
    output = np.zeros(output_length, dtype=np.float32)
    window_sum = np.zeros(output_length, dtype=np.float32)
    for index in range(frame_count):
        magnitude = np.abs(spectrum[:, index])
        segment = np.fft.irfft(magnitude * np.exp(1j * output_phase[:, index]))
        start = index * output_hop
        output[start : start + frame] += segment * window
        window_sum[start : start + frame] += window * window

    window_sum[window_sum < 1e-6] = 1.0
    return (output / window_sum).astype(np.float32)


def _match_length(signal: np.ndarray, target: int) -> np.ndarray:
    if signal.shape[0] > target:
        return signal[:target]
    if signal.shape[0] < target:
        return np.pad(signal, (0, target - signal.shape[0]))
    return signal


@register_effect
class PitchShiftEffect(Effect):
    effect_type: ClassVar[str] = "pitch"
    description: ClassVar[str] = "Shift pitch in semitones, preserving duration."
    default_params: ClassVar[Mapping[str, Any]] = {"semitones": 0.0}

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(params)
        semitones = float(self.params["semitones"])
        if not -24.0 <= semitones <= 24.0:
            raise EffectError("'semitones' must be in [-24, 24]")

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        semitones = float(self.params["semitones"])
        if semitones == 0.0:
            return np.array(samples, copy=True)
        factor = 2.0 ** (semitones / 12.0)
        down = max(1, int(round(factor * 1000.0)))

        channels = []
        for channel in samples:
            stretched = _phase_vocoder_stretch(channel, factor)
            shifted = resample_poly(stretched, up=1000, down=down).astype(np.float32)
            channels.append(_match_length(shifted, samples.shape[1]))
        return np.stack(channels)
