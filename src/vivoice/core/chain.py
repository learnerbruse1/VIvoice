"""Ordered effect pipeline and offline file rendering."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from vivoice.audio import AudioBuffer, load_audio, save_audio
from vivoice.core.effect import Effect, EffectContext, create_effect
from vivoice.core.errors import ChainError, EffectError

ProgressCallback = Callable[[float], None]


class Chain:
    """A named-at-the-preset-level, ordered sequence of effects."""

    def __init__(self, effects: Sequence[Effect]) -> None:
        if not effects:
            raise ChainError("A chain needs at least one effect.")
        self.effects = list(effects)

    def process(self, samples: np.ndarray, sample_rate: int) -> np.ndarray:
        """Run the chain over a whole ``(channels, frames)`` buffer."""
        return self._run(samples, sample_rate, progress=None)

    def render_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        """Read a file, run the chain, and write the result."""
        source = load_audio(input_path)
        rendered = self._run(source.samples, source.sample_rate, progress)
        save_audio(AudioBuffer(rendered, source.sample_rate), output_path)

    def _run(
        self,
        samples: np.ndarray,
        sample_rate: int,
        progress: ProgressCallback | None,
    ) -> np.ndarray:
        if samples.ndim != 2:
            raise ChainError("samples must have shape (channels, frames)")
        context = EffectContext(sample_rate=sample_rate, channels=samples.shape[0])
        output = np.asarray(samples, dtype=np.float32)
        total = len(self.effects)
        for index, effect in enumerate(self.effects):
            output = effect.process(output, context)
            if output.shape != samples.shape:
                raise ChainError(
                    f"Effect '{effect.effect_type}' changed the buffer shape from "
                    f"{samples.shape} to {output.shape}"
                )
            if progress is not None:
                progress((index + 1) / total)
        return np.asarray(output, dtype=np.float32)

    @classmethod
    def from_config(cls, config: Sequence[Mapping[str, Any]]) -> Chain:
        """Build a chain from preset ``chain`` entries."""
        effects: list[Effect] = []
        for index, entry in enumerate(config):
            if not isinstance(entry, dict):
                raise ChainError(f"chain[{index}] must be a mapping")
            effect_type = entry.get("type")
            if not isinstance(effect_type, str) or not effect_type:
                raise ChainError(f"chain[{index}] is missing a string 'type'")
            params = entry.get("params") or {}
            if not isinstance(params, dict):
                raise ChainError(f"chain[{index}] 'params' must be a mapping")
            try:
                effects.append(create_effect(effect_type, params))
            except EffectError as exc:
                raise ChainError(f"chain[{index}]: {exc}") from exc
        return cls(effects)
