import json
from guardrails import blocked_answer, contains_sensitive_data, is_advice_request

TOPICS = [
    {
        "keywords": ["sip", "systematic investment plan"],
        "title": "Systematic Investment Plan",
        "answer": "A SIP is a way to invest a fixed amount at regular intervals. It can build discipline and reduce the stress of timing the market. The key ideas are consistency, suitable time horizon, and risk awareness.",
    },
    {
        "keywords": ["emergency fund", "emergency"],
        "title": "Emergency fund",
        "answer": "An emergency fund is money kept aside for unexpected needs such as job loss, medical costs, urgent travel, or repairs. Many education frameworks discuss keeping several months of essential expenses in safe and liquid instruments.",
    },
    {
        "keywords": ["compounding", "compound"],
        "title": "Compounding",
        "answer": "Compounding means earning returns on earlier returns. Time, consistency, and reinvestment are the main drivers. Small regular contributions can grow meaningfully over long periods, but returns are not guaranteed.",
    },
    {
        "keywords": ["diversification", "diversify"],
        "title": "Diversification",
        "answer": "Diversification means spreading money across assets, sectors, or instruments so one bad outcome does not dominate the entire plan. It reduces concentration risk but does not remove all risk.",
    },
    {
        "keywords": ["risk tolerance", "risk capacity", "risk"],
        "title": "Risk capacity",
        "answer": "Risk capacity depends on income stability, dependents, debt, emergency fund, goal horizon, and ability to handle losses. It is different from risk preference, which is how comfortable someone feels with volatility.",
    },
]


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

    lower = message.lower()
    for topic in TOPICS:
        if any(keyword in lower for keyword in topic["keywords"]):
            return {
                "blocked": False,
                "source": "demo_knowledge_base",
                "answer": topic["answer"] + " This is education-only information, not investment advice.",
                "citations": [{"title": topic["title"], "text": "Demo knowledge base topic match"}],
            }

    return {
        "blocked": False,
        "source": "ai_fallback_ready",
        "answer": "I can help explain finance concepts in simple language. Try asking about SIPs, emergency funds, compounding, diversification, insurance, taxation, or risk capacity. I will keep the response educational and avoid product recommendations.",
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
