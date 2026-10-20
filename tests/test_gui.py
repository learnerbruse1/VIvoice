from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_constructs(tmp_path, monkeypatch, qapp) -> None:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    from vivoice.gui.app import MainWindow

    window = MainWindow()
    assert window.windowTitle() == "VIvoice"
    assert window.stack.count() == 4
    window.close()
