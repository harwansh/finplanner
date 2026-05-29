"""
SmartFinly Chatbot Lambda — /chat endpoint.

Flow for every user message:
  1. Guardrail: if the user is asking for buy/sell/product advice -> redirect
     (never give actionable advice). This check happens FIRST.
  2. Retrieve from the knowledge base (the sanitized PDFs).
  3. If the KB has a usable answer -> compose answer from KB. Optionally use
     Bedrock ONLY to rephrase the retrieved passages into clean prose (grounded,
     no new facts). If Bedrock is unavailable, return the cleaned passages.
  4. If the KB has NO usable answer -> fall back to Bedrock AI for a general
     educational explanation (still no advice, still brand-free).
  5. Final scrub: strip any brand names / advice phrases from the answer.

Hard rules enforced on every path: no brand names, no buy/sell guidance.
"""

import json
import os
import re

import boto3

from retrieval import kb_answer, load_index
from guardrails import (
    wants_advice, scrub_answer, answer_violates_advice,
    ADVICE_REDIRECT, DISCLAIMER, contains_brand,
)

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
AI_FALLBACK = os.environ.get("AI_FALLBACK", "true").lower() == "true"
AI_REWRITE_KB = os.environ.get("AI_REWRITE_KB", "true").lower() == "true"
MAX_MSG_LEN = int(os.environ.get("MAX_MSG_LEN", "1200"))

_bedrock = None


def _bedrock_client():
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    return _bedrock


RESPONSE_HEADERS = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}

SYSTEM_RULES = (
    "You are SmartFinly, an educational financial-literacy assistant for salaried "
    "individuals in India. Strict rules you must always follow:\n"
    "1. You provide EDUCATION ONLY. Never tell the user what to buy, sell, or hold. "
    "Never recommend a specific stock, mutual fund, scheme, insurer, or product. "
    "Never predict prices or promise returns.\n"
    "2. Never mention any coaching institute, training brand, certification mark, "
    "company brand name, or promotional website. Explain concepts generically.\n"
    "3. Be concise, clear, and neutral. Explain the concept and the trade-offs so the "
    "reader can decide for themselves.\n"
    "4. If a question needs personalised advice, say it is educational only and suggest "
    "consulting a SEBI-registered adviser."
)


def _resp(status, body):
    return {"statusCode": status, "headers": RESPONSE_HEADERS,
            "body": json.dumps(body, ensure_ascii=False, allow_nan=False)}


def _parse(event):
    method = (event.get("requestContext", {}).get("http", {}).get("method")
              or event.get("httpMethod") or "POST").upper()
    if method == "OPTIONS":
        return None
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        raise ValueError("Invalid JSON body.")
    if not isinstance(data, dict):
        raise ValueError("Body must be a JSON object.")
    return data


def _bedrock_chat(prompt, max_tokens=700, temperature=0.3):
    resp = _bedrock_client().converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_RULES}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature, "topP": 0.9},
    )
    return resp["output"]["message"]["content"][0]["text"]


def _compose_from_kb_locally(kb):
    """Fallback composition when Bedrock is unavailable: stitch the snippets."""
    parts = []
    for s in kb["snippets"][:3]:
        parts.append(s["text"])
    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 1100:
        text = text[:1100].rsplit(". ", 1)[0] + "."
    return text


def _rewrite_kb_with_ai(question, kb):
    context = "\n\n".join(f"- {s['text']}" for s in kb["snippets"][:4])
    prompt = (
        f"A learner asked: \"{question}\"\n\n"
        f"Using ONLY the reference material below, write a clear, concise educational "
        f"answer (120-200 words). Do not add facts that are not in the material. "
        f"Do not give buy/sell advice. Do not mention any brand or institute name.\n\n"
        f"Reference material:\n{context}"
    )
    return _bedrock_chat(prompt, max_tokens=500, temperature=0.2)


def _ai_general_answer(question):
    prompt = (
        f"A learner asked an educational personal-finance question: \"{question}\"\n"
        f"Give a clear, concise, neutral educational explanation (120-220 words). "
        f"Concept-level only. No buy/sell advice, no product names, no brand names."
    )
    return _bedrock_chat(prompt, max_tokens=600, temperature=0.35)


def handle_chat(data):
    message = (data.get("message") or data.get("question") or "").strip()
    if not message:
        raise ValueError("Please enter a question.")
    if len(message) > MAX_MSG_LEN:
        raise ValueError("Your question is too long. Please shorten it.")

    # --- Guardrail 1: refuse actionable advice up front.
    if wants_advice(message):
        return {
            "answer": ADVICE_REDIRECT,
            "source": "guardrail",
            "confidence": "n/a",
            "topics": [],
            "disclaimer": DISCLAIMER,
        }

    # --- Step 2/3: knowledge base first.
    kb = kb_answer(message)

    if kb["used_kb"]:
        answer = ""
        source = "knowledge_base"
        if AI_REWRITE_KB:
            try:
                answer = _rewrite_kb_with_ai(message, kb)
                source = "knowledge_base"  # grounded, AI only rephrased
            except Exception as exc:
                print("KB rewrite failed, using local compose:", exc.__class__.__name__)
                answer = ""
        if not answer:
            answer = _compose_from_kb_locally(kb)

        answer = scrub_answer(answer)
        if answer_violates_advice(answer) or contains_brand(answer):
            # Safety net: never emit advice or brand. Fall back to neutral compose.
            answer = scrub_answer(_compose_from_kb_locally(kb))
        return {
            "answer": answer,
            "source": source,
            "confidence": kb["confidence"],
            "topics": kb["topics"],
            "disclaimer": DISCLAIMER,
        }

    # --- Step 4: AI fallback (no KB match).
    if AI_FALLBACK:
        try:
            answer = scrub_answer(_ai_general_answer(message))
            if answer and not answer_violates_advice(answer) and not contains_brand(answer):
                return {
                    "answer": answer,
                    "source": "ai",
                    "confidence": "ai",
                    "topics": [],
                    "disclaimer": DISCLAIMER,
                }
        except Exception as exc:
            print("AI fallback failed:", exc.__class__.__name__, str(exc)[:200])

    # --- Step 5: graceful no-answer.
    return {
        "answer": ("I couldn't find this in my educational material, and the AI helper "
                   "isn't available right now. Try rephrasing, or ask about topics like "
                   "budgeting, emergency funds, insurance, tax basics, investing concepts, "
                   "retirement planning, or estate planning."),
        "source": "none",
        "confidence": "none",
        "topics": [],
        "disclaimer": DISCLAIMER,
    }


def handler(event, context):
    try:
        data = _parse(event)
        if data is None:  # OPTIONS preflight
            return {"statusCode": 204, "headers": RESPONSE_HEADERS, "body": ""}
        return _resp(200, handle_chat(data))
    except ValueError as exc:
        return _resp(400, {"error": str(exc), "code": "INPUT_ERROR"})
    except Exception as exc:
        print("Chatbot error:", exc.__class__.__name__, str(exc)[:200])
        return _resp(500, {"error": "Something went wrong. Please try again.",
                           "code": "INTERNAL_ERROR"})


# Lambda entry alias
def lambda_handler(event, context):
    return handler(event, context)
