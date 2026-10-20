from __future__ import annotations

import numpy as np
import pytest

import vivoice.effects  # noqa: F401  (register built-in effects)
from vivoice.audio import load_audio, save_audio
from vivoice.core import Chain, ChainError, Effect, EffectContext
from vivoice.core.effect import create_effect
from vivoice.core.errors import Cancelled


def test_effects_run_in_order(sine_440: np.ndarray) -> None:
    from vivoice.effects.gain import GainEffect

    chain = Chain([GainEffect({"gain_db": 6.0}), GainEffect({"gain_db": -6.0})])
    output = chain.process(sine_440, 48_000)
    assert np.allclose(output, sine_440, atol=1e-6)


def test_unknown_effect_type_is_rejected() -> None:
    with pytest.raises(ChainError, match="Unknown effect type 'does-not-exist'"):
        Chain.from_config([{"type": "does-not-exist", "params": {}}])


def test_shape_changes_are_rejected(sine_440: np.ndarray) -> None:
    class _BrokenEffect(Effect):
        effect_type = "broken"

        def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
            return samples[:, :16]

    chain = Chain([_BrokenEffect()])
    with pytest.raises(ChainError, match="changed the buffer shape"):
        chain.process(sine_440, 48_000)


def test_render_file(tmp_path, robot_preset, sine_440: np.ndarray) -> None:
    from vivoice.presets import Preset

    source = tmp_path / "in.wav"
    destination = tmp_path / "out.wav"
    from vivoice.audio import AudioBuffer

    save_audio(AudioBuffer(sine_440, 48_000), source)
    Preset.load(robot_preset).build_chain().render_file(source, destination)

    output = load_audio(destination)
    assert output.samples.shape == sine_440.shape
    assert not np.allclose(output.samples, sine_440)


def test_cancellation_stops_pipeline(sine_440: np.ndarray) -> None:
    from vivoice.effects.gain import GainEffect

    chain = Chain([GainEffect(), GainEffect(), GainEffect()])
    with pytest.raises(Cancelled):
        chain.process(sine_440, 48_000, should_cancel=lambda: True)


def test_chunked_render_matches_whole_buffer(tmp_path, sine_440: np.ndarray) -> None:
    from vivoice.audio import AudioBuffer

    source = tmp_path / "in.wav"
    chunked_path = tmp_path / "chunked.wav"
    whole_path = tmp_path / "whole.wav"
    save_audio(AudioBuffer(sine_440, 48_000), source)

    config = [
        {"type": "gain", "params": {"gain_db": 2.0}},
        {"type": "echo", "params": {"delay_seconds": 0.08, "feedback": 0.3, "mix": 0.5}},
        {"type": "eq", "params": {"mid_gain_db": 3.0}},
        {"type": "reverb", "params": {"room_size": 0.3, "mix": 0.2}},
    ]
    fractions: list[float] = []
    Chain.from_config(config).render_file(
        source, chunked_path, progress=fractions.append, block_frames=1024
    )
    source_buffer = load_audio(source)
    whole = Chain.from_config(config).process(source_buffer.samples, 48_000)
    save_audio(AudioBuffer(whole, 48_000), whole_path)

    chunked = load_audio(chunked_path)
    whole_from_file = load_audio(whole_path)
    assert chunked.samples.shape == whole_from_file.samples.shape
    assert np.array_equal(chunked.samples, whole_from_file.samples)
    assert fractions == sorted(fractions)
    assert fractions[-1] == 1.0
    assert len(fractions) > 4


def test_chunked_render_cancellation_cleans_output(tmp_path, sine_440: np.ndarray) -> None:
    from vivoice.audio import AudioBuffer

    source = tmp_path / "in.wav"
    destination = tmp_path / "out.wav"
    save_audio(AudioBuffer(sine_440, 48_000), source)
    chain = Chain.from_config(
        [{"type": "gain"}, {"type": "echo", "params": {"delay_seconds": 0.1}}]
    )
    with pytest.raises(Cancelled):
        chain.render_file(source, destination, should_cancel=lambda: True, block_frames=512)
    assert not destination.exists()


def test_whole_buffer_cancellation_writes_nothing(tmp_path, sine_440: np.ndarray) -> None:
    from vivoice.audio import AudioBuffer

    source = tmp_path / "in.wav"
    destination = tmp_path / "out.wav"
    save_audio(AudioBuffer(sine_440, 48_000), source)
    chain = Chain([create_effect("pitch", {"semitones": 1.0})])
    with pytest.raises(Cancelled):
        chain.render_file(source, destination, should_cancel=lambda: True)
    assert not destination.exists()
