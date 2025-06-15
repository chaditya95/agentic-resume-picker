"""Enhanced widgets with better file handling"""
from PyQt6.QtWidgets import QListWidget, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import List

from ..utils.file_io import is_supported_file


class ResumeListWidget(QListWidget):
    """Enhanced list widget with better drag and drop support"""
    
    files_dropped = pyqtSignal(list)  # Emits list of Path objects
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setToolTip("Drag and drop resume files here\nSupported: PDF, DOCX, DOC, TXT")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if any of the files are supported
            urls = event.mimeData().urls()
            has_supported = any(
                is_supported_file(Path(url.toLocalFile())) 
                for url in urls
            )
            
            if has_supported:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dragEnterEvent(event)
    
    def dropEvent(self, event):
        file_paths = []
        unsupported = []
        
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                if is_supported_file(path):
                    file_paths.append(path)
                else:
                    unsupported.append(path.name)
        
        if file_paths:
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        
        if unsupported:
            QMessageBox.warning(
                self, "Unsupported Files",
                f"The following files are not supported:\n" +
                "\n".join(unsupported) +
                "\n\nSupported formats: PDF, DOCX, DOC, TXT"
            )