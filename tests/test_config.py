from __future__ import annotations

import pytest

from vivoice.config import UserConfig
from vivoice.core import ConfigError


@pytest.fixture
def config(tmp_path, monkeypatch) -> UserConfig:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    return UserConfig()


def test_config_defaults_and_roundtrip(config: UserConfig) -> None:
    assert config.get("sample_rate") == 48_000
    assert config.get("device") == "auto"
    config.set("sample_rate", 44_100)
    config.set("input_device", "My Microphone")
    reloaded = UserConfig().load()
    assert reloaded["sample_rate"] == 44_100
    assert reloaded["input_device"] == "My Microphone"


def test_config_rejects_unknown_key(config: UserConfig) -> None:
    with pytest.raises(ConfigError, match="Unknown config key"):
        config.set("bogus", 1)


def test_config_rejects_invalid_value(config: UserConfig) -> None:
    with pytest.raises(ConfigError, match="sample_rate"):
        config.set("sample_rate", 100)


def test_config_rejects_invalid_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    config = UserConfig()
    config.path.write_text("name: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match="config"):
        config.load()
