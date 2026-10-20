"""Schroeder/Freeverb-style reverb for voice presets."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np

from vivoice.core.effect import Effect, EffectContext, register_effect
from vivoice.core.errors import EffectError

_COMB_DELAYS = (1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116)
_ALLPASS_DELAYS = (225, 556, 441, 341)


@register_effect
class ReverbEffect(Effect):
    effect_type: ClassVar[str] = "reverb"
    description: ClassVar[str] = "Room reverb from comb and all-pass delays."
    streaming: ClassVar[bool] = True
    block_process: ClassVar[bool] = True
    default_params: ClassVar[Mapping[str, Any]] = {
        "room_size": 0.5,
        "damping": 0.5,
        "mix": 0.25,
    }
    param_constraints: ClassVar[Mapping[str, Mapping[str, Any]]] = {
        "room_size": {"minimum": 0.01, "maximum": 0.99},
        "damping": {"minimum": 0.0, "maximum": 1.0},
        "mix": {"minimum": 0.0, "maximum": 1.0},
    }

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        super().__init__(params)
        if not 0.0 < float(self.params["room_size"]) < 1.0:
            raise EffectError("'room_size' must be in (0, 1)")
        if not 0.0 <= float(self.params["damping"]) <= 1.0:
            raise EffectError("'damping' must be in [0, 1]")
        if not 0.0 <= float(self.params["mix"]) <= 1.0:
            raise EffectError("'mix' must be in [0, 1]")
        self._channels = 0
        self._comb_buffers: list[list[np.ndarray]] = []
        self._comb_indexes: list[list[int]] = []
        self._filter_stores: np.ndarray | None = None
        self._allpass_buffers: list[list[np.ndarray]] = []
        self._allpass_indexes: list[list[int]] = []

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        channels = samples.shape[0]
        if self._channels != channels:
            self._allocate(channels)
        filter_stores = self._filter_stores
        assert filter_stores is not None

        feedback = 0.7 + 0.28 * float(self.params["room_size"])
        damp_1 = float(self.params["damping"])
        damp_2 = 1.0 - damp_1
        mix = float(self.params["mix"])
        output = np.empty_like(samples)

        for frame in range(samples.shape[1]):
            for channel in range(channels):
                wet = 0.0
                for index in range(len(_COMB_DELAYS)):
                    position = self._comb_indexes[index][channel]
                    buffer = self._comb_buffers[index][channel]
                    delayed = float(buffer[position])
                    if abs(delayed) < 1e-9:
                        delayed = 0.0
                    filtered = delayed * damp_2 + float(filter_stores[index, channel]) * damp_1
                    filter_stores[index, channel] = filtered
                    buffer[position] = samples[channel, frame] + filtered * feedback
                    self._comb_indexes[index][channel] = (position + 1) % _COMB_DELAYS[index]
                    wet += delayed
                wet *= 0.25

                for index in range(len(_ALLPASS_DELAYS)):
                    position = self._allpass_indexes[index][channel]
                    buffer = self._allpass_buffers[index][channel]
                    delayed = float(buffer[position])
                    if abs(delayed) < 1e-9:
                        delayed = 0.0
                    buffer[position] = wet + delayed * 0.5
                    wet = -wet + delayed
                    self._allpass_indexes[index][channel] = (
                        position + 1
                    ) % _ALLPASS_DELAYS[index]

                output[channel, frame] = samples[channel, frame] * (1.0 - mix) + wet * mix
        return output

    def reset(self) -> None:
        self._channels = 0
        self._comb_buffers = []
        self._comb_indexes = []
        self._filter_stores = None
        self._allpass_buffers = []
        self._allpass_indexes = []

    def _allocate(self, channels: int) -> None:
        self._channels = channels
        self._comb_buffers = [
            [np.zeros(delay, dtype=np.float32) for _ in range(channels)]
            for delay in _COMB_DELAYS
        ]
        self._comb_indexes = [[0] * channels for _ in _COMB_DELAYS]
        self._filter_stores = np.zeros((len(_COMB_DELAYS), channels), dtype=np.float32)
        self._allpass_buffers = [
            [np.zeros(delay, dtype=np.float32) for _ in range(channels)]
            for delay in _ALLPASS_DELAYS
        ]
        self._allpass_indexes = [[0] * channels for _ in _ALLPASS_DELAYS]
