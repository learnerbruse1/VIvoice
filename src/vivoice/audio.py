"""Audio buffer conventions and file I/O.

VIvoice processes float32 samples shaped ``(channels, frames)`` at 48 kHz by
default. The AI layer converts to engine-native rates (e.g. RVC's 40 kHz) at
the adapter boundary.
"""

from __future__ import annotations

from collections.abc import Iterator
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
    from vivoice.core.errors import AudioIOError

    try:
        data, sample_rate = sf.read(str(path), dtype="float32", always_2d=True)
    except (OSError, sf.LibsndfileError) as exc:
        raise AudioIOError(f"Cannot read audio file '{path}': {exc}") from exc
    return AudioBuffer(data.T, sample_rate)


def save_audio(buffer: AudioBuffer, path: str | Path) -> None:
    """Write an :class:`AudioBuffer` to disk, creating parent directories."""
    from vivoice.core.errors import AudioIOError

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        sf.write(str(destination), buffer.samples.T, buffer.sample_rate)
    except (OSError, sf.LibsndfileError) as exc:
        raise AudioIOError(f"Cannot write audio file '{destination}': {exc}") from exc


def audio_info(path: str | Path) -> tuple[int, int]:
    """Return ``(frames, channels)`` for an audio file."""
    from vivoice.core.errors import AudioIOError

    try:
        info = sf.info(str(path))
        return int(info.frames), int(info.channels)
    except (OSError, sf.LibsndfileError) as exc:
        raise AudioIOError(f"Cannot inspect audio file '{path}': {exc}") from exc


def iter_blocks(path: str | Path, block_frames: int) -> Iterator[np.ndarray]:
    """Yield contiguous ``(channels, frames)`` float32 blocks of a file."""
    from vivoice.core.errors import AudioIOError

    if block_frames <= 0:
        raise ValueError("block_frames must be positive")
    try:
        with sf.SoundFile(str(path)) as source:
            while True:
                data = source.read(block_frames, dtype="float32", always_2d=True)
                if len(data) == 0:
                    return
                yield np.ascontiguousarray(data.T)
    except (OSError, sf.LibsndfileError) as exc:
        raise AudioIOError(f"Cannot read audio file '{path}': {exc}") from exc
