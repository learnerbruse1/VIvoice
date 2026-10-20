"""Shared exception hierarchy.

Front-ends catch :class:`VivoiceError` for expected, user-facing failures and
let unexpected exceptions surface as crashes with a traceback.
"""


class VivoiceError(Exception):
    """Base class for all expected VIvoice failures."""


class EffectError(VivoiceError):
    """An effect was misconfigured or failed to process audio."""


class ChainError(VivoiceError):
    """A chain definition or pipeline execution failed."""


class PresetError(VivoiceError):
    """A preset file is missing, unreadable, or invalid."""


class ModelError(VivoiceError):
    """A voice model operation failed."""


class ModelNotFoundError(ModelError):
    """A requested voice model is not in the local registry."""


class DeviceError(VivoiceError):
    """The requested compute device is unavailable or unknown."""


class MissingDependencyError(VivoiceError):
    """An optional dependency (engine) is not installed."""


class UnsupportedFeatureError(VivoiceError):
    """A known-but-not-yet-implemented feature was requested."""
