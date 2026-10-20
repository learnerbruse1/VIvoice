"""Worker threads so heavy work never blocks the Qt event loop."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from vivoice.core.errors import Cancelled, VivoiceError
from vivoice.models import pull_model
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

    def __init__(self, repo_id: str, name: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._repo_id = repo_id
        self._name = name

    def run(self) -> None:
        try:
            model = pull_model(self._repo_id, name=self._name)
        except VivoiceError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.finished_ok.emit(model.name, model.source)
