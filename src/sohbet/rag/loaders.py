"""Doküman yükleyiciler (PDF/TXT/MD/HTML).

Ağır ayrıştırıcılar (pypdf, bs4) lazy import edilir; .txt/.md için harici
bağımlılık gerekmez.
"""

from __future__ import annotations

from pathlib import Path


def load_document(path: str | Path) -> str:
    """Dosyayı düz metne çevirir. Desteklenmeyen uzantı için ham metni dener."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(p)
    if suffix in (".html", ".htm"):
        return _load_html(p)
    # .txt, .md ve diğerleri: düz metin
    return p.read_text(encoding="utf-8", errors="ignore")


def _load_pdf(p: Path) -> str:
    from pypdf import PdfReader  # lazy

    reader = PdfReader(str(p))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _load_html(p: Path) -> str:
    from bs4 import BeautifulSoup  # lazy

    soup = BeautifulSoup(p.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    return soup.get_text(separator="\n")


def iter_documents(directory: str | Path) -> list[Path]:
    """Bir dizindeki desteklenen dokümanları listeler."""
    d = Path(directory)
    exts = {".pdf", ".txt", ".md", ".html", ".htm"}
    return sorted(p for p in d.rglob("*") if p.is_file() and p.suffix.lower() in exts)
