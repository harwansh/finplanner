import argparse
import json
import re
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError as exc:
    raise SystemExit("Install pypdf first: python -m pip install pypdf") from exc

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PDF_DIR = ROOT / "knowledge" / "pdfs"
DEFAULT_INDEX_PATH = Path(__file__).resolve().parent / "knowledge" / "index" / "index.json"

BRAND_PATTERNS = [
    re.compile(r"\bSmartFinly\b", re.I),
]


def clean_text(text: str) -> str:
    text = text or ""
    for pattern in BRAND_PATTERNS:
        text = pattern.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120):
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        boundary = text.rfind(". ", start, end)
        if boundary > start + 300:
            end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return clean_text("\n".join(pages))


def build_index(pdf_dir: Path, output_path: Path):
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDF files found in {pdf_dir}")

    chunks = []
    for pdf in pdfs:
        text = extract_pdf_text(pdf)
        for index, chunk in enumerate(chunk_text(text), start=1):
            chunks.append({
                "id": f"{pdf.stem}-{index:04d}",
                "source": pdf.name,
                "title": pdf.stem.replace("-", " ").replace("_", " ").title(),
                "text": chunk,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "description": "Generated from PDFs. Keep source PDFs in knowledge/pdfs.",
        "chunks": chunks,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Indexed {len(pdfs)} PDF files into {len(chunks)} chunks: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build SmartFinly chatbot knowledge index from PDFs.")
    parser.add_argument("--pdf-dir", default=str(DEFAULT_PDF_DIR))
    parser.add_argument("--output", default=str(DEFAULT_INDEX_PATH))
    args = parser.parse_args()
    build_index(Path(args.pdf_dir), Path(args.output))


if __name__ == "__main__":
    main()
