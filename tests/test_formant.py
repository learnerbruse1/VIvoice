from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import lfilter

import vivoice.effects  # noqa: F401  (register built-in effects)
from vivoice.core import Chain, ChainError, EffectContext, create_effect


def _formant_signal(sample_rate: int = 48_000, seconds: int = 2) -> np.ndarray:
    time = np.arange(sample_rate * seconds, dtype=np.float32) / sample_rate
    f0 = 140.0 + 5.0 * np.sin(2.0 * np.pi * 3.0 * time)
    phase = 2.0 * np.pi * np.cumsum(f0) / sample_rate
    harmonic = sum((1.0 / (n + 1)) * np.sin(n * phase) for n in range(1, 26))

    def resonator(frequency: float) -> tuple[np.ndarray, np.ndarray]:
        radius = 0.97
        omega = 2.0 * np.pi * frequency / sample_rate
        return np.array([1.0]), np.array([1.0, -2.0 * radius * np.cos(omega), radius**2])

    b1, a1 = resonator(700.0)
    b2, a2 = resonator(1_800.0)
    shaped = lfilter(b2, a2, lfilter(b1, a1, harmonic))
    shaped = np.asarray(shaped, dtype=np.float32)
    return (0.3 * shaped / max(1e-8, float(np.max(np.abs(shaped))))).astype(np.float32)


def _spectral_centroid(signal: np.ndarray, sample_rate: int) -> float:
    window = np.hanning(signal.shape[0]).astype(np.float32)
    spectrum = np.abs(np.fft.rfft(signal * window))
    frequencies = np.fft.rfftfreq(signal.shape[0], d=1.0 / sample_rate)
    return float(np.sum(frequencies * spectrum) / np.sum(spectrum))


def test_formant_zero_shift_is_identity() -> None:
    signal = np.stack([_formant_signal(), _formant_signal() * 0.7])
    effect = create_effect("formant", {"semitones": 0.0})
    output = effect.process(signal, EffectContext(48_000, 2))
    assert np.array_equal(output, signal)


def test_formant_shift_preserves_shape_and_is_deterministic() -> None:
    signal = _formant_signal()
    effect = create_effect("formant", {"semitones": 4.0})
    first = effect.process(signal[None, :], EffectContext(48_000, 1))
    second = create_effect("formant", {"semitones": 4.0}).process(
        signal[None, :], EffectContext(48_000, 1)
    )
    assert first.shape == (1, signal.shape[0])
    assert np.array_equal(first, second)
    assert np.isfinite(first).all()


def test_formant_shift_raises_spectral_centroid() -> None:
    signal = _formant_signal()
    baseline = create_effect("formant", {"semitones": 0.0}).process(
        signal[None, :], EffectContext(48_000, 1)
    )[0]
    shifted = create_effect("formant", {"semitones": 5.0}).process(
        signal[None, :], EffectContext(48_000, 1)
    )[0]
    assert _spectral_centroid(shifted, 48_000) > _spectral_centroid(baseline, 48_000) * 1.08


def test_formant_is_not_streamable() -> None:
    chain = Chain([create_effect("formant", {"semitones": 2.0})])
    with pytest.raises(ChainError, match="not available for streaming"):
        chain.open_stream(48_000)


def test_formant_rejects_out_of_range_shift() -> None:
    from vivoice.core import VivoiceError

    with pytest.raises(VivoiceError, match="semitones"):
        create_effect("formant", {"semitones": 20.0})
