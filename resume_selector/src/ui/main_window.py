import logging
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSplitter,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
)
from PyQt6.QtCore import Qt

from ..orchestrator import Orchestrator
from .widgets import ResumeListWidget
from .dialogs import open_file

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.orchestrator = Orchestrator()
        self.setWindowTitle("Resume Selector")
        self._setup_ui()

    def _setup_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.resume_list = ResumeListWidget()
        jd_widget = QWidget()
        jd_layout = QVBoxLayout(jd_widget)
        self.jd_text = QTextEdit()
        load_btn = QPushButton("Load JD")
        load_btn.clicked.connect(self.load_jd)
        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self.run_orchestration)
        jd_layout.addWidget(self.jd_text)
        jd_layout.addWidget(load_btn)
        jd_layout.addWidget(run_btn)
        splitter.addWidget(self.resume_list)
        splitter.addWidget(jd_widget)
        self.setCentralWidget(splitter)

    def load_jd(self):
        path = open_file(self, "Open Job Description")
        if path:
            self.jd_text.setPlainText(path.read_text(encoding="utf-8"))

    def _collect_resumes(self) -> List[str]:
        paths = [Path(self.resume_list.item(i).text()) for i in range(self.resume_list.count())]
        return [p.read_text(encoding="utf-8") for p in paths]

    def run_orchestration(self):
        jd = self.jd_text.toPlainText()
        resumes = self._collect_resumes()
        if not resumes or not jd:
            logger.warning("Missing resumes or JD text")
            return
        report = self.orchestrator.run_sync(resumes, jd)
        report_path, _ = QFileDialog.getSaveFileName(self, "Save Report", filter="JSON (*.json)")
        if report_path:
            Path(report_path).write_text(report.json(indent=2), encoding="utf-8")
