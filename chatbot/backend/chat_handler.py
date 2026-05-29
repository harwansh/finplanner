import json
from ai_fallback import answer_with_ai_fallback
from guardrails import blocked_answer, contains_sensitive_data, is_advice_request
from retrieval import build_grounded_answer, search_knowledge_base


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "access-control-allow-origin": "*",
            "access-control-allow-headers": "content-type,authorization",
            "access-control-allow-methods": "OPTIONS,POST",
        },
        "body": json.dumps(payload),
    }


def answer_question(message):
    message = str(message or "").strip()
    if not message:
        return {"blocked": False, "source": "validation", "answer": "Please ask a finance education question to get started.", "citations": []}

    if contains_sensitive_data(message):
        return {"blocked": True, "source": "guardrail", "answer": "Please do not share PAN, Aadhaar, OTPs, passwords, bank details, or other sensitive identifiers. Ask the question without personal identifiers.", "citations": []}

    if is_advice_request(message):
        return {"blocked": True, "source": "guardrail", "answer": blocked_answer(), "citations": []}

    matches = search_knowledge_base(message)
    if matches:
        return {
            "blocked": False,
            "source": "pdf_knowledge_base",
            "answer": build_grounded_answer(message, matches),
            "citations": [
                {
                    "id": match.get("id"),
                    "title": match.get("title"),
                    "source": match.get("source"),
                    "score": match.get("score"),
                    "text": match.get("text", "")[:500],
                }
                for match in matches
            ],
        }

    return {
        "blocked": False,
        "source": "ai_fallback",
        "answer": answer_with_ai_fallback(message),
        "citations": [],
    }


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _response(204, {})

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    return _response(200, answer_question(body.get("message", "")))
