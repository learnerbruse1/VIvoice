from __future__ import annotations

import numpy as np

from vivoice.core.effect import (
    Effect,
    EffectContext,
    register_effect,
    registered_effects,
    unregister_effect,
)
from vivoice.plugins import load_plugins


class _PluginEffect(Effect):
    effect_type = "plugin-demo"
    description = "Test plugin effect."

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        return samples


class _FakeEntryPoint:
    def __init__(self, effect_class: type[Effect]) -> None:
        self._effect_class = effect_class

    def load(self) -> object:
        # Real plugins register during module import; the entry point load is
        # the trigger for that import side effect.
        register_effect(self._effect_class)
        return self._effect_class


class _FakeEntryPoints:
    def __init__(self, mapping: dict) -> None:
        self._mapping = mapping

    def select(self, group: str) -> list:
        return self._mapping.get(group, [])


def test_load_plugins_registers_third_party_effect(monkeypatch) -> None:
    monkeypatch.setattr(
        "vivoice.plugins.metadata.entry_points",
        lambda: _FakeEntryPoints({"vivoice.effects": [_FakeEntryPoint(_PluginEffect)]}),
    )
    try:
        load_plugins()
        assert "plugin-demo" in registered_effects()
    finally:
        unregister_effect("plugin-demo")
