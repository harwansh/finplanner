"""POST /analyze - returns net worth (deterministic) + ranked financial goals (Bedrock)."""
import json
import os
import sys
from decimal import Decimal

import boto3

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.utils import respond, get_user_id  # noqa: E402

TABLE_NAME = os.environ["TABLE_NAME"]
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

ddb = boto3.resource("dynamodb")
table = ddb.Table(TABLE_NAME)
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)


# ---------------- deterministic math ----------------
def _num(x) -> float:
    if x is None:
        return 0.0
    if isinstance(x, Decimal):
        return float(x)
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def compute_networth(profile: dict) -> dict:
    assets = profile.get("assets", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}
    income = profile.get("income", {}) or {}
    expenses = profile.get("expenses", {}) or {}

    total_assets = sum(_num(v) for v in assets.values())
    total_liabilities = sum(_num(v) for v in liabilities.values())
    net_worth = total_assets - total_liabilities

    monthly_income = _num(income.get("monthlyAfterTax")) + _num(income.get("otherMonthly"))
    monthly_expenses = (
        _num(expenses.get("fixed"))
        + _num(expenses.get("variable"))
        + _num(expenses.get("annual")) / 12.0
    )
    monthly_surplus = monthly_income - monthly_expenses
    savings_rate = (monthly_surplus / monthly_income * 100.0) if monthly_income > 0 else 0.0
    emergency_months = (
        _num(assets.get("savings")) / monthly_expenses if monthly_expenses > 0 else 0.0
    )

    return {
        "totalAssets": round(total_assets, 2),
        "totalLiabilities": round(total_liabilities, 2),
        "netWorth": round(net_worth, 2),
        "monthlyIncome": round(monthly_income, 2),
        "monthlyExpenses": round(monthly_expenses, 2),
        "monthlySurplus": round(monthly_surplus, 2),
        "savingsRatePct": round(savings_rate, 1),
        "emergencyFundMonths": round(emergency_months, 1),
    }


# ---------------- Bedrock-driven goals ----------------
SYSTEM_PROMPT = """You are a careful, conservative personal-finance planner.
You will receive a user's profile JSON and a computed financial summary.
Generate exactly 15 personalized financial goals, organized into three buckets:
  - "mustHave": 5 goals (non-negotiable foundations: emergency fund, insurance, high-interest debt, etc.)
  - "goodToHave": 5 goals (medium-term: retirement on track, kids' education, home, etc.)
  - "optional": 5 goals (lifestyle / wealth: travel fund, second home, early retirement, etc.)

For EACH goal, return:
  - title: short name (max 60 chars)
  - rationale: 1-2 sentence reason tailored to THIS user
  - targetAmount: numeric estimate in user's currency (use country to infer currency)
  - timelineMonths: integer
  - monthlyContribution: integer estimate
  - priority: 1 (highest) within its bucket

Rules:
- Be realistic given the user's monthly surplus. Do not propose contributions exceeding it in total for mustHave.
- If the user has high-interest debt (credit card), prioritize paying it before investing.
- Respect risk tolerance, dependents, marital status, and any ethical/religious constraints.
- Output ONLY valid JSON, no prose, no markdown fences. Schema:
{"mustHave":[...5...],"goodToHave":[...5...],"optional":[...5...]}
"""


def _profile_to_decimal_safe(obj):
    """Convert Decimals back to plain numbers for JSON serialization to Bedrock."""
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    if isinstance(obj, dict):
        return {k: _profile_to_decimal_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_profile_to_decimal_safe(v) for v in obj]
    return obj


def call_bedrock(profile: dict, summary: dict) -> dict:
    user_msg = json.dumps(
        {"profile": _profile_to_decimal_safe(profile), "summary": summary},
        ensure_ascii=False,
    )
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "temperature": 0.2,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_msg}],
    }
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    payload = json.loads(resp["body"].read())
    text = "".join(
        block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text"
    ).strip()

    # Strip accidental fences just in case
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "model returned non-JSON", "raw": text[:500]}


def handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return respond(401, {"error": "unauthorized"})

    result = table.get_item(Key={"userId": user_id})
    item = result.get("Item")
    if not item or not item.get("profile"):
        return respond(404, {"error": "profile not found - submit profile first"})

    profile = item["profile"]
    summary = compute_networth(profile)

    try:
        goals = call_bedrock(profile, summary)
    except Exception as e:
        return respond(500, {"error": f"bedrock error: {str(e)}", "summary": summary})

    return respond(200, {"summary": summary, "goals": goals})
