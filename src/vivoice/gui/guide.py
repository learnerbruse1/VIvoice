"""In-app user guide page that renders docs/USER_GUIDE.md with clickable links."""

from __future__ import annotations

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from vivoice.paths import load_guide_markdown


class GuidePage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser)
        self.reload()

    def reload(self) -> None:
        try:
            markdown = load_guide_markdown()
        except Exception as exc:  # noqa: BLE001 - the guide must never crash the app
            markdown = f"# User guide unavailable\n\n{exc}"
        self.browser.setMarkdown(markdown)
