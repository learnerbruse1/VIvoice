"""RVC adapter.

The full inference path is the v0.2 milestone (see docs/ROADMAP.md). The setup
checks and the engine boundary are already in place so other contributors can
wire inference without touching the core.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np

from vivoice.ai.adapter import VoiceConversionAdapter, register_adapter
from vivoice.core.errors import MissingDependencyError, UnsupportedFeatureError
from vivoice.models.model import VoiceModel
from vivoice.paths import repo_root

RVC_SAMPLE_RATE = 40_000


@register_adapter
class RVCAdapter(VoiceConversionAdapter):
    engine: ClassVar[str] = "rvc"
    sample_rate: ClassVar[int] = RVC_SAMPLE_RATE

    def convert(
        self,
        audio_mono: np.ndarray,
        voice_model: VoiceModel,
        params: Mapping[str, Any],
    ) -> np.ndarray:
        self._check_installed()
        raise UnsupportedFeatureError(
            "RVC inference is not wired yet (planned for v0.2, see docs/ROADMAP.md). "
            f"Setup is valid and voice model '{voice_model.name}' is ready at "
            f"{voice_model.checkpoint}."
        )

    def _check_installed(self) -> None:
        try:
            import torch  # noqa: F401
        except ImportError as exc:
            raise MissingDependencyError(
                "PyTorch is required for the RVC engine. Run: uv sync --extra ai"
            ) from exc
        root = repo_root()
        vendor = root / "third_party" / "RVC" if root is not None else None
        if vendor is None or not vendor.is_dir():
            raise MissingDependencyError(
                "The RVC engine is not vendored. Run: python scripts/fetch_rvc.py"
            )
