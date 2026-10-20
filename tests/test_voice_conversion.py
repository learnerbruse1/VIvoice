from __future__ import annotations

import numpy as np
from scipy.signal import resample_poly

import vivoice.effects  # noqa: F401  (register built-in effects)
from vivoice.ai.adapter import VoiceConversionAdapter, register_adapter, unregister_adapter
from vivoice.core.effect import EffectContext, create_effect
from vivoice.models import ModelRegistry


class _FakeAdapter(VoiceConversionAdapter):
    engine = "fake"
    sample_rate = 40_000

    def convert(self, audio_mono, voice_model, params):
        assert voice_model.name == "alice"
        assert params["engine"] == "fake"
        return (audio_mono * 0.5).astype(np.float32)


def test_voice_conversion_pipeline_end_to_end(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    checkpoint = tmp_path / "voice.pth"
    checkpoint.write_bytes(b"checkpoint")
    ModelRegistry().add("alice", checkpoint)
    register_adapter(_FakeAdapter)
    try:
        sample_rate = 48_000
        time = np.arange(sample_rate, dtype=np.float32) / sample_rate
        sine = (0.2 * np.sin(2.0 * np.pi * 440.0 * time)).astype(np.float32)
        samples = np.stack([sine, sine * 0.5])

        effect = create_effect(
            "voice-conversion", {"model": "alice", "engine": "fake", "device": "cpu"}
        )
        output = effect.process(samples, EffectContext(sample_rate, 2))

        assert output.shape == samples.shape
        mono = samples.mean(axis=0).astype(np.float32)
        engine_audio = resample_poly(mono, up=40_000, down=48_000).astype(np.float32)
        converted = (engine_audio * 0.5).astype(np.float32)
        restored = resample_poly(converted, up=48_000, down=40_000).astype(np.float32)
        restored = restored[: samples.shape[1]]
        expected = np.tile(restored, (2, 1))
        assert np.allclose(output, expected, atol=1e-5)
    finally:
        unregister_adapter("fake")
