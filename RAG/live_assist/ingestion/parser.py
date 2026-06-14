from __future__ import annotations

from pathlib import Path


def parse_pdf_pages(pdf_path: Path) -> list[dict]:
    """Extract page text from a PDF using pypdf."""

    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": index, "text": text.strip()})
    return pages

