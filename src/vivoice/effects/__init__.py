"""Built-in effects.

Importing this package registers every built-in effect. Third-party effects
will eventually register the same way through Python entry points.
"""

from vivoice.effects import (
    echo,
    eq,
    formant,
    gain,
    gate,
    pitch,
    reverb,
    robot,
    voice_conversion,
)

__all__ = [
    "echo",
    "eq",
    "formant",
    "gain",
    "gate",
    "pitch",
    "reverb",
    "robot",
    "voice_conversion",
]
