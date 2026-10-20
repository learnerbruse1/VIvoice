"""User configuration stored under ``~/.vivoice/config.yaml``."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from vivoice.core.errors import ConfigError
from vivoice.paths import data_home

DEFAULT_CONFIG: dict[str, Any] = {
    "device": "auto",
    "sample_rate": 48_000,
    "block_size": 0,
    "input_device": None,
    "output_device": None,
    "log_level": "INFO",
}

_COMPUTE_DEVICES = {"auto", "cpu", "cuda", "mps"}
_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class UserConfig:
    """Small, validated, atomically-written YAML configuration."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or data_home() / "config.yaml"

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return dict(DEFAULT_CONFIG)
        try:
            data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigError(f"Cannot read config '{self.path}': {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"Config '{self.path}' must be a YAML mapping")
        merged = {**DEFAULT_CONFIG, **data}
        self._validate(merged)
        return merged

    def get(self, key: str) -> Any:
        _ensure_key(key)
        return self.load().get(key)

    def set(self, key: str, value: Any) -> None:
        _ensure_key(key)
        merged = self.load()
        merged[key] = value
        self._validate(merged)
        self.save(merged)

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".yaml.tmp")
        temporary.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    @staticmethod
    def _validate(data: dict[str, Any]) -> None:
        device = data.get("device")
        if device not in _COMPUTE_DEVICES:
            raise ConfigError(f"'device' must be one of {sorted(_COMPUTE_DEVICES)}")
        sample_rate = data.get("sample_rate")
        if (
            isinstance(sample_rate, bool)
            or not isinstance(sample_rate, int)
            or not 8000 <= sample_rate <= 384_000
        ):
            raise ConfigError("'sample_rate' must be an integer in [8000, 384000]")
        block_size = data.get("block_size")
        if isinstance(block_size, bool) or not isinstance(block_size, int) or block_size < 0:
            raise ConfigError("'block_size' must be a non-negative integer (0 = auto)")
        for key in ("input_device", "output_device"):
            value = data.get(key)
            if value is not None and not isinstance(value, (str, int)):
                raise ConfigError(f"'{key}' must be a device name, index, or null")
        if data.get("log_level") not in _LOG_LEVELS:
            raise ConfigError(f"'log_level' must be one of {sorted(_LOG_LEVELS)}")


def _ensure_key(key: str) -> None:
    if key not in DEFAULT_CONFIG:
        available = ", ".join(sorted(DEFAULT_CONFIG))
        raise ConfigError(f"Unknown config key '{key}'. Available: {available}")


def load_user_config() -> dict[str, Any]:
    """Load the user config, falling back to defaults when unreadable."""
    try:
        return UserConfig().load()
    except ConfigError:
        return dict(DEFAULT_CONFIG)
