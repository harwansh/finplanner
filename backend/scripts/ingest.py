#!/usr/bin/env python3
"""Build the SmartFinly finance education RAG knowledge base.

This one-time local script scans the CFP PDFs in the repository root, extracts text,
chunks it, embeds chunks with Amazon Bedrock Titan Embeddings, and writes a FAISS
index plus chunk metadata into backend/src/chat/kb/.

It is idempotent by default: if both the FAISS index and chunks JSON already exist,
it exits without re-embedding. Pass --force to rebuild.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

import boto3
import numpy as np
from pypdf import PdfReader

try:
    import faiss  # type: ignore
except Exception as exc:  # pragma: no cover - local tooling dependency
    raise SystemExit("Install faiss-cpu before ingesting: python -m pip install faiss-cpu") from exc

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KB_DIR = REPO_ROOT / "backend" / "src" / "chat" / "kb"
DEFAULT_EMBED_MODEL = os.environ.get("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
DEFAULT_REGION = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1"))

PDF_NAMES = [
    "5.+Retirementplanning_ifp.pdf",
    "CFP+IPS+PFM.pdf",
    "CFP+IPS+Regulatory.pdf",
    "CFP+estate+lecture+1.pdf",
    "CFP+estate+lecture+2.pdf",
    "CFP+estate+lecture+3.pdf",
    "CFP+ipam+global+lec+1-4.pdf",
    "CFP+ipam+indian+mkts.pdf",
    "CFP+risk+Lecture+1.pdf",
    "CFP+risk+Lecture+2.pdf",
    "CFP+risk+lecture+3.pdf",
    "CFP+risk+lecture+4.pdf",
    "Tax+Planning.pdf",
]

TOKEN_RE = re.compile(r"\S+")
SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    return SPACE_RE.sub(" ", text or "").strip()


def chunk_words(words: list[str], size: int = 500, overlap: int = 50) -> Iterable[tuple[int, int, str]]:
    if not words:
        return
    step = max(1, size - overlap)
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        yield start, end, " ".join(words[start:end])
        if end >= len(words):
            break
        start += step


def extract_chunks(pdf_path: Path, chunk_size: int, overlap: int) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    chunks: list[dict] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        words = TOKEN_RE.findall(text)
        for chunk_index, (_, _, chunk) in enumerate(chunk_words(words, chunk_size, overlap), start=1):
            if len(chunk) < 80:
                continue
            chunks.append(
                {
                    "id": f"{pdf_path.stem}-p{page_index}-c{chunk_index}",
                    "file": pdf_path.name,
                    "page": page_index,
                    "text": chunk,
                }
            )
    return chunks


def embed_texts(texts: list[str], model_id: str, region: str) -> np.ndarray:
    client = boto3.client("bedrock-runtime", region_name=region)
    vectors: list[list[float]] = []
    for idx, text in enumerate(texts, start=1):
        body = json.dumps({"inputText": text[:8000]})
        response = client.invoke_model(modelId=model_id, body=body)
        payload = json.loads(response["body"].read())
        embedding = payload.get("embedding")
        if not isinstance(embedding, list):
            raise RuntimeError(f"No embedding returned for chunk {idx}")
        vectors.append([float(x) for x in embedding])
        if idx % 25 == 0:
            print(f"Embedded {idx}/{len(texts)} chunks")
    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)
    return matrix


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SmartFinly chatbot FAISS KB from CFP PDFs")
    parser.add_argument("--kb-dir", default=str(DEFAULT_KB_DIR))
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    kb_dir = Path(args.kb_dir)
    index_path = kb_dir / "index.faiss"
    chunks_path = kb_dir / "chunks.json"

    if index_path.exists() and chunks_path.exists() and not args.force:
        print(f"Knowledge base already exists at {kb_dir}. Use --force to rebuild.")
        return 0

    pdf_paths = [REPO_ROOT / name for name in PDF_NAMES]
    missing = [str(path) for path in pdf_paths if not path.exists()]
    if missing:
        print("Missing expected PDFs:\n" + "\n".join(missing), file=sys.stderr)
        return 1

    all_chunks: list[dict] = []
    for pdf_path in pdf_paths:
        extracted = extract_chunks(pdf_path, args.chunk_size, args.overlap)
        print(f"{pdf_path.name}: {len(extracted)} chunks")
        all_chunks.extend(extracted)

    if not all_chunks:
        print("No chunks extracted.", file=sys.stderr)
        return 1

    vectors = embed_texts([chunk["text"] for chunk in all_chunks], args.embed_model, args.region)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    kb_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    chunks_path.write_text(
        json.dumps(
            {
                "version": 1,
                "embedding_model": args.embed_model,
                "region": args.region,
                "chunk_count": len(all_chunks),
                "chunks": all_chunks,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {index_path} and {chunks_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
