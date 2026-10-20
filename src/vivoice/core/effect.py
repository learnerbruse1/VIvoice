"""Effect base class and registry.

Effects are deterministic transforms over float32 buffers of shape
``(channels, frames)``. The registry maps preset ``type`` strings to classes,
which keeps YAML presets decoupled from Python class names.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np

from vivoice.core.errors import EffectError


@dataclass(frozen=True)
class EffectContext:
    """Per-render information passed to every effect."""

    sample_rate: int
    channels: int


class Effect(ABC):
    """Base class for all effects."""

    effect_type: ClassVar[str]
    description: ClassVar[str] = ""
    streaming: ClassVar[bool] = False
    block_process: ClassVar[bool] = False
    required_params: ClassVar[Sequence[str]] = ()
    default_params: ClassVar[Mapping[str, Any]] = {}
    param_constraints: ClassVar[Mapping[str, Mapping[str, Any]]] = {}

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        merged: dict[str, Any] = {**self.default_params, **(params or {})}
        missing = [key for key in self.required_params if key not in merged]
        if missing:
            raise EffectError(
                f"Effect '{self.effect_type}' is missing required params: {', '.join(missing)}"
            )
        self.params = merged

    @abstractmethod
    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        """Transform ``samples`` without mutating it."""

    def to_config(self) -> dict[str, Any]:
        """Serializable form used by presets."""
        return {"type": self.effect_type, "params": dict(self.params)}

    def reset(self) -> None:
        """Clear per-render state.

        Stateful effects override this. The offline pipeline calls it before
        every render so results stay deterministic; streaming sessions call it
        once when the session opens.
        """
        return None

    def process_stream(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        """Process one block in the real-time path.

        The default delegates to :meth:`process`. Effects with a dedicated
        streaming algorithm (e.g. the pitch shifter) override it.
        """
        return self.process(samples, context)

    @classmethod
    def params_schema(cls) -> dict[str, Any]:
        """JSON-serializable description of the effect's parameters."""
        names = dict.fromkeys((*cls.default_params, *cls.required_params))
        params: dict[str, Any] = {}
        for name in names:
            entry: dict[str, Any] = {
                "required": name in cls.required_params,
                "default": cls.default_params.get(name),
            }
            entry.update(cls.param_constraints.get(name, {}))
            params[name] = entry
        return {
            "type": cls.effect_type,
            "description": cls.description,
            "streaming": cls.streaming,
            "block_process": cls.block_process,
            "params": params,
        }


_REGISTRY: dict[str, type[Effect]] = {}


def register_effect(cls: type[Effect]) -> type[Effect]:
    """Class decorator that registers an effect under its ``effect_type``."""
    _REGISTRY[cls.effect_type] = cls
    return cls


def get_effect_class(effect_type: str) -> type[Effect]:
    try:
        return _REGISTRY[effect_type]
    except KeyError:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise EffectError(f"Unknown effect type '{effect_type}'. Available: {available}") from None


def create_effect(effect_type: str, params: Mapping[str, Any] | None = None) -> Effect:
    """Instantiate a registered effect from a type string and parameters."""
    return get_effect_class(effect_type)(params)


def registered_effects() -> dict[str, type[Effect]]:
    """Snapshot of the registry, keyed by effect type."""
    return dict(_REGISTRY)


def unregister_effect(effect_type: str) -> None:
    """Remove an effect from the registry (used by tests and plugin reloads)."""
    _REGISTRY.pop(effect_type, None)
