"""In-process RVC adapter.

The native path requires PyTorch and the vendored RVC-Project repository
(``python scripts/fetch_rvc.py``). Upstream modules are imported lazily so the
rest of VIvoice works without them; the wiring logic itself is covered by unit
tests that substitute a fake engine.
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import soundfile as sf

from vivoice.ai.adapter import VoiceConversionAdapter, register_adapter
from vivoice.ai.device import Device
from vivoice.core.errors import ConversionError, MissingDependencyError, VivoiceError
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
        vendor = self._vendor_root()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary:
            temporary_path = Path(temporary.name)
        try:
            sf.write(str(temporary_path), audio_mono, self.sample_rate)
            with _vendored_path(vendor):
                try:
                    from infer.modules.vc.modules import VC
                except ImportError as exc:
                    raise MissingDependencyError(
                        "The vendored RVC engine could not be imported. "
                        "Re-run: python scripts/fetch_rvc.py"
                    ) from exc

                vc = VC()
                device = _upstream_device(self.device)
                vc.get_vc(str(voice_model.checkpoint), device=device)
                index_path = str(voice_model.index) if voice_model.index else ""
                f0_method = str(params.get("f0_method", "rmvpe"))
                index_rate = float(params.get("index_rate", 0.75))
                _info, (sample_rate, converted) = vc.vc_single(
                    sid=0,
                    input_audio_path=str(temporary_path),
                    f0_up_key=0,
                    f0_method=f0_method,
                    file_index=index_path,
                    index_rate=index_rate,
                )
            result = np.asarray(converted, dtype=np.float32).reshape(-1)
            if int(sample_rate) != self.sample_rate:
                from scipy.signal import resample_poly

                result = resample_poly(
                    result, up=self.sample_rate, down=int(sample_rate)
                ).astype(np.float32)
            return result
        except VivoiceError:
            raise
        except Exception as exc:
            raise ConversionError(f"RVC conversion failed: {exc}") from exc
        finally:
            temporary_path.unlink(missing_ok=True)

    def _check_installed(self) -> None:
        try:
            import torch  # noqa: F401
        except ImportError as exc:
            raise MissingDependencyError(
                "PyTorch is required for the RVC engine. Run: uv sync --extra ai"
            ) from exc
        if not self._vendor_root().is_dir():
            raise MissingDependencyError(
                "The RVC engine is not vendored. Run: python scripts/fetch_rvc.py"
            )

    @staticmethod
    def _vendor_root() -> Path:
        override = os.environ.get("VIVOICE_RVC_DIR")
        if override:
            return Path(override).expanduser()
        root = repo_root()
        if root is None:
            return Path("third_party/RVC")
        return root / "third_party" / "RVC"


def _upstream_device(device: Device) -> str:
    return "cuda" if device == Device.CUDA else "cpu"


@contextmanager
def _vendored_path(vendor: Path) -> Iterator[None]:
    path = str(vendor)
    inserted = path not in sys.path
    if inserted:
        sys.path.insert(0, path)
    try:
        yield
    finally:
        if inserted:
            sys.path.remove(path)
