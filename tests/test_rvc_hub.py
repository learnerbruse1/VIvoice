from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

from vivoice.ai.device import Device
from vivoice.ai.rvc.hub import RvcHubAdapter
from vivoice.core import MissingDependencyError
from vivoice.models.model import VoiceModel


def _install_fake_pipeline(module: types.ModuleType) -> dict:
    class FakeRVCPipeline:
        last_instance: FakeRVCPipeline | None = None

        def __init__(self) -> None:
            FakeRVCPipeline.last_instance = self

        @classmethod
        def from_pretrained(cls, directory, **kwargs) -> FakeRVCPipeline:
            instance = cls()
            instance.directory = directory
            instance.kwargs = kwargs
            return instance

        def convert_file(self, source: Path, output: Path, **kwargs) -> None:
            self.source = source
            self.output = output
            self.kwargs.update(kwargs)
            import soundfile as sf

            data, sample_rate = sf.read(str(source), dtype="float32")
            sf.write(str(output), data * 0.5, 40_000)

    module.RVCPipeline = FakeRVCPipeline
    sys.modules["huggingface_hub_rvc"] = module
    return {}


def test_rvc_hub_adapter_wiring(tmp_path, monkeypatch) -> None:
    module = types.ModuleType("huggingface_hub_rvc")
    monkeypatch.setitem(sys.modules, "huggingface_hub_rvc", module)
    _install_fake_pipeline(module)
    directory = tmp_path / "alice"
    model = VoiceModel("alice", directory, directory / "model.pth", None, "test")

    adapter = RvcHubAdapter(Device.CPU)
    output = adapter.convert(
        np.zeros(4_000, dtype=np.float32),
        model,
        {"f0_method": "crepe", "index_rate": 0.5},
    )
    assert output.shape == (4_000,)
    pipeline = module.RVCPipeline.last_instance
    assert pipeline is not None
    assert pipeline.kwargs["device"] == "cpu"
    assert pipeline.kwargs["audio_mode"] == "vocal_only"
    assert pipeline.kwargs["f0_method"] == "crepe"
    assert pipeline.kwargs["retrieval_strength"] == 0.5
    assert pipeline.kwargs["output_sample_rate"] == 40_000


def test_rvc_hub_adapter_requires_package(tmp_path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "huggingface_hub_rvc", None)
    model = VoiceModel("alice", tmp_path, tmp_path / "model.pth", None, "test")
    with pytest.raises(MissingDependencyError, match="huggingface-hub-rvc"):
        RvcHubAdapter(Device.CPU).convert(np.zeros(16, np.float32), model, {})
