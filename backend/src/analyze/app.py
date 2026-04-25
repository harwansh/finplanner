"""POST /analyze - takes profile JSON, returns net worth + markdown plan via Bedrock Converse API."""
import copy
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


def _int(x):
    return int(max(0, round(_num(x))))


def _money(x):
    return round(_num(x), 2)


def normalize_profile(profile):
    """Normalize transient UI state before computing or prompting the model.

    This prevents stale child rows, hidden child values for non-married users, and
    inconsistent parent dependency state from leaking into the generated plan.
    """
    cleaned = copy.deepcopy(profile)
    basics = cleaned.setdefault("basics", {})

    kids = basics.get("kids") or []
    if not isinstance(kids, list):
        kids = []

    normalized_kids = []
    for i, kid in enumerate(kids):
        if not isinstance(kid, dict):
            continue
        name = str(kid.get("name") or "").strip()
        age_raw = kid.get("age")
        has_name = bool(name)
        has_age = age_raw not in ("", None)
        if not has_name and not has_age:
            continue

        normalized_kids.append(
            {
                "name": name or f"Child {i + 1}",
                "age": _int(age_raw),
            }
        )

    if basics.get("maritalStatus") != "married":
        normalized_kids = []

    basics["kids"] = normalized_kids

    parents_dependent = bool(basics.get("parentsDependent"))
    basics["parentsDependent"] = parents_dependent
    basics["dependentParentsCount"] = _int(basics.get("dependentParentsCount")) if parents_dependent else 0

    cleaned["basics"] = basics
    return cleaned


def compute_networth(profile):
    assets = profile.get("assets", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}
    income = profile.get("income", {}) or {}
    expenses = profile.get("expenses", {}) or {}

    total_assets = sum(_num(v) for v in assets.values())
    total_liabilities = sum(_num(v) for v in liabilities.values())
    net_worth = total_assets - total_liabilities

    recurring_income = _num(income.get("monthlyAfterTax")) + _num(income.get("otherMonthly"))
    prorated_bonus = _num(income.get("bonusAnnual")) / 12.0
    monthly_income = recurring_income + prorated_bonus

    monthly_emi = _num(profile.get("monthlyEmi"))
    fixed_expenses = _num(expenses.get("fixed"))
    variable_expenses = _num(expenses.get("variable"))
    annual_expenses_monthly = _num(expenses.get("annual")) / 12.0
    monthly_expenses = fixed_expenses + variable_expenses + annual_expenses_monthly + monthly_emi

    monthly_surplus = monthly_income - monthly_expenses
    savings_rate = (monthly_surplus / monthly_income * 100.0) if monthly_income > 0 else 0.0

    emergency_have = (
        _num(profile.get("emergencyFund"))
        or _num(assets.get("savings"))
        or _num(assets.get("bankSavings"))
    )
    emergency_months = (emergency_have / monthly_expenses) if monthly_expenses > 0 else 0.0

    essential_monthly_expenses = fixed_expenses + monthly_emi + annual_expenses_monthly
    emergency_target_6m = monthly_expenses * 6.0
    emergency_target_12m = monthly_expenses * 12.0

    warnings = []
    basics = profile.get("basics", {}) or {}

    if monthly_income > 0 and monthly_surplus < 0:
        warnings.append(
            "Monthly expenses exceed average monthly income. Treat this as a feasibility blocker before starting new SIPs."
        )
    if monthly_expenses > 0 and emergency_months < 3:
        warnings.append("Emergency fund is below 3 months of expenses.")
    if basics.get("parentsDependent") and _int(basics.get("dependentParentsCount")) < 1:
        warnings.append("Parents are marked financially dependent, but dependent parents count is 0.")
    if _num(expenses.get("annual")) > 0 and annual_expenses_monthly > recurring_income * 0.5:
        warnings.append("Annual lump-sum expenses are unusually high relative to recurring monthly income.")
    if monthly_income > 0 and monthly_expenses / monthly_income > 0.8:
        warnings.append("Expense ratio is above 80% of income; long-term goals will need trade-offs.")

    return {
        "totalAssets": round(total_assets, 2),
        "totalLiabilities": round(total_liabilities, 2),
        "netWorth": round(net_worth, 2),
        "monthlyIncome": round(monthly_income, 2),
        "monthlyRecurringIncome": round(recurring_income, 2),
        "monthlyBonusProrated": round(prorated_bonus, 2),
        "monthlyExpenses": round(monthly_expenses, 2),
        "monthlyExpenseBreakdown": {
            "fixed": round(fixed_expenses, 2),
            "variable": round(variable_expenses, 2),
            "annualProrated": round(annual_expenses_monthly, 2),
            "emi": round(monthly_emi, 2),
        },
        "essentialMonthlyExpenses": round(essential_monthly_expenses, 2),
        "monthlySurplus": round(monthly_surplus, 2),
        "savingsRatePct": round(savings_rate, 1),
        "emergencyFundMonths": round(emergency_months, 1),
        "emergencyFundCurrent": round(emergency_have, 2),
        "emergencyFundTarget6Months": round(emergency_target_6m, 2),
        "emergencyFundTarget12Months": round(emergency_target_12m, 2),
        "feasibilityStatus": "blocked" if monthly_surplus <= 0 else "feasible",
        "warnings": warnings,
    }


SYSTEM_PROMPT = """You are an expert financial planning AI assistant for Indian users (or whichever country the user specifies). Your job is to use the user's financial and family details to calculate realistic inflation-adjusted financial goals and generate a personalized long-term financial roadmap.

Use real-world financial planning logic, inflation-adjusted values, expected return assumptions, risk profiling, and goal-based investing calculations.

Do not give generic advice. Every goal amount, monthly investment, future value, and timeline must be calculated based on the user's inputs.

## Hard rules for data integrity
- Use only the children present in `profile.basics.kids`; do not invent or retain previously removed children.
- If `profile.basics.parentsDependent` is false, do not include parent-support goals.
- If parents are dependent but `dependentParentsCount` is 0, call this out as a data issue instead of assuming parent expenses.
- Separate user-entered goals from suggested goals. Label auto-added goals as "Suggested" and make them removable/deferrable in the advice.
- Do not create duplicate emergency-fund goals. Use one emergency fund only.
- If `summary.feasibilityStatus` is "blocked" or monthly surplus is negative/zero, start with a feasibility warning and do not recommend starting new long-term SIPs until cash flow is fixed. In that case, show SIPs as target amounts only and prioritize expense reduction, emergency fund, insurance, and debt actions.

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

### 1. Feasibility Check
Show average monthly income, monthly expense breakdown, monthly surplus, savings rate, emergency fund months, and whether the plan is feasible. If surplus is negative/zero, state the exact monthly gap to fix before new SIPs.

### 2. User Financial Snapshot
A concise bulleted summary: age, retirement age, monthly income, monthly expenses, dependents, children's ages, parent dependency, total assets, total liabilities, insurance status, risk profile.

### 3. Key Assumptions Used
List inflation and return assumptions actually used.

### 4. Financial Goal Summary Table
A markdown table:

| No. | Goal | Type | Timeline | Present Cost | Future Cost | Existing Allocation | Gap | Monthly Investment | Priority |

Use Type = "User-entered", "Required", or "Suggested".
Pick the most relevant goals from this list, but only include those that apply to the user:
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

### 5. Detailed Goal-Wise Plan
For each selected goal provide:
- Goal explanation (1-2 sentences)
- Calculation logic (show the formula used)
- Future value (compute it)
- Investment required (Monthly SIP)
- Suggested investment strategy (asset allocation, products)
- Risk level
- Priority (Critical / High / Medium / Low)
- Step-by-step action plan (3-5 bullet points)

### 6. Retirement Planning
Compute and show current monthly expenses, monthly expense at retirement after inflation, annual expenses at retirement, retirement corpus required, existing retirement savings projected forward, retirement gap, monthly SIP required, corpus sustainability until age 85-90.

### 7. Child Planning
If user has children, compute for each child in `profile.basics.kids`: education cost, higher education cost, marriage cost (if applicable), timeline based on child's current age, monthly investment required.

### 8. Parents Dependency
If parents are dependent and parent count is valid: monthly support requirement, medical emergency corpus, health insurance need, annual support cost after inflation. Otherwise state no parent-dependent planning was included.

### 9. Home Planning
If user does NOT own a home: estimate future home cost, down payment, loan, EMI affordability, monthly investment for down payment.
If user owns: home loan status, prepayment strategy if useful.

### 10. Insurance Gap Analysis
Required life cover = 15-20× annual expenses + liabilities + high-priority future goals - liquid assets. Show existing life cover, insurance gap, health insurance recommendation, and critical illness cover recommendation. Do not say coverage is adequate without this calculation.

### 11. Monthly Investment Feasibility
Total target monthly investment, user's monthly surplus, are goals achievable, and which goals to delay/reduce. If surplus is negative/zero, show "Not currently feasible" and give a cash-flow repair target.

### 12. Priority-Based Action Plan
Group actions by horizon: Immediate (0-3 months), Short term (3 months - 2 years), Medium term (2-7 years), Long term (7+ years).

### 13. Final Recommendations
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

    profile = normalize_profile(profile)
    summary = compute_networth(profile)
    try:
        report = call_bedrock_converse(profile, summary)
    except Exception as e:
        return respond(500, {"error": f"bedrock error: {str(e)}", "summary": summary})

    return respond(200, {"summary": summary, "report": report})
