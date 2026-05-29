import os

DEFAULT_MODEL_ID = "amazon.nova-pro-v1:0"
DEFAULT_REGION = "us-east-1"

SYSTEM_PROMPT = """You are SmartFinly, an education-only finance chatbot for Indian users.

Write like a helpful chatbot, not like copied study notes.
Use simple language.
Do not recommend a specific stock, mutual fund, insurance policy, broker, loan provider, or financial product.
Do not give buy or sell calls, timing advice, price predictions, guaranteed returns, legal advice, tax filing advice, or regulated advice.
When context is provided, answer from the context and say when the context is insufficient.
"""


def _safe_generic_answer(question: str) -> str:
    return (
        "I could not find a strong match in the PDF knowledge base. "
        "In education-only terms, review cash flow, risk, time horizon, liquidity, taxes, insurance, debt obligations, and family constraints. "
        "This is general learning, not personal financial advice."
    )


def is_bedrock_enabled() -> bool:
    return os.environ.get("ENABLE_BEDROCK_FALLBACK", "false").lower() == "true"


def _converse(user_text: str, max_tokens: int = 900) -> str:
    import boto3

    model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    region = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", DEFAULT_REGION))
    client = boto3.client("bedrock-runtime", region_name=region)
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def answer_from_pdf_context(question: str, matches: list[dict]) -> str:
    if not is_bedrock_enabled() or not matches:
        return ""

    context_parts = []
    for index, match in enumerate(matches[:4], start=1):
        title = match.get("title") or match.get("source") or f"Source {index}"
        text = str(match.get("text") or "")[:1800]
        context_parts.append(f"Source {index}: {title}\n{text}")

    prompt = (
        "Answer the user's question using only the PDF context below. "
        "Do not paste raw fragments. Write a clear, concise chatbot answer with practical explanation. "
        "If the PDF context is not enough, say that the PDFs do not contain enough detail and explain only at a high level.\n\n"
        f"Question: {question}\n\nPDF context:\n" + "\n\n".join(context_parts)
    )

    try:
        return _converse(prompt, max_tokens=800)
    except Exception:
        return ""


def answer_with_ai_fallback(question: str) -> str:
    if not is_bedrock_enabled():
        return _safe_generic_answer(question)

    prompt = (
        "The PDF knowledge base did not have a strong match for this question. "
        "Give a general education-only answer. Keep it concise and practical.\n\n"
        f"Question: {question}"
    )

    try:
        return _converse(prompt, max_tokens=900) or _safe_generic_answer(question)
    except Exception as exc:
        return f"AI fallback is configured but failed: {str(exc)}"
