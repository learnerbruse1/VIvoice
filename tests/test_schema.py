from __future__ import annotations

import vivoice.effects  # noqa: F401  (register built-in effects)
from vivoice.core.effect import get_effect_class


def test_gain_schema_exposes_defaults_and_bounds() -> None:
    schema = get_effect_class("gain").params_schema()
    assert schema["params"]["gain_db"]["default"] == 0.0
    assert schema["params"]["gain_db"]["minimum"] == -48.0
    assert schema["block_process"] is True


def test_pitch_schema_flags_streaming_algorithm() -> None:
    schema = get_effect_class("pitch").params_schema()
    assert schema["streaming"] is True
    assert schema["block_process"] is False
    assert schema["params"]["semitones"]["minimum"] == -24.0


def test_voice_conversion_schema_marks_required_model() -> None:
    schema = get_effect_class("voice-conversion").params_schema()
    assert schema["params"]["model"]["required"] is True
    assert "rvc" in schema["params"]["engine"]["enum"]
