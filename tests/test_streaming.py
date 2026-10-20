from __future__ import annotations

import numpy as np
import pytest

from vivoice.core import Chain, ChainError, EffectContext, create_effect

STREAMING_EFFECTS = [
    ("gain", {"gain_db": 3.0}),
    ("robot", {"frequency": 120.0, "mix": 0.8}),
    ("echo", {"delay_seconds": 0.1, "feedback": 0.4, "mix": 0.6}),
    ("eq", {"low_gain_db": 3.0, "mid_gain_db": -2.0, "high_gain_db": 2.0}),
    ("noise-gate", {}),
    ("reverb", {"room_size": 0.4, "damping": 0.5, "mix": 0.2}),
]


def _signal(sample_rate: int = 48_000, seconds: int = 1) -> np.ndarray:
    time = np.arange(sample_rate * seconds, dtype=np.float32) / sample_rate
    signal = 0.2 * np.sin(2.0 * np.pi * 330.0 * time) + 0.05 * np.sin(2.0 * np.pi * 997.0 * time)
    return np.stack([signal, signal * 0.7])


@pytest.mark.parametrize("effect_type,params", STREAMING_EFFECTS)
def test_streaming_matches_offline(effect_type: str, params: dict) -> None:
    sample_rate = 48_000
    signal = _signal()
    offline = create_effect(effect_type, params).process(
        np.array(signal, copy=True),
        EffectContext(sample_rate, signal.shape[0]),
    )

    session = Chain([create_effect(effect_type, params)]).open_stream(sample_rate)
    blocks = [
        session.process_block(signal[:, start : start + 333])
        for start in range(0, signal.shape[1], 333)
    ]
    streamed = np.concatenate(blocks, axis=1)

    assert streamed.shape == offline.shape
    assert np.allclose(streamed, offline, atol=1e-5, rtol=1e-4)


def test_non_streaming_effects_are_rejected() -> None:
    chain = Chain([create_effect("pitch", {"semitones": 3.0})])
    with pytest.raises(ChainError, match="not available for streaming"):
        chain.open_stream(48_000)
