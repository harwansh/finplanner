"""
Output guardrails for the SmartFinly chatbot.

Two non-negotiable rules enforced here:
1. NO buy/sell/hold or product-recommendation guidance of any kind.
2. NO third-party brand / coaching-institute / certification-mark names.

Both are applied to EVERY outgoing answer, regardless of whether the answer
came from the knowledge base or the AI fallback.
"""

import re

from sanitize import contains_brand, sanitize_text

# Phrases that indicate the user is asking for actionable buy/sell advice.
_ADVICE_REQUEST_RE = re.compile(
    r"\b(should i (buy|sell|invest|put|hold)|which (stock|fund|mutual fund|scheme|share|policy) "
    r"should i|what should i (buy|sell|invest)|recommend (me )?(a |some )?(stock|fund|share)|"
    r"best (stock|mutual fund|fund|share|scheme) to (buy|invest)|"
    r"is .* a good (buy|investment|stock)|will .* (go up|rise|crash|fall)|"
    r"tell me what to (buy|invest)|where should i invest my)\b",
    re.I,
)

# Tokens in OUR OWN output that would constitute prohibited advice.
_OUTPUT_ADVICE_RE = re.compile(
    r"\b(you should (buy|sell|invest in)|i recommend (buying|selling)|"
    r"buy this|sell this|i suggest you (buy|sell|invest)|"
    r"the best stock is|guaranteed return|will definitely (rise|grow|go up))\b",
    re.I,
)

ADVICE_REDIRECT = (
    "I'm an educational assistant, so I can't tell you what to buy, sell, or hold, "
    "or recommend any specific stock, fund, or product. What I can do is explain the "
    "underlying concept so you can make your own informed decision. "
    "For personalised, regulated advice, please consult a SEBI-registered investment adviser. "
    "Would you like me to explain the relevant concept instead?"
)


def wants_advice(text):
    return bool(_ADVICE_REQUEST_RE.search(text or ""))


def scrub_answer(text):
    """Final pass over any answer before it leaves the system."""
    if not text:
        return text
    # Strip brand names / marks defensively (AI could echo them).
    text = sanitize_text(text)
    return text.strip()


def answer_violates_advice(text):
    return bool(_OUTPUT_ADVICE_RE.search(text or ""))


DISCLAIMER = (
    "Educational information only — not investment, tax, or legal advice, and not a "
    "recommendation to buy or sell anything. Consult a qualified, registered professional "
    "for decisions specific to you."
)
