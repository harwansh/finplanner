"""SmartFinly finance education RAG chatbot Lambda."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

import boto3
import numpy as np

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - fallback path for local smoke tests
    faiss = None

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
EMBED_MODEL_ID = os.environ.get("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1"))
TOP_K = int(os.environ.get("CHAT_TOP_K", "4"))
SIMILARITY_THRESHOLD = float(os.environ.get("CHAT_SIMILARITY_THRESHOLD", "0.35"))
KB_DIR = Path(__file__).resolve().parent / "kb"

SYSTEM_PROMPT = """You are SmartFinly's finance education assistant for young salary earners in India. Use the provided context when relevant, but always explain in your own clear, original words — never copy source text. Be accurate, concise, and educational, with simple India-relevant examples (SIP, 80C, NPS, EPF, HRA) where useful. If the context lacks the answer, use your own finance knowledge and answer correctly. Refuse non-finance questions politely. This is education only — never give personalized buy/sell advice, guaranteed returns, or ask for PAN/Aadhaar/OTP/bank details."""

CORS_HEADERS = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type,authorization",
    "Access-Control-Allow-Methods": "OPTIONS,POST",
}

SENSITIVE_RE = re.compile(
    r"(aadhaar|aadhar|pan|otp|password|passcode|secret|token|bank.?account|account.?number|ifsc|upi|vpa|"
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b|\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b)",
    re.I,
)

_bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
_index = None
_chunks: list[dict[str, Any]] | None = None


def response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, ensure_ascii=False)}


def parse_event(event: dict[str, Any]) -> dict[str, Any] | str:
    method = (event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod") or "POST").upper()
    if method == "OPTIONS":
        return "__OPTIONS__"
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_kb() -> tuple[Any, list[dict[str, Any]]]:
    global _index, _chunks
    if _index is not None and _chunks is not None:
        return _index, _chunks

    chunks_path = KB_DIR / "chunks.json"
    index_path = KB_DIR / "index.faiss"
    chunks_payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    _chunks = chunks_payload.get("chunks", [])

    if faiss is not None and index_path.exists():
        _index = faiss.read_index(str(index_path))
    else:
        _index = None
    return _index, _chunks


def embed_query(message: str) -> np.ndarray:
    body = json.dumps({"inputText": message[:8000]})
    result = _bedrock.invoke_model(modelId=EMBED_MODEL_ID, body=body)
    payload = json.loads(result["body"].read())
    vector = np.array([float(x) for x in payload["embedding"]], dtype="float32").reshape(1, -1)
    norm = np.linalg.norm(vector, axis=1, keepdims=True)
    vector = vector / np.maximum(norm, 1e-12)
    return vector


def fallback_text_search(message: str, chunks: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    query_terms = {term for term in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", message.lower())}
    scored = []
    for chunk in chunks:
        text = (chunk.get("text") or "").lower()
        overlap = sum(1 for term in query_terms if term in text)
        if overlap:
            scored.append({"score": min(0.34, overlap / max(len(query_terms), 1)), "chunk": chunk})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:k]


def retrieve(message: str) -> list[dict[str, Any]]:
    index, chunks = load_kb()
    if not chunks:
        return []
    if index is None:
        return fallback_text_search(message, chunks, TOP_K)

    vector = embed_query(message)
    scores, ids = index.search(vector, TOP_K)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(chunks):
            continue
        results.append({"score": float(score), "chunk": chunks[idx]})
    return results


def build_context(results: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    references = []
    parts = []
    seen = set()
    for item in results:
        chunk = item["chunk"]
        ref = {"file": chunk.get("file"), "page": int(chunk.get("page") or 0)}
        ref_key = (ref["file"], ref["page"])
        if ref_key not in seen:
            seen.add(ref_key)
            references.append(ref)
        parts.append(f"File: {ref['file']} | Page: {ref['page']}\n{chunk.get('text', '')[:1600]}")
    return "\n\n---\n\n".join(parts), references


def generate_answer(message: str, context: str, grounded: bool) -> str:
    if grounded:
        user_text = (
            "Use the context below when it is relevant. Explain in your own words and do not copy phrases verbatim.\n\n"
            f"Question: {message}\n\nContext:\n{context}"
        )
    else:
        user_text = f"No relevant study-material context was found. Answer using general finance education knowledge.\n\nQuestion: {message}"

    result = _bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 900, "temperature": 0.2},
    )
    return result["output"]["message"]["content"][0]["text"].strip()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    payload = parse_event(event or {})
    if payload == "__OPTIONS__":
        return response(204, {})

    message = str(payload.get("message") or "").strip() if isinstance(payload, dict) else ""
    if not message:
        return response(400, {"answer": "Please enter a finance education question.", "source": "ai", "references": []})
    if len(message) > 2500:
        return response(400, {"answer": "Please keep the question shorter.", "source": "ai", "references": []})
    if SENSITIVE_RE.search(message):
        return response(
            400,
            {
                "answer": "Please do not share PAN, Aadhaar, OTP, UPI, passwords, bank/account numbers, or other sensitive details.",
                "source": "ai",
                "references": [],
            },
        )

    try:
        results = retrieve(message)
        top_score = results[0]["score"] if results else 0.0
        grounded = top_score >= SIMILARITY_THRESHOLD
        context_text, references = build_context(results if grounded else [])
        answer = generate_answer(message, context_text, grounded)
        return response(
            200,
            {
                "answer": answer,
                "source": "knowledge_base" if grounded else "ai",
                "references": references if grounded else [],
            },
        )
    except Exception as exc:
        print("SmartFinly chat failed:", exc.__class__.__name__, str(exc))
        return response(500, {"answer": "I am having trouble answering right now. Please try again.", "source": "ai", "references": []})


handler = lambda_handler
