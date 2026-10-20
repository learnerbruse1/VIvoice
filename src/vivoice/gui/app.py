"""Desktop application entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from vivoice.ai.device import describe_device
from vivoice.gui.guide import GuidePage
from vivoice.gui.pages import ConvertPage, ModelsPage, PresetsPage
from vivoice.models import ModelRegistry


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VIvoice")
        self.resize(960, 640)

        central = QWidget(self)
        body_layout = QHBoxLayout(central)

        self.stack = QStackedWidget(central)
        self.pages = {
            "Convert": ConvertPage(central),
            "Models": ModelsPage(central),
            "Presets": PresetsPage(central),
            "User guide": GuidePage(central),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.nav = QListWidget(central)
        self.nav.setMaximumWidth(180)
        for name in self.pages:
            self.nav.addItem(name)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)

        body_layout.addWidget(self.nav)
        body_layout.addWidget(self.stack, 1)

        model_count = len(ModelRegistry().all())
        self.statusBar().showMessage(
            f"{describe_device()}  |  {model_count} voice model(s)"
        )


def main(argv: Sequence[str] | None = None) -> int:
    app = QApplication.instance() or QApplication(sys.argv if argv is None else list(argv))
    window = MainWindow()
    window.show()
    return app.exec()
