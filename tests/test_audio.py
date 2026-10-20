from __future__ import annotations

import numpy as np

from vivoice.audio import AudioBuffer, load_audio, save_audio


def test_roundtrip(tmp_path, sine_440: np.ndarray) -> None:
    path = tmp_path / "roundtrip.wav"
    save_audio(AudioBuffer(sine_440, 48_000), path)

    loaded = load_audio(path)

    assert loaded.sample_rate == 48_000
    assert loaded.samples.shape == sine_440.shape
    assert np.allclose(loaded.samples, sine_440, atol=1e-3)


def test_mono_mean(sine_440: np.ndarray) -> None:
    buffer = AudioBuffer(sine_440, 48_000)
    assert np.allclose(buffer.mono(), sine_440[0])
