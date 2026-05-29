import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from chat_handler import answer_question, handler
from guardrails import contains_sensitive_data, is_advice_request
from retrieval import search_knowledge_base


def test_blocks_buy_sell_advice():
    response = answer_question("Should I buy this stock?")
    assert response["blocked"] is True
    assert response["source"] == "guardrail"


def test_blocks_product_selection():
    assert is_advice_request("Which mutual fund should I invest in?")


def test_blocks_sensitive_data():
    assert contains_sensitive_data("My PAN is ABCDE1234F")


def test_retrieval_finds_pdf_index_topic():
    matches = search_knowledge_base("How much EMI can I manage from income?")
    assert matches
    assert matches[0]["title"] == "EMI and Income Capacity"


def test_answers_known_topic_from_pdf_index():
    response = answer_question("What is SIP?")
    assert response["blocked"] is False
    assert response["source"] == "pdf_knowledge_base"
    assert response["citations"]
    assert "SIP" in response["answer"] or "Systematic Investment Plan" in response["answer"]


def test_unknown_topic_uses_ai_fallback():
    response = answer_question("Explain a family budget envelope method")
    assert response["blocked"] is False
    assert response["source"] in {"ai_fallback", "pdf_knowledge_base"}


def test_handler_rejects_invalid_json():
    response = handler({"body": "{"}, None)
    assert response["statusCode"] == 400


def test_handler_returns_json():
    response = handler({"body": json.dumps({"message": "Explain compounding"})}, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["blocked"] is False
