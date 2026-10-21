"""Worker threads so heavy work never blocks the Qt event loop."""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal

from vivoice.core.errors import Cancelled, VivoiceError
from vivoice.models import ModelRegistry, pull_model
from vivoice.presets import Preset


class ConversionWorker(QThread):
    progress = Signal(int)
    finished_ok = Signal(str)
    cancelled = Signal()
    failed = Signal(str)

    def __init__(
        self,
        preset: Preset,
        input_path: str | Path,
        output_path: str | Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._preset = preset
        self._input = Path(input_path)
        self._output = Path(output_path)
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Ask the render to stop at the next effect boundary."""
        self._cancel_event.set()

    def run(self) -> None:
        try:
            self._preset.build_chain().render_file(
                self._input,
                self._output,
                lambda fraction: self.progress.emit(int(fraction * 100)),
                should_cancel=self._cancel_event.is_set,
            )
        except Cancelled:
            self.cancelled.emit()
        except VivoiceError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - report everything to the UI
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.finished_ok.emit(str(self._output))


class ModelPullWorker(QThread):
    finished_ok = Signal(str, str)
    failed = Signal(str)

    def __init__(
        self,
        repo_id: str,
        name: str | None = None,
        path: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._repo_id = repo_id
        self._name = name
        self._path = path

    def run(self) -> None:
        try:
            model = pull_model(self._repo_id, name=self._name, path=self._path)
        except VivoiceError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.finished_ok.emit(model.name, model.source)


class ModelAddWorker(QThread):
    """Copy a local checkpoint without blocking the event loop."""

    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        name: str,
        checkpoint: str | Path,
        index: str | Path | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._name = name
        self._checkpoint = Path(checkpoint)
        self._index = Path(index) if index else None

    def run(self) -> None:
        try:
            model = ModelRegistry().add(self._name, self._checkpoint, self._index)
        except VivoiceError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.finished_ok.emit(model.name)


class StreamWorker(QThread):
    """Run a real-time stream in a worker thread until cancelled."""

    started_ok = Signal()
    stopped = Signal()
    failed = Signal(str)

    def __init__(
        self,
        preset: Preset,
        sample_rate: int,
        block_size: int,
        input_device,
        output_device,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._preset = preset
        self._sample_rate = int(sample_rate)
        self._block_size = int(block_size)
        self._input_device = input_device
        self._output_device = output_device
        self._stop_event = threading.Event()

    def cancel(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            self.failed.emit(
                "sounddevice is required for streaming. "
                f"Run: uv sync --extra realtime ({exc})"
            )
            return
        try:
            session = self._preset.build_chain().open_stream(self._sample_rate)
        except VivoiceError as exc:
            self.failed.emit(str(exc))
            return

        def callback(
            indata: np.ndarray,
            outdata: np.ndarray,
            frames: int,
            time_info: object,
            status: object,
        ) -> None:
            block = np.ascontiguousarray(indata, dtype=np.float32).T
            try:
                processed = session.process_block(block)
            except Exception:
                self._stop_event.set()
                raise sd.CallbackAbort from None
            outdata.fill(0.0)
            copied = min(frames, processed.shape[1])
            channels = min(outdata.shape[1], processed.shape[0])
            outdata[:copied, :channels] = processed[:channels, :copied].T

        try:
            with sd.Stream(
                samplerate=self._sample_rate,
                blocksize=self._block_size or 0,
                dtype="float32",
                device=(self._input_device, self._output_device),
                latency="low",
                callback=callback,
            ) as _:
                self.started_ok.emit()
                while not self._stop_event.wait(0.1):
                    pass
        except (ValueError, sd.PortAudioError) as exc:
            self.failed.emit(f"Audio stream failed: {exc}")
        except VivoiceError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.stopped.emit()
