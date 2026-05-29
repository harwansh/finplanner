"""
Ingest pipeline for SmartFinly knowledge base.

Steps:
1. Read every source PDF.
2. Extract text per page.
3. Sanitize (strip all brand names, designation marks, promo URLs, watermarks).
4. Chunk into overlapping passages.
5. Save the consolidated, brand-free PDFs into one folder (knowledge/pdfs).
6. Build a compact TF-IDF style keyword index (knowledge/index/index.json)
   that the Lambda can load with zero heavy ML dependencies.

The index is intentionally dependency-light (pure Python + json) so it runs
inside a small Lambda without bundling sentence-transformers / numpy wheels.
"""

import json
import math
import os
import re
import sys
from collections import Counter

from pypdf import PdfReader
from pypdf import PdfWriter

from sanitize import sanitize_text, contains_brand, FILE_TOPIC_MAP

SRC_DIR = os.environ.get("SRC_DIR", "/home/claude/finplanner")
PDF_OUT = os.environ.get("PDF_OUT", "/home/claude/finplanner/knowledge/pdfs")
INDEX_OUT = os.environ.get("INDEX_OUT", "/home/claude/finplanner/knowledge/index")

CHUNK_WORDS = 220
CHUNK_OVERLAP = 50

_STOP = set("""a an the and or but if then else of to in on at by for with from as is are was were be been
being this that these those it its it's their there here we you they i he she him her them our your my me
do does did done have has had having will would shall should can could may might must not no nor so such
than too very just only also more most some any each other into over under above below between within
about against during before after while because how what when where which who whom whose why""".split())

_WORD_RE = re.compile(r"[a-z][a-z0-9\-]{1,}")


def tokenize(text):
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOP and len(w) > 2]


def chunk_words(words, size, overlap):
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        piece = words[start:start + size]
        if len(piece) < 25 and start != 0:
            break
        yield " ".join(piece)


def main():
    os.makedirs(PDF_OUT, exist_ok=True)
    os.makedirs(INDEX_OUT, exist_ok=True)

    chunks = []          # list of {id, doc, topic, category, text, tokens}
    doc_meta = {}        # clean_name -> {topic, category, pages}

    for src_name, (clean_name, topic, category) in FILE_TOPIC_MAP.items():
        src_path = os.path.join(SRC_DIR, src_name)
        if not os.path.exists(src_path):
            print(f"  ! missing {src_name}, skipping")
            continue

        reader = PdfReader(src_path)
        pages_text = []
        for page in reader.pages:
            raw = page.extract_text() or ""
            clean = sanitize_text(raw)
            pages_text.append(clean)

        full_clean = "\n\n".join(t for t in pages_text if t)

        # Defensive: assert no brand survived.
        if contains_brand(full_clean):
            # Re-run sanitize once more; if still present, hard-strip the token.
            full_clean = sanitize_text(full_clean)
            full_clean = re.sub(r"\b\w*proschool\w*\b", " ", full_clean, flags=re.I)

        # --- Save a clean, brand-free copy of the PDF text as a lightweight PDF.
        # We rebuild the PDF from sanitized text so the stored "pdfs" folder
        # contains brand-free documents (the originals carry watermarks we must
        # not redistribute). Visual fidelity is sacrificed for compliance.
        writer = PdfWriter()
        # Use reportlab to lay out sanitized text into pages.
        _write_text_pdf(os.path.join(PDF_OUT, clean_name), topic, full_clean)

        doc_meta[clean_name] = {
            "topic": topic, "category": category, "pages": len(reader.pages),
        }

        # --- Chunk for retrieval.
        words = full_clean.split()
        for ci, chunk_text in enumerate(chunk_words(words, CHUNK_WORDS, CHUNK_OVERLAP)):
            toks = tokenize(chunk_text)
            if len(toks) < 12:
                continue
            chunks.append({
                "id": f"{clean_name}#{ci}",
                "doc": clean_name,
                "topic": topic,
                "category": category,
                "text": chunk_text,
                "tf": dict(Counter(toks)),
            })
        print(f"  + {clean_name}: {len(reader.pages)}p -> {sum(1 for c in chunks if c['doc']==clean_name)} chunks")

    # --- Build IDF over the corpus.
    N = len(chunks)
    df = Counter()
    for c in chunks:
        for term in c["tf"]:
            df[term] += 1
    idf = {term: math.log((N + 1) / (dfi + 1)) + 1.0 for term, dfi in df.items()}

    # Precompute per-chunk vector norms for cosine similarity.
    for c in chunks:
        weights = {t: (1 + math.log(f)) * idf.get(t, 0.0) for t, f in c["tf"].items()}
        norm = math.sqrt(sum(w * w for w in weights.values())) or 1.0
        c["w"] = weights
        c["norm"] = norm
        del c["tf"]  # shrink index

    index = {
        "version": 2,
        "doc_count": N,
        "idf": idf,
        "docs": doc_meta,
        "chunks": chunks,
    }
    out_path = os.path.join(INDEX_OUT, "index.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"\nIndexed {N} chunks across {len(doc_meta)} documents.")
    print(f"Index size: {size_kb:.0f} KB -> {out_path}")


def _write_text_pdf(path, title, body):
    """Render sanitized text into a clean PDF using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT

    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Title"], fontSize=18, spaceAfter=14)
    p = ParagraphStyle("p", parent=styles["BodyText"], fontSize=10.5,
                       leading=15, alignment=TA_LEFT, spaceAfter=8)

    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title=f"SmartFinly Knowledge — {title}",
                            author="SmartFinly (Educational)")
    flow = [Paragraph(_esc(title), h),
            Paragraph("Educational reference. Not investment, tax or legal advice.", p),
            Spacer(1, 8)]
    for para in body.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        flow.append(Paragraph(_esc(para), p))
    doc.build(flow)


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))[:8000]


if __name__ == "__main__":
    sys.exit(main())
