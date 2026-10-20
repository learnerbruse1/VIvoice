from __future__ import annotations

import numpy as np
import pytest

from vivoice.audio import load_audio, save_audio
from vivoice.core import Chain, ChainError, Effect, EffectContext


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
