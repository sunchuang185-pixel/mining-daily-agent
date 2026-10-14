"""Local-only PDF ingestion with content hash and physical page citations."""

import hashlib
import re
from pathlib import Path

import pymupdf

from .resource_schemas import Document, Page


class EvidenceError(ValueError):
    """Evidence cannot be safely processed within the configured bounds."""


def read_pdf(path: Path, pages: list[int] | None = None, max_chars: int = 180_000) -> Document:
    if not path.is_file() or path.stat().st_size > 50 * 1024 * 1024:
        raise EvidenceError("PDF missing or exceeds 50 MiB")
    blob = path.read_bytes()
    if not blob.startswith(b"%PDF-"):
        raise EvidenceError("Input is not a PDF")
    try:
        with pymupdf.open(stream=blob, filetype="pdf") as pdf:  # type: ignore[no-untyped-call]
            if pdf.needs_pass:
                raise EvidenceError("Encrypted PDF requires an unlocked local copy")
            if len(pdf) > 1000:
                raise EvidenceError("PDF exceeds 1000-page limit")
            all_pages = [Page(number=i + 1, text=p.get_text(sort=True)) for i, p in enumerate(pdf)]
    except EvidenceError:
        raise
    except Exception as exc:
        raise EvidenceError("PDF parser could not read this document") from exc
    if not all_pages:
        raise EvidenceError("PDF is empty")
    if pages is not None:
        if not pages or min(pages) < 1 or max(pages) > len(all_pages):
            raise EvidenceError("Requested page is outside PDF bounds")
        selected = sorted(set(pages))
        selection = "explicit physical pages"
    else:
        hits = [p.number for p in all_pages if re.search(r"\b(indicated|inferred)\b", p.text, re.I)]
        selected = sorted({n for h in hits for n in (h - 1, h, h + 1) if 1 <= n <= len(all_pages)})
        selection = "all indicated/inferred keyword pages plus adjacent pages"
    if not selected:
        raise EvidenceError("No readable resource evidence; OCR or explicit pages required")
    evidence = [all_pages[n - 1] for n in selected]
    if sum(len(p.text.strip()) for p in evidence) < 80:
        raise EvidenceError("Insufficient text; OCR required; image-only PDF is not auto-accepted")
    if sum(len(p.text) for p in evidence) > max_chars:
        raise EvidenceError("Evidence exceeds context limit; specify a narrower page scope")
    return Document(
        document_id=hashlib.sha256(blob).hexdigest(),
        filename=path.name,
        page_count=len(all_pages),
        pages=evidence,
        selection=selection,
    )
