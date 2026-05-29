import re

ADVICE_PATTERNS = [
    re.compile(r"should\s+i\s+(buy|sell|invest)", re.I),
    re.compile(r"\b(best|top)\s+(stock|fund|mutual fund|sip|share)", re.I),
    re.compile(r"price\s+prediction", re.I),
    re.compile(r"guaranteed\s+return", re.I),
    re.compile(r"multibagger", re.I),
    re.compile(r"which\s+(stock|fund|share)", re.I),
]

SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{12}\b"),
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    re.compile(r"\botp\b", re.I),
    re.compile(r"password", re.I),
]


def is_advice_request(message: str) -> bool:
    return any(pattern.search(message or "") for pattern in ADVICE_PATTERNS)


def contains_sensitive_data(message: str) -> bool:
    return any(pattern.search(message or "") for pattern in SENSITIVE_PATTERNS)


def blocked_answer() -> str:
    return (
        "I cannot recommend buying, selling, timing, or choosing a specific stock, fund, "
        "or product. I can explain the concept, risks, and evaluation framework in "
        "education-only terms. For personal advice, consult a SEBI-registered investment adviser."
    )
