"""Preset: a named, validated chain of effects serialized as YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from vivoice.audio import DEFAULT_SAMPLE_RATE
from vivoice.core.chain import Chain
from vivoice.core.errors import PresetError


@dataclass(frozen=True)
class Preset:
    name: str
    chain_config: list[dict[str, Any]]
    description: str = ""
    sample_rate: int = DEFAULT_SAMPLE_RATE

    @classmethod
    def load(cls, path: str | Path) -> Preset:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise PresetError(f"Cannot read preset '{path}': {exc}") from exc
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise PresetError(f"Invalid YAML in '{path}': {exc}") from exc
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: Any) -> Preset:
        if not isinstance(data, dict):
            raise PresetError("A preset must be a YAML mapping")
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            raise PresetError("Preset 'name' must be a non-empty string")
        chain = data.get("chain")
        if not isinstance(chain, list) or not chain:
            raise PresetError("Preset 'chain' must be a non-empty list")
        sample_rate = data.get("sample_rate", DEFAULT_SAMPLE_RATE)
        if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate < 8000:
            raise PresetError("'sample_rate' must be an integer >= 8000")
        description = data.get("description", "")
        if not isinstance(description, str):
            raise PresetError("'description' must be a string")
        return cls(
            name=name.strip(),
            chain_config=chain,
            description=description,
            sample_rate=int(sample_rate),
        )

    def build_chain(self) -> Chain:
        """Validate and materialize the chain."""
        return Chain.from_config(self.chain_config)

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": self.name,
            "description": self.description,
            "sample_rate": self.sample_rate,
            "chain": self.chain_config,
        }
        destination.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
