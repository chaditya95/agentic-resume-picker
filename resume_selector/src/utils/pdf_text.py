from importlib import import_module


def pdf_to_text(path: str) -> str:
    """Extract text from a PDF file."""
    try:
        pdfminer = import_module("pdfminer.high_level")
        return pdfminer.extract_text(path)
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF {path}: {e}")
