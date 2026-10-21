from __future__ import annotations

import numpy as np
import pytest

from vivoice.audio import AudioBuffer, audio_info, iter_blocks, load_audio, save_audio
from vivoice.core import VivoiceError


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


def test_audio_info_and_iter_blocks(tmp_path, sine_440: np.ndarray) -> None:
    path = tmp_path / "blocks.wav"
    save_audio(AudioBuffer(sine_440, 48_000), path)
    assert audio_info(path) == (sine_440.shape[1], sine_440.shape[0])
    blocks = list(iter_blocks(path, 10_000))
    assert np.allclose(np.concatenate(blocks, axis=1), sine_440, atol=1e-3)


def test_missing_audio_raises_friendly_error(tmp_path) -> None:
    with pytest.raises(VivoiceError, match="Cannot read"):
        load_audio(tmp_path / "missing.wav")
