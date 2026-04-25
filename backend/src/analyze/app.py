"POST /analyze - FinOS CFP engine: cashflow, tax, risk, goals, retirement, insurance, allocation."

import copy
import json
import os
from datetime import datetime

import boto3

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
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

RETIREMENT_CATEGORIES = {"epf", "ppf", "nps", "retirementSip", "equityIndex", "equityLargeCap", "equityFlexiCap", "nifty50"}
LOW_RISK_CATEGORIES = {"fdRd", "debtFund", "liquidFund", "ppf", "epf"}
GROWTH_CATEGORIES = {"momentum", "value", "midcap", "smallcap", "niftyNext50", "customStockBasket", "multicap", "flexicap", "nifty50", "us500", "smallcase", "equityLargeCap", "equityMidCap", "equitySmallCap", "equityFlexiCap", "equityIndex"}

DEFAULT_RETURNS = {
    "momentum": 18,
    "value": 17,
    "midcap": 17,
    "smallcap": 16,
    "niftyNext50": 16,
    "customStockBasket": 18,
    "multicap": 15,
    "flexicap": 14,
    "nifty50": 13,
    "us500": 15,
    "gold": 12,
    "reitInvit": 12,
    "equityLargeCap": 11,
    "equityMidCap": 12,
    "equitySmallCap": 13,
    "equityFlexiCap": 11,
    "equityIndex": 11,
    "elss": 11,
    "smallcase": 12,
    "debtFund": 7,
    "liquidFund": 5.5,
    "hybridFund": 9,
    "fdRd": 6.5,
    "epf": 8.25,
    "ppf": 7.1,
    "nps": 10,
    "retirementSip": 10,
    "childEducation": 10,
    "realEstate": 6,
    "other": 8,
}



def _money_value(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _goal_row_for_truth(goal):
    return {
        "name": goal.get("name", "Goal"),
        "priority": goal.get("priority", "Medium"),
        "years": goal.get("years", 0),
        "todayNeed": _money(goal.get("presentCost", goal.get("todayNeed", 0))),
        "futureNeed": _money(goal.get("futureCost", goal.get("futureNeed", 0))),
        "existingAllocation": _money(goal.get("existingAllocation", 0)),
        "gap": _money(goal.get("gap", 0)),
        "targetMonthlyInvestment": _money(goal.get("targetMonthlyInvestment", 0)),
        "recommendedMonthlyInvestment": _money(goal.get("recommendedMonthlyInvestment", 0)),
        "fundingStatus": goal.get("fundingStatus", ""),
        "notes": goal.get("notes", ""),
    }


def _format_tax_slabs_markdown(title, rows):
    if not rows:
        return f"#### {title}\n\nNo slab rows available.\n"
    lines = [
        f"#### {title}",
        "",
        "| Slab | Rate | Taxable amount | Tax |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('range', '')} | {row.get('ratePct', 0)}% | {_fmt_money(row.get('taxableAmount'))} | {_fmt_money(row.get('tax'))} |"
        )
    return "\n".join(lines)


def _build_truth_sheet(body):
    summary = body.get("summary", {}) or {}
    plan = body.get("plan", {}) or {}
    tax = summary.get("tax", {}) or {}
    insurance = plan.get("insurance", {}) or {}

    goals = [_goal_row_for_truth(g) for g in (plan.get("goals", []) or [])]
    total_target_sip = sum(_money_value(g.get("targetMonthlyInvestment")) for g in goals)
    total_recommended_sip = sum(_money_value(g.get("recommendedMonthlyInvestment")) for g in goals)
    total_future_need = sum(_money_value(g.get("futureNeed")) for g in goals)
    total_today_need = sum(_money_value(g.get("todayNeed")) for g in goals)

    life_required = _money(insurance.get("requiredLifeCover", insurance.get("recommendedLifeCover", 0)))
    life_existing = _money(insurance.get("existingLifeCover", insurance.get("currentLifeCover", 0)))
    health_required = _money(insurance.get("requiredHealthCover", insurance.get("recommendedHealthCover", 0)))
    health_existing = _money(insurance.get("existingHealthCover", insurance.get("currentHealthCover", 0)))

    return {
        "fyLabel": tax.get("fyLabel", "FY 2026-27"),
        "aiGuardrails": {
            "aiGenerated": True,
            "guardrailChecked": True,
            "maxNewMonthlyInvestment": _money(summary.get("remainingSurplusAfterExistingInvestments", 0)),
            "noGuaranteedReturns": True,
            "educationalOnly": True,
        },
        "cashflow": {
            "monthlyIncome": _money(summary.get("monthlyIncome", 0)),
            "monthlyExpenses": _money(summary.get("monthlyExpenses", 0)),
            "monthlySurplus": _money(summary.get("monthlySurplus", 0)),
            "currentMonthlyInvestments": _money(summary.get("currentMonthlyInvestments", 0)),
            "remainingSurplusAfterExistingInvestments": _money(summary.get("remainingSurplusAfterExistingInvestments", 0)),
        },
        "goals": goals,
        "goalTotals": {
            "todayNeed": _money(total_today_need),
            "futureNeed": _money(total_future_need),
            "targetMonthlyInvestment": _money(total_target_sip),
            "recommendedMonthlyInvestment": _money(total_recommended_sip),
        },
        "tax": tax,
        "insurance": {
            **insurance,
            "existingLifeCover": life_existing,
            "requiredLifeCover": life_required,
            "lifeCoverGap": _money(max(0, _money_value(life_required) - _money_value(life_existing))),
            "existingHealthCover": health_existing,
            "requiredHealthCover": health_required,
            "healthCoverGap": _money(max(0, _money_value(health_required) - _money_value(health_existing))),
        },
    }


def _build_visual_markdown_report(profile, body):
    truth = body.get("truthSheet") or _build_truth_sheet(body)
    summary = body.get("summary", {}) or {}
    plan = body.get("plan", {}) or {}
    tax = truth.get("tax", {}) or {}
    insurance = truth.get("insurance", {}) or {}
    goals = truth.get("goals", []) or []
    cashflow = truth.get("cashflow", {}) or {}

    risk = summary.get("riskProfile", {}) or {}
    top_priorities = summary.get("topPriorities") or []
    diagnosis = summary.get("oneLineDiagnosis") or "SmartFinly AI has reviewed your cash-flow, tax, insurance, goals and investments."

    lines = [
        "# SmartFinly AI Financial Plan",
        "",
        "> **AI generated with guardrails:** SmartFinly AI creates the recommendation, while backend guardrails cap affordability, preserve tax math, preserve insurance facts, and prevent guaranteed-return claims.",
        "",
        f"**Financial year:** {truth.get('fyLabel', 'FY 2026-27')}",
        "",
        "## 1. AI Diagnosis",
        "",
        diagnosis,
        "",
    ]

    if top_priorities:
        lines.extend(["### Top priorities", ""])
        for idx, priority in enumerate(top_priorities[:5], 1):
            lines.append(f"{idx}. {priority}")
        lines.append("")

    lines.extend([
        "## 2. Cash-flow Guardrail",
        "",
        "| Item | Amount |",
        "|---|---:|",
        f"| Monthly income | {_fmt_money(cashflow.get('monthlyIncome'))} |",
        f"| Monthly expenses | {_fmt_money(cashflow.get('monthlyExpenses'))} |",
        f"| Monthly surplus | {_fmt_money(cashflow.get('monthlySurplus'))} |",
        f"| Current monthly investments | {_fmt_money(cashflow.get('currentMonthlyInvestments'))} |",
        f"| Maximum new monthly investment allowed | {_fmt_money(cashflow.get('remainingSurplusAfterExistingInvestments'))} |",
        "",
        "## 3. Goal Summary",
        "",
        "| Goal | Priority | Years | Today need | Future need | Gap | Target SIP | AI recommended SIP | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ])

    if goals:
        for goal in goals:
            lines.append(
                f"| {goal.get('name')} | {goal.get('priority')} | {goal.get('years')} | {_fmt_money(goal.get('todayNeed'))} | {_fmt_money(goal.get('futureNeed'))} | {_fmt_money(goal.get('gap'))} | {_fmt_money(goal.get('targetMonthlyInvestment'))} | {_fmt_money(goal.get('recommendedMonthlyInvestment'))} | {goal.get('fundingStatus', '')} |"
            )
    else:
        lines.append("| No goals returned | — | — | — | — | — | — | — | — |")

    lines.extend([
        "",
        "### Goal totals",
        "",
        f"- Total today need: **{_fmt_money(truth.get('goalTotals', {}).get('todayNeed'))}**",
        f"- Total future need: **{_fmt_money(truth.get('goalTotals', {}).get('futureNeed'))}**",
        f"- Total calculated target SIP: **{_fmt_money(truth.get('goalTotals', {}).get('targetMonthlyInvestment'))}**",
        f"- Total AI recommended SIP after affordability guardrail: **{_fmt_money(truth.get('goalTotals', {}).get('recommendedMonthlyInvestment'))}**",
        "",
        "## 4. Tax Calculation",
        "",
        f"- Regime suggested: **{tax.get('preferredRegime', '—')}**",
        f"- Gross income considered: **{_fmt_money(tax.get('grossIncome'))}**",
        f"- Old regime deductions: **{_fmt_money(tax.get('oldDeductions'))}**",
        f"- New regime deductions: **{_fmt_money(tax.get('newDeductions'))}**",
        f"- Old taxable income: **{_fmt_money(tax.get('oldTaxable'))}**",
        f"- New taxable income: **{_fmt_money(tax.get('newTaxable'))}**",
        f"- Old tax after rebate/surcharge/cess: **{_fmt_money(tax.get('oldTax'))}**",
        f"- New tax after rebate/marginal relief/surcharge/cess: **{_fmt_money(tax.get('newTax'))}**",
        "",
        _format_tax_slabs_markdown("Old regime slab-wise calculation", tax.get("oldSlabBreakdown", [])),
        "",
        f"- Old regime rebate: **{_fmt_money(tax.get('oldRebate'))}**",
        f"- Old regime surcharge: **{_fmt_money(tax.get('oldSurcharge'))}**",
        f"- Old regime cess: **{_fmt_money(tax.get('oldCess'))}**",
        "",
        _format_tax_slabs_markdown("New regime slab-wise calculation", tax.get("newSlabBreakdown", [])),
        "",
        f"- New regime rebate: **{_fmt_money(tax.get('newRebate'))}**",
        f"- New regime marginal relief: **{_fmt_money(tax.get('newMarginalRelief'))}**",
        f"- New regime surcharge: **{_fmt_money(tax.get('newSurcharge'))}**",
        f"- New regime cess: **{_fmt_money(tax.get('newCess'))}**",
        "",
        "## 5. Insurance Calculation",
        "",
        "| Cover | Existing | Required | Gap | Formula / assumption |",
        "|---|---:|---:|---:|---|",
        f"| Life cover | {_fmt_money(insurance.get('existingLifeCover'))} | {_fmt_money(insurance.get('requiredLifeCover'))} | {_fmt_money(insurance.get('lifeCoverGap'))} | Liabilities + family income replacement + major dependent goals |",
        f"| Health cover | {_fmt_money(insurance.get('existingHealthCover'))} | {_fmt_money(insurance.get('requiredHealthCover'))} | {_fmt_money(insurance.get('healthCoverGap'))} | Base family floater adjusted for spouse, children, parents and city type |",
        "",
        insurance.get("notes", "Insurance numbers are educational estimates and should be validated before purchase."),
        "",
        "## 6. Investment Mapping",
        "",
        f"- AI risk profile: **{risk.get('label', '—')}**",
        f"- Suggested allocation: **{risk.get('equity', '—')}% equity / {risk.get('debt', '—')}% debt / {risk.get('gold', '—')}% gold**",
        f"- Reason: {risk.get('reason', 'Based on age, goal timelines, dependents and cash-flow capacity.')}",
        "",
        "## 7. Action Plan",
        "",
    ])

    action_plan = plan.get("actionPlan") or []
    if action_plan:
        for idx, item in enumerate(action_plan[:8], 1):
            lines.append(f"{idx}. {item}")
    else:
        lines.extend([
            "1. Keep emergency fund and insurance gaps as first priority.",
            "2. Invest only up to the affordability-capped surplus.",
            "3. Review tax regime before payroll declaration.",
        ])

    lines.extend([
        "",
        "## 8. Trust & Compliance Note",
        "",
        "- This output is AI-generated and guardrail-checked.",
        "- It is for educational/sampling use only.",
        "- It is not SEBI-registered investment advice.",
        "- It does not guarantee returns.",
        "- Verify tax, insurance and investment actions with a qualified professional before acting.",
    ])

    return "\n".join(lines)


def _upgrade_ai_output_contract(body):
    if not isinstance(body, dict):
        return body
    body = dict(body)
    truth = _build_truth_sheet(body)
    body["truthSheet"] = truth
    body["report"] = _build_visual_markdown_report({}, body)

    summary = body.setdefault("summary", {})
    summary["aiGeneratedWithGuardrails"] = True
    summary["factsSource"] = "truthSheet"
    summary["trustMessage"] = "AI-generated plan with affordability, tax, insurance and compliance guardrails."
    return body


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

    normalized_investments = []
    for idx, inv in enumerate(cleaned.get("investments") or []):
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
            "expectedReturnPct": _num(inv.get("expectedReturnPct")) or DEFAULT_RETURNS.get(category, 8),
            "goal": inv.get("goal") or infer_goal_from_category(category),
        })
    salary = cleaned.get("salary", {}) or {}
    employee_epf_monthly = _num(salary.get("monthlyEmployeeEpf"))
    employer_nps_monthly = _num(salary.get("monthlyEmployerNps"))

    if employee_epf_monthly > 0:
        normalized_investments.append({
            "name": "Auto EPF from salary",
            "category": "epf",
            "monthlyAmount": employee_epf_monthly,
            "currentValue": 0,
            "expectedReturnPct": DEFAULT_RETURNS.get("epf", 8.25),
            "goal": "retirement",
            "source": "salary",
        })

    if employer_nps_monthly > 0:
        normalized_investments.append({
            "name": "Auto employer NPS from salary",
            "category": "nps",
            "monthlyAmount": employer_nps_monthly,
            "currentValue": 0,
            "expectedReturnPct": DEFAULT_RETURNS.get("nps", 10),
            "goal": "retirement",
            "source": "salary",
        })

    cleaned["investments"] = normalized_investments

    normalized_goals = []
    for idx, goal in enumerate(cleaned.get("goals") or []):
        if not isinstance(goal, dict):
            continue
        present_cost = _num(goal.get("presentCost"))
        years = _int(goal.get("years"))
        if present_cost <= 0 or years <= 0:
            continue
        category = goal.get("category") or "wealth"
        normalized_goals.append({
            "name": str(goal.get("name") or f"Goal {idx + 1}").strip(),
            "category": category,
            "presentCost": present_cost,
            "years": years,
            "inflationPct": _num(goal.get("inflationPct")) or default_goal_inflation(category) * 100,
            "expectedReturnPct": _num(goal.get("expectedReturnPct")) or 9,
            "priority": goal.get("priority") or default_goal_priority(category),
        })
    cleaned["goals"] = normalized_goals
    return cleaned


def infer_goal_from_category(category):
    if category in RETIREMENT_CATEGORIES:
        return "retirement"
    if category == "childEducation":
        return "childEducation"
    if category == "elss":
        return "taxSaving"
    return "wealth"


def default_goal_inflation(category):
    if category in {"education", "childEducation"}:
        return ASSUMPTIONS["educationInflation"]
    if category in {"medical", "parentsMedical"}:
        return ASSUMPTIONS["medicalInflation"]
    if category in {"home", "realEstate"}:
        return ASSUMPTIONS["realEstateInflation"]
    return ASSUMPTIONS["generalInflation"]


def default_goal_priority(category):
    if category in {"retirement", "emergency", "debt"}:
        return "Critical"
    if category in {"education", "childEducation", "insurance"}:
        return "High"
    if category in {"home", "medical"}:
        return "Medium"
    return "Low"


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
    if basics.get("parentsDependent") and _int(basics.get("dependentParentsCount")) < 1:
        errors.append("Dependent parent count must be at least 1.")
    return errors



def compute_tax(profile):
    income = profile.get("income", {}) or {}
    salary = profile.get("salary", {}) or {}
    basics = profile.get("basics", {}) or {}
    tax = profile.get("tax", {}) or {}

    def annual_value(*keys, monthly_fallback=False):
        for key in keys:
            value = _num(salary.get(key))
            if value:
                return value * 12 if monthly_fallback else value
        return 0

    def annual_from_monthly_or_annual(annual_key, monthly_key):
        annual = _num(salary.get(annual_key))
        if annual:
            return annual
        return _num(salary.get(monthly_key)) * 12

    # New annual salary fields. Existing monthly fields are kept as fallback.
    basic_salary = annual_from_monthly_or_annual("basicSalary", "monthlyBasic")
    hra_received = annual_from_monthly_or_annual("hraReceived", "monthlyHra")
    lta = annual_from_monthly_or_annual("lta", "monthlyLta")
    flexible_comp_plan = _num(salary.get("flexibleCompPlan")) or _num(salary.get("monthlySpecialAllowance")) * 12
    bonus_variable = _num(salary.get("bonusVariablePay")) or _num(salary.get("monthlyBonus")) * 12
    nps_employer = _num(salary.get("npsEmployer")) or _num(salary.get("monthlyEmployerNps")) * 12
    epf_contribution = _num(salary.get("epfContribution")) or _num(salary.get("monthlyEmployeeEpf")) * 12
    prof_tax = _num(salary.get("profTax")) or _num(salary.get("monthlyProfessionalTax")) * 12

    telephone_reimbursement = _num(salary.get("telephoneReimbursement"))
    internet_allowance = _num(salary.get("internetAllowance")) or _num(salary.get("internet"))
    meal_allowance = _num(salary.get("meal"))
    leave_encashment = _num(salary.get("leaveEncashment"))
    superannuation = _num(salary.get("superannuation"))
    shift_allowance = _num(salary.get("shiftAllowance"))
    on_call_allowance = _num(salary.get("onCallAllowance"))
    team_party = _num(salary.get("teamParty"))
    awards_non_cash = _num(salary.get("awardsNonCashTaxable"))
    labour_welfare_fund = _num(salary.get("labourWelfareFund"))
    notice_recovery = _num(salary.get("noticeRecovery"))
    income_tax_paid_salary = _num(salary.get("incomeTax"))
    nps_employee = _num(salary.get("npsEmployee")) or _num(tax.get("nps80CCD1B"))
    gross_deductions_input = _num(salary.get("grossDeductions"))
    net_salary = _num(salary.get("netSalary"))

    # Prefer explicit annual gross earning, else sum salary components, else fallback income.
    salary_components_total = (
        basic_salary
        + hra_received
        + lta
        + flexible_comp_plan
        + bonus_variable
        + nps_employer
        + telephone_reimbursement
        + internet_allowance
        + meal_allowance
        + leave_encashment
        + superannuation
        + shift_allowance
        + on_call_allowance
        + team_party
        + awards_non_cash
    )

    fallback_income = (
        (_num(income.get("monthlyAfterTax")) + _num(income.get("otherMonthly"))) * 12
        + _num(income.get("bonusAnnual"))
    )

    gross_salary = _num(salary.get("grossEarning")) or _num(salary.get("annualGross")) or salary_components_total or fallback_income
    other_income = _num(tax.get("otherAnnualIncome"))
    savings_interest = _num(tax.get("interest80TTA_TTB"))
    capital_gain = _num(tax.get("capitalGain"))
    gross_total_income_before_deductions = gross_salary + other_income + capital_gain

    # HRA exemption = minimum of actual HRA, rent paid - 10% basic, 50%/40% basic.
    rent_paid = _num(salary.get("rentPaid")) or _num(salary.get("rentPaidMonthly")) * 12
    city_type = basics.get("cityTier")
    basic_ratio = 0.50 if city_type in {"Metro", "Tier 1"} else 0.40
    auto_hra_exemption = 0
    if hra_received > 0 and basic_salary > 0 and rent_paid > 0:
        auto_hra_exemption = max(
            0,
            min(
                hra_received,
                max(0, rent_paid - (0.10 * basic_salary)),
                basic_ratio * basic_salary,
            ),
        )

    hra_exemption = _num(tax.get("hraExemption")) or auto_hra_exemption

    # Allowance/reimbursement exemptions, capped where common limits are used.
    meal_exemption = min(meal_allowance, 26400)
    telephone_exemption = min(telephone_reimbursement, 24000)
    internet_exemption = min(internet_allowance, 24000)
    leave_encashment_exemption = min(leave_encashment, 300000)

    standard_old = 50000
    standard_new = 75000

    taxable_salary_old = max(
        0,
        gross_salary
        - hra_exemption
        - prof_tax
        - standard_old
        - meal_exemption
        - telephone_exemption
        - internet_exemption
        - leave_encashment_exemption
    )

    taxable_salary_new = max(0, gross_salary - standard_new)

    total_income_old_before_chapter_vi = taxable_salary_old + other_income + capital_gain
    total_income_new_before_chapter_vi = taxable_salary_new + other_income + capital_gain

    # Chapter VI-A deductions for old regime.
    deduction_80c_value = _num(tax.get("deduction80C")) + epf_contribution
    deduction_80c = min(150000, deduction_80c_value)

    deduction_80ccd_1b_value = nps_employee
    deduction_80ccd_1b = min(50000, deduction_80ccd_1b_value)

    # Employer NPS 80CCD(2): 10% basic old, 14% basic new.
    deduction_80ccd2_old_value = nps_employer
    deduction_80ccd2_old_max = basic_salary * 0.10 if basic_salary else nps_employer
    deduction_80ccd2_old = min(deduction_80ccd2_old_value, deduction_80ccd2_old_max)

    deduction_80ccd2_new_value = nps_employer
    deduction_80ccd2_new_max = basic_salary * 0.14 if basic_salary else nps_employer
    deduction_80ccd2_new = min(deduction_80ccd2_new_value, deduction_80ccd2_new_max)

    deduction_80d_self = min(_num(tax.get("health80D")), 25000)
    deduction_80d_parents = min(_num(tax.get("health80DParents")), 50000)
    deduction_80d_total = deduction_80d_self + deduction_80d_parents

    deduction_80g = _num(tax.get("donation80G"))
    deduction_80e = _num(tax.get("educationLoan80E"))
    deduction_80tta = min(savings_interest, 10000)
    home_loan_interest = min(_num(tax.get("homeLoanInterest24B")), 200000)
    deduction_80ee = min(_num(tax.get("homeLoan80EE")), 50000)
    deduction_80eea = min(_num(tax.get("homeLoan80EEA")), 150000)

    old_gross_deductions = (
        deduction_80c
        + deduction_80ccd_1b
        + deduction_80ccd2_old
        + deduction_80d_total
        + deduction_80g
        + deduction_80e
        + deduction_80tta
        + home_loan_interest
        + deduction_80ee
        + deduction_80eea
    )

    old_taxable_income = max(0, total_income_old_before_chapter_vi - old_gross_deductions)
    new_taxable_income = max(0, total_income_new_before_chapter_vi - deduction_80ccd2_new)

    old_slabs = [(250000, 0), (500000, 0.05), (1000000, 0.20), (10**18, 0.30)]
    new_slabs = [
        (400000, 0),
        (800000, 0.05),
        (1200000, 0.10),
        (1600000, 0.15),
        (2000000, 0.20),
        (2400000, 0.25),
        (10**18, 0.30),
    ]

    old_breakdown, old_tax_before_rebate = slab_breakdown(old_taxable_income, old_slabs)
    new_breakdown, new_tax_before_rebate = slab_breakdown(new_taxable_income, new_slabs)

    old_rebate = old_tax_before_rebate if old_taxable_income <= 500000 else 0
    new_rebate = new_tax_before_rebate if new_taxable_income <= 1200000 else 0

    old_tax_after_rebate = max(0, old_tax_before_rebate - old_rebate)
    new_tax_after_rebate_before_relief = max(0, new_tax_before_rebate - new_rebate)

    new_marginal_relief = 0
    if new_taxable_income > 1200000:
        max_tax_due_to_threshold = new_taxable_income - 1200000
        if new_tax_after_rebate_before_relief > max_tax_due_to_threshold:
            new_marginal_relief = new_tax_after_rebate_before_relief - max_tax_due_to_threshold

    new_tax_after_rebate = max(0, new_tax_after_rebate_before_relief - new_marginal_relief)

    def surcharge_rate(taxable_income, regime):
        if taxable_income <= 5000000:
            return 0
        if taxable_income <= 10000000:
            return 0.10
        if taxable_income <= 20000000:
            return 0.15
        if taxable_income <= 50000000:
            return 0.25
        return 0.25 if regime == "new" else 0.37

    old_surcharge_rate = surcharge_rate(old_taxable_income, "old")
    new_surcharge_rate = surcharge_rate(new_taxable_income, "new")
    old_surcharge = old_tax_after_rebate * old_surcharge_rate
    new_surcharge = new_tax_after_rebate * new_surcharge_rate

    old_tax_before_cess = old_tax_after_rebate + old_surcharge
    new_tax_before_cess = new_tax_after_rebate + new_surcharge

    old_cess = old_tax_before_cess * 0.04
    new_cess = new_tax_before_cess * 0.04

    old_tax_payable = old_tax_before_cess + old_cess
    new_tax_payable = new_tax_before_cess + new_cess

    total_tax_paid = _num(tax.get("taxPaid")) or income_tax_paid_salary
    old_refund_or_pay = total_tax_paid - old_tax_payable
    new_refund_or_pay = total_tax_paid - new_tax_payable

    preferred = "Old" if old_tax_payable < new_tax_payable else "New"

    old_tax_percent = (old_tax_payable / gross_salary * 100) if gross_salary else 0
    new_tax_percent = (new_tax_payable / gross_salary * 100) if gross_salary else 0

    return {
        "fyLabel": "FY 2026-27",
        "salaryInputRequired": basics.get("employmentType") == "salaried",
        "grossIncome": _money(gross_salary),
        "grossSalary": _money(gross_salary),
        "grossEarning": _money(gross_salary),
        "salaryComponentsTotal": _money(salary_components_total),
        "grossDeductionsInput": _money(gross_deductions_input),
        "netSalary": _money(net_salary),
        "totalTaxPaid": _money(total_tax_paid),

        "oldDeductions": _money(old_gross_deductions),
        "newDeductions": _money(deduction_80ccd2_new),
        "oldTaxable": _money(old_taxable_income),
        "newTaxable": _money(new_taxable_income),
        "oldTax": _money(old_tax_payable),
        "newTax": _money(new_tax_payable),
        "oldRefundOrNeedToPay": _money(old_refund_or_pay),
        "newRefundOrNeedToPay": _money(new_refund_or_pay),
        "oldTaxPercent": round(old_tax_percent, 2),
        "newTaxPercent": round(new_tax_percent, 2),
        "preferredRegime": preferred,
        "savingsVsOther": _money(abs(old_tax_payable - new_tax_payable)),

        "oldSlabBreakdown": old_breakdown,
        "newSlabBreakdown": new_breakdown,
        "oldTaxBeforeRebate": _money(old_tax_before_rebate),
        "newTaxBeforeRebate": _money(new_tax_before_rebate),
        "oldRebate": _money(old_rebate),
        "newRebate": _money(new_rebate),
        "newMarginalRelief": _money(new_marginal_relief),
        "oldSurcharge": _money(old_surcharge),
        "newSurcharge": _money(new_surcharge),
        "oldCess": _money(old_cess),
        "newCess": _money(new_cess),

        "oldRegimeRows": [
            {"description": "Gross Salary", "value": _money(gross_salary), "maximumNonTaxable": None, "nonTaxable": 0, "netTaxable": _money(gross_salary)},
            {"description": "HRA", "value": _money(hra_received), "maximumNonTaxable": None, "nonTaxable": _money(hra_exemption), "netTaxable": _money(max(0, hra_received - hra_exemption))},
            {"description": "P-Tax", "value": _money(prof_tax), "maximumNonTaxable": None, "nonTaxable": _money(prof_tax), "netTaxable": 0},
            {"description": "Standard Deduction", "value": _money(standard_old), "maximumNonTaxable": _money(standard_old), "nonTaxable": _money(standard_old), "netTaxable": 0},
            {"description": "Total Taxable Salary", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(taxable_salary_old), "netTaxable": None},
            {"description": "Income From Other sources", "value": _money(other_income), "maximumNonTaxable": None, "nonTaxable": 0, "netTaxable": _money(other_income)},
            {"description": "Capital Gain", "value": _money(capital_gain), "maximumNonTaxable": None, "nonTaxable": 0, "netTaxable": _money(capital_gain)},
            {"description": "Total Income", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(total_income_old_before_chapter_vi), "netTaxable": None},
            {"description": "80C", "value": _money(deduction_80c_value), "maximumNonTaxable": 150000, "nonTaxable": _money(deduction_80c), "netTaxable": _money(max(0, deduction_80c_value - deduction_80c))},
            {"description": "80CCD(1B)", "value": _money(deduction_80ccd_1b_value), "maximumNonTaxable": 50000, "nonTaxable": _money(deduction_80ccd_1b), "netTaxable": _money(max(0, deduction_80ccd_1b_value - deduction_80ccd_1b))},
            {"description": "80CCD(2) Employer NPS", "value": _money(deduction_80ccd2_old_value), "maximumNonTaxable": _money(deduction_80ccd2_old_max), "nonTaxable": _money(deduction_80ccd2_old), "netTaxable": _money(max(0, deduction_80ccd2_old_value - deduction_80ccd2_old))},
            {"description": "80D Self/Family", "value": _money(_num(tax.get("health80D"))), "maximumNonTaxable": 25000, "nonTaxable": _money(deduction_80d_self), "netTaxable": _money(max(0, _num(tax.get("health80D")) - deduction_80d_self))},
            {"description": "80D Parents", "value": _money(_num(tax.get("health80DParents"))), "maximumNonTaxable": 50000, "nonTaxable": _money(deduction_80d_parents), "netTaxable": _money(max(0, _num(tax.get("health80DParents")) - deduction_80d_parents))},
            {"description": "80G", "value": _money(deduction_80g), "maximumNonTaxable": None, "nonTaxable": _money(deduction_80g), "netTaxable": 0},
            {"description": "80TTA", "value": _money(savings_interest), "maximumNonTaxable": 10000, "nonTaxable": _money(deduction_80tta), "netTaxable": _money(max(0, savings_interest - deduction_80tta))},
            {"description": "Meal Allowance", "value": _money(meal_allowance), "maximumNonTaxable": 26400, "nonTaxable": _money(meal_exemption), "netTaxable": _money(max(0, meal_allowance - meal_exemption))},
            {"description": "Telephone", "value": _money(telephone_reimbursement), "maximumNonTaxable": 24000, "nonTaxable": _money(telephone_exemption), "netTaxable": _money(max(0, telephone_reimbursement - telephone_exemption))},
            {"description": "Internet", "value": _money(internet_allowance), "maximumNonTaxable": 24000, "nonTaxable": _money(internet_exemption), "netTaxable": _money(max(0, internet_allowance - internet_exemption))},
            {"description": "Leave Encashment", "value": _money(leave_encashment), "maximumNonTaxable": 300000, "nonTaxable": _money(leave_encashment_exemption), "netTaxable": _money(max(0, leave_encashment - leave_encashment_exemption))},
            {"description": "Home Loan Interest", "value": _money(_num(tax.get("homeLoanInterest24B"))), "maximumNonTaxable": 200000, "nonTaxable": _money(home_loan_interest), "netTaxable": _money(max(0, _num(tax.get("homeLoanInterest24B")) - home_loan_interest))},
            {"description": "80EE", "value": _money(_num(tax.get("homeLoan80EE"))), "maximumNonTaxable": 50000, "nonTaxable": _money(deduction_80ee), "netTaxable": _money(max(0, _num(tax.get("homeLoan80EE")) - deduction_80ee))},
            {"description": "80EEA", "value": _money(_num(tax.get("homeLoan80EEA"))), "maximumNonTaxable": 150000, "nonTaxable": _money(deduction_80eea), "netTaxable": _money(max(0, _num(tax.get("homeLoan80EEA")) - deduction_80eea))},
            {"description": "Gross Deductions", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_gross_deductions), "netTaxable": None},
            {"description": "Net Taxable Income", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_taxable_income), "netTaxable": None},
            {"description": "Total Tax", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_tax_after_rebate + old_surcharge), "netTaxable": None},
            {"description": "Health & Cess", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_cess), "netTaxable": None},
            {"description": "Net Tax Payable", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_tax_payable), "netTaxable": None},
            {"description": "Total Tax Paid", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(total_tax_paid), "netTaxable": None},
            {"description": "Refund / Need To Pay", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_refund_or_pay), "netTaxable": None},
            {"description": "Tax %", "value": None, "maximumNonTaxable": None, "nonTaxable": old_tax_percent, "netTaxable": None},
        ],

        "newRegimeRows": [
            {"description": "Gross Salary", "formula": _money(gross_salary)},
            {"description": "Standard Deduction", "formula": _money(standard_new)},
            {"description": "Employer NPS 80CCD(2)", "formula": _money(deduction_80ccd2_new)},
            {"description": "Taxable Income", "formula": _money(new_taxable_income)},
            {"description": "Total Tax Before Rebate", "formula": _money(new_tax_before_rebate)},
            {"description": "Rebate", "formula": _money(new_rebate)},
            {"description": "Marginal Relief", "formula": _money(new_marginal_relief)},
            {"description": "Surcharge", "formula": _money(new_surcharge)},
            {"description": "Cess (4%)", "formula": _money(new_cess)},
            {"description": "Total Tax Payable", "formula": _money(new_tax_payable)},
        ],

        "hraCalculation": {
            "actualHra": _money(hra_received),
            "rentMinus10PctBasic": _money(max(0, rent_paid - 0.10 * basic_salary)),
            "basicLimit": _money(basic_ratio * basic_salary),
            "hraExemption": _money(hra_exemption),
            "formula": "Minimum of actual HRA, rent paid minus 10% basic, and 50% basic for metro / 40% for non-metro.",
        },

        "deductionBreakdown": {
            "standardDeductionOld": _money(standard_old),
            "standardDeductionNew": _money(standard_new),
            "autoHraExemption": _money(auto_hra_exemption),
            "hraUsed": _money(hra_exemption),
            "profTax": _money(prof_tax),
            "section80C": _money(deduction_80c),
            "section80CCD1B": _money(deduction_80ccd_1b),
            "employerNpsOld": _money(deduction_80ccd2_old),
            "employerNpsNew": _money(deduction_80ccd2_new),
            "section80D": _money(deduction_80d_total),
            "section80DParents": _money(deduction_80d_parents),
            "section80G": _money(deduction_80g),
            "section80E": _money(deduction_80e),
            "section80TTA": _money(deduction_80tta),
            "section80EE": _money(deduction_80ee),
            "section80EEA": _money(deduction_80eea),
            "section24B": _money(home_loan_interest),
            "mealAllowance": _money(meal_exemption),
            "telephone": _money(telephone_exemption),
            "internet": _money(internet_exemption),
            "leaveEncashment": _money(leave_encashment_exemption),
        },
    }


def slab_breakdown(taxable, slabs):
    taxable = _num(taxable)
    rows = []
    prev = 0
    total = 0
    for limit, rate in slabs:
        if taxable <= prev:
            break
        amount = max(0, min(taxable, limit) - prev)
        tax = amount * rate
        label_to = "Above" if limit >= 10**17 else _fmt_money(limit)
        label = f"{_fmt_money(prev)} to {label_to}"
        rows.append({
            "range": label,
            "ratePct": round(rate * 100, 2),
            "taxableAmount": _money(amount),
            "tax": _money(tax),
        })
        total += tax
        prev = limit
    return rows, _money(total)


def slab_tax_old(taxable):
    taxable = _num(taxable)
    tax = 0
    slabs = [(250000, 0), (500000, 0.05), (1000000, 0.20), (10**18, 0.30)]
    prev = 0
    for limit, rate in slabs:
        if taxable > prev:
            tax += (min(taxable, limit) - prev) * rate
        prev = limit
        if taxable <= limit:
            break
    return tax


def slab_tax_new_2025(taxable):
    taxable = _num(taxable)
    if taxable <= 1200000:
        return 0
    tax = 0
    slabs = [(400000, 0), (800000, 0.05), (1200000, 0.10), (1600000, 0.15), (2000000, 0.20), (2400000, 0.25), (10**18, 0.30)]
    prev = 0
    for limit, rate in slabs:
        if taxable > prev:
            tax += (min(taxable, limit) - prev) * rate
        prev = limit
        if taxable <= limit:
            break
    return tax


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

    total_assets = sum(_num(v) for v in assets.values()) + sum(_num(i.get("currentValue")) for i in investments) + _num(profile.get("emergencyFund"))
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
        "tax": compute_tax(profile),
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
    equity_like = sum(_num(i.get("monthlyAmount")) for i in investments if i.get("category") in GROWTH_CATEGORIES)
    if monthly_investments > 0 and equity_like / monthly_investments > 0.6:
        score += 1
    if score >= 3:
        return {"label": "Growth", "equity": 70, "debt": 20, "gold": 10, "reason": "Age, surplus, dependents, emergency fund and existing investment pattern support growth allocation."}
    if score >= 1:
        return {"label": "Balanced", "equity": 55, "debt": 35, "gold": 10, "reason": "Profile supports moderate risk with a balanced equity-debt allocation."}
    return {"label": "Conservative", "equity": 35, "debt": 55, "gold": 10, "reason": "Dependents, emergency fund, cash-flow or liabilities suggest capital protection first."}


def project_investments(investments, years, goal=None, categories=None):
    total = 0
    rows = []
    for inv in investments:
        if goal and inv.get("goal") != goal:
            continue
        if categories and inv.get("category") not in categories:
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
    dependents = summary["dependentsCount"]
    annual_expenses = summary["monthlyExpenses"] * 12
    high_priority_goal_gap = sum(g["gap"] for g in goals if g["priority"] in {"Critical", "High"} and "Insurance" not in g["name"])

    if dependents == 0:
        required_life = max(0, summary["totalLiabilities"] + annual_expenses * 2 - summary["totalAssets"])
        life_note = "No dependents entered. Term insurance is good-to-have mainly for liabilities, final expenses, and future family plans."
        priority = "Medium" if required_life > 0 else "Low"
    else:
        years_to_retirement = max(5, _int(basics.get("desiredRetirementAge")) - _int(basics.get("age")))
        income_replacement_years = min(20, years_to_retirement)
        required_life = max(0, annual_expenses * income_replacement_years + summary["totalLiabilities"] + high_priority_goal_gap - summary["totalAssets"])
        life_note = f"Dependents found. CFP need uses {income_replacement_years} years of expense replacement plus liabilities and high-priority goals."
        priority = "High"

    existing_life = _num(insurance.get("life"))
    base_health = 1000000 if basics.get("maritalStatus") == "single" else 2000000
    base_health += 500000 * len(basics.get("kids", []))
    base_health += 750000 * _int(basics.get("dependentParentsCount"))
    city_type = basics.get("cityTier")
    if city_type in {"Metro", "Tier 1"}:
        base_health *= 1.30
    elif city_type in {"Tier 2", "Tier 3"}:
        base_health *= 1.10
    elif city_type in {"Tier 4", "Rural / Village"}:
        base_health *= 0.90
    existing_health = _num(insurance.get("health"))

    return {
        "requiredLifeCover": _money(required_life),
        "existingLifeCover": _money(existing_life),
        "lifeCoverGap": _money(max(0, required_life - existing_life)),
        "lifePriority": priority,
        "lifeNote": life_note,
        "requiredHealthCover": _money(base_health),
        "existingHealthCover": _money(existing_health),
        "healthCoverGap": _money(max(0, base_health - existing_health)),
    }


def build_plan(profile, summary):
    basics = profile.get("basics", {}) or {}
    investments = profile.get("investments", []) or []
    goals_input = profile.get("goals", []) or []
    liabilities = profile.get("liabilities", {}) or {}

    goals = []
    years_to_retirement = max(1, _int(basics.get("desiredRetirementAge")) - _int(basics.get("age")))
    available_surplus = summary["remainingSurplusAfterExistingInvestments"]

    emergency_target = summary["monthlyExpenses"] * ASSUMPTIONS["emergencyFundMonths"]
    add_goal(goals, "Emergency Fund", "Required", "Critical", 0, emergency_target, emergency_target, summary["emergencyFundCurrent"], max(0, emergency_target - summary["emergencyFundCurrent"]), "Build 6 months of expenses before optional goals.")

    monthly_expense_at_retirement = _fv_lumpsum(summary["monthlyExpenses"], ASSUMPTIONS["retirementExpenseInflation"], years_to_retirement)
    retirement_corpus = (monthly_expense_at_retirement * 12) / ASSUMPTIONS["safeWithdrawalRate"]
    retirement_existing, retirement_rows = project_investments(investments, years_to_retirement, goal="retirement")
    retirement_gap = max(0, retirement_corpus - retirement_existing)
    retirement_target_sip = _sip_required(retirement_gap, ASSUMPTIONS["defaultBalancedReturn"], years_to_retirement)
    add_goal(goals, "Retirement Corpus", "Required", "Critical", years_to_retirement, retirement_corpus / ((1 + ASSUMPTIONS["retirementExpenseInflation"]) ** years_to_retirement), retirement_corpus, retirement_existing, retirement_target_sip, "Includes current EPF/NPS/PPF/SIP rows mapped to retirement and editable return assumptions.")

    unsecured_debt = _num(liabilities.get("personalLoan")) + _num(liabilities.get("creditCard")) + _num(liabilities.get("vehicleLoan")) + _num(liabilities.get("otherDebt"))
    if unsecured_debt > 0:
        add_goal(goals, "High-Interest Debt Repayment", "Required", "Critical", 1, unsecured_debt, unsecured_debt, 0, unsecured_debt / 12, "Repay high-interest debt before adding optional investments.")

    kids = basics.get("kids", [])
    for kid in kids:
        child_age = _int(kid.get("age"))
        child_name = kid.get("name") or "Child"

        if child_age < 17:
            years = max(1, 17 - child_age)
            pv = 2500000
            fv = _fv_lumpsum(pv, ASSUMPTIONS["educationInflation"], years)
            existing_child, _ = project_investments(investments, years, goal="childEducation")
            if len(kids) > 1:
                existing_child = existing_child / len(kids)
            gap = max(0, fv - existing_child)
            add_goal(
                goals,
                f"{child_name} Higher Education",
                "Auto-added",
                "High",
                years,
                pv,
                fv,
                existing_child,
                _sip_required(gap, ASSUMPTIONS["defaultBalancedReturn"], years),
                "Auto-created at child age 17 using education inflation.",
            )

        if child_age < 22:
            years = max(1, 22 - child_age)
            pv = 1500000
            marriage_inflation = 0.07
            fv = _fv_lumpsum(pv, marriage_inflation, years)
            existing_marriage, _ = project_investments(investments, years, goal="marriage")
            if len(kids) > 1:
                existing_marriage = existing_marriage / len(kids)
            gap = max(0, fv - existing_marriage)
            add_goal(
                goals,
                f"{child_name} Marriage",
                "Auto-added",
                "Medium",
                years,
                pv,
                fv,
                existing_marriage,
                _sip_required(gap, ASSUMPTIONS["defaultBalancedReturn"], years),
                "Auto-created at child age 22 using 7% inflation.",
            )

    for user_goal in goals_input:
        years = _int(user_goal.get("years"))
        pv = _num(user_goal.get("presentCost"))
        inflation = _num(user_goal.get("inflationPct")) / 100
        expected_return = _num(user_goal.get("expectedReturnPct")) / 100
        fv = _fv_lumpsum(pv, inflation, years)
        existing, _ = project_investments(investments, years, goal=user_goal.get("category"))
        gap = max(0, fv - existing)
        add_goal(goals, user_goal.get("name"), "User-entered", user_goal.get("priority"), years, pv, fv, existing, _sip_required(gap, expected_return, years), "Structured goal row entered by user.")

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
        "tax": summary["tax"],
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
    tax = plan["tax"]
    lines = [
        "### 1. FinOS CFP Dashboard",
        "",
        f"- Average monthly income: {_fmt_money(summary['monthlyIncome'])}",
        f"- Monthly expenses: {_fmt_money(summary['monthlyExpenses'])}",
        f"- Existing monthly investments: {_fmt_money(summary['currentMonthlyInvestments'])}",
        f"- Remaining surplus for new recommendations: {_fmt_money(summary['remainingSurplusAfterExistingInvestments'])}",
        f"- Recommended new investments: {_fmt_money(plan['totalRecommendedMonthlyInvestment'])}",
        f"- Auto risk profile: **{risk['label']}** ({risk['equity']}% equity / {risk['debt']}% debt / {risk['gold']}% gold). {risk['reason']}",
        f"- Tax regime suggestion: **{tax['preferredRegime']} regime** saves approx {_fmt_money(tax['savingsVsOther'])} vs the other regime.",
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
        f"- Existing retirement investments projected: {_fmt_money(ret['existingProjected'])}",
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
        "### 5. Tax Snapshot FY 2026-27",
        "",
        f"- Gross annual income considered: {_fmt_money(tax['grossIncome'])}",
        f"- Salary components total: {_fmt_money(tax.get('salaryComponentsTotal'))}",
        f"- Old regime deductions considered: {_fmt_money(tax.get('oldDeductions'))}",
        f"- New regime deductions considered: {_fmt_money(tax.get('newDeductions'))}",
        f"- Old regime taxable income: {_fmt_money(tax.get('oldTaxable'))}",
        f"- New regime taxable income: {_fmt_money(tax.get('newTaxable'))}",
        f"- Old regime tax estimate: {_fmt_money(tax['oldTax'])}",
        f"- New regime tax estimate: {_fmt_money(tax['newTax'])}",
        f"- Suggested regime: {tax['preferredRegime']}",
        "",
        "#### Old regime slab-wise tax",
        "| Slab | Rate | Taxable amount | Tax |",
        "|---|---:|---:|---:|",
        *[f"| {row['range']} | {row['ratePct']}% | {_fmt_money(row['taxableAmount'])} | {_fmt_money(row['tax'])} |" for row in tax.get("oldSlabBreakdown", [])],
        f"- Old regime rebate: {_fmt_money(tax.get('oldRebate'))}",
        f"- Old regime cess: {_fmt_money(tax.get('oldCess'))}",
        "",
        "#### New regime slab-wise tax",
        "| Slab | Rate | Taxable amount | Tax |",
        "|---|---:|---:|---:|",
        *[f"| {row['range']} | {row['ratePct']}% | {_fmt_money(row['taxableAmount'])} | {_fmt_money(row['tax'])} |" for row in tax.get("newSlabBreakdown", [])],
        f"- New regime rebate: {_fmt_money(tax.get('newRebate'))}",
        f"- New regime cess: {_fmt_money(tax.get('newCess'))}",
        "",
        "### 6. Investment Mapping",
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
        "### 7. Action Plan",
        "",
        "- Keep total new SIP recommendations within remaining surplus.",
        "- Fund emergency fund and high-interest debt before optional goals.",
        "- Continue EPF/NPS/PPF/SIPs already mapped to retirement; only add the recommended additional SIP if surplus allows.",
        "- Review insurance after major life events: marriage, child, home loan, dependent parents, income change.",
        "- Use tax regime comparison before March investment decisions.",
        "",
        "### 8. CFP Notes",
        "",
        ai_notes.strip() if ai_notes else "Review this plan annually and update SIP rows, expected returns, insurance, expenses, and dependents.",
        "",
        "This is educational financial planning guidance, not registered financial advice.",
    ]
    return "\n".join(lines)


AI_NOTES_PROMPT = """You are a CFP-style financial planning assistant for Indian users. Backend numbers are deterministic.
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



AI_PLANNER_MODE = os.environ.get("AI_PLANNER_MODE", "true").lower() == "true"


def _json_from_text(text):
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None
    return None


def _ai_first_system_prompt():
    return """You are SmartFinly AI Planner, an India-focused CFP-style educational financial planning engine.

Your job:
- Create the financial plan using AI reasoning.
- Use calculated facts as guardrails, not as the full answer.
- Do not invent user inputs.
- Do not recommend total new monthly investments above remaining surplus.
- Do not claim guaranteed returns.
- Do not claim SEBI/RBI registration.
- Output must be valid JSON only.

Return this exact JSON shape:
{
  "summary": {
    "aiMode": true,
    "oneLineDiagnosis": "...",
    "topPriorities": ["...", "..."],
    "riskProfile": {"label": "Conservative|Balanced|Growth", "reason": "...", "equity": 0, "debt": 0, "gold": 0},
    "warnings": ["..."]
  },
  "plan": {
    "goals": [
      {
        "name": "...",
        "priority": "Critical|High|Medium|Low",
        "timeline": "...",
        "years": 0,
        "presentCost": 0,
        "futureCost": 0,
        "existingAllocation": 0,
        "gap": 0,
        "targetMonthlyInvestment": 0,
        "recommendedMonthlyInvestment": 0,
        "fundingStatus": "Fully funded|Partially funded|Not funded",
        "notes": "..."
      }
    ],
    "insurance": {
      "existingLifeCover": 0,
      "requiredLifeCover": 0,
      "lifeCoverGap": 0,
      "existingHealthCover": 0,
      "requiredHealthCover": 0,
      "healthCoverGap": 0,
      "priority": "Low|Medium|High",
      "notes": "..."
    },
    "tax": {
      "preferredRegime": "Old|New",
      "notes": "..."
    },
    "actionPlan": ["...", "..."]
  },
  "report": "Markdown report with sections: AI Diagnosis, Cash-flow, Goals, Tax, Insurance, Investment Mapping, Action Plan, Compliance Note"
}
"""


def _invoke_ai_json(profile, calculated):
    payload = {
        "profile": profile,
        "calculatedGuardrails": calculated,
        "nonNegotiableRules": {
            "maxNewMonthlyInvestment": calculated.get("summary", {}).get("remainingSurplusAfterExistingInvestments", 0),
            "monthlySurplus": calculated.get("summary", {}).get("monthlySurplus", 0),
            "currentMonthlyInvestments": calculated.get("summary", {}).get("currentMonthlyInvestments", 0),
            "taxFacts": calculated.get("summary", {}).get("tax", {}),
            "insuranceFacts": calculated.get("plan", {}).get("insurance", {}),
            "goalFacts": calculated.get("plan", {}).get("goals", []),
            "fyLabel": "FY 2026-27"
        }
    }

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": _ai_first_system_prompt()
                    + "\n\nCreate SmartFinly AI planner output for this user. Return JSON only.\n\n"
                    + json.dumps(payload, ensure_ascii=False)
                }
            ],
        }
    ]

    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=messages,
        inferenceConfig={"maxTokens": 3500, "temperature": 0.2, "topP": 0.9},
    )
    text = response["output"]["message"]["content"][0]["text"]
    return _json_from_text(text)


def _num_for_guard(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _apply_ai_guardrails(ai_body, calculated):
    """AI remains the planner; backend only enforces hard safety constraints."""
    if not isinstance(ai_body, dict):
        return calculated

    calc_summary = calculated.get("summary", {}) or {}
    calc_plan = calculated.get("plan", {}) or {}
    max_new_sip = max(0, _num_for_guard(calc_summary.get("remainingSurplusAfterExistingInvestments")))

    ai_summary = ai_body.setdefault("summary", {})
    ai_plan = ai_body.setdefault("plan", {})

    merged_summary = dict(calc_summary)
    merged_summary.update(ai_summary)
    merged_summary["aiMode"] = True

    # Preserve factual numbers for charts and hard affordability checks.
    for key in [
        "monthlyIncome",
        "monthlyExpenses",
        "monthlySurplus",
        "currentMonthlyInvestments",
        "remainingSurplusAfterExistingInvestments",
        "netWorth",
        "tax",
    ]:
        if key in calc_summary:
            merged_summary[key] = calc_summary[key]

    merged_summary["remainingSurplusAfterExistingInvestments"] = max_new_sip
    ai_body["summary"] = merged_summary

    goals = ai_plan.get("goals")
    if not isinstance(goals, list) or not goals:
        goals = calc_plan.get("goals", [])

    total_requested = sum(_num_for_guard(g.get("recommendedMonthlyInvestment")) for g in goals if isinstance(g, dict))
    if total_requested > max_new_sip and total_requested > 0:
        scale = max_new_sip / total_requested
        for g in goals:
            if not isinstance(g, dict):
                continue
            g["recommendedMonthlyInvestment"] = round(_num_for_guard(g.get("recommendedMonthlyInvestment")) * scale, 2)
            target = _num_for_guard(g.get("targetMonthlyInvestment"))
            rec = _num_for_guard(g.get("recommendedMonthlyInvestment"))
            if rec <= 0:
                g["fundingStatus"] = "Not funded"
            elif target > 0 and rec >= target:
                g["fundingStatus"] = "Fully funded"
            else:
                g["fundingStatus"] = "Partially funded"

    ai_plan["goals"] = goals

    calc_insurance = calc_plan.get("insurance", {}) or {}
    ai_insurance = ai_plan.get("insurance", {}) if isinstance(ai_plan.get("insurance"), dict) else {}
    merged_insurance = dict(calc_insurance)
    for key in ["priority", "notes"]:
        if key in ai_insurance:
            merged_insurance[key] = ai_insurance[key]
    ai_plan["insurance"] = merged_insurance

    ai_tax = ai_plan.get("tax", {}) if isinstance(ai_plan.get("tax"), dict) else {}
    ai_plan["tax"] = {
        "preferredRegime": calc_summary.get("tax", {}).get("preferredRegime"),
        "facts": calc_summary.get("tax", {}),
        "notes": ai_tax.get("notes", ""),
    }

    ai_body["plan"] = ai_plan

    report = ai_body.get("report")
    if not isinstance(report, str) or len(report.strip()) < 50:
        report = calculated.get("report", "")

    ai_body["report"] = (
        report
        + "\n\n---\n"
        + "**SmartFinly AI Mode:** Recommendations are AI-generated and then checked against hard affordability, tax, insurance and compliance guardrails. Educational use only, not registered financial advice."
    )

    return ai_body


def ai_first_output(profile, calculated):
    if not AI_PLANNER_MODE:
        return calculated
    try:
        ai_body = _invoke_ai_json(profile, calculated)
        return _apply_ai_guardrails(ai_body, calculated)
    except Exception as exc:
        print("AI-first planner failed; falling back to calculated plan:", str(exc))
        fallback = dict(calculated)
        fallback["aiModeError"] = str(exc)
        return fallback



def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
    if method == "OPTIONS":
        response_body = {}
        response_body = ai_first_output(profile, response_body)
        return respond(200, response_body)
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
