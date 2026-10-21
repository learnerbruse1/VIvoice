from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

from vivoice.ai.device import Device
from vivoice.ai.rvc.adapter import RVCAdapter
from vivoice.core import MissingDependencyError
from vivoice.models.model import VoiceModel


def _install_fake_infer(result: np.ndarray, sample_rate: int = 40_000) -> type:
    class FakeVC:
        last_instance: FakeVC | None = None

        def __init__(self) -> None:
            self.calls: dict = {}
            FakeVC.last_instance = self

        def get_vc(self, model_path: str, device: str | None = None) -> None:
            self.calls["model"] = model_path
            self.calls["device"] = device

        def vc_single(self, **kwargs) -> tuple[None, tuple[int, np.ndarray]]:
            self.calls.update(kwargs)
            return None, (sample_rate, result)

    modules = types.ModuleType("infer.modules.vc.modules")
    modules.VC = FakeVC
    vc = types.ModuleType("infer.modules.vc")
    vc.modules = modules
    infer_modules = types.ModuleType("infer.modules")
    infer_modules.vc = vc
    infer = types.ModuleType("infer")
    infer.modules = infer_modules
    sys.modules["infer"] = infer
    sys.modules["infer.modules"] = infer_modules
    sys.modules["infer.modules.vc"] = vc
    sys.modules["infer.modules.vc.modules"] = modules
    return FakeVC


def _model(tmp_path: Path, name: str = "alice") -> VoiceModel:
    directory = tmp_path / name
    return VoiceModel(
        name=name,
        directory=directory,
        checkpoint=directory / "model.pth",
        index=directory / "model.index",
        source="test",
    )


def test_native_rvc_adapter_wiring(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VIVOICE_RVC_DIR", str(tmp_path))
    monkeypatch.setitem(sys.modules, "torch", types.ModuleType("torch"))
    fake_class = _install_fake_infer(np.zeros(8_000, dtype=np.float32))
    try:
        adapter = RVCAdapter(Device.CPU)
        output = adapter.convert(
            np.zeros(4_000, dtype=np.float32),
            _model(tmp_path),
            {"f0_method": "crepe", "index_rate": 0.5},
        )
        assert output.shape == (8_000,)
        assert np.isfinite(output).all()
        instance = fake_class.last_instance
        assert instance is not None
        assert instance.calls["device"] == "cpu"
        assert instance.calls["model"].endswith("model.pth")
        assert instance.calls["f0_method"] == "crepe"
        assert instance.calls["index_rate"] == 0.5
        assert instance.calls["file_index"].endswith("model.index")
    finally:
        for key in list(sys.modules):
            if key.startswith("infer"):
                del sys.modules[key]


def test_native_adapter_requires_torch(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VIVOICE_RVC_DIR", str(tmp_path))
    monkeypatch.setitem(sys.modules, "torch", None)
    with pytest.raises(MissingDependencyError, match="PyTorch"):
        RVCAdapter(Device.CPU).convert(np.zeros(16, np.float32), _model(tmp_path), {})


def test_native_adapter_requires_vendor(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VIVOICE_RVC_DIR", str(tmp_path / "missing"))
    monkeypatch.setitem(sys.modules, "torch", types.ModuleType("torch"))
    with pytest.raises(MissingDependencyError, match="not vendored"):
        RVCAdapter(Device.CPU).convert(np.zeros(16, np.float32), _model(tmp_path), {})
