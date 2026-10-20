"""Audio buffer conventions and file I/O.

VIvoice processes float32 samples shaped ``(channels, frames)`` at 48 kHz by
default. The AI layer converts to engine-native rates (e.g. RVC's 40 kHz) at
the adapter boundary.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

DEFAULT_SAMPLE_RATE = 48_000


class AudioBuffer:
    """Immutable-in-practice buffer of float32 samples ``(channels, frames)``."""

    def __init__(self, samples: np.ndarray, sample_rate: int) -> None:
        if not isinstance(samples, np.ndarray):
            raise TypeError("samples must be a numpy array")
        if samples.ndim != 2:
            raise ValueError("samples must have shape (channels, frames)")
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self.samples = np.ascontiguousarray(samples, dtype=np.float32)
        self.sample_rate = int(sample_rate)

    @property
    def channels(self) -> int:
        return self.samples.shape[0]

    @property
    def frames(self) -> int:
        return self.samples.shape[1]

    @property
    def duration(self) -> float:
        return self.frames / self.sample_rate

    def mono(self) -> np.ndarray:
        """Mean across channels, shape ``(frames,)``."""
        return self.samples.mean(axis=0)


def load_audio(path: str | Path) -> AudioBuffer:
    """Read a WAV/FLAC/OGG file into an :class:`AudioBuffer`."""
    data, sample_rate = sf.read(str(path), dtype="float32", always_2d=True)
    return AudioBuffer(data.T, sample_rate)


def save_audio(buffer: AudioBuffer, path: str | Path) -> None:
    """Write an :class:`AudioBuffer` to disk, creating parent directories."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(destination), buffer.samples.T, buffer.sample_rate)
