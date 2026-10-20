from __future__ import annotations

from pathlib import Path

import pytest

from vivoice.core import ChainError, PresetError
from vivoice.presets import Preset


def test_load_example_and_roundtrip(tmp_path, robot_preset) -> None:
    preset = Preset.load(robot_preset)
    assert preset.name == "robot"
    assert preset.build_chain().effects  # non-empty

    saved = tmp_path / "copy.yaml"
    preset.save(saved)
    reloaded = Preset.load(saved)
    assert reloaded.chain_config == preset.chain_config


def test_missing_name_is_rejected() -> None:
    with pytest.raises(PresetError, match="name"):
        Preset.from_mapping({"chain": [{"type": "gain"}]})


def test_empty_chain_is_rejected() -> None:
    with pytest.raises(PresetError, match="chain"):
        Preset.from_mapping({"name": "empty", "chain": []})


def test_unknown_effect_fails_validation() -> None:
    preset = Preset.from_mapping({"name": "bad", "chain": [{"type": "nope"}]})
    with pytest.raises(ChainError):
        preset.build_chain()


def test_bad_yaml_is_rejected(tmp_path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("name: [unclosed", encoding="utf-8")
    with pytest.raises(PresetError, match="YAML"):
        Preset.load(path)


def test_all_example_presets_load() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "presets"
    for path in sorted(root.glob("*.yaml")):
        preset = Preset.load(path)
        assert preset.build_chain().effects
