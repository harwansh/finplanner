import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from chat_handler import answer_question, handler
from guardrails import contains_sensitive_data, is_advice_request


def test_blocks_buy_sell_advice():
    response = answer_question("Should I buy this stock?")
    assert response["blocked"] is True
    assert response["source"] == "guardrail"


def test_blocks_product_selection():
    assert is_advice_request("Which mutual fund should I invest in?")


def test_blocks_sensitive_data():
    assert contains_sensitive_data("My PAN is ABCDE1234F")


def test_answers_known_topic():
    response = answer_question("What is SIP?")
    assert response["blocked"] is False
    assert response["source"] == "demo_knowledge_base"
    assert "SIP" in response["answer"]


def test_handler_rejects_invalid_json():
    response = handler({"body": "{"}, None)
    assert response["statusCode"] == 400


def test_handler_returns_json():
    response = handler({"body": json.dumps({"message": "Explain compounding"})}, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["blocked"] is False
