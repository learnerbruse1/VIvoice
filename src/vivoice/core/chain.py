"""Ordered effect pipeline and offline file rendering."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import soundfile as sf

from vivoice.audio import AudioBuffer, audio_info, load_audio, save_audio
from vivoice.core.effect import Effect, EffectContext, create_effect
from vivoice.core.errors import Cancelled, ChainError, EffectError

if TYPE_CHECKING:
    from vivoice.core.stream import StreamSession

ProgressCallback = Callable[[float], None]
ShouldCancel = Callable[[], bool]
DEFAULT_BLOCK_FRAMES = 4096


class Chain:
    """A named-at-the-preset-level, ordered sequence of effects."""

    def __init__(self, effects: Sequence[Effect]) -> None:
        if not effects:
            raise ChainError("A chain needs at least one effect.")
        self.effects = list(effects)

    def process(
        self,
        samples: np.ndarray,
        sample_rate: int,
        should_cancel: ShouldCancel | None = None,
    ) -> np.ndarray:
        """Run the chain over a whole ``(channels, frames)`` buffer."""
        return self._run(samples, sample_rate, progress=None, should_cancel=should_cancel)

    def render_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
        progress: ProgressCallback | None = None,
        should_cancel: ShouldCancel | None = None,
        block_frames: int = DEFAULT_BLOCK_FRAMES,
    ) -> None:
        """Read a file, run the chain, and write the result."""
        if all(effect.block_process for effect in self.effects):
            self._render_chunked(
                input_path, output_path, progress, should_cancel, block_frames
            )
            return
        source = load_audio(input_path)
        rendered = self._run(
            source.samples,
            source.sample_rate,
            progress,
            should_cancel,
        )
        save_audio(AudioBuffer(rendered, source.sample_rate), output_path)

    def _render_chunked(
        self,
        input_path: str | Path,
        output_path: str | Path,
        progress: ProgressCallback | None,
        should_cancel: ShouldCancel | None,
        block_frames: int,
    ) -> None:
        """Render with bounded memory: one block in flight at a time."""
        if block_frames <= 0:
            raise ChainError("block_frames must be positive")
        frames, _channels = audio_info(input_path)
        for effect in self.effects:
            effect.reset()
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        opened = False
        try:
            with sf.SoundFile(str(input_path)) as source, sf.SoundFile(
                str(destination),
                mode="w",
                samplerate=source.samplerate,
                channels=source.channels,
            ) as writer:
                opened = True
                processed = 0
                while True:
                    data = source.read(block_frames, dtype="float32", always_2d=True)
                    if len(data) == 0:
                        break
                    if should_cancel is not None and should_cancel():
                        raise Cancelled("Operation cancelled")
                    block = np.ascontiguousarray(data.T)
                    context = EffectContext(source.samplerate, block.shape[0])
                    for effect in self.effects:
                        block = effect.process(block, context)
                        if block.shape != (data.shape[1], data.shape[0]):
                            raise ChainError(
                                f"Effect '{effect.effect_type}' changed the block shape "
                                f"from {(data.shape[1], data.shape[0])} to {block.shape}"
                            )
                    writer.write(np.ascontiguousarray(block.T))
                    processed += block.shape[1]
                    if progress is not None:
                        progress(min(1.0, processed / max(1, frames)))
        except BaseException:
            if opened:
                destination.unlink(missing_ok=True)
            raise

    def open_stream(self, sample_rate: int) -> StreamSession:
        """Open a block-wise processing session for real-time use."""
        from vivoice.core.stream import StreamSession

        return StreamSession(self, sample_rate)

    def _run(
        self,
        samples: np.ndarray,
        sample_rate: int,
        progress: ProgressCallback | None,
        should_cancel: ShouldCancel | None,
    ) -> np.ndarray:
        if samples.ndim != 2:
            raise ChainError("samples must have shape (channels, frames)")
        for effect in self.effects:
            effect.reset()
        context = EffectContext(sample_rate=sample_rate, channels=samples.shape[0])
        output = np.asarray(samples, dtype=np.float32)
        total = len(self.effects)
        for index, effect in enumerate(self.effects):
            if should_cancel is not None and should_cancel():
                raise Cancelled("Operation cancelled")
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
