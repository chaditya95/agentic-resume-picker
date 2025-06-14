import sys
import pathlib
from pathlib import Path

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from resume_selector.src.utils.file_io import load_text_file


def test_load_text_file(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello")
    assert load_text_file(file_path) == "hello"
