"""Audio core: effects, chains, and the shared error hierarchy."""

from vivoice.core.chain import Chain
from vivoice.core.effect import Effect, EffectContext, create_effect, registered_effects
from vivoice.core.errors import (
    AudioIOError,
    Cancelled,
    ChainError,
    ConfigError,
    ConversionError,
    DeviceError,
    EffectError,
    MissingDependencyError,
    ModelError,
    ModelNotFoundError,
    PresetError,
    UnsupportedFeatureError,
    VivoiceError,
)
from vivoice.core.stream import StreamSession

__all__ = [
    "AudioIOError",
    "Cancelled",
    "Chain",
    "ChainError",
    "ConfigError",
    "ConversionError",
    "DeviceError",
    "Effect",
    "EffectContext",
    "EffectError",
    "MissingDependencyError",
    "ModelError",
    "ModelNotFoundError",
    "PresetError",
    "StreamSession",
    "UnsupportedFeatureError",
    "VivoiceError",
    "create_effect",
    "registered_effects",
]
