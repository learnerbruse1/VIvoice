from __future__ import annotations

import numpy as np
import pytest

from vivoice.core import VivoiceError
from vivoice.core.effect import EffectContext, create_effect
from vivoice.effects import gain, pitch, robot  # noqa: F401  (register built-ins)
from vivoice.models import ModelRegistry


def test_gain_applies_db() -> None:
    effect = create_effect("gain", {"gain_db": 6.0})
    output = effect.process(np.array([[0.5]], dtype=np.float32), EffectContext(48_000, 1))
    assert output[0, 0] == pytest.approx(0.99763, abs=1e-3)


def test_gain_clips() -> None:
    effect = create_effect("gain", {"gain_db": 40.0})
    output = effect.process(np.array([[0.5]], dtype=np.float32), EffectContext(48_000, 1))
    assert output[0, 0] == 1.0


def test_robot_silences_dc_at_full_mix() -> None:
    effect = create_effect("robot", {"frequency": 100.0, "mix": 1.0})
    output = effect.process(np.ones((1, 4800), dtype=np.float32), EffectContext(48_000, 1))
    assert output[0, 0] == pytest.approx(0.0, abs=1e-6)
    assert np.max(np.abs(output)) <= 1.0


def test_echo_comb_taps() -> None:
    from vivoice.effects.echo import EchoEffect

    effect = EchoEffect({"delay_seconds": 0.1, "feedback": 0.5, "mix": 1.0})
    impulse = np.zeros((1, 48_000), dtype=np.float32)
    impulse[0, 0] = 1.0
    output = effect.process(impulse, EffectContext(48_000, 1))
    assert output[0, 0] == pytest.approx(1.0, abs=1e-6)
    assert output[0, 4800] == pytest.approx(1.5, abs=1e-6)
    assert output[0, 9600] == pytest.approx(0.75, abs=1e-6)


def test_pitch_shift_doubles_frequency(sine_440: np.ndarray) -> None:
    effect = create_effect("pitch", {"semitones": 12.0})
    output = effect.process(sine_440[:1], EffectContext(48_000, 1))
    assert output.shape == sine_440[:1].shape

    window = np.hanning(output.shape[1]).astype(np.float32)
    spectrum = np.abs(np.fft.rfft(output[0] * window))
    frequencies = np.fft.rfftfreq(output.shape[1], d=1.0 / 48_000)
    dominant = frequencies[np.argmax(spectrum)]
    assert 820.0 <= dominant <= 940.0


def test_voice_conversion_without_engine_fails_cleanly(
    tmp_path, monkeypatch, sine_440: np.ndarray
) -> None:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    checkpoint = tmp_path / "voice.pth"
    checkpoint.write_bytes(b"fake checkpoint")
    ModelRegistry().add("alice", checkpoint)

    effect = create_effect("voice-conversion", {"model": "alice"})
    with pytest.raises(VivoiceError, match="PyTorch|RVC"):
        effect.process(sine_440, EffectContext(48_000, 2))
