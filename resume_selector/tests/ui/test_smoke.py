import sys
import pytest
pytest.importorskip("PyQt6")
from PyQt6.QtWidgets import QApplication
from resume_selector.src.ui.main_window import MainWindow


def test_main_window_creation(qtbot):
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "Resume Selector"
