from __future__ import annotations

import pytest

from vivoice.ai.device import Device, describe_device, resolve_device
from vivoice.core import DeviceError


class _FakeTorch:
    class _Cuda:
        def __init__(self, available: bool) -> None:
            self._available = available

        def is_available(self) -> bool:
            return self._available

    class _Mps:
        def __init__(self, available: bool) -> None:
            self._available = available

        def is_available(self) -> bool:
            return self._available

    class _Backends:
        def __init__(self, mps_available: bool | None) -> None:
            self.mps = _FakeTorch._Mps(mps_available) if mps_available is not None else None

    def __init__(self, cuda: bool = False, mps: bool | None = None) -> None:
        self.cuda = _FakeTorch._Cuda(cuda)
        self.backends = _FakeTorch._Backends(mps)


def test_auto_prefers_cuda() -> None:
    assert resolve_device("auto", torch_module=_FakeTorch(cuda=True)) == Device.CUDA


def test_auto_falls_back_to_mps() -> None:
    assert resolve_device("auto", torch_module=_FakeTorch(cuda=False, mps=True)) == Device.MPS


def test_auto_falls_back_to_cpu() -> None:
    assert resolve_device("auto", torch_module=_FakeTorch()) == Device.CPU


def test_explicit_cpu_always_works() -> None:
    assert resolve_device("cpu", torch_module=None) == Device.CPU


def test_explicit_cuda_without_gpu_is_rejected() -> None:
    with pytest.raises(DeviceError, match="not available"):
        resolve_device("cuda", torch_module=_FakeTorch(cuda=False))


def test_unknown_device_is_rejected() -> None:
    with pytest.raises(DeviceError, match="Unknown device"):
        resolve_device("tpu", torch_module=None)


def test_describe_device_reports_fallback() -> None:
    text = describe_device("auto", torch_module=_FakeTorch())
    assert "CPU" in text
