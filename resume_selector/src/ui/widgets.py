from PyQt6.QtWidgets import QListWidget
from PyQt6.QtCore import Qt
from pathlib import Path


class ResumeListWidget(QListWidget):
    """List widget supporting drag and drop of resume files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            self.addItem(str(path))
        event.acceptProposedAction()
