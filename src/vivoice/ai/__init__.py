"""AI layer: device detection and the voice-conversion adapter boundary."""

from vivoice.ai import rvc  # noqa: F401  (registers the RVC adapter)
from vivoice.ai.adapter import VoiceConversionAdapter, get_adapter
from vivoice.ai.device import Device, describe_device, resolve_device

__all__ = [
    "Device",
    "VoiceConversionAdapter",
    "describe_device",
    "get_adapter",
    "resolve_device",
]
