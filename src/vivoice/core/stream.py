"""Block-wise processing for real-time streaming.

Only effects that declare ``streaming = True`` may run here: they must keep all
state on the instance and support ``reset()``. Whole-signal effects such as the
phase-vocoder pitch shift are rejected with a clear error.
"""

from __future__ import annotations

import numpy as np

from vivoice.core.chain import Chain
from vivoice.core.effect import EffectContext
from vivoice.core.errors import ChainError


class StreamSession:
    """A stateful, block-oriented view over a :class:`Chain`."""

    def __init__(self, chain: Chain, sample_rate: int) -> None:
        blocked = [effect.effect_type for effect in chain.effects if not effect.streaming]
        if blocked:
            raise ChainError(
                "Effects not available for streaming: "
                f"{', '.join(blocked)}. Remove them or process the file offline."
            )
        if sample_rate <= 0:
            raise ChainError("sample_rate must be positive")
        self._effects = list(chain.effects)
        self._sample_rate = int(sample_rate)
        for effect in self._effects:
            effect.reset()

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def process_block(self, samples: np.ndarray) -> np.ndarray:
        """Process one ``(channels, frames)`` float32 block."""
        if samples.ndim != 2:
            raise ChainError("samples must have shape (channels, frames)")
        context = EffectContext(sample_rate=self._sample_rate, channels=samples.shape[0])
        output = np.asarray(samples, dtype=np.float32)
        for effect in self._effects:
            output = effect.process(output, context)
            if output.shape != samples.shape:
                raise ChainError(
                    f"Effect '{effect.effect_type}' changed the buffer shape from "
                    f"{samples.shape} to {output.shape}"
                )
        return np.asarray(output, dtype=np.float32)
