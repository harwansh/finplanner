"POST /analyze - deterministic CFP-style financial planner with optional Bedrock recommendation notes."

import copy
import json
import os
from datetime import datetime

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

ASSUMPTIONS = {
    "generalInflation": 0.06,
    "educationInflation": 0.10,
    "medicalInflation": 0.10,
    "realEstateInflation": 0.06,
    "retirementExpenseInflation": 0.06,
    "safeWithdrawalRate": 0.035,
    "defaultBalancedReturn": 0.09,
    "emergencyFundMonths": 6,
    "lifeExpectancy": 90,
}

RETIREMENT_CATEGORIES = {"epf", "ppf", "nps", "retirementSip", "equityIndex", "equityLargeCap", "equityFlexiCap"}
CHILD_CATEGORIES = {"childEducation"}
LOW_RISK_CATEGORIES = {"fdRd", "debtFund", "liquidFund", "ppf", "epf"}


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
    return round(max(0.0, _num(x)), 2)


def _fmt_money(value):
    return f"₹{round(_num(value)):,.0f}"


def _fmt_pct(value):
    return f"{round(_num(value) * 100, 1)}%"


def _fv_lumpsum(pv, annual_return, years):
    return _money(_num(pv) * ((1 + annual_return) ** max(0, years)))


def _fv_monthly(monthly, annual_return, years):
    monthly = _num(monthly)
    months = int(max(1, round(years * 12)))
    r = annual_return / 12.0
    if monthly <= 0:
        return 0.0
    if r <= 0:
        return _money(monthly * months)
    return _money(monthly * ((((1 + r) ** months - 1) * (1 + r)) / r))


def _sip_required(future_gap, annual_return, years):
    future_gap = _num(future_gap)
    months = int(max(1, round(years * 12)))
    r = annual_return / 12.0
    if future_gap <= 0:
        return 0.0
    if r <= 0:
        return _money(future_gap / months)
    factor = (((1 + r) ** months - 1) * (1 + r)) / r
    return _money(future_gap / factor)


def normalize_profile(profile):
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
        if not name and age_raw in ("", None):
            continue
        normalized_kids.append({"name": name or f"Child {i + 1}", "age": _int(age_raw)})
    if basics.get("maritalStatus") != "married":
        normalized_kids = []
    basics["kids"] = normalized_kids
    basics["parentsDependent"] = bool(basics.get("parentsDependent"))
    basics["dependentParentsCount"] = _int(basics.get("dependentParentsCount")) if basics["parentsDependent"] else 0
    cleaned["basics"] = basics

    investments = cleaned.get("investments") or []
    normalized_investments = []
    if isinstance(investments, list):
        for idx, inv in enumerate(investments):
            if not isinstance(inv, dict):
                continue
            current_value = _num(inv.get("currentValue"))
            monthly_amount = _num(inv.get("monthlyAmount"))
            if current_value <= 0 and monthly_amount <= 0:
                continue
            category = inv.get("category") or "other"
            normalized_investments.append({
                "name": str(inv.get("name") or f"Investment {idx + 1}").strip(),
                "category": category,
                "monthlyAmount": monthly_amount,
                "currentValue": current_value,
                "expectedReturnPct": _num(inv.get("expectedReturnPct")) or default_return_pct(category),
                "goal": inv.get("goal") or infer_goal_from_category(category),
            })
    cleaned["investments"] = normalized_investments
    return cleaned


def default_return_pct(category):
    return {
        "equityLargeCap": 11,
        "equityMidCap": 12,
        "equitySmallCap": 13,
        "equityFlexiCap": 11,
        "equityIndex": 11,
        "elss": 11,
        "debtFund": 7,
        "liquidFund": 5.5,
        "hybridFund": 9,
        "fdRd": 6.5,
        "epf": 8,
        "ppf": 7.1,
        "nps": 10,
        "gold": 7,
        "realEstate": 6,
        "smallcase": 12,
        "childEducation": 10,
        "retirementSip": 10,
        "other": 8,
    }.get(category, 8)


def infer_goal_from_category(category):
    if category in RETIREMENT_CATEGORIES:
        return "retirement"
    if category in CHILD_CATEGORIES:
        return "childEducation"
    return "wealth"


def validate_profile(profile):
    errors = []
    basics = profile.get("basics", {}) or {}
    income = profile.get("income", {}) or {}
    expenses = profile.get("expenses", {}) or {}

    age = _int(basics.get("age"))
    retirement_age = _int(basics.get("desiredRetirementAge"))
    if age <= 0:
        errors.append("Current age is required.")
    if retirement_age <= age:
        errors.append("Desired retirement age must be greater than current age.")
    if _num(income.get("monthlyAfterTax")) <= 0:
        errors.append("Monthly after-tax income is required.")
    for field, label in [("fixed", "Fixed monthly expenses"), ("variable", "Variable monthly expenses"), ("annual", "Annual lump-sum expenses")]:
        if expenses.get(field) in ("", None):
            errors.append(f"{label} are required. Enter 0 if not applicable.")
    if profile.get("monthlyEmi") in ("", None):
        errors.append("Total monthly EMI is required. Enter 0 if not applicable.")
    if profile.get("emergencyFund") in ("", None):
        errors.append("Emergency fund is required. Enter 0 if none.")
    return errors


def compute_summary(profile):
    basics = profile.get("basics", {}) or {}
    income = profile.get("income", {}) or {}
    expenses = profile.get("expenses", {}) or {}
    assets = profile.get("assets", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}
    investments = profile.get("investments", []) or []

    monthly_income = _num(income.get("monthlyAfterTax")) + _num(income.get("otherMonthly")) + _num(income.get("bonusAnnual")) / 12.0
    monthly_expenses = _num(expenses.get("fixed")) + _num(expenses.get("variable")) + _num(expenses.get("annual")) / 12.0 + _num(profile.get("monthlyEmi"))
    monthly_surplus = monthly_income - monthly_expenses

    existing_monthly_investments = sum(_num(i.get("monthlyAmount")) for i in investments)
    remaining_surplus = max(0, monthly_surplus - existing_monthly_investments)

    total_assets = sum(_num(v) for v in assets.values()) + sum(_num(i.get("currentValue")) for i in investments)
    total_liabilities = sum(_num(v) for v in liabilities.values())
    emergency_have = _num(profile.get("emergencyFund")) or _num(assets.get("bankSavings"))
    emergency_months = emergency_have / monthly_expenses if monthly_expenses > 0 else 0

    dependents_count = len(basics.get("kids", [])) + _int(basics.get("dependentParentsCount")) + (1 if basics.get("maritalStatus") == "married" else 0)

    warnings = []
    if monthly_surplus <= 0:
        warnings.append("Monthly expenses are greater than or equal to income. New investments are blocked until cash flow is positive.")
    if existing_monthly_investments > max(0, monthly_surplus):
        warnings.append("Existing monthly investments exceed available surplus. Confirm SIPs are not also included in expenses.")
    if emergency_months < 3:
        warnings.append("Emergency fund is below 3 months of expenses.")

    risk_profile = derive_risk_profile(profile, monthly_surplus, monthly_income, emergency_months, total_liabilities, dependents_count, investments)

    return {
        "monthlyIncome": round(monthly_income, 2),
        "monthlyExpenses": round(monthly_expenses, 2),
        "monthlyExpenseBreakdown": {
            "fixed": round(_num(expenses.get("fixed")), 2),
            "variable": round(_num(expenses.get("variable")), 2),
            "annualProrated": round(_num(expenses.get("annual")) / 12.0, 2),
            "emi": round(_num(profile.get("monthlyEmi")), 2),
        },
        "monthlySurplus": round(monthly_surplus, 2),
        "currentMonthlyInvestments": round(existing_monthly_investments, 2),
        "remainingSurplusAfterExistingInvestments": round(remaining_surplus, 2),
        "savingsRatePct": round((monthly_surplus / monthly_income * 100) if monthly_income > 0 else 0, 1),
        "totalAssets": round(total_assets, 2),
        "totalLiabilities": round(total_liabilities, 2),
        "netWorth": round(total_assets - total_liabilities, 2),
        "emergencyFundCurrent": round(emergency_have, 2),
        "emergencyFundMonths": round(emergency_months, 1),
        "dependentsCount": dependents_count,
        "riskProfile": risk_profile,
        "warnings": warnings,
    }


def derive_risk_profile(profile, surplus, income, emergency_months, liabilities, dependents_count, investments):
    basics = profile.get("basics", {}) or {}
    age = _int(basics.get("age"))
    score = 0
    if age < 35:
        score += 2
    elif age <= 50:
        score += 1
    else:
        score -= 1

    if dependents_count == 0:
        score += 1
    elif dependents_count >= 3:
        score -= 2
    else:
        score -= 1

    if emergency_months >= 6:
        score += 1
    elif emergency_months < 3:
        score -= 2

    surplus_ratio = surplus / income if income > 0 else 0
    if surplus_ratio >= 0.30:
        score += 2
    elif surplus_ratio < 0.10:
        score -= 1

    if liabilities > income * 24:
        score -= 1

    monthly_investments = sum(_num(i.get("monthlyAmount")) for i in investments)
    equity_like = sum(_num(i.get("monthlyAmount")) for i in investments if i.get("category") not in LOW_RISK_CATEGORIES)
    if monthly_investments > 0 and equity_like / monthly_investments > 0.6:
        score += 1

    if score >= 3:
        return {"label": "Growth", "equity": 70, "debt": 20, "gold": 10, "reason": "Age, cash-flow capacity, dependents, emergency fund and current investment pattern support growth allocation."}
    if score >= 1:
        return {"label": "Balanced", "equity": 55, "debt": 35, "gold": 10, "reason": "Profile supports moderate risk with a balanced equity-debt allocation."}
    return {"label": "Conservative", "equity": 35, "debt": 55, "gold": 10, "reason": "Dependents, emergency fund, cash-flow or liabilities suggest capital protection first."}


def project_investments(investments, years, goal_filter=None):
    total = 0
    rows = []
    for inv in investments:
        if goal_filter and inv.get("goal") != goal_filter and inv.get("category") not in goal_filter:
            continue
        annual_return = _num(inv.get("expectedReturnPct")) / 100.0
        fv = _fv_lumpsum(inv.get("currentValue"), annual_return, years) + _fv_monthly(inv.get("monthlyAmount"), annual_return, years)
        total += fv
        rows.append({"name": inv.get("name"), "category": inv.get("category"), "fv": _money(fv), "returnPct": inv.get("expectedReturnPct")})
    return _money(total), rows


def add_goal(goals, name, goal_type, priority, years, present_cost, future_cost, existing_fv, target_monthly, notes):
    gap = max(0, _num(future_cost) - _num(existing_fv))
    goals.append({
        "name": name,
        "type": goal_type,
        "priority": priority,
        "timeline": "Immediate" if years <= 0 else f"{years} years",
        "years": years,
        "presentCost": _money(present_cost),
        "futureCost": _money(future_cost),
        "existingAllocation": _money(existing_fv),
        "gap": _money(gap),
        "targetMonthlyInvestment": _money(target_monthly),
        "recommendedMonthlyInvestment": 0,
        "fundingStatus": "Not funded",
        "notes": notes,
    })


def allocate_recommendations(goals, available_surplus):
    remaining = max(0, _num(available_surplus))
    priority_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    for goal in sorted(goals, key=lambda g: (priority_rank.get(g["priority"], 9), g["years"])):
        target = _num(goal.get("targetMonthlyInvestment"))
        allocation = min(target, remaining)
        goal["recommendedMonthlyInvestment"] = _money(allocation)
        goal["fundingStatus"] = "Fully funded" if allocation >= target else ("Partially funded" if allocation > 0 else "Not funded")
        remaining -= allocation
    return _money(remaining)


def compute_insurance(profile, summary, goals):
    basics = profile.get("basics", {}) or {}
    insurance = profile.get("insurance", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}

    dependents = summary["dependentsCount"]
    annual_expenses = summary["monthlyExpenses"] * 12
    liquid_assets = summary["totalAssets"] - sum(_num(v) for v in liabilities.values())

    high_priority_goal_gap = sum(g["gap"] for g in goals if g["priority"] in {"Critical", "High"} and "Insurance" not in g["name"])

    if dependents == 0:
        required_life = max(0, summary["totalLiabilities"] + annual_expenses * 2 - liquid_assets)
        life_note = "No dependents entered. Term insurance is good-to-have mainly for liabilities, final expenses, and future family plans, not a high mandatory need."
        priority = "Medium" if required_life > 0 else "Low"
    else:
        income_replacement_years = min(20, max(5, _int(basics.get("desiredRetirementAge")) - _int(basics.get("age"))))
        required_life = max(0, annual_expenses * income_replacement_years + summary["totalLiabilities"] + high_priority_goal_gap - liquid_assets)
        life_note = f"Dependents found. CFP-style need uses {income_replacement_years} years of expense replacement plus liabilities and high-priority goals."
        priority = "High"

    existing_life = _num(insurance.get("life"))
    life_gap = max(0, required_life - existing_life)

    base_health = 1000000 if basics.get("maritalStatus") == "single" else 2000000
    base_health += 500000 * len(basics.get("kids", []))
    base_health += 750000 * _int(basics.get("dependentParentsCount"))
    if basics.get("cityTier") == "Tier 1":
        base_health *= 1.25
    existing_health = _num(insurance.get("health"))
    health_gap = max(0, base_health - existing_health)

    return {
        "requiredLifeCover": _money(required_life),
        "existingLifeCover": _money(existing_life),
        "lifeCoverGap": _money(life_gap),
        "lifePriority": priority,
        "lifeNote": life_note,
        "requiredHealthCover": _money(base_health),
        "existingHealthCover": _money(existing_health),
        "healthCoverGap": _money(health_gap),
    }


def build_plan(profile, summary):
    basics = profile.get("basics", {}) or {}
    investments = profile.get("investments", []) or {}
    assets = profile.get("assets", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}

    goals = []
    years_to_retirement = max(1, _int(basics.get("desiredRetirementAge")) - _int(basics.get("age")))
    available_surplus = summary["remainingSurplusAfterExistingInvestments"]

    emergency_target = summary["monthlyExpenses"] * ASSUMPTIONS["emergencyFundMonths"]
    add_goal(goals, "Emergency Fund", "Required", "Critical", 0, emergency_target, emergency_target, summary["emergencyFundCurrent"], max(0, emergency_target - summary["emergencyFundCurrent"]), "Build 6 months of expenses before optional goals.")

    monthly_expense_at_retirement = _fv_lumpsum(summary["monthlyExpenses"], ASSUMPTIONS["retirementExpenseInflation"], years_to_retirement)
    retirement_corpus = (monthly_expense_at_retirement * 12) / ASSUMPTIONS["safeWithdrawalRate"]
    retirement_existing, retirement_rows = project_investments(investments, years_to_retirement, goal_filter={"retirement", "epf", "ppf", "nps", "retirementSip", "equityIndex", "equityLargeCap", "equityFlexiCap"})
    retirement_existing += _fv_lumpsum(_num(assets.get("epfPpfNps")), 0.08, years_to_retirement)
    retirement_gap = max(0, retirement_corpus - retirement_existing)
    retirement_target_sip = _sip_required(retirement_gap, ASSUMPTIONS["defaultBalancedReturn"], years_to_retirement)
    add_goal(goals, "Retirement Corpus", "Required", "Critical", years_to_retirement, retirement_corpus / ((1 + ASSUMPTIONS["retirementExpenseInflation"]) ** years_to_retirement), retirement_corpus, retirement_existing, retirement_target_sip, "Includes current EPF/NPS/PPF/SIP rows and their editable return assumptions.")

    unsecured_debt = _num(liabilities.get("personalLoan")) + _num(liabilities.get("creditCard")) + _num(liabilities.get("vehicleLoan")) + _num(liabilities.get("otherDebt"))
    if unsecured_debt > 0:
        add_goal(goals, "High-Interest Debt Repayment", "Required", "Critical", 1, unsecured_debt, unsecured_debt, 0, unsecured_debt / 12, "Repay high-interest debt before adding optional investments.")

    if not basics.get("ownsHouse"):
        home_years = 7
        present_home_cost = 7500000 if basics.get("cityTier") == "Tier 1" else 5000000
        future_home_cost = _fv_lumpsum(present_home_cost, ASSUMPTIONS["realEstateInflation"], home_years)
        down_payment = future_home_cost * 0.20
        add_goal(goals, "Home Down Payment", "Suggested", "Medium", home_years, present_home_cost * 0.20, down_payment, 0, _sip_required(down_payment, ASSUMPTIONS["defaultBalancedReturn"], home_years), "Suggested because user does not own a home. Edit/remove later when explicit goal module is added.")

    kids = basics.get("kids", [])
    for kid in kids:
        child_age = _int(kid.get("age"))
        child_name = kid.get("name") or "Child"
        years = max(1, 18 - child_age)
        pv = 1500000
        fv = _fv_lumpsum(pv, ASSUMPTIONS["educationInflation"], years)
        existing_child, _ = project_investments(investments, years, goal_filter={"childEducation"})
        if len(kids) > 1:
            existing_child = existing_child / len(kids)
        gap = max(0, fv - existing_child)
        add_goal(goals, f"{child_name} Education", "Required", "High", years, pv, fv, existing_child, _sip_required(gap, ASSUMPTIONS["defaultBalancedReturn"], years), "Uses child age and existing child education SIP rows.")

    insurance = compute_insurance(profile, summary, goals)
    add_goal(goals, "Life Insurance Gap", "Required", insurance["lifePriority"], 0, insurance["requiredLifeCover"], insurance["requiredLifeCover"], insurance["existingLifeCover"], 0, insurance["lifeNote"])
    add_goal(goals, "Health Insurance Gap", "Required", "High" if insurance["healthCoverGap"] > 0 else "Low", 0, insurance["requiredHealthCover"], insurance["requiredHealthCover"], insurance["existingHealthCover"], 0, "Health cover uses family size, dependent parents, and city tier.")

    unallocated = allocate_recommendations(goals, available_surplus)
    return {
        "goals": goals,
        "insurance": insurance,
        "riskProfile": summary["riskProfile"],
        "retirement": {
            "yearsToRetirement": years_to_retirement,
            "monthlyExpenseAtRetirement": monthly_expense_at_retirement,
            "corpusRequired": retirement_corpus,
            "existingProjected": retirement_existing,
            "investmentRowsUsed": retirement_rows,
            "gap": retirement_gap,
            "targetMonthlySip": retirement_target_sip,
            "recommendedMonthlySip": next((g["recommendedMonthlyInvestment"] for g in goals if g["name"] == "Retirement Corpus"), 0),
        },
        "totalTargetMonthlyInvestment": _money(sum(g["targetMonthlyInvestment"] for g in goals)),
        "totalRecommendedMonthlyInvestment": _money(sum(g["recommendedMonthlyInvestment"] for g in goals)),
        "unallocatedSurplus": unallocated,
    }


def goal_row(i, g):
    return f"| {i} | {g['name']} | {g['type']} | {g['timeline']} | {_fmt_money(g['futureCost'])} | {_fmt_money(g['existingAllocation'])} | {_fmt_money(g['gap'])} | {_fmt_money(g['targetMonthlyInvestment'])} | {_fmt_money(g['recommendedMonthlyInvestment'])} | {g['fundingStatus']} | {g['priority']} |"


def build_report(profile, summary, plan, ai_notes=None):
    risk = plan["riskProfile"]
    ins = plan["insurance"]
    ret = plan["retirement"]
    lines = [
        "### 1. CFP Feasibility Check",
        "",
        f"- Average monthly income: {_fmt_money(summary['monthlyIncome'])}",
        f"- Monthly expenses: {_fmt_money(summary['monthlyExpenses'])}",
        f"- Existing monthly investments: {_fmt_money(summary['currentMonthlyInvestments'])}",
        f"- Remaining surplus for new recommendations: {_fmt_money(summary['remainingSurplusAfterExistingInvestments'])}",
        f"- Recommended new investments: {_fmt_money(plan['totalRecommendedMonthlyInvestment'])}",
        f"- Auto risk profile: **{risk['label']}** ({risk['equity']}% equity / {risk['debt']}% debt / {risk['gold']}% gold). {risk['reason']}",
    ]
    for warning in summary.get("warnings", []):
        lines.append(f"- Warning: {warning}")

    lines += [
        "",
        "### 2. Goal Summary",
        "",
        "| No. | Goal | Type | Timeline | Future Cost / Need | Existing Projected | Gap | Target Monthly | Recommended New Monthly | Funding | Priority |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for i, g in enumerate(plan["goals"], 1):
        lines.append(goal_row(i, g))

    lines += [
        "",
        "### 3. Retirement Calculation",
        "",
        f"- Years to retirement: {ret['yearsToRetirement']}",
        f"- Monthly expense at retirement: {_fmt_money(ret['monthlyExpenseAtRetirement'])}",
        f"- Corpus required: {_fmt_money(ret['corpusRequired'])}",
        f"- Existing retirement corpus + SIPs projected: {_fmt_money(ret['existingProjected'])}",
        f"- Retirement gap: {_fmt_money(ret['gap'])}",
        f"- Target additional SIP: {_fmt_money(ret['targetMonthlySip'])}",
        f"- Recommended additional SIP now, capped to surplus: {_fmt_money(ret['recommendedMonthlySip'])}",
        "",
        "### 4. Insurance Need Analysis",
        "",
        f"- Required life cover: {_fmt_money(ins['requiredLifeCover'])}",
        f"- Existing life cover: {_fmt_money(ins['existingLifeCover'])}",
        f"- Life cover gap: {_fmt_money(ins['lifeCoverGap'])}",
        f"- Life cover logic: {ins['lifeNote']}",
        f"- Required health cover: {_fmt_money(ins['requiredHealthCover'])}",
        f"- Existing health cover: {_fmt_money(ins['existingHealthCover'])}",
        f"- Health cover gap: {_fmt_money(ins['healthCoverGap'])}",
        "",
        "### 5. Investment Mapping",
        "",
    ]
    investments = profile.get("investments", []) or []
    if investments:
        for inv in investments:
            lines.append(f"- {inv['name']}: {inv['category']}, current {_fmt_money(inv['currentValue'])}, monthly {_fmt_money(inv['monthlyAmount'])}, expected return {inv['expectedReturnPct']}%, mapped to {inv['goal']}.")
    else:
        lines.append("- No existing SIP/investment rows entered.")

    lines += [
        "",
        "### 6. Priority Action Plan",
        "",
        "- Keep total new SIP recommendations within remaining surplus.",
        "- Fund emergency fund and high-interest debt before optional goals.",
        "- Continue EPF/NPS/PPF/SIPs already mapped to retirement; only add the recommended additional SIP if surplus allows.",
        "- Review insurance after every major life event: marriage, child, home loan, dependent parents, income change.",
        "",
        "### 7. Final Recommendations",
        "",
        ai_notes.strip() if ai_notes else "Review this plan annually and update SIP rows, expected returns, insurance, expenses, and dependents.",
        "",
        "This is educational financial planning guidance, not registered financial advice.",
    ]
    return "\n".join(lines)


AI_NOTES_PROMPT = """You are a CFP-style financial planning assistant. Backend numbers are deterministic.
Write 3-5 practical recommendation bullets only. Do not change numbers. Do not add goals.
Do not recommend new monthly investment above remainingSurplusAfterExistingInvestments.
"""


def call_bedrock_notes(profile, summary, plan):
    payload = {"summary": summary, "plan": plan}
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": json.dumps(payload, ensure_ascii=False)}]}],
        system=[{"text": AI_NOTES_PROMPT}],
        inferenceConfig={"maxTokens": 700, "temperature": 0.1},
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
    if method == "OPTIONS":
        return respond(200, {})
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return respond(400, {"error": "invalid JSON body"})
    profile = body.get("profile")
    if not isinstance(profile, dict):
        return respond(400, {"error": "profile object required in request body"})
    profile = normalize_profile(profile)
    validation_errors = validate_profile(profile)
    if validation_errors:
        return respond(400, {"error": "Please fix required fields.", "validationErrors": validation_errors})
    summary = compute_summary(profile)
    plan = build_plan(profile, summary)
    try:
        ai_notes = call_bedrock_notes(profile, summary, plan)
    except Exception:
        ai_notes = None
    return respond(200, {"summary": summary, "plan": plan, "report": build_report(profile, summary, plan, ai_notes)})
