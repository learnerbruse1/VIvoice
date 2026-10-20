"""Audio core: effects, chains, and the shared error hierarchy."""

from vivoice.core.chain import Chain
from vivoice.core.effect import Effect, EffectContext, create_effect, registered_effects
from vivoice.core.errors import (
    Cancelled,
    ChainError,
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
    "Cancelled",
    "Chain",
    "ChainError",
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
