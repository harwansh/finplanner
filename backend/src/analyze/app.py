"POST /analyze - deterministic financial planner with optional Bedrock recommendation notes."

import copy
import json
import os
import re
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
    "marriageInflation": 0.07,
    "realEstateInflation": 0.06,
    "preRetirementDebtReturn": 0.07,
    "balancedReturn": 0.09,
    "retirementExpenseInflation": 0.06,
    "safeWithdrawalRate": 0.035,
    "lifeExpectancy": 90,
    "emergencyFundMonths": 6,
}

LIQUID_ASSET_KEYS = {"bankSavings", "fixedDeposits", "mutualFunds", "stocks", "epfPpfNps"}
RETIREMENT_CONTRIBUTION_KEYS = {"epfPpfNps", "nps", "ppf", "retirementSip"}
PRIORITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


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


def _years_until_retirement(profile):
    basics = profile.get("basics", {}) or {}
    age = _int(basics.get("age"))
    retirement_age = _int(basics.get("desiredRetirementAge")) or 60
    return max(1, retirement_age - age)


def _fv(present_value, annual_rate, years):
    return _money(_num(present_value) * ((1 + annual_rate) ** max(0, years)))


def _project_lumpsum(present_value, annual_return, years):
    return _money(_num(present_value) * ((1 + annual_return) ** max(0, years)))


def _future_value_monthly(monthly_amount, annual_return, years):
    monthly_amount = _num(monthly_amount)
    months = int(max(1, round(years * 12)))
    monthly_return = annual_return / 12.0
    if monthly_amount <= 0:
        return 0.0
    if monthly_return <= 0:
        return _money(monthly_amount * months)
    factor = (((1 + monthly_return) ** months - 1) * (1 + monthly_return)) / monthly_return
    return _money(monthly_amount * factor)


def _sip_required(future_value, annual_return, years):
    future_value = _num(future_value)
    months = int(max(1, round(years * 12)))
    monthly_return = annual_return / 12.0
    if future_value <= 0:
        return 0.0
    if annual_return <= 0:
        return _money(future_value / months)
    factor = (((1 + monthly_return) ** months - 1) * (1 + monthly_return)) / monthly_return
    return _money(future_value / factor) if factor > 0 else 0.0


def _fmt_money(value):
    return f"₹{round(_num(value)):,.0f}"


def _fmt_pct(value):
    return f"{round(value * 100, 1)}%"


def _contains_goal_text(profile, *keywords):
    text = " ".join([str(profile.get("oneTimeFutureExpenses") or ""), str(profile.get("existingGoals") or "")]).lower()
    return any(keyword in text for keyword in keywords)


def _extract_timeline_years(profile, keywords, default_years):
    text = " ".join([str(profile.get("oneTimeFutureExpenses") or ""), str(profile.get("existingGoals") or "")]).lower()
    if not any(keyword in text for keyword in keywords):
        return default_years
    current_year = datetime.utcnow().year
    year_match = re.search(r"\b(20[2-9]\d|21\d{2})\b", text)
    if year_match:
        return max(1, int(year_match.group(1)) - current_year)
    years_match = re.search(r"(?:in|after|within)\s+(\d{1,2})\s+years?", text)
    if years_match:
        return max(1, int(years_match.group(1)))
    return default_years


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
    cleaned.setdefault("currentInvestments", {})
    return cleaned


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
        errors.append("Monthly after-tax income is required and must be greater than 0.")
    for field, label in [("fixed", "Fixed monthly expenses"), ("variable", "Variable monthly expenses"), ("annual", "Annual lump-sum expenses")]:
        if expenses.get(field) in ("", None):
            errors.append(f"{label} are required. Enter 0 if not applicable.")
    if profile.get("monthlyEmi") in ("", None):
        errors.append("Total monthly EMIs are required. Enter 0 if not applicable.")
    if profile.get("emergencyFund") in ("", None):
        errors.append("Emergency fund amount is required. Enter 0 if none.")
    if basics.get("parentsDependent") and _int(basics.get("dependentParentsCount")) < 1:
        errors.append("Dependent parents count must be at least 1 when parents are financially dependent.")
    for kid in basics.get("kids", []):
        if _int(kid.get("age")) > age:
            errors.append(f"{kid.get('name', 'Child')} age cannot be greater than current age.")
    return errors


def compute_summary(profile):
    assets = profile.get("assets", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}
    income = profile.get("income", {}) or {}
    expenses = profile.get("expenses", {}) or {}
    basics = profile.get("basics", {}) or {}
    current_investments = profile.get("currentInvestments", {}) or {}
    total_assets = sum(_num(v) for v in assets.values())
    total_liabilities = sum(_num(v) for v in liabilities.values())
    recurring_income = _num(income.get("monthlyAfterTax")) + _num(income.get("otherMonthly"))
    prorated_bonus = _num(income.get("bonusAnnual")) / 12.0
    monthly_income = recurring_income + prorated_bonus
    fixed_expenses = _num(expenses.get("fixed"))
    variable_expenses = _num(expenses.get("variable"))
    annual_expenses_monthly = _num(expenses.get("annual")) / 12.0
    monthly_emi = _num(profile.get("monthlyEmi"))
    monthly_expenses = fixed_expenses + variable_expenses + annual_expenses_monthly + monthly_emi
    monthly_surplus = monthly_income - monthly_expenses
    emergency_have = _num(profile.get("emergencyFund")) or _num(assets.get("bankSavings"))
    emergency_months = (emergency_have / monthly_expenses) if monthly_expenses > 0 else 0.0
    liquid_assets = sum(_num(assets.get(key)) for key in LIQUID_ASSET_KEYS)
    current_monthly_investments = sum(_num(v) for v in current_investments.values())
    current_retirement_monthly = sum(_num(current_investments.get(key)) for key in RETIREMENT_CONTRIBUTION_KEYS)
    remaining_surplus = max(0.0, monthly_surplus - current_monthly_investments)
    warnings = []
    if monthly_income > 0 and monthly_surplus < 0:
        warnings.append("Monthly expenses exceed average monthly income. Fix cash flow before starting new long-term SIPs.")
    if monthly_expenses > 0 and emergency_months < 3:
        warnings.append("Emergency fund is below 3 months of expenses.")
    if current_monthly_investments > max(0, monthly_surplus):
        warnings.append("Existing monthly investments are higher than available surplus. Check whether SIPs are already included in expenses.")
    if basics.get("parentsDependent") and _int(basics.get("dependentParentsCount")) < 1:
        warnings.append("Parents are marked financially dependent, but dependent parents count is 0.")
    if monthly_income > 0 and monthly_expenses / monthly_income > 0.8:
        warnings.append("Expense ratio is above 80% of income; long-term goals need trade-offs.")
    return {
        "totalAssets": round(total_assets, 2),
        "totalLiabilities": round(total_liabilities, 2),
        "netWorth": round(total_assets - total_liabilities, 2),
        "liquidAssets": round(liquid_assets, 2),
        "monthlyIncome": round(monthly_income, 2),
        "monthlyRecurringIncome": round(recurring_income, 2),
        "monthlyBonusProrated": round(prorated_bonus, 2),
        "monthlyExpenses": round(monthly_expenses, 2),
        "monthlyExpenseBreakdown": {"fixed": round(fixed_expenses, 2), "variable": round(variable_expenses, 2), "annualProrated": round(annual_expenses_monthly, 2), "emi": round(monthly_emi, 2)},
        "monthlySurplus": round(monthly_surplus, 2),
        "currentMonthlyInvestments": round(current_monthly_investments, 2),
        "currentRetirementMonthlyInvestments": round(current_retirement_monthly, 2),
        "remainingSurplusAfterExistingInvestments": round(remaining_surplus, 2),
        "savingsRatePct": round((monthly_surplus / monthly_income * 100.0) if monthly_income > 0 else 0.0, 1),
        "emergencyFundMonths": round(emergency_months, 1),
        "emergencyFundCurrent": round(emergency_have, 2),
        "feasibilityStatus": "blocked" if monthly_surplus <= 0 else "feasible",
        "warnings": warnings,
    }


def _add_goal(goals, name, goal_type, timeline, years, present_cost, future_cost, existing, target_monthly, priority, notes, formula, existing_monthly=0):
    gap = _money(_num(future_cost) - _num(existing))
    goals.append({"name": name, "type": goal_type, "timeline": timeline, "years": years, "presentCost": _money(present_cost), "futureCost": _money(future_cost), "existingAllocation": _money(existing), "gap": gap, "existingMonthlyInvestment": _money(existing_monthly), "targetMonthlyInvestment": _money(target_monthly), "monthlyInvestment": 0, "priority": priority, "notes": notes, "formula": formula})


def _allocate_recommended_investments(goals, available_new_surplus):
    remaining = max(0.0, _num(available_new_surplus))
    for goal in sorted(goals, key=lambda g: (PRIORITY_ORDER.get(g["priority"], 99), g.get("years") or 999)):
        target = max(0.0, _num(goal.get("targetMonthlyInvestment")) - _num(goal.get("existingMonthlyInvestment")))
        allocation = min(target, remaining)
        goal["monthlyInvestment"] = _money(allocation)
        goal["fundingStatus"] = "Fully funded" if allocation >= target else ("Partially funded" if allocation > 0 else "Not funded")
        remaining -= allocation
    return _money(remaining)


def build_goal_plan(profile, summary):
    basics = profile.get("basics", {}) or {}
    assets = profile.get("assets", {}) or {}
    liabilities = profile.get("liabilities", {}) or {}
    insurance = profile.get("insurance", {}) or {}
    current_investments = profile.get("currentInvestments", {}) or {}
    goals = []
    monthly_expenses = _num(summary["monthlyExpenses"])
    liquid_assets = _num(summary.get("liquidAssets"))
    available_new_surplus = _num(summary.get("remainingSurplusAfterExistingInvestments"))
    years_to_retirement = _years_until_retirement(profile)
    retirement_age = _int(basics.get("desiredRetirementAge")) or 60
    existing_retirement_assets = _num(assets.get("epfPpfNps")) + _num(assets.get("mutualFunds")) + _num(assets.get("stocks"))
    existing_retirement_monthly = _num(summary.get("currentRetirementMonthlyInvestments"))
    emergency_target = monthly_expenses * ASSUMPTIONS["emergencyFundMonths"]
    _add_goal(goals, "Emergency Fund", "Required", "Immediate", 0, emergency_target, emergency_target, summary["emergencyFundCurrent"], max(0, emergency_target - _num(summary["emergencyFundCurrent"])), "Critical", "Immediate goal; future value equals present target because it should be built now.", "Emergency target = monthly expenses × 6")
    retirement_monthly_expense = _fv(monthly_expenses, ASSUMPTIONS["retirementExpenseInflation"], years_to_retirement)
    retirement_annual_expense = retirement_monthly_expense * 12
    retirement_corpus = retirement_annual_expense / ASSUMPTIONS["safeWithdrawalRate"]
    existing_retirement_assets_fv = _project_lumpsum(existing_retirement_assets, ASSUMPTIONS["balancedReturn"], years_to_retirement)
    existing_retirement_contrib_fv = _future_value_monthly(existing_retirement_monthly, ASSUMPTIONS["balancedReturn"], years_to_retirement)
    existing_retirement_fv = existing_retirement_assets_fv + existing_retirement_contrib_fv
    retirement_gap = max(0, retirement_corpus - existing_retirement_fv)
    retirement_sip = _sip_required(retirement_gap, ASSUMPTIONS["balancedReturn"], years_to_retirement)
    _add_goal(goals, "Retirement Corpus", "Required", f"{years_to_retirement} years", years_to_retirement, retirement_corpus / ((1 + ASSUMPTIONS["retirementExpenseInflation"]) ** years_to_retirement), retirement_corpus, existing_retirement_fv, retirement_sip, "Critical", f"Includes current EPF/PPF/NPS/retirement SIP monthly contributions projected to age {retirement_age}.", "Corpus = annual expense at retirement ÷ 3.5%; existing allocation = current retirement assets FV + current retirement SIP FV", existing_monthly=existing_retirement_monthly)
    unsecured_debt = _num(liabilities.get("personalLoan")) + _num(liabilities.get("educationLoan")) + _num(liabilities.get("creditCard")) + _num(liabilities.get("vehicleLoan")) + _num(liabilities.get("otherDebt"))
    if unsecured_debt > 0:
        _add_goal(goals, "High-Interest Debt Repayment", "Required", "12 months", 1, unsecured_debt, unsecured_debt, 0, unsecured_debt / 12, "Critical", "Clear unsecured/high-interest debt before optional investing.", "Debt gap = outstanding unsecured debt")
    if not basics.get("ownsHouse"):
        home_years = _extract_timeline_years(profile, ["home", "house", "flat"], 7)
        present_home_cost = 7500000 if basics.get("cityTier") == "Tier 1" else 5000000
        future_home_cost = _fv(present_home_cost, ASSUMPTIONS["realEstateInflation"], home_years)
        down_payment = future_home_cost * 0.20
        home_existing = min(liquid_assets, down_payment)
        _add_goal(goals, "Home Down Payment", "Suggested", f"{home_years} years", home_years, present_home_cost * 0.20, down_payment, home_existing, _sip_required(max(0, down_payment - home_existing), ASSUMPTIONS["balancedReturn"], home_years), "Medium", "Only the down payment is treated as the goal; the rest would normally be financed by a loan.", "Future down payment = home cost × 20% × (1 + real-estate inflation)^years")
    elif _num(liabilities.get("homeLoan")) > 0:
        home_loan = _num(liabilities.get("homeLoan"))
        _add_goal(goals, "Home Loan Prepayment", "Required", "As cash flow allows", 1, home_loan, home_loan, 0, home_loan / 12, "Medium", "Prepay only after emergency fund and insurance are fixed.", "Prepayment target = outstanding home loan")
    kids = basics.get("kids", [])
    for kid in kids:
        child_name = kid.get("name") or "Child"
        child_age = _int(kid.get("age"))
        existing_child_monthly = _num(current_investments.get("childEducationSip")) / max(1, len(kids))
        school_years = max(1, 18 - child_age)
        education_pv = 1500000
        education_fv = _fv(education_pv, ASSUMPTIONS["educationInflation"], school_years)
        education_existing_fv = _future_value_monthly(existing_child_monthly, ASSUMPTIONS["balancedReturn"], school_years)
        _add_goal(goals, f"{child_name} Education", "Required", f"{school_years} years", school_years, education_pv, education_fv, education_existing_fv, _sip_required(max(0, education_fv - education_existing_fv), ASSUMPTIONS["balancedReturn"], school_years), "High", "Timeline is based on the child reaching age 18 and includes existing child education SIPs if entered.", "FV = education cost today × (1 + education inflation)^years", existing_monthly=existing_child_monthly)
        higher_ed_years = max(1, 21 - child_age)
        higher_ed_pv = 3000000
        higher_ed_fv = _fv(higher_ed_pv, ASSUMPTIONS["educationInflation"], higher_ed_years)
        _add_goal(goals, f"{child_name} Higher Education", "Suggested", f"{higher_ed_years} years", higher_ed_years, higher_ed_pv, higher_ed_fv, 0, _sip_required(higher_ed_fv, ASSUMPTIONS["balancedReturn"], higher_ed_years), "High", "Suggested for college/professional education; edit/remove if not applicable.", "FV = higher education cost today × (1 + education inflation)^years")
        if _contains_goal_text(profile, "marriage", "wedding"):
            marriage_years = max(1, 25 - child_age)
            marriage_pv = 2000000
            marriage_fv = _fv(marriage_pv, ASSUMPTIONS["marriageInflation"], marriage_years)
            _add_goal(goals, f"{child_name} Marriage", "User-entered", f"{marriage_years} years", marriage_years, marriage_pv, marriage_fv, 0, _sip_required(marriage_fv, ASSUMPTIONS["balancedReturn"], marriage_years), "Medium", "Included only because marriage/wedding was mentioned in future goals.", "FV = marriage cost today × (1 + marriage inflation)^years")
    if _contains_goal_text(profile, "marriage", "wedding") and not kids:
        marriage_years = _extract_timeline_years(profile, ["marriage", "wedding"], 5)
        marriage_pv = 2000000
        marriage_fv = _fv(marriage_pv, ASSUMPTIONS["marriageInflation"], marriage_years)
        _add_goal(goals, "Marriage / Wedding Fund", "User-entered", f"{marriage_years} years", marriage_years, marriage_pv, marriage_fv, 0, _sip_required(marriage_fv, ASSUMPTIONS["balancedReturn"], marriage_years), "Medium", "Included only because marriage/wedding was explicitly entered by the user.", "FV = wedding cost today × (1 + marriage inflation)^years")
    if basics.get("parentsDependent") and _int(basics.get("dependentParentsCount")) > 0:
        parent_count = _int(basics.get("dependentParentsCount"))
        parent_medical_pv = 500000 * parent_count
        parent_medical_years = 5
        parent_medical_fv = _fv(parent_medical_pv, ASSUMPTIONS["medicalInflation"], parent_medical_years)
        _add_goal(goals, "Parents Medical Support Fund", "Required", f"{parent_medical_years} years", parent_medical_years, parent_medical_pv, parent_medical_fv, 0, _sip_required(parent_medical_fv, ASSUMPTIONS["balancedReturn"], parent_medical_years), "High", "Included because parents are financially dependent.", "FV = medical support cost today × (1 + medical inflation)^years")
    if _contains_goal_text(profile, "car", "vehicle"):
        car_years = _extract_timeline_years(profile, ["car", "vehicle"], 5)
        car_pv = 1500000
        car_fv = _fv(car_pv, ASSUMPTIONS["generalInflation"], car_years)
        _add_goal(goals, "Vehicle Purchase", "User-entered", f"{car_years} years", car_years, car_pv, car_fv, 0, _sip_required(car_fv, ASSUMPTIONS["balancedReturn"], car_years), "Low", "Included only because car/vehicle was mentioned in future goals.", "FV = vehicle cost today × (1 + general inflation)^years")
    if _contains_goal_text(profile, "vacation", "travel", "trip"):
        vacation_years = _extract_timeline_years(profile, ["vacation", "travel", "trip"], 2)
        vacation_pv = 500000
        vacation_fv = _fv(vacation_pv, ASSUMPTIONS["generalInflation"], vacation_years)
        _add_goal(goals, "Vacation / Travel Fund", "User-entered", f"{vacation_years} years", vacation_years, vacation_pv, vacation_fv, 0, _sip_required(vacation_fv, ASSUMPTIONS["preRetirementDebtReturn"], vacation_years), "Low", "Included only because vacation/travel was mentioned in future goals.", "FV = travel cost today × (1 + general inflation)^years")
    high_priority_future_goals = sum(g["gap"] for g in goals if g["priority"] in {"Critical", "High"} and g["name"] != "Emergency Fund")
    required_life_cover = max(0, monthly_expenses * 12 * 15 + _num(summary["totalLiabilities"]) + high_priority_future_goals - liquid_assets)
    _add_goal(goals, "Life Insurance Gap", "Required", "Immediate review", 0, required_life_cover, required_life_cover, _num(insurance.get("life")), 0, "High" if required_life_cover > _num(insurance.get("life")) else "Low", "This is a cover-gap calculation, not an investment SIP.", "Required cover = 15× annual expenses + liabilities + high-priority goals - liquid assets")
    health_required = 1000000 if basics.get("maritalStatus") == "single" else 2000000
    health_required += 500000 * len(kids) + 500000 * _int(basics.get("dependentParentsCount"))
    _add_goal(goals, "Health Insurance Gap", "Required", "Immediate review", 0, health_required, health_required, _num(insurance.get("health")), 0, "High" if health_required > _num(insurance.get("health")) else "Low", "This is a cover-gap calculation, not an investment SIP.", "Required cover uses base family cover plus child/parent buffers")
    unallocated_surplus = _allocate_recommended_investments(goals, available_new_surplus)
    total_target_monthly = sum(g["targetMonthlyInvestment"] for g in goals)
    total_recommended_monthly = sum(g["monthlyInvestment"] for g in goals)
    return {"goals": goals, "retirement": {"yearsToRetirement": years_to_retirement, "monthlyExpenseAtRetirement": retirement_monthly_expense, "annualExpenseAtRetirement": retirement_annual_expense, "corpusRequired": retirement_corpus, "existingRetirementAssetsProjected": existing_retirement_assets_fv, "existingRetirementContributionsProjected": existing_retirement_contrib_fv, "existingRetirementProjected": existing_retirement_fv, "gap": retirement_gap, "targetMonthlySip": retirement_sip, "recommendedAdditionalSip": next((g["monthlyInvestment"] for g in goals if g["name"] == "Retirement Corpus"), 0)}, "totalTargetMonthlyInvestment": _money(total_target_monthly), "totalMonthlyInvestment": _money(total_recommended_monthly), "unallocatedSurplus": unallocated_surplus}


def _goal_row(no, goal):
    return (
        f"| {no} | {goal['name']} | {goal['type']} | {goal['timeline']} | "
        f"{_fmt_money(goal['presentCost'])} | {_fmt_money(goal['futureCost'])} | "
        f"{_fmt_money(goal['existingAllocation'])} | {_fmt_money(goal['gap'])} | "
        f"{_fmt_money(goal['targetMonthlyInvestment'])} | {_fmt_money(goal['existingMonthlyInvestment'])} | "
        f"{_fmt_money(goal['monthlyInvestment'])} | {goal.get('fundingStatus', 'Not funded')} | {goal['priority']} |"
    )


def build_report(profile, summary, plan, ai_notes=None):
    basics = profile.get("basics", {}) or {}
    insurance = profile.get("insurance", {}) or {}
    goals = plan["goals"]
    lines = []
    lines.append("### 1. Feasibility Check")
    lines.append("")
    if summary["monthlySurplus"] <= 0:
        lines.append(f"**Not currently feasible.** Monthly expenses exceed average monthly income by **{_fmt_money(abs(summary['monthlySurplus']))}**. Do not start new long-term SIPs until this gap is fixed.")
    else:
        lines.append(f"Current monthly surplus before existing investments: **{_fmt_money(summary['monthlySurplus'])}**.")
    lines.append("")
    lines.append(f"- Average monthly income: {_fmt_money(summary['monthlyIncome'])}")
    lines.append(f"- Monthly expenses: {_fmt_money(summary['monthlyExpenseBreakdown']['fixed'])} fixed + {_fmt_money(summary['monthlyExpenseBreakdown']['variable'])} variable + {_fmt_money(summary['monthlyExpenseBreakdown']['annualProrated'])} annual prorated + {_fmt_money(summary['monthlyExpenseBreakdown']['emi'])} EMI = {_fmt_money(summary['monthlyExpenses'])}")
    lines.append(f"- Existing monthly investments entered: {_fmt_money(summary['currentMonthlyInvestments'])}")
    lines.append(f"- Remaining surplus available for new recommendations: {_fmt_money(summary['remainingSurplusAfterExistingInvestments'])}")
    lines.append(f"- Recommended new monthly investments in this plan: {_fmt_money(plan['totalMonthlyInvestment'])}")
    lines.append(f"- Emergency fund: {summary['emergencyFundMonths']} months")
    for warning in summary.get("warnings", []):
        lines.append(f"- Warning: {warning}")
    lines.append("")
    lines.append("### 2. User Financial Snapshot")
    lines.append("")
    child_summary = ", ".join(f"{k['name']} age {k['age']}" for k in basics.get("kids", [])) or "None"
    lines.extend([f"- Age: {basics.get('age')}", f"- Desired retirement age: {basics.get('desiredRetirementAge')}", f"- Country / city tier: {basics.get('country')} / {basics.get('cityTier')}", f"- Marital status: {basics.get('maritalStatus')}", f"- Children: {child_summary}", f"- Parents dependent: {'Yes' if basics.get('parentsDependent') else 'No'}", f"- Owns house: {'Yes' if basics.get('ownsHouse') else 'No'}", f"- Total assets: {_fmt_money(summary['totalAssets'])}", f"- Total liabilities: {_fmt_money(summary['totalLiabilities'])}", f"- Life cover: {_fmt_money(insurance.get('life'))}", f"- Health cover: {_fmt_money(insurance.get('health'))}", f"- Risk profile: {profile.get('risk')}"])
    lines.append("")
    lines.append("### 3. Key Assumptions Used")
    lines.append("")
    lines.extend([f"- General inflation: {_fmt_pct(ASSUMPTIONS['generalInflation'])}", f"- Education inflation: {_fmt_pct(ASSUMPTIONS['educationInflation'])}", f"- Medical inflation: {_fmt_pct(ASSUMPTIONS['medicalInflation'])}", f"- Real estate inflation: {_fmt_pct(ASSUMPTIONS['realEstateInflation'])}", f"- Balanced portfolio return: {_fmt_pct(ASSUMPTIONS['balancedReturn'])}", f"- Debt/short-term return: {_fmt_pct(ASSUMPTIONS['preRetirementDebtReturn'])}", f"- Safe withdrawal rate: {_fmt_pct(ASSUMPTIONS['safeWithdrawalRate'])}", f"- Life expectancy: {ASSUMPTIONS['lifeExpectancy']}"])
    lines.append("")
    lines.append("### 4. Financial Goal Summary Table")
    lines.append("")
    lines.append("| No. | Goal | Type | Timeline | Present Cost | Future Cost | Existing Allocation | Gap | Target Monthly | Existing Monthly | Recommended New Monthly | Funding | Priority |")
    lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for index, goal in enumerate(goals, 1):
        lines.append(_goal_row(index, goal))
    lines.append("")
    lines.append("### 5. Detailed Goal-Wise Plan")
    for index, goal in enumerate(goals, 1):
        lines.extend(["", f"#### {index}. {goal['name']}", f"- Type: {goal['type']}", f"- Timeline: {goal['timeline']}", f"- Formula: {goal['formula']}", f"- Present cost: {_fmt_money(goal['presentCost'])}", f"- Future cost: {_fmt_money(goal['futureCost'])}", f"- Existing allocation at goal date: {_fmt_money(goal['existingAllocation'])}", f"- Gap: {_fmt_money(goal['gap'])}", f"- Target monthly investment: {_fmt_money(goal['targetMonthlyInvestment'])}", f"- Existing monthly investment mapped to this goal: {_fmt_money(goal['existingMonthlyInvestment'])}", f"- Recommended new monthly investment: {_fmt_money(goal['monthlyInvestment'])}", f"- Funding status: {goal.get('fundingStatus', 'Not funded')}", f"- Priority: {goal['priority']}", f"- Notes: {goal['notes']}"])
    retirement = plan["retirement"]
    lines.extend(["", "### 6. Retirement Planning", "", f"- Years to retirement: {retirement['yearsToRetirement']}", f"- Current monthly expenses: {_fmt_money(summary['monthlyExpenses'])}", f"- Monthly expenses at retirement: {_fmt_money(retirement['monthlyExpenseAtRetirement'])}", f"- Annual expenses at retirement: {_fmt_money(retirement['annualExpenseAtRetirement'])}", f"- Retirement corpus required: {_fmt_money(retirement['corpusRequired'])}", f"- Current retirement assets projected: {_fmt_money(retirement['existingRetirementAssetsProjected'])}", f"- Current monthly retirement contributions projected: {_fmt_money(retirement['existingRetirementContributionsProjected'])}", f"- Total projected retirement allocation: {_fmt_money(retirement['existingRetirementProjected'])}", f"- Retirement gap after existing EPF/NPS/PPF/SIP contributions: {_fmt_money(retirement['gap'])}", f"- Target additional SIP required: {_fmt_money(retirement['targetMonthlySip'])}", f"- Recommended additional SIP now: {_fmt_money(retirement['recommendedAdditionalSip'])}", "", "### 7. Child Planning", ""])
    child_goals = [g for g in goals if "Education" in g["name"] or "Marriage" in g["name"]]
    if child_goals:
        for goal in child_goals:
            lines.append(f"- {goal['name']}: {goal['timeline']}, future cost {_fmt_money(goal['futureCost'])}, target monthly {_fmt_money(goal['targetMonthlyInvestment'])}, recommended new monthly {_fmt_money(goal['monthlyInvestment'])}")
    else:
        lines.append("Not applicable because no children were entered.")
    lines.extend(["", "### 8. Parents Dependency", ""])
    if basics.get("parentsDependent") and _int(basics.get("dependentParentsCount")) > 0:
        lines.append(f"Planning included for {_int(basics.get('dependentParentsCount'))} dependent parent(s).")
    else:
        lines.append("Not applicable because parents were not marked financially dependent.")
    lines.extend(["", "### 9. Home Planning", ""])
    home_goals = [g for g in goals if "Home" in g["name"]]
    if home_goals:
        for goal in home_goals:
            lines.append(f"- {goal['name']}: {goal['timeline']}, gap {_fmt_money(goal['gap'])}, target monthly {_fmt_money(goal['targetMonthlyInvestment'])}, recommended new monthly {_fmt_money(goal['monthlyInvestment'])}")
    else:
        lines.append("No home goal included because no home purchase/prepayment condition applied.")
    lines.extend(["", "### 10. Insurance Gap Analysis", ""])
    for goal in [g for g in goals if "Insurance Gap" in g["name"]]:
        gap = max(0, goal["futureCost"] - goal["existingAllocation"])
        lines.append(f"- {goal['name']}: required {_fmt_money(goal['futureCost'])}, existing {_fmt_money(goal['existingAllocation'])}, gap {_fmt_money(gap)}")
    lines.extend(["", "### 11. Monthly Investment Feasibility", ""])
    lines.append(f"- Total target monthly investment to fully fund all goals: {_fmt_money(plan['totalTargetMonthlyInvestment'])}")
    lines.append(f"- Current monthly surplus before existing investments: {_fmt_money(summary['monthlySurplus'])}")
    lines.append(f"- Existing monthly investments entered: {_fmt_money(summary['currentMonthlyInvestments'])}")
    lines.append(f"- Remaining surplus for new investment recommendations: {_fmt_money(summary['remainingSurplusAfterExistingInvestments'])}")
    lines.append(f"- Recommended new monthly investment total: {_fmt_money(plan['totalMonthlyInvestment'])}")
    if summary["monthlySurplus"] <= 0:
        lines.append(f"- Status: Not feasible. First reduce expenses or increase income by at least {_fmt_money(abs(summary['monthlySurplus']))}.")
    elif plan["totalTargetMonthlyInvestment"] > summary["remainingSurplusAfterExistingInvestments"]:
        lines.append("- Status: Partially funded. Recommendations are capped to surplus and prioritized by urgency.")
    else:
        lines.append("- Status: Fully feasible with current surplus.")
    lines.extend(["", "### 12. Priority-Based Action Plan", "", "#### Immediate (0-3 months)"])
    if summary["monthlySurplus"] <= 0:
        lines.append(f"- Fix monthly cash-flow gap of {_fmt_money(abs(summary['monthlySurplus']))}.")
    lines.extend(["- Keep recommendations capped to available surplus; do not start SIPs beyond cash-flow capacity.", "- Build or restore emergency fund before optional goals.", "- Review insurance gaps and buy term/health cover if required.", "", "#### Short term (3 months - 2 years)", "- Fund Critical and High priority goals first.", "- Map every existing SIP to a goal so projections stay accurate.", "", "#### Medium term (2-7 years)", "- Add Medium priority goals only after emergency, insurance, and retirement tracking are stable.", "", "#### Long term (7+ years)", "- Increase SIPs with income growth and review assumptions yearly.", "", "### 13. Final Recommendations", ""])
    lines.append(ai_notes.strip() if ai_notes else "Use this plan as a baseline. Update expenses, insurance, assets, current SIPs, and goals yearly so timelines and SIPs stay realistic.")
    lines.append("")
    lines.append("This is educational financial planning guidance, not registered financial advice.")
    return "\n".join(lines)


AI_NOTES_PROMPT = """You are a financial planning assistant. The backend already calculated the plan deterministically.
Write only 3-5 concise recommendation bullets based on the supplied profile, summary, and deterministic goals.
Do not add new goals. Do not change any number. Do not recommend investments beyond remainingSurplusAfterExistingInvestments.
If cash flow is negative, focus on cash-flow repair, emergency fund, and insurance review.
No markdown heading. Bullets only.
"""


def call_bedrock_notes(profile, summary, plan):
    payload = {"profile": profile, "summary": summary, "deterministicGoals": [{"name": g["name"], "timeline": g["timeline"], "futureCost": g["futureCost"], "gap": g["gap"], "targetMonthlyInvestment": g["targetMonthlyInvestment"], "existingMonthlyInvestment": g["existingMonthlyInvestment"], "recommendedNewMonthlyInvestment": g["monthlyInvestment"], "priority": g["priority"]} for g in plan["goals"]]}
    response = bedrock.converse(modelId=MODEL_ID, messages=[{"role": "user", "content": [{"text": json.dumps(payload, ensure_ascii=False)}]}], system=[{"text": AI_NOTES_PROMPT}], inferenceConfig={"maxTokens": 700, "temperature": 0.1})
    return response["output"]["message"]["content"][0]["text"].strip()


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
    validation_errors = validate_profile(profile)
    if validation_errors:
        return respond(400, {"error": "Please fix required fields.", "validationErrors": validation_errors})
    summary = compute_summary(profile)
    plan = build_goal_plan(profile, summary)
    try:
        ai_notes = call_bedrock_notes(profile, summary, plan)
    except Exception:
        ai_notes = None
    report = build_report(profile, summary, plan, ai_notes)
    return respond(200, {"summary": summary, "plan": plan, "report": report})
