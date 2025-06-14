from pathlib import Path
from PyQt6.QtWidgets import QFileDialog


def open_file(parent=None, caption="Open File", filter="All Files (*)") -> Path:
    path, _ = QFileDialog.getOpenFileName(parent, caption, filter=filter)
    return Path(path) if path else None
