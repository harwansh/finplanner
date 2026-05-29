import json
import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9-]{1,}")
STOPWORDS = {
    "about", "after", "again", "also", "and", "are", "because", "been", "before", "being", "can", "could",
    "does", "for", "from", "have", "how", "into", "not", "that", "the", "their", "then", "there", "this",
    "through", "what", "when", "where", "which", "while", "with", "would", "your", "you",
}

DEFAULT_INDEX_PATH = Path(__file__).resolve().parent / "knowledge" / "index" / "index.json"


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "") if token.lower() not in STOPWORDS]


@lru_cache(maxsize=1)
def load_index() -> Dict:
    configured = os.environ.get("INDEX_PATH")
    path = Path(configured) if configured else DEFAULT_INDEX_PATH
    if not path.exists():
        return {"chunks": []}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {"chunks": data}
    return data


def _chunk_text(chunk: Dict) -> str:
    return " ".join(str(chunk.get(key, "")) for key in ("title", "source", "text", "content"))


def search_knowledge_base(query: str, limit: int = 3, min_score: float = 0.08) -> List[Dict]:
    index = load_index()
    chunks = index.get("chunks", [])
    query_tokens = tokenize(query)
    if not query_tokens or not chunks:
        return []

    query_counts = {token: query_tokens.count(token) for token in set(query_tokens)}
    document_tokens = [tokenize(_chunk_text(chunk)) for chunk in chunks]
    document_count = max(len(document_tokens), 1)

    doc_freq = {}
    for tokens in document_tokens:
        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1

    def idf(token: str) -> float:
        return math.log((1 + document_count) / (1 + doc_freq.get(token, 0))) + 1

    query_norm = math.sqrt(sum((count * idf(token)) ** 2 for token, count in query_counts.items())) or 1.0
    results = []

    for chunk, tokens in zip(chunks, document_tokens):
        if not tokens:
            continue
        token_counts = {token: tokens.count(token) for token in set(tokens)}
        dot = 0.0
        doc_norm = 0.0
        for token, count in token_counts.items():
            weight = count * idf(token)
            doc_norm += weight * weight
            if token in query_counts:
                dot += weight * query_counts[token] * idf(token)
        score = dot / ((math.sqrt(doc_norm) or 1.0) * query_norm)
        if score >= min_score:
            enriched = dict(chunk)
            enriched["score"] = round(score, 4)
            enriched["text"] = str(enriched.get("text") or enriched.get("content") or "")
            results.append(enriched)

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def build_grounded_answer(question: str, matches: List[Dict]) -> str:
    if not matches:
        return ""

    top = matches[0]
    text = str(top.get("text", "")).strip()
    title = str(top.get("title") or top.get("source") or "the knowledge base")

    sentences = re.split(r"(?<=[.!?])\s+", text)
    answer_sentences = [sentence.strip() for sentence in sentences if sentence.strip()][:4]
    answer = " ".join(answer_sentences) if answer_sentences else text[:700]
    return f"From {title}: {answer}\n\nThis is education-only information, not investment advice."
