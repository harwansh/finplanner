"""POST /analyze - takes profile JSON, returns net worth + markdown plan via Bedrock Converse API."""
import json
import os

import boto3

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}


def respond(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def _num(x):
    if x is None or x == "":
        return 0.0
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def compute_networth(profile):
    assets = profile.get("assets", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}
    income = profile.get("income", {}) or {}
    expenses = profile.get("expenses", {}) or {}

    total_assets = sum(_num(v) for v in assets.values())
    total_liabilities = sum(_num(v) for v in liabilities.values())
    net_worth = total_assets - total_liabilities

    monthly_income = _num(income.get("monthlyAfterTax")) + _num(income.get("otherMonthly"))
    monthly_emi = _num(profile.get("monthlyEmi"))
    monthly_expenses = (
        _num(expenses.get("fixed"))
        + _num(expenses.get("variable"))
        + _num(expenses.get("annual")) / 12.0
        + monthly_emi
    )
    monthly_surplus = monthly_income - monthly_expenses
    savings_rate = (monthly_surplus / monthly_income * 100.0) if monthly_income > 0 else 0.0
    emergency_have = _num(profile.get("emergencyFund")) or _num(assets.get("savings")) or _num(assets.get("bankSavings"))
    emergency_months = (emergency_have / monthly_expenses) if monthly_expenses > 0 else 0.0

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


SYSTEM_PROMPT = """You are an expert financial planning AI assistant for Indian users (or whichever country the user specifies). Your job is to use the user's financial and family details to calculate realistic inflation-adjusted financial goals and generate a personalized long-term financial roadmap.

Use real-world financial planning logic, inflation-adjusted values, expected return assumptions, risk profiling, and goal-based investing calculations.

Do not give generic advice. Every goal amount, monthly investment, future value, and timeline must be calculated based on the user's inputs.

## Default Assumptions (India)
- General inflation: 6% per year
- Education inflation: 10% per year
- Medical inflation: 10% per year
- Marriage inflation: 7% per year
- Real estate inflation: 6% per year
- Pre-retirement equity return: 11% per year
- Pre-retirement debt return: 7% per year
- Balanced portfolio return: 9% per year
- Post-retirement return: 7% per year
- Retirement expense inflation: 6% per year
- Safe withdrawal rate: 3.5% to 4% per year
- Emergency fund requirement: 6 to 12 months of expenses
- Life expectancy assumption: 85 to 90 years

State assumptions used.

## Output Format

Output a single Markdown document with these sections in this exact order:

### 1. User Financial Snapshot
A concise bulleted summary: age, retirement age, monthly income, monthly expenses, dependents, children's ages, parent dependency, total assets, total liabilities, insurance status, risk profile.

### 2. Key Assumptions Used
List inflation and return assumptions actually used.

### 3. Financial Goal Summary Table
A markdown table:

| No. | Goal | Timeline | Present Cost | Future Cost | Existing Allocation | Gap | Monthly Investment | Priority |

Pick the 15 most relevant goals from this list (only include those that apply to the user):
1. Emergency fund
2. Health insurance planning
3. Life insurance planning
4. Debt repayment
5. Early retirement
6. Regular retirement
7. Child education
8. Child marriage
9. Home purchase (if user does not own)
10. Home loan prepayment (if user has a home loan)
11. Vehicle purchase
12. Parents' medical support fund
13. Parents' monthly support
14. Vacation/travel fund
15. Wealth creation
16. Tax-saving investment
17. Children's skill/hobby development
18. Higher education abroad (if applicable)
19. Business/startup fund (if applicable)
20. Legacy/estate planning

### 4. Detailed Goal-Wise Plan
For each of the 15 selected goals provide:
- Goal explanation (1-2 sentences)
- Calculation logic (show the formula used)
- Future value (compute it)
- Investment required (Monthly SIP)
- Suggested investment strategy (asset allocation, products)
- Risk level
- Priority (Critical / High / Medium / Low)
- Step-by-step action plan (3-5 bullet points)

### 5. Retirement Planning
Compute and show monthly expense at retirement (after inflation), annual expenses at retirement, retirement corpus required, existing retirement savings, retirement gap, monthly SIP required, corpus sustainability until age 85-90.

### 6. Child Planning
If user has children, compute for each child: education cost, higher education cost, marriage cost (if applicable), timeline based on child's current age, monthly investment required.

### 7. Parents Dependency
If parents are dependent: monthly support requirement, medical emergency corpus, health insurance need, annual support cost after inflation.

### 8. Home Planning
If user does NOT own a home: estimate future home cost, down payment, loan, EMI affordability, monthly investment for down payment.
If user owns: home loan status, prepayment strategy if useful.

### 9. Insurance Gap Analysis
Required life cover (15-20× annual expenses + liabilities + future goals - existing liquid assets), existing life cover, insurance gap, health insurance recommendation, critical illness cover recommendation.

### 10. Monthly Investment Feasibility
Total required monthly investment, user's monthly surplus, are goals achievable? Which to delay/reduce?

### 11. Priority-Based Action Plan
Group actions by horizon: Immediate (0-3 months), Short term (3 months - 2 years), Medium term (2-7 years), Long term (7+ years).

### 12. Final Recommendations
Practical recommendations on emergency fund, insurance, debt, allocation, retirement, child goals, parent support, tax planning, annual review.

## Formulas to use
- Future Value: FV = PV × (1 + inflation_rate)^years
- Monthly SIP: SIP = FV × r / [((1 + r)^n - 1) × (1 + r)] where r = monthly expected return, n = months

## Rules
- Every amount must be calculated, not guessed.
- Show formulas inline where useful.
- Use post-tax realistic return assumptions where possible.
- If surplus is insufficient, prioritize and suggest trade-offs.
- Do not promise guaranteed returns.
- End with this disclaimer: "This is educational financial planning guidance, not registered financial advice."
- Output ONLY the Markdown document, no preamble, no closing remarks beyond the disclaimer.
"""


def call_bedrock_converse(profile, summary):
    """Use Bedrock Converse API - works with any model (Nova, Llama, Mistral, Anthropic)."""
    user_msg = json.dumps({"profile": profile, "summary": summary}, ensure_ascii=False)
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_msg}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 8000, "temperature": 0.2},
    )
    text = response["output"]["message"]["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("markdown"):
            text = text[len("markdown"):]
        text = text.strip()
    return text


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
    if method == "OPTIONS":
        return respond(200, {})

    raw = event.get("body") or "{}"
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return respond(400, {"error": "invalid JSON body"})

    profile = body.get("profile")
    if not isinstance(profile, dict):
        return respond(400, {"error": "profile object required in request body"})

    summary = compute_networth(profile)
    try:
        report = call_bedrock_converse(profile, summary)
    except Exception as e:
        return respond(500, {"error": f"bedrock error: {str(e)}", "summary": summary})

    return respond(200, {"summary": summary, "report": report})
