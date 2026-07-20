from __future__ import annotations

from pathlib import Path

import docx2txt
from pypdf import PdfReader


TEXT_EXTENSIONS = {
    ".asm",
    ".bas",
    ".bat",
    ".c",
    ".cfg",
    ".cl",
    ".cob",
    ".cbl",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".ctl",
    ".ddl",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsp",
    ".log",
    ".md",
    ".pas",
    ".php",
    ".pl",
    ".properties",
    ".py",
    ".r",
    ".rb",
    ".rpg",
    ".rs",
    ".scala",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".txt",
    ".vb",
    ".xml",
    ".yaml",
    ".yml",
}

DOCUMENT_EXTENSIONS = {".pdf", ".docx"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | DOCUMENT_EXTENSIONS


class UnsupportedFileTypeError(ValueError):
    pass


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def load_file_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return _load_text(path)
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix == ".docx":
        return _load_docx(path)
    raise UnsupportedFileTypeError(f"Unsupported file type: {path.suffix}")


def _load_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def _load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"\n\n--- Page {page_number} ---\n{text}")
    return "\n".join(pages).strip()


def _load_docx(path: Path) -> str:
    return docx2txt.process(str(path)).strip()
