import json
import os


def _safe_generic_answer(question: str) -> str:
    return (
        "I could not find a strong match in the uploaded knowledge base. "
        "In education-only terms, this topic should be understood by looking at cash flow, risk, time horizon, "
        "liquidity needs, taxes, insurance, debt obligations, and personal constraints. "
        "Please treat this as general learning, not investment advice."
    )


def answer_with_ai_fallback(question: str) -> str:
    """Return an education-only AI fallback answer.

    In AWS Lambda, set ENABLE_BEDROCK_FALLBACK=true and BEDROCK_MODEL_ID to enable Bedrock.
    Without those env vars, this deliberately returns a deterministic safe answer for tests and local runs.
    """
    if os.environ.get("ENABLE_BEDROCK_FALLBACK", "false").lower() != "true":
        return _safe_generic_answer(question)

    model_id = os.environ.get("BEDROCK_MODEL_ID")
    if not model_id:
        return _safe_generic_answer(question)

    try:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1")))
        prompt = (
            "You are SmartFinly, an education-only finance assistant for Indian users. "
            "Do not provide buy, sell, timing, stock, fund, tax filing, legal, insurance, or product-selection advice. "
            "Explain the concept in simple language and include a brief education-only disclaimer.\n\n"
            f"Question: {question}"
        )

        body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 450, "temperature": 0.2},
        }
        response = client.invoke_model(modelId=model_id, body=json.dumps(body))
        payload = json.loads(response["body"].read())
        message = payload.get("output", {}).get("message", {})
        parts = message.get("content", [])
        text = " ".join(part.get("text", "") for part in parts).strip()
        return text or _safe_generic_answer(question)
    except Exception:
        return _safe_generic_answer(question)
