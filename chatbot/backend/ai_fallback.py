import os

DEFAULT_MODEL_ID = "amazon.nova-pro-v1:0"
DEFAULT_REGION = "us-east-1"

SYSTEM_PROMPT = """You are SmartFinly, an education-only finance assistant for Indian users.

Rules:
- Use simple language.
- Do not recommend a specific stock, mutual fund, insurance policy, broker, loan provider, or financial product.
- Do not give buy, sell, timing, price prediction, guaranteed return, legal, tax filing, or regulated advice.
- Explain concepts, frameworks, trade-offs, risks, and questions the user should consider.
- Keep answers concise and practical.
"""


def _safe_generic_answer(question: str) -> str:
    return (
        "I could not find a strong match in the PDF knowledge base. "
        "In education-only terms, review cash flow, risk, time horizon, liquidity, taxes, insurance, debt obligations, and family constraints. "
        "This is general learning, not personal financial advice."
    )


def answer_with_ai_fallback(question: str) -> str:
    """Use the old working Bedrock Converse pattern with Amazon Nova Pro.

    Required Lambda env vars:
    - ENABLE_BEDROCK_FALLBACK=true
    - BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
    - BEDROCK_REGION=us-east-1
    """
    if os.environ.get("ENABLE_BEDROCK_FALLBACK", "false").lower() != "true":
        return _safe_generic_answer(question)

    try:
        import boto3

        model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
        region = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", DEFAULT_REGION))
        client = boto3.client("bedrock-runtime", region_name=region)

        response = client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": question}]}],
            system=[{"text": SYSTEM_PROMPT}],
            inferenceConfig={"maxTokens": 900, "temperature": 0.2},
        )
        text = response["output"]["message"]["content"][0]["text"].strip()
        return text or _safe_generic_answer(question)
    except Exception as exc:
        return f"AI fallback is configured but failed: {str(exc)}"
