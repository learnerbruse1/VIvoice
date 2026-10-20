from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def sine_440() -> np.ndarray:
    """Two channels of a 0.3-amplitude 440 Hz sine, 2 s at 48 kHz."""
    sample_rate = 48_000
    time = np.arange(sample_rate * 2, dtype=np.float32) / sample_rate
    signal = (0.3 * np.sin(2.0 * np.pi * 440.0 * time)).astype(np.float32)
    return np.stack([signal, signal])


@pytest.fixture
def robot_preset() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "presets" / "robot.yaml"
