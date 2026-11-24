"""Stamp authorship and licence on every page of the teaching PDFs.

Each page gets a discreet footer line naming the author, the licence and the
URL of the page the file is published on; the PDF metadata names the author.
Stamping is idempotent: files already stamped are skipped.

Usage (from the repository root):
    python _tools/stamp_pdfs.py teaching/econometrics/s01/worksheet/*.pdf

Requires: pip install pypdf reportlab
"""

import io
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

AUTHOR = "Ibrahim Goni Abdoulkadiri"
LICENSE = "CC BY-NC-ND 4.0"
SITE = "https://ibgoni.github.io"
MARK = "/IGAStamped"
YEAR = "2026"


def page_url(pdf_path: Path) -> str:
    parts = pdf_path.resolve().relative_to(Path.cwd().resolve()).parts
    # teaching/<course>/<session>/<group>/<file>  ->  /teaching/<course>/<session>/
    folder = parts[:3] if parts[0] == "teaching" and len(parts) >= 4 else parts[:-1]
    return f"{SITE}/{'/'.join(folder)}/"


def footer_overlay(width: float, height: float, text: str) -> PdfReader:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setFillColor(Color(0.42, 0.45, 0.50))
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(width / 2, 11, text)
    c.save()
    buf.seek(0)
    return PdfReader(buf)


def stamp(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    meta = reader.metadata or {}
    if meta.get(MARK):
        return "already stamped"

    url = page_url(pdf_path)
    text = f"© {YEAR} {AUTHOR} · {LICENSE} · {url}"

    writer = PdfWriter(clone_from=reader)
    for page in writer.pages:
        box = page.mediabox
        overlay = footer_overlay(float(box.width), float(box.height), text).pages[0]
        page.merge_page(overlay)

    title = (meta.get("/Title") or "").strip() or pdf_path.stem.replace("_", " ")
    writer.add_metadata({
        "/Author": AUTHOR,
        "/Title": title,
        "/Subject": f"Teaching material by {AUTHOR}. Source: {url}",
        "/Keywords": f"{AUTHOR}; {LICENSE}; {url}",
        "/Copyright": f"© {YEAR} {AUTHOR}, {LICENSE}",
        "/Creator": (meta.get("/Creator") or "").strip(),
        MARK: "1",
    })

    out = io.BytesIO()
    writer.write(out)
    pdf_path.write_bytes(out.getvalue())
    return f"stamped -> {url}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        p = Path(arg)
        print(f"{p}: {stamp(p)}")
