from pathlib import Path
from typing import List

from .pdf_text import pdf_to_text


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def load_pdf(path: Path) -> str:
    return pdf_to_text(str(path))


def load_resume(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return load_pdf(path)
    elif path.suffix.lower() in {".docx", ".doc"}:
        return load_docx(path)
    else:
        return load_text_file(path)


def load_resumes(paths: List[Path]) -> List[str]:
    return [load_resume(p) for p in paths]
