"""
Brand-name and PII sanitisation for SmartFinly knowledge ingestion.

Hard rule: no third-party brand names, coaching-institute names, certification
marks, or promotional URLs may ever appear in stored knowledge or in answers.
This module is the single source of truth for that cleaning so it is applied
identically at ingest time and (defensively) at answer time.
"""

import re

# Phrases / tokens that must be scrubbed from any extracted text.
# Kept deliberately broad and case-insensitive. Order matters (longer first).
_BRAND_PATTERNS = [
    r"www\.[a-z0-9\-]*proschool[a-z0-9\-]*\.com",
    r"[a-z0-9\-]*proschool[a-z0-9\-]*online\.com",
    r"\bpro\s*school\s*online\b",
    r"\bproschool\b",
    r"\bims\s*proschool\b",
    r"\bims\b(?=\s*(pro|learning|institute|academy)?)",  # IMS as an institute brand
    r"\bnj\s+gurukul\b",
    r"\bnism\s+study\s+material\b",  # promotional study-material tags only
]

# Certification / designation marks to neutralise so the bot stays brand-free.
# We replace with a neutral phrase rather than deleting, to keep sentences readable.
_MARK_REPLACEMENTS = [
    (r"\bC\s*F\s*A\b", "the investment-analysis curriculum"),
    (r"\bC\s*F\s*P\b", "the financial-planning curriculum"),
    (r"\bCWM\b", "the wealth-management curriculum"),
    (r"\bCERTIFIED FINANCIAL PLANNER\b", "the financial-planning curriculum"),
    (r"\bChartered Financial Analyst\b", "the investment-analysis curriculum"),
]

# Stray promotional / watermark lines that add no educational value.
_NOISE_LINES = [
    r"^\s*page\s*\d+\s*of\s*\d+\s*$",
    r"^\s*\d+\s*$",
    r"^\s*copyright.*$",
    r"^\s*all rights reserved.*$",
]

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
# Fragmented watermark debris left after PDF extraction splits a URL across
# spaces/linebreaks, e.g. "www. .c om", "w w w .", ". c o m".
_URL_FRAGMENT_RE = re.compile(
    r"w\s*w\s*w\s*\.[^a-zA-Z0-9]*|\.?\s*c\s*o\s*m\b|\.\s*c\s*o\s*m|"
    r"\bw\s*w\s*w\b|\bhttp\s*s?\b",
    re.I,
)
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")
_MULTINEWLINE_RE = re.compile(r"\n{3,}")
# Private-use-area glyphs (e.g. \ue25f bullets) — BMP private use block only.
_PUA_RE = re.compile(r"[\ue000-\uf8ff]")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _compile(patterns, flags=re.I):
    return [re.compile(p, flags) for p in patterns]


_BRAND_RE = _compile(_BRAND_PATTERNS)
_MARK_RE = [(re.compile(p, re.I), r) for p, r in _MARK_REPLACEMENTS]
_NOISE_RE = _compile(_NOISE_LINES, re.I | re.M)


def sanitize_text(text: str) -> str:
    """Remove brand names, promo URLs, designation marks and watermark noise."""
    if not text:
        return ""

    # 0. Strip private-use-area glyphs (decorative bullets) and control chars.
    text = _PUA_RE.sub(" ", text)
    text = _CTRL_RE.sub(" ", text)

    # 1. Neutralise certification marks first (before generic URL strip).
    for rx, repl in _MARK_RE:
        text = rx.sub(repl, text)

    # 2. Remove explicit brand patterns.
    for rx in _BRAND_RE:
        text = rx.sub(" ", text)

    # 3. Remove any remaining URLs (watermarks are usually URLs).
    text = _URL_RE.sub(" ", text)
    # 3b. Remove fragmented watermark debris from PDF extraction.
    text = _URL_FRAGMENT_RE.sub(" ", text)

    # 4. Drop noise lines.
    for rx in _NOISE_RE:
        text = rx.sub("", text)

    # 5. Tidy whitespace.
    text = _MULTISPACE_RE.sub(" ", text)
    text = _MULTINEWLINE_RE.sub("\n\n", text)

    return text.strip()


def contains_brand(text: str) -> bool:
    """Defensive check used before any answer leaves the system."""
    if not text:
        return False
    low = text.lower()
    if "proschool" in low or "gurukul" in low:
        return True
    for rx in _BRAND_RE:
        if rx.search(text):
            return True
    return False


# Neutral, topic-based names for the source files (no brand / cert marks).
# Maps original filename -> (clean_filename, human_topic, category).
FILE_TOPIC_MAP = {
    "5.+Retirementplanning_ifp.pdf": (
        "retirement-planning.pdf", "Retirement Planning", "retirement"),
    "CFP+IPS+PFM.pdf": (
        "personal-finance-management.pdf", "Personal Finance Management", "personal-finance"),
    "CFP+IPS+Regulatory.pdf": (
        "financial-regulation-and-intermediaries.pdf",
        "Financial Regulation & Intermediaries", "regulation"),
    "CFP+estate+lecture+1.pdf": (
        "estate-planning-basics.pdf", "Estate Planning - Basics", "estate"),
    "CFP+estate+lecture+2.pdf": (
        "estate-planning-succession-laws.pdf", "Estate Planning - Succession Laws", "estate"),
    "CFP+estate+lecture+3.pdf": (
        "estate-planning-distribution-vehicles.pdf",
        "Estate Planning - Distribution Vehicles", "estate"),
    "CFP+ipam+global+lec+1-4.pdf": (
        "investments-asset-classes-and-returns.pdf",
        "Investments - Asset Classes & Returns", "investments"),
    "CFP+ipam+indian+mkts.pdf": (
        "indian-securities-markets.pdf", "Indian Securities Markets", "investments"),
    "CFP+risk+Lecture+1.pdf": (
        "risk-and-insurance-fundamentals.pdf",
        "Risk Management & Insurance - Fundamentals", "insurance"),
    "CFP+risk+Lecture+2.pdf": (
        "life-insurance.pdf", "Life Insurance", "insurance"),
    "CFP+risk+lecture+3.pdf": (
        "general-insurance.pdf", "General Insurance", "insurance"),
    "CFP+risk+lecture+4.pdf": (
        "health-insurance.pdf", "Health Insurance", "insurance"),
    "Tax+Planning.pdf": (
        "tax-planning.pdf", "Tax Planning", "tax"),
}
