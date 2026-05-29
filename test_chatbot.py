"""Tests for the SmartFinly chatbot backend: brand-stripping, advice guardrails, routing."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import sanitize
import guardrails
import retrieval
import chat_handler


def _ask(message, monkeypatch_bedrock=None):
    if monkeypatch_bedrock is not None:
        chat_handler._bedrock_chat = monkeypatch_bedrock
    ev = {"body": json.dumps({"message": message}),
          "requestContext": {"http": {"method": "POST"}}}
    out = chat_handler.handler(ev, None)
    return json.loads(out["body"]), out["statusCode"]


# ---------- Brand / mark stripping ----------
def test_sanitize_strips_proschool():
    assert "proschool" not in sanitize.sanitize_text("Visit www.proschoolonline.com today").lower()

def test_sanitize_strips_fragmented_watermark():
    assert "www" not in sanitize.sanitize_text("Planning www. .c om Intro").lower()

def test_sanitize_neutralises_marks():
    out = sanitize.sanitize_text("This CFA CFP course")
    assert "cfa" not in out.lower() and "cfp" not in out.lower()

def test_sanitize_keeps_real_words():
    out = sanitize.sanitize_text("The company computes compound interest on common stock")
    for w in ["company", "computes", "compound", "common"]:
        assert w in out

def test_contains_brand_detector():
    assert sanitize.contains_brand("proschool material")
    assert not sanitize.contains_brand("emergency fund basics")


# ---------- Advice guardrails ----------
def test_wants_advice_buy():
    assert guardrails.wants_advice("Should I buy Reliance stock?")

def test_wants_advice_which_fund():
    assert guardrails.wants_advice("Which mutual fund should I invest in?")

def test_not_advice_concept():
    assert not guardrails.wants_advice("What is a mutual fund?")

def test_handler_refuses_advice():
    data, status = _ask("Should I sell my shares now?")
    assert status == 200
    assert data["source"] == "guardrail"
    assert "buy" in data["answer"].lower()


# ---------- Routing ----------
def test_kb_hit_for_known_topic(monkeypatch=None):
    os.environ["AI_REWRITE_KB"] = "false"
    os.environ["AI_FALLBACK"] = "false"
    data, status = _ask("Explain term and whole life insurance")
    assert status == 200
    assert data["source"] == "knowledge_base"
    assert data["topics"]

def test_offtopic_no_kb_no_ai():
    os.environ["AI_REWRITE_KB"] = "false"
    os.environ["AI_FALLBACK"] = "false"
    data, status = _ask("How do I bake sourdough bread?")
    assert data["source"] in ("none", "ai")

def test_empty_message_rejected():
    data, status = _ask("   ")
    assert status == 400

def test_disclaimer_always_present():
    os.environ["AI_REWRITE_KB"] = "false"
    os.environ["AI_FALLBACK"] = "false"
    data, _ = _ask("What is an emergency fund?")
    assert data["disclaimer"]
    data2, _ = _ask("Should I buy gold?")
    assert data2["disclaimer"]


# ---------- Answer never leaks brand / advice ----------
def test_answer_scrubbed_of_brand():
    # Simulate an AI that wrongly echoes a brand; scrub must remove it.
    os.environ["AI_REWRITE_KB"] = "true"
    os.environ["AI_FALLBACK"] = "false"
    def evil(prompt, **kw):
        return "Emergency funds matter. Learn more at www.proschoolonline.com today."
    data, _ = _ask("What is an emergency fund?", monkeypatch_bedrock=evil)
    assert "proschool" not in data["answer"].lower()
