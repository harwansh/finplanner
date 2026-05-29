"""SmartFinly Lambda.

This handler supports the chatbot site request shape and keeps the same Bedrock settings
used by the earlier app: amazon.nova-pro-v1:0 in us-east-1 unless env vars override it.
"""

import json
import os
import re

import boto3

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type,authorization",
    "Access-Control-Allow-Methods": "OPTIONS,POST",
}

SENSITIVE_RE = re.compile(r"(aadhaar|aadhar|pan|otp|password|passcode|secret|token|bank.?account|account.?number|ifsc|upi|vpa|\b[A-Z]{5}[0-9]{4}[A-Z]\b|\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b)", re.I)
ADVICE_RE = re.compile(r"(which\s+(stock|fund|share)|best\s+(stock|fund|mutual fund|sip|share)|should\s+i\s+(buy|sell)|price\s+prediction|multibagger|guaranteed\s+return)", re.I)

KNOWLEDGE = [
    {
        "title": "SIP and disciplined investing",
        "keywords": ["sip", "systematic investment", "monthly investment"],
        "text": "A Systematic Investment Plan is a method of investing a fixed amount at regular intervals. It supports discipline and reduces the pressure of timing the market. Outcomes depend on the asset, time horizon, cost, risk and investor behaviour."
    },
    {
        "title": "EMI affordability",
        "keywords": ["emi", "loan", "afford", "debt", "income"],
        "text": "EMI affordability should be judged from net take-home income after rent, essentials, existing EMIs, insurance, dependents and emergency-fund savings. Many education frameworks treat total EMI above 30 to 40 percent of take-home income as potentially stressful, depending on job stability and family obligations."
    },
    {
        "title": "Emergency fund",
        "keywords": ["emergency", "emergency fund", "buffer"],
        "text": "An emergency fund is money kept aside for unexpected events such as job loss, medical expenses, urgent travel or repairs. It is usually kept liquid and relatively safe before taking higher investment risk."
    },
    {
        "title": "Health insurance",
        "keywords": ["health", "medical", "insurance", "hospital"],
        "text": "Health insurance is protection against large medical costs. Cover needs depend on city, age, family size, employer cover, existing illnesses, dependents, hospital costs and emergency savings. Employer cover alone may not be enough because it can end when employment changes."
    },
    {
        "title": "Compounding",
        "keywords": ["compound", "compounding", "return"],
        "text": "Compounding means earning returns on earlier returns. Time, reinvestment and consistency are important. Compounding can be powerful over long periods, but it does not guarantee returns because market risk, cost and withdrawals matter."
    },
    {
        "title": "Retirement planning",
        "keywords": ["retirement", "retire", "corpus", "inflation", "longevity"],
        "text": "Retirement planning considers expenses, inflation, longevity, healthcare costs, withdrawal strategy and asset allocation. A plan should consider both essential needs and lifestyle goals, and should not rely only on fixed income if inflation protection is required."
    },
    {
        "title": "Tax planning",
        "keywords": ["tax", "80c", "80d", "hra", "nps", "deduction"],
        "text": "Tax planning compares available deductions, exemptions, income composition and old-versus-new tax regime outcomes. It should be based on actual income and eligible deductions, not only on generic tips."
    },
]

SYSTEM_PROMPT = """You are SmartFinly, a production finance education chatbot for Indian users.
Write clear, polished, practical answers in simple language.
Use the provided knowledge context when it is relevant, but do not mention sources or internal retrieval.
Do not recommend specific stocks, mutual funds, insurance policies, brokers, lenders or products.
Do not give buy/sell calls, timing advice, guaranteed returns, legal advice, tax filing advice or regulated advice.
If more personal details are needed, ask for the minimum relevant details, such as income, expense, EMI, family size or time horizon.
Keep answers concise and useful.
"""


def _response(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, ensure_ascii=False)}


def _parse_event(event):
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
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _extract_message(payload):
    for key in ("message", "question", "query", "prompt"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    messages = payload.get("messages")
    if isinstance(messages, list) and messages:
        last = messages[-1]
        if isinstance(last, dict):
            value = last.get("content") or last.get("text")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _find_context(question):
    q = question.lower()
    matches = []
    for item in KNOWLEDGE:
        score = sum(1 for keyword in item["keywords"] if keyword in q)
        if score:
            matches.append((score, item))
    matches.sort(key=lambda row: row[0], reverse=True)
    return "\n\n".join(f"{item['title']}: {item['text']}" for _, item in matches[:3])


def _bedrock_answer(question, context):
    context_block = context or "No direct knowledge-base match was found. Give a general education-only answer."
    user_prompt = f"Question: {question}\n\nKnowledge context:\n{context_block}\n\nAnswer as SmartFinly."
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 900, "temperature": 0.2},
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def _safe_answer(question):
    q = question.lower()
    if "sip" in q or "systematic" in q:
        return "A SIP is a way to invest a fixed amount regularly, usually monthly. It helps build discipline and reduces the pressure of timing the market. The right amount depends on your goal, time horizon, risk comfort and monthly surplus. This is education only, not a product recommendation."
    if "emi" in q or "loan" in q or "afford" in q:
        return "Think about EMI affordability from take-home income, not gross salary. First subtract rent, essentials, existing EMIs, insurance, dependents and emergency-fund savings. As a learning rule, many households try to keep total EMIs around 30% to 40% of take-home income or lower, but the safe level depends on job stability and family obligations."
    if "emergency" in q:
        return "An emergency fund is money kept aside for unexpected events like job loss, medical costs or urgent repairs. Many planning frameworks suggest keeping several months of essential expenses in liquid and relatively safe places before taking higher investment risk."
    if "health" in q or "insurance" in q:
        return "Health insurance is protection against large medical bills. The right cover depends on city, age, family size, employer cover, existing illnesses, dependents and hospital costs. Employer cover alone may not be enough because it can end when the job changes."
    if "compound" in q:
        return "Compounding means earning returns on earlier returns. Time is the biggest driver: the longer money stays invested and reinvested, the more compounding can help. It is powerful, but not guaranteed because market risk, costs and withdrawals affect outcomes."
    return "I can explain finance topics in education-only terms. Ask about SIP, EMI, emergency fund, insurance, tax planning, retirement or compounding."


def _chat_response(question):
    if SENSITIVE_RE.search(question):
        return {"answer": "Please do not share PAN, Aadhaar, OTP, passwords, bank details or other sensitive identifiers. Ask the question without personal data.", "source": "guardrail"}
    if ADVICE_RE.search(question):
        return {"answer": "I cannot recommend buying, selling, timing or choosing a specific financial product. I can explain the concept, risks and evaluation framework in education-only terms.", "source": "guardrail"}
    context = _find_context(question)
    try:
        answer = _bedrock_answer(question, context)
        if answer:
            return {"answer": answer, "source": "knowledge_plus_ai" if context else "ai_fallback"}
    except Exception as exc:
        print("Bedrock chat failed:", exc.__class__.__name__, str(exc))
    return {"answer": _safe_answer(question), "source": "safe_fallback"}


def lambda_handler(event, context):
    try:
        payload = _parse_event(event or {})
        if payload == "__OPTIONS__":
            return _response(204, {})
        question = _extract_message(payload)
        if question:
            return _response(200, _chat_response(question))
        return _response(400, {"answer": "Please ask a finance education question to get started.", "error": "Missing message."})
    except Exception as exc:
        print("Unhandled SmartFinly error:", exc.__class__.__name__, str(exc))
        return _response(500, {"answer": "I am having trouble preparing an answer right now. Please try again in a moment.", "error": "Internal error."})


handler = lambda_handler
