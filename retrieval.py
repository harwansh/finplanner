"""
Retrieval engine for SmartFinly chatbot.

Pure-Python TF-IDF cosine retrieval over the prebuilt index.json.
No numpy / ML wheels required, so it runs in a minimal Lambda.

Public API:
    load_index(path) -> index dict (cached)
    search(query, k) -> list of {score, doc, topic, category, text}
    best_answer(query) -> {answer, sources, confidence, used_kb}  (KB-only)
"""

import json
import math
import os
import re
from functools import lru_cache

from sanitize import contains_brand

_WORD_RE = re.compile(r"[a-z][a-z0-9\-]{1,}")
_STOP = set("""a an the and or but if then else of to in on at by for with from as is are was were be been
being this that these those it its their there here we you they i he she him her them our your my me
do does did done have has had having will would shall should can could may might must not no nor so such
than too very just only also more most some any each other into over under above below between within
about against during before after while because how what when where which who whom whose why what's
explain tell define describe meaning means difference between""".split())

INDEX_PATH = os.environ.get(
    "INDEX_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "index", "index.json"),
)

# Retrieval thresholds (calibrated for long-passage cosine scores).
MIN_SCORE_ANSWER = 0.085    # below this, KB is considered "no good answer"
STRONG_SCORE = 0.20         # at/above this, KB answer is high-confidence
MAX_SNIPPETS = 4


def _tokenize(text):
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOP and len(w) > 2]


@lru_cache(maxsize=1)
def load_index(path=INDEX_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _query_vector(query, idf):
    toks = _tokenize(query)
    if not toks:
        return {}, 1.0
    from collections import Counter
    tf = Counter(toks)
    weights = {t: (1 + math.log(f)) * idf.get(t, 1.0) for t, f in tf.items()}
    norm = math.sqrt(sum(w * w for w in weights.values())) or 1.0
    return weights, norm


def search(query, k=MAX_SNIPPETS, index=None):
    index = index or load_index()
    idf = index["idf"]
    qw, qnorm = _query_vector(query, idf)
    if not qw:
        return []

    # Bigram phrase signal: reward chunks that contain consecutive query terms.
    q_tokens = _tokenize(query)
    q_bigrams = {f"{a} {b}" for a, b in zip(q_tokens, q_tokens[1:])}

    scored = []
    for c in index["chunks"]:
        cw = c["w"]
        if len(qw) <= len(cw):
            dot = sum(w * cw.get(t, 0.0) for t, w in qw.items())
        else:
            dot = sum(w * qw.get(t, 0.0) for t, w in cw.items())
        if dot <= 0:
            continue
        score = dot / (qnorm * c["norm"])
        # Phrase boost: if a query bigram appears verbatim in the chunk text.
        if q_bigrams:
            low = c["text"].lower()
            hits = sum(1 for bg in q_bigrams if bg in low)
            if hits:
                score *= (1.0 + 0.25 * hits)
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    seen_docs = set()
    for score, c in scored[:k * 3]:
        # light diversity: prefer not to return 4 chunks from same doc
        if len([s for s in out if s["doc"] == c["doc"]]) >= 2:
            continue
        out.append({
            "score": round(score, 4),
            "doc": c["doc"],
            "topic": c["topic"],
            "category": c["category"],
            "text": c["text"],
        })
        seen_docs.add(c["doc"])
        if len(out) >= k:
            break
    return out


def _clean_snippet(text, max_chars=600):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        cut = text[:max_chars]
        last = cut.rfind(". ")
        text = cut[: last + 1] if last > 200 else cut + "…"
    return text


def kb_answer(query, index=None):
    """Build an answer purely from the knowledge base.

    Returns dict with:
      used_kb: bool   - whether KB had a usable answer
      confidence: 'high' | 'low' | 'none'
      answer: str     - composed educational answer (KB only) or ''
      snippets: list  - source snippets for grounding / display
      topics: list    - source topic labels
    """
    hits = search(query, index=index)
    if not hits or hits[0]["score"] < MIN_SCORE_ANSWER:
        return {"used_kb": False, "confidence": "none", "answer": "",
                "snippets": [], "topics": []}

    top = hits[0]["score"]
    confidence = "high" if top >= STRONG_SCORE else "low"

    snippets = []
    topics = []
    for h in hits:
        if h["score"] < MIN_SCORE_ANSWER * 0.6:
            continue
        snip = _clean_snippet(h["text"])
        if contains_brand(snip):
            continue
        snippets.append({"topic": h["topic"], "text": snip, "score": h["score"]})
        if h["topic"] not in topics:
            topics.append(h["topic"])

    if not snippets:
        return {"used_kb": False, "confidence": "none", "answer": "",
                "snippets": [], "topics": []}

    return {
        "used_kb": True,
        "confidence": confidence,
        "answer": "",          # composed downstream (optionally via AI rewrite)
        "snippets": snippets,
        "topics": topics,
    }


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is an emergency fund and how big should it be?"
    r = kb_answer(q)
    print("Q:", q)
    print("used_kb:", r["used_kb"], "| confidence:", r["confidence"], "| topics:", r["topics"])
    for s in r["snippets"]:
        print(f"\n[{s['topic']} | {s['score']}]\n{s['text'][:300]}")
