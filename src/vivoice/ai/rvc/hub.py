"""RVC engine backed by the MIT-licensed ``huggingface-hub-rvc`` pipeline.

This pipeline reimplements the RVC architecture without the hard-to-install
upstream toolchain (no fairseq/av) and loads classic RVC-WebUI ``.pth`` /
``.index`` character models directly, which keeps VIvoice compatible with the
community voice-model ecosystem.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import soundfile as sf
import torch
import torchaudio

from vivoice.ai.adapter import VoiceConversionAdapter, register_adapter
from vivoice.ai.device import Device
from vivoice.core.errors import ConversionError, MissingDependencyError, VivoiceError
from vivoice.models.model import VoiceModel

RVC_SAMPLE_RATE = 40_000


@register_adapter
class RvcHubAdapter(VoiceConversionAdapter):
    engine: ClassVar[str] = "rvc-hub"
    sample_rate: ClassVar[int] = RVC_SAMPLE_RATE

    def convert(
        self,
        audio_mono: np.ndarray,
        voice_model: VoiceModel,
        params: Mapping[str, Any],
    ) -> np.ndarray:
        try:
            from huggingface_hub_rvc import RVCPipeline
        except ImportError as exc:
            cause = exc.__cause__ or exc.__context__
            raise MissingDependencyError(
                "huggingface-hub-rvc is required for the 'rvc-hub' engine. "
                f"Install it with: uv pip install huggingface-hub-rvc "
                f"({exc}"
                + (f"; caused by: {cause}" if cause is not None else "")
                + ")"
            ) from exc

        device = "cuda" if self.device == Device.CUDA else "cpu"
        f0_method = str(params.get("f0_method", "rmvpe"))
        retrieval_strength = float(params.get("index_rate", 0.75))
        with tempfile.TemporaryDirectory(prefix="vivoice-rvc-") as temporary:
            root = Path(temporary)
            source = root / "input.wav"
            output = root / "output.wav"
            model_directory = root / "model"
            model_directory.mkdir()
            shutil.copy2(voice_model.checkpoint, model_directory / "model.pth")
            if voice_model.index:
                shutil.copy2(voice_model.index, model_directory / "model.index")
            sf.write(str(source), audio_mono, self.sample_rate)
            try:
                with _soundfile_torchaudio_backend():
                    pipeline = RVCPipeline.from_pretrained(model_directory)
                    pipeline.convert_file(
                        source,
                        output,
                        audio_mode="vocal_only",
                        device=device,
                        f0_method=f0_method,
                        retrieval_strength=retrieval_strength,
                        output_sample_rate=self.sample_rate,
                    )
                converted, sample_rate = sf.read(str(output), dtype="float32", always_2d=False)
            except VivoiceError:
                raise
            except Exception as exc:
                raise ConversionError(f"RVC conversion failed: {exc}") from exc
        result = np.asarray(converted, dtype=np.float32).reshape(-1)
        if int(sample_rate) != self.sample_rate:
            from scipy.signal import resample_poly

            result = resample_poly(
                result, up=self.sample_rate, down=int(sample_rate)
            ).astype(np.float32)
        return result


@contextmanager
def _soundfile_torchaudio_backend() -> Iterator[None]:
    """Swap torchaudio's file I/O for soundfile, avoiding the torchcodec/ffmpeg
    backend requirement on machines that do not have shared FFmpeg libraries."""
    real_load = torchaudio.load
    real_save = torchaudio.save

    def load(path: str, **kwargs: Any) -> tuple[torch.Tensor, int]:
        data, sample_rate = sf.read(str(path), dtype="float32", always_2d=True)
        waveform = torch.from_numpy(np.ascontiguousarray(data.T))
        return waveform.float(), int(sample_rate)

    def save(path: str, waveform: torch.Tensor, sample_rate: int, **kwargs: Any) -> None:
        samples = waveform.detach().cpu()
        if samples.ndim == 1:
            samples = samples.unsqueeze(0)
        sf.write(str(path), samples.numpy().T, int(sample_rate))

    torchaudio.load = load
    torchaudio.save = save
    try:
        yield
    finally:
        torchaudio.load = real_load
        torchaudio.save = real_save
