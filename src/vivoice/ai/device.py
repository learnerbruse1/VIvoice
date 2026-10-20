"""Compute-device detection: auto → CUDA → MPS → CPU."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

from vivoice.core.errors import DeviceError

logger = logging.getLogger(__name__)


class Device(StrEnum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"


def _import_torch(torch_module: Any | None) -> Any | None:
    if torch_module is not None:
        return torch_module
    try:
        import torch

        return torch
    except ImportError:
        logger.debug("PyTorch is not installed; AI engines are unavailable")
        return None


def resolve_device(request: str = "auto", torch_module: Any | None = None) -> Device:
    """Resolve a device request, validating availability."""
    normalized = (request or "auto").strip().lower()
    if normalized not in {"auto", "cpu", "cuda", "mps"}:
        raise DeviceError(f"Unknown device '{request}'. Use auto, cpu, cuda, or mps.")

    torch = _import_torch(torch_module)
    if normalized == "cpu":
        return Device.CPU
    if normalized in {"cuda", "mps"}:
        if torch is None:
            raise DeviceError(
                f"Device '{normalized}' requires PyTorch. "
                "Install the 'ai' extra: uv sync --extra ai"
            )
        available = (
            torch.cuda.is_available()
            if normalized == "cuda"
            else _mps_available(torch)
        )
        if not available:
            raise DeviceError(f"Device '{normalized}' is not available on this machine")
        return Device.CUDA if normalized == "cuda" else Device.MPS

    if torch is not None:
        if torch.cuda.is_available():
            return Device.CUDA
        if _mps_available(torch):
            return Device.MPS
    return Device.CPU


def describe_device(request: str = "auto", torch_module: Any | None = None) -> str:
    """Human-readable summary for the GUI status bar and ``vivoice devices``."""
    torch = _import_torch(torch_module)
    device = resolve_device(request, torch_module=torch)
    if device == Device.CUDA:
        return "CUDA (NVIDIA GPU detected and selected)"
    if device == Device.MPS:
        return "MPS (Apple Silicon GPU detected and selected)"
    if torch is None:
        return "CPU (PyTorch not installed; AI voice conversion is unavailable)"
    return "CPU (no CUDA/MPS GPU detected)"


def _mps_available(torch: Any) -> bool:
    backend = getattr(torch, "backends", None)
    mps = getattr(backend, "mps", None)
    return bool(mps is not None and mps.is_available())
