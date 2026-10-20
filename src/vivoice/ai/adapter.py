"""The voice-conversion adapter boundary.

AI engines never touch the audio core. Adapters convert mono float32 audio at
their engine-native sample rate (RVC: 40 kHz); the ``voice-conversion`` effect
handles resampling and channel layout.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np

from vivoice.ai.device import Device
from vivoice.core.errors import MissingDependencyError
from vivoice.models.model import VoiceModel


class VoiceConversionAdapter(ABC):
    """Base class for voice-conversion engines."""

    engine: ClassVar[str]
    sample_rate: ClassVar[int]

    def __init__(self, device: Device) -> None:
        self.device = device

    @abstractmethod
    def convert(
        self,
        audio_mono: np.ndarray,
        voice_model: VoiceModel,
        params: Mapping[str, Any],
    ) -> np.ndarray:
        """Convert mono float32 audio at :attr:`sample_rate`."""


_ADAPTERS: dict[str, type[VoiceConversionAdapter]] = {}


def register_adapter(cls: type[VoiceConversionAdapter]) -> type[VoiceConversionAdapter]:
    _ADAPTERS[cls.engine] = cls
    return cls


def get_adapter(engine: str, device: Device) -> VoiceConversionAdapter:
    try:
        adapter_class = _ADAPTERS[engine]
    except KeyError:
        available = ", ".join(sorted(_ADAPTERS)) or "(none)"
        raise MissingDependencyError(
            f"Unknown voice-conversion engine '{engine}'. Available: {available}"
        ) from None
    return adapter_class(device)


def unregister_adapter(engine: str) -> None:
    """Remove an adapter from the registry (used by tests and plugin reloads)."""
    _ADAPTERS.pop(engine, None)
