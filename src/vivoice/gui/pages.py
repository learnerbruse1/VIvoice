"""Main application pages: convert, models, presets."""

from __future__ import annotations

from pathlib import Path

import yaml
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vivoice.ai.device import describe_device
from vivoice.config import load_user_config
from vivoice.core.errors import VivoiceError
from vivoice.gui.workers import ConversionWorker, ModelAddWorker, ModelPullWorker
from vivoice.models import ModelRegistry
from vivoice.paths import shipped_presets_dir, user_presets_dir
from vivoice.presets import Preset


def collect_presets() -> list[Path]:
    paths: list[Path] = []
    shipped = shipped_presets_dir()
    if shipped is not None and shipped.is_dir():
        paths.extend(sorted(shipped.glob("*.yaml")))
    user = user_presets_dir()
    if user.is_dir():
        paths.extend(sorted(user.glob("*.yaml")))
    return paths


class ConvertPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: ConversionWorker | None = None

        form = QFormLayout()
        self.input_edit = QLineEdit(self)
        self.input_button = QPushButton("Browse…", self)
        self.input_button.clicked.connect(self._browse_input)
        form.addRow("Input", _with_button(self, self.input_edit, self.input_button))

        self.output_edit = QLineEdit(self)
        self.output_button = QPushButton("Browse…", self)
        self.output_button.clicked.connect(self._browse_output)
        form.addRow("Output", _with_button(self, self.output_edit, self.output_button))

        self.preset_combo = QComboBox(self)
        self.preset_combo.currentIndexChanged.connect(lambda _index: self._update_chain_label())
        form.addRow("Preset", self.preset_combo)

        self.device_label = QLabel(describe_device(str(load_user_config()["device"])), self)
        form.addRow("Device", self.device_label)

        self.chain_label = QLabel("", self)
        self.chain_label.setWordWrap(True)
        form.addRow("Chain", self.chain_label)

        layout = QVBoxLayout(self)
        layout.addLayout(form)

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self._start)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self._cancel)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        self.status_label = QLabel("Ready.", self)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        self.refresh()

    def refresh(self) -> None:
        current = self.preset_combo.currentData()
        self.preset_combo.clear()
        for path in collect_presets():
            self.preset_combo.addItem(path.stem, str(path))
        if current is not None:
            index = self.preset_combo.findData(current)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)
        self._update_chain_label()

    def _selected_preset(self) -> Path | None:
        data = self.preset_combo.currentData()
        return Path(data) if data else None

    def _update_chain_label(self) -> None:
        path = self._selected_preset()
        if path is None:
            self.chain_label.setText("")
            return
        try:
            preset = Preset.load(path)
            names = [entry.get("type", "?") for entry in preset.chain_config]
            self.chain_label.setText(" → ".join(names))
        except VivoiceError as exc:
            self.chain_label.setText(f"invalid preset: {exc}")

    def _browse_input(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(self, "Choose input audio")
        if path:
            self.input_edit.setText(path)

    def _browse_output(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(self, "Choose output audio")
        if path:
            self.output_edit.setText(path)

    def _start(self) -> None:
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()
        preset_path = self._selected_preset()
        if not input_path or not output_path or preset_path is None:
            QMessageBox.warning(self, "VIvoice", "Choose an input file, output file, and preset.")
            return
        try:
            preset = Preset.load(preset_path)
        except VivoiceError as exc:
            QMessageBox.warning(self, "VIvoice", str(exc))
            return

        self._worker = ConversionWorker(preset, input_path, output_path, self)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_worker_done)
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status_label.setText("Converting…")
        self._worker.start()

    def _cancel(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()

    def _on_cancelled(self) -> None:
        self.status_label.setText("Cancelled.")

    def _on_finished(self, output_path: str) -> None:
        self.progress.setValue(100)
        self.status_label.setText(f"Done: {output_path}")

    def _on_failed(self, message: str) -> None:
        self.status_label.setText("Failed.")
        QMessageBox.critical(self, "Conversion failed", message)

    def _on_worker_done(self) -> None:
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)


class ModelsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pull_worker: ModelPullWorker | None = None
        self._add_worker: ModelAddWorker | None = None
        self.registry = ModelRegistry()

        self.list_widget = QListWidget(self)
        self.list_widget.itemDoubleClicked.connect(
            lambda item: QMessageBox.information(self, item.text(), item.toolTip())
        )

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Voice models (use with the 'voice-conversion' effect):", self))
        layout.addWidget(self.list_widget)

        buttons = QHBoxLayout()
        add_button = QPushButton("Add local…", self)
        add_button.clicked.connect(self._add_local)
        pull_button = QPushButton("Download from HuggingFace…", self)
        pull_button.clicked.connect(self._pull)
        remove_button = QPushButton("Remove", self)
        remove_button.clicked.connect(self._remove)
        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh)
        for button in (add_button, pull_button, remove_button, refresh_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        for model in self.registry.all():
            item = QListWidgetItem(model.name)
            item.setToolTip(f"{model.checkpoint}\nsource: {model.source}")
            self.list_widget.addItem(item)

    def _add_local(self) -> None:
        checkpoint, _filter = QFileDialog.getOpenFileName(self, "Choose a .pth checkpoint")
        if not checkpoint:
            return
        index, _filter = QFileDialog.getOpenFileName(self, "Choose a .index file (optional)")
        name, ok = QInputDialog.getText(self, "Model name", "Name for this voice model:")
        if not ok or not name.strip():
            return
        self._add_worker = ModelAddWorker(name, checkpoint, index or None, parent=self)
        self._add_worker.finished_ok.connect(self._on_add_finished)
        self._add_worker.failed.connect(self._on_add_failed)
        self._add_worker.start()

    def _on_add_finished(self, name: str) -> None:
        self.refresh()
        QMessageBox.information(self, "Import complete", f"Imported voice model '{name}'.")

    def _on_add_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Import failed", message)

    def _pull(self) -> None:
        repo_id, ok = QInputDialog.getText(
            self, "Download model", "HuggingFace repository (owner/name):"
        )
        if not ok or not repo_id.strip():
            return
        self._pull_worker = ModelPullWorker(repo_id.strip(), parent=self)
        self._pull_worker.finished_ok.connect(self._on_pull_finished)
        self._pull_worker.failed.connect(self._on_pull_failed)
        self._pull_worker.start()

    def _remove(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        try:
            self.registry.remove(item.text())
        except VivoiceError as exc:
            QMessageBox.critical(self, "Remove failed", str(exc))
            return
        self.refresh()

    def _on_pull_finished(self, name: str, _source: str) -> None:
        self.refresh()
        QMessageBox.information(self, "Download complete", f"Imported voice model '{name}'.")

    def _on_pull_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Download failed", message)


class PresetsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.combo = QComboBox(self)
        self.combo.currentIndexChanged.connect(lambda _index: self._load_selected())
        self.editor = QPlainTextEdit(self)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Presets are YAML documents. See docs/preset-format.md.", self))
        layout.addWidget(self.combo)
        layout.addWidget(self.editor)

        buttons = QHBoxLayout()
        save_button = QPushButton("Save copy…", self)
        save_button.clicked.connect(self._save_copy)
        buttons.addWidget(save_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        current = self.combo.currentData()
        self.combo.clear()
        for path in collect_presets():
            self.combo.addItem(path.name, str(path))
        if current is not None:
            index = self.combo.findData(current)
            if index >= 0:
                self.combo.setCurrentIndex(index)
        self._load_selected()

    def _load_selected(self) -> None:
        data = self.combo.currentData()
        if not data:
            self.editor.setPlainText("")
            return
        self.editor.setPlainText(Path(data).read_text(encoding="utf-8"))

    def _save_copy(self) -> None:
        try:
            preset = Preset.from_mapping(yaml.safe_load(self.editor.toPlainText()))
            preset.build_chain()
        except VivoiceError as exc:
            QMessageBox.critical(self, "Invalid preset", str(exc))
            return
        except yaml.YAMLError as exc:
            QMessageBox.critical(self, "Invalid YAML", str(exc))
            return

        name, ok = QInputDialog.getText(self, "Preset name", "File name (no extension):")
        if not ok or not name.strip():
            return
        directory = user_presets_dir()
        directory.mkdir(parents=True, exist_ok=True)
        try:
            preset.save(directory / f"{name.strip()}.yaml")
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self.refresh()


def _with_button(parent: QWidget, edit: QLineEdit, button: QPushButton) -> QWidget:
    row = QWidget(parent)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(edit, 1)
    layout.addWidget(button)
    return row
