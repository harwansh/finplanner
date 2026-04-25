"SmartFinly /analyze Lambda - stable build used to fix Bad Gateway."

import copy
import json
import math
import os
import re

import boto3

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
AI_PLANNER_MODE = os.environ.get("AI_PLANNER_MODE", "true").lower() == "true"
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
    "retirementExpenseInflation": 0.06,
    "safeWithdrawalRate": 0.035,
    "defaultBalancedReturn": 0.09,
    "lifeExpectancy": 90,
    "emergencyFundMonths": 6,
}

DEFAULT_RETURNS = {
    "epf": 8.25,
    "ppf": 7.1,
    "nps": 10,
    "retirementSip": 10,
    "childEducation": 10,
    "equityIndex": 11,
    "equityLargeCap": 11,
    "equityFlexiCap": 11,
    "equityMidCap": 12,
    "equitySmallCap": 13,
    "gold": 8,
    "debtFund": 7,
    "liquidFund": 5.5,
    "fdRd": 6.5,
    "other": 8,
}

RETIREMENT_CATEGORIES = {"epf", "ppf", "nps", "retirementSip", "equityIndex", "equityLargeCap", "equityFlexiCap"}

PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I)
AADHAAR_RE = re.compile(r"\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b")
OTP_RE = re.compile(r"\b(?:otp|one time password)[^\d]{0,20}\d{4,8}\b", re.I)
SENSITIVE_KEY_RE = re.compile(r"(aadhaar|aadhar|pan|otp|password|passcode|secret|token|bank.?account|account.?number|ifsc|upi|vpa)", re.I)


class UserInputError(Exception):
    pass


def _num(value, default=0.0):
    if value is None or value == "":
        return default
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(n) or math.isinf(n):
        return default
    return n


def _int(value):
    return int(max(0, round(_num(value))))


def _money(value):
    return round(_num(value), 2)


def _money_pos(value):
    return round(max(0.0, _num(value)), 2)


def _fmt_money(value):
    n = _num(value)
    sign = "-" if n < 0 else ""
    return f"{sign}₹{abs(round(n)):,.0f}"


def _json_response(status, body):
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, allow_nan=False),
    }


def _parse_event(event):
    if not isinstance(event, dict):
        return {}
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "POST"
    ).upper()
    if method == "OPTIONS":
        raise UserInputError("__OPTIONS__")
    raw = event.get("body") or "{}"
    if len(str(raw).encode("utf-8")) > int(os.environ.get("MAX_BODY_BYTES", "131072")):
        raise UserInputError("Request body is too large.")
    try:
        payload = json.loads(raw)
    except Exception:
        raise UserInputError("Invalid JSON request body.")
    if not isinstance(payload, dict):
        raise UserInputError("Request body must be a JSON object.")
    return payload


def _security_scan(value, path="root"):
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY_RE.search(str(key)) and child not in ("", None, [], {}):
                raise UserInputError("Do not enter PAN, Aadhaar, bank account, OTP, password, UPI or other sensitive identifiers.")
            _security_scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        if path.endswith(".goals") and len(value) > 50:
            raise UserInputError("Maximum 50 goals allowed.")
        if path.endswith(".investments") and len(value) > 100:
            raise UserInputError("Maximum 100 investment rows allowed.")
        if path.endswith(".kids") and len(value) > 10:
            raise UserInputError("Maximum 10 children rows allowed.")
        for i, child in enumerate(value):
            _security_scan(child, f"{path}[{i}]")
    elif isinstance(value, str):
        if len(value) > 2500:
            raise UserInputError("One or more text fields are too long.")
        if PAN_RE.search(value) or AADHAAR_RE.search(value) or OTP_RE.search(value):
            raise UserInputError("Do not enter PAN, Aadhaar, OTP, bank or other sensitive identifiers.")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < 0:
            raise UserInputError("Negative numbers are not allowed.")
        if abs(value) > float(os.environ.get("MAX_ABS_NUMBER", "1000000000000")):
            raise UserInputError("One or more numbers are unrealistically large.")


def _fv_lumpsum(pv, rate, years):
    return _money_pos(_num(pv) * ((1 + rate) ** max(0, years)))


def _fv_monthly(monthly, annual_return, years):
    monthly = _num(monthly)
    if monthly <= 0:
        return 0
    months = max(1, int(round(years * 12)))
    r = annual_return / 12
    if r <= 0:
        return _money_pos(monthly * months)
    return _money_pos(monthly * ((((1 + r) ** months - 1) * (1 + r)) / r))


def _sip_required(gap, annual_return, years):
    gap = _num(gap)
    if gap <= 0:
        return 0
    months = max(1, int(round(years * 12)))
    r = annual_return / 12
    if r <= 0:
        return _money_pos(gap / months)
    factor = (((1 + r) ** months - 1) * (1 + r)) / r
    return _money_pos(gap / factor)


def infer_goal_from_category(category):
    if category in RETIREMENT_CATEGORIES:
        return "retirement"
    if category == "childEducation":
        return "childEducation"
    return "wealth"


def goal_inflation(category):
    if category in {"education", "childEducation"}:
        return ASSUMPTIONS["educationInflation"]
    if category in {"home", "realEstate"}:
        return 0.06
    return ASSUMPTIONS["generalInflation"]



def _first_value(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def align_profile_field_aliases(profile):
    """Accept old/new frontend field names so demo/manual form and backend validation match."""
    if not isinstance(profile, dict):
        return profile

    basics = profile.setdefault("basics", {})
    income = profile.setdefault("income", {})
    salary = profile.setdefault("salary", {})
    expenses = profile.setdefault("expenses", {})

    basics["age"] = _first_value(
        basics.get("age"),
        basics.get("currentAge"),
        basics.get("current_age"),
        profile.get("age"),
        profile.get("currentAge"),
    )
    basics["desiredRetirementAge"] = _first_value(
        basics.get("desiredRetirementAge"),
        basics.get("retirementAge"),
        basics.get("desired_retirement_age"),
        profile.get("desiredRetirementAge"),
        profile.get("retirementAge"),
    )
    basics["cityTier"] = _first_value(
        basics.get("cityTier"),
        basics.get("cityType"),
        basics.get("city"),
    )
    basics["employmentType"] = _first_value(
        basics.get("employmentType"),
        basics.get("employment"),
    )

    income["monthlyAfterTax"] = _first_value(
        income.get("monthlyAfterTax"),
        income.get("monthlyIncomeAfterTax"),
        income.get("monthlyIncome"),
        income.get("netMonthlyIncome"),
        income.get("takeHomeMonthly"),
        profile.get("monthlyAfterTax"),
        profile.get("monthlyIncomeAfterTax"),
    )
    income["otherMonthly"] = _first_value(
        income.get("otherMonthly"),
        income.get("otherMonthlyIncome"),
        income.get("otherIncomeMonthly"),
    )
    income["bonusAnnual"] = _first_value(
        income.get("bonusAnnual"),
        income.get("annualBonus"),
        salary.get("bonusVariablePay"),
    )

    expenses["fixed"] = _first_value(
        expenses.get("fixed"),
        expenses.get("fixedMonthly"),
        expenses.get("fixedMonthlyExpenses"),
    )
    expenses["variable"] = _first_value(
        expenses.get("variable"),
        expenses.get("variableMonthly"),
        expenses.get("variableMonthlyExpenses"),
    )
    expenses["annual"] = _first_value(
        expenses.get("annual"),
        expenses.get("annualLumpSums"),
        expenses.get("annualExpenses"),
    )

    salary["basicSalary"] = _first_value(
        salary.get("basicSalary"),
        salary.get("basic"),
        salary.get("annualBasic"),
    )
    salary["hraReceived"] = _first_value(
        salary.get("hraReceived"),
        salary.get("hra"),
        salary.get("annualHra"),
    )
    salary["epfContribution"] = _first_value(
        salary.get("epfContribution"),
        salary.get("employeeEpf"),
        salary.get("employeeEPF"),
        salary.get("ePfContribution"),
    )
    salary["npsEmployer"] = _first_value(
        salary.get("npsEmployer"),
        salary.get("employerNps"),
        salary.get("employerNPS"),
    )
    salary["grossEarning"] = _first_value(
        salary.get("grossEarning"),
        salary.get("grossSalary"),
        salary.get("annualGross"),
    )
    salary["rentPaid"] = _first_value(
        salary.get("rentPaid"),
        salary.get("annualRentPaid"),
    )

    return profile



def normalize_profile(profile):
    profile = align_profile_field_aliases(profile)
    p = copy.deepcopy(profile or {})
    basics = p.setdefault("basics", {})

    kids = basics.get("kids") if isinstance(basics.get("kids"), list) else []
    normalized_kids = []
    for i, kid in enumerate(kids):
        if not isinstance(kid, dict):
            continue
        age = _int(kid.get("age"))
        if age > 0:
            normalized_kids.append({"name": str(kid.get("name") or f"Child {i + 1}").strip(), "age": age})
    if basics.get("maritalStatus") != "married":
        normalized_kids = []
    basics["kids"] = normalized_kids
    basics["parentsDependent"] = bool(basics.get("parentsDependent"))
    basics["dependentParentsCount"] = _int(basics.get("dependentParentsCount")) if basics["parentsDependent"] else 0

    investments = []
    for i, inv in enumerate(p.get("investments") or []):
        if not isinstance(inv, dict):
            continue
        current = _num(inv.get("currentValue"))
        monthly = _num(inv.get("monthlyAmount"))
        if current <= 0 and monthly <= 0:
            continue
        category = inv.get("category") or "other"
        investments.append({
            "name": str(inv.get("name") or f"Investment {i + 1}").strip(),
            "category": category,
            "currentValue": current,
            "monthlyAmount": monthly,
            "expectedReturnPct": _num(inv.get("expectedReturnPct")) or DEFAULT_RETURNS.get(category, 8),
            "goal": inv.get("goal") or infer_goal_from_category(category),
            "source": inv.get("source"),
        })

    salary = p.get("salary", {}) or {}
    epf_monthly = _num(salary.get("monthlyEmployeeEpf")) or (_num(salary.get("epfContribution")) / 12)
    nps_monthly = _num(salary.get("monthlyEmployerNps")) or (_num(salary.get("npsEmployer")) / 12)
    if epf_monthly > 0:
        investments.append({"name": "Auto EPF from salary", "category": "epf", "currentValue": 0, "monthlyAmount": epf_monthly, "expectedReturnPct": 8.25, "goal": "retirement", "source": "salary"})
    if nps_monthly > 0:
        investments.append({"name": "Auto employer NPS from salary", "category": "nps", "currentValue": 0, "monthlyAmount": nps_monthly, "expectedReturnPct": 10, "goal": "retirement", "source": "salary"})

    p["investments"] = investments

    goals = []
    for i, goal in enumerate(p.get("goals") or []):
        if not isinstance(goal, dict):
            continue
        cost = _num(goal.get("presentCost"))
        years = _int(goal.get("years"))
        if cost <= 0 or years <= 0:
            continue
        category = goal.get("category") or "wealth"
        goals.append({
            "name": str(goal.get("name") or f"Goal {i + 1}").strip(),
            "category": category,
            "presentCost": cost,
            "years": years,
            "inflationPct": _num(goal.get("inflationPct")) or goal_inflation(category) * 100,
            "expectedReturnPct": _num(goal.get("expectedReturnPct")) or 9,
            "priority": goal.get("priority") or "Medium",
        })
    p["goals"] = goals
    return p


def validate_profile(p):
    errors = []
    basics = p.get("basics", {}) or {}
    age = _int(basics.get("age"))
    retirement_age = _int(basics.get("desiredRetirementAge"))
    if age <= 0:
        errors.append("Current age is required.")
    if retirement_age <= age:
        errors.append("Desired retirement age must be greater than current age.")
    if _num(p.get("income", {}).get("monthlyAfterTax")) <= 0:
        errors.append("Monthly after-tax income is required.")
    if basics.get("employmentType") == "salaried":
        s = p.get("salary", {}) or {}
        if _num(s.get("basicSalary")) <= 0 and _num(s.get("monthlyBasic")) <= 0:
            errors.append("Basic Salary is required for salaried tax calculation.")
        if _num(s.get("hraReceived")) <= 0 and _num(s.get("monthlyHra")) <= 0:
            errors.append("HRA received is required for salaried tax calculation.")
        if _num(s.get("epfContribution")) <= 0 and _num(s.get("monthlyEmployeeEpf")) <= 0:
            errors.append("E-PF Contribution is required for salaried tax calculation.")
    if errors:
        raise UserInputError(" ".join(errors))


def cashflow(p):
    inc = p.get("income", {}) or {}
    exp = p.get("expenses", {}) or {}
    monthly_income = _num(inc.get("monthlyAfterTax")) + _num(inc.get("otherMonthly"))
    monthly_expenses = _num(exp.get("fixed")) + _num(exp.get("variable")) + _num(exp.get("annual")) / 12 + _num(p.get("monthlyEmi"))
    surplus = monthly_income - monthly_expenses
    current_investments = sum(_num(i.get("monthlyAmount")) for i in p.get("investments", []))
    remaining = max(0, surplus - current_investments)
    return {
        "monthlyIncome": _money(monthly_income),
        "monthlyExpenses": _money(monthly_expenses),
        "monthlySurplus": _money(surplus),
        "currentMonthlyInvestments": _money(current_investments),
        "remainingSurplusAfterExistingInvestments": _money(remaining),
        "annualSurplus": _money(surplus * 12),
    }


def slab_breakdown(taxable, slabs):
    taxable = max(0, _num(taxable))
    rows, total, prev = [], 0, 0
    for limit, rate in slabs:
        if taxable <= prev:
            break
        amount = max(0, min(taxable, limit) - prev)
        tax = amount * rate
        rows.append({"range": f"{_fmt_money(prev)} to {'Above' if limit >= 10**17 else _fmt_money(limit)}", "ratePct": round(rate * 100, 2), "taxableAmount": _money(amount), "tax": _money(tax)})
        total += tax
        prev = limit
    return rows, _money(total)


def compute_tax(p):
    s = p.get("salary", {}) or {}
    tax = p.get("tax", {}) or {}
    basics = p.get("basics", {}) or {}

    annual = lambda a, m: _num(s.get(a)) or _num(s.get(m)) * 12
    basic = annual("basicSalary", "monthlyBasic")
    hra = annual("hraReceived", "monthlyHra")
    lta = annual("lta", "monthlyLta")
    flex = _num(s.get("flexibleCompPlan")) or _num(s.get("monthlySpecialAllowance")) * 12
    bonus = _num(s.get("bonusVariablePay")) or _num(s.get("monthlyBonus")) * 12
    employer_nps = _num(s.get("npsEmployer")) or _num(s.get("monthlyEmployerNps")) * 12
    epf = _num(s.get("epfContribution")) or _num(s.get("monthlyEmployeeEpf")) * 12
    prof_tax = _num(s.get("profTax")) or _num(s.get("monthlyProfessionalTax")) * 12
    telephone = _num(s.get("telephoneReimbursement"))
    internet = _num(s.get("internetAllowance")) or _num(s.get("internet"))
    meal = _num(s.get("meal"))
    leave = _num(s.get("leaveEncashment"))
    other_salary = _num(s.get("superannuation")) + _num(s.get("shiftAllowance")) + _num(s.get("onCallAllowance")) + _num(s.get("teamParty")) + _num(s.get("awardsNonCashTaxable"))

    components = basic + hra + lta + flex + bonus + employer_nps + telephone + internet + meal + leave + other_salary
    fallback = (_num(p.get("income", {}).get("monthlyAfterTax")) + _num(p.get("income", {}).get("otherMonthly"))) * 12 + _num(p.get("income", {}).get("bonusAnnual"))
    gross = _num(s.get("grossEarning")) or _num(s.get("annualGross")) or components or fallback

    rent = _num(s.get("rentPaid")) or _num(s.get("rentPaidMonthly")) * 12
    city_ratio = 0.50 if basics.get("cityTier") in {"Metro", "Tier 1"} else 0.40
    hra_exemption = 0
    if hra > 0 and basic > 0 and rent > 0:
        hra_exemption = min(hra, max(0, rent - 0.10 * basic), city_ratio * basic)
    hra_exemption = _num(tax.get("hraExemption")) or max(0, hra_exemption)

    meal_ex = min(meal, 26400)
    tel_ex = min(telephone, 24000)
    net_ex = min(internet, 24000)
    leave_ex = min(leave, 300000)

    other_income = _num(tax.get("otherAnnualIncome"))
    capital_gain = _num(tax.get("capitalGain"))
    savings_interest = _num(tax.get("interest80TTA_TTB"))

    old_taxable_salary = max(0, gross - hra_exemption - prof_tax - 50000 - meal_ex - tel_ex - net_ex - leave_ex)
    new_taxable_salary = max(0, gross - 75000)

    d80c_value = _num(tax.get("deduction80C")) + epf
    d80c = min(150000, d80c_value)
    d80ccd1b_value = _num(tax.get("nps80CCD1B")) or _num(s.get("npsEmployee"))
    d80ccd1b = min(50000, d80ccd1b_value)
    d80ccd2_old = min(employer_nps, basic * 0.10 if basic else employer_nps)
    d80ccd2_new = min(employer_nps, basic * 0.14 if basic else employer_nps)
    d80d_self_value = _num(tax.get("health80D"))
    d80d_parents_value = _num(tax.get("health80DParents"))
    d80d_self = min(d80d_self_value, 25000)
    d80d_parents = min(d80d_parents_value, 50000)
    d80g = _num(tax.get("donation80G"))
    d80e = _num(tax.get("educationLoan80E"))
    d80tta = min(savings_interest, 10000)
    d24b_value = _num(tax.get("homeLoanInterest24B"))
    d24b = min(d24b_value, 200000)
    d80ee = min(_num(tax.get("homeLoan80EE")), 50000)
    d80eea = min(_num(tax.get("homeLoan80EEA")), 150000)

    old_deductions = d80c + d80ccd1b + d80ccd2_old + d80d_self + d80d_parents + d80g + d80e + d80tta + d24b + d80ee + d80eea
    old_taxable = max(0, old_taxable_salary + other_income + capital_gain - old_deductions)
    new_taxable = max(0, new_taxable_salary + other_income + capital_gain - d80ccd2_new)

    old_rows, old_before = slab_breakdown(old_taxable, [(250000, 0), (500000, 0.05), (1000000, 0.20), (10**18, 0.30)])
    new_rows, new_before = slab_breakdown(new_taxable, [(400000, 0), (800000, 0.05), (1200000, 0.10), (1600000, 0.15), (2000000, 0.20), (2400000, 0.25), (10**18, 0.30)])

    old_rebate = old_before if old_taxable <= 500000 else 0
    new_rebate = new_before if new_taxable <= 1200000 else 0
    old_after = max(0, old_before - old_rebate)
    new_after_pre_relief = max(0, new_before - new_rebate)
    new_relief = 0
    if new_taxable > 1200000 and new_after_pre_relief > new_taxable - 1200000:
        new_relief = new_after_pre_relief - (new_taxable - 1200000)
    new_after = max(0, new_after_pre_relief - new_relief)

    surcharge = lambda taxable, regime: 0 if taxable <= 5000000 else 0.10 if taxable <= 10000000 else 0.15 if taxable <= 20000000 else 0.25 if taxable <= 50000000 or regime == "new" else 0.37
    old_surcharge = old_after * surcharge(old_taxable, "old")
    new_surcharge = new_after * surcharge(new_taxable, "new")
    old_cess = (old_after + old_surcharge) * 0.04
    new_cess = (new_after + new_surcharge) * 0.04
    old_tax = old_after + old_surcharge + old_cess
    new_tax = new_after + new_surcharge + new_cess
    tax_paid = _num(tax.get("taxPaid")) or _num(s.get("incomeTax"))

    old_regime_rows = [
        {"description": "Gross Salary", "value": _money(gross), "maximumNonTaxable": None, "nonTaxable": 0, "netTaxable": _money(gross)},
        {"description": "HRA", "value": _money(hra), "maximumNonTaxable": None, "nonTaxable": _money(hra_exemption), "netTaxable": _money(max(0, hra - hra_exemption))},
        {"description": "P-Tax", "value": _money(prof_tax), "maximumNonTaxable": None, "nonTaxable": _money(prof_tax), "netTaxable": 0},
        {"description": "Standard Deduction", "value": 50000, "maximumNonTaxable": 50000, "nonTaxable": 50000, "netTaxable": 0},
        {"description": "80C", "value": _money(d80c_value), "maximumNonTaxable": 150000, "nonTaxable": _money(d80c), "netTaxable": _money(max(0, d80c_value - d80c))},
        {"description": "80CCD(1B)", "value": _money(d80ccd1b_value), "maximumNonTaxable": 50000, "nonTaxable": _money(d80ccd1b), "netTaxable": _money(max(0, d80ccd1b_value - d80ccd1b))},
        {"description": "80CCD(2) Employer NPS", "value": _money(employer_nps), "maximumNonTaxable": _money(basic * 0.10 if basic else employer_nps), "nonTaxable": _money(d80ccd2_old), "netTaxable": _money(max(0, employer_nps - d80ccd2_old))},
        {"description": "80D Self/Family", "value": _money(d80d_self_value), "maximumNonTaxable": 25000, "nonTaxable": _money(d80d_self), "netTaxable": _money(max(0, d80d_self_value - d80d_self))},
        {"description": "80D Parents", "value": _money(d80d_parents_value), "maximumNonTaxable": 50000, "nonTaxable": _money(d80d_parents), "netTaxable": _money(max(0, d80d_parents_value - d80d_parents))},
        {"description": "Home Loan Interest 24(b)", "value": _money(d24b_value), "maximumNonTaxable": 200000, "nonTaxable": _money(d24b), "netTaxable": _money(max(0, d24b_value - d24b))},
        {"description": "Gross Deductions", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_deductions), "netTaxable": None},
        {"description": "Net Taxable Income", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_taxable), "netTaxable": None},
        {"description": "Net Tax Payable", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(old_tax), "netTaxable": None},
        {"description": "Total Tax Paid", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(tax_paid), "netTaxable": None},
        {"description": "Refund / Need To Pay", "value": None, "maximumNonTaxable": None, "nonTaxable": _money(tax_paid - old_tax), "netTaxable": None},
    ]

    return {
        "fyLabel": "FY 2026-27",
        "grossIncome": _money(gross),
        "grossSalary": _money(gross),
        "grossEarning": _money(gross),
        "salaryComponentsTotal": _money(components),
        "oldDeductions": _money(old_deductions),
        "newDeductions": _money(d80ccd2_new),
        "oldTaxable": _money(old_taxable),
        "newTaxable": _money(new_taxable),
        "oldSlabBreakdown": old_rows,
        "newSlabBreakdown": new_rows,
        "oldTaxBeforeRebate": _money(old_before),
        "newTaxBeforeRebate": _money(new_before),
        "oldRebate": _money(old_rebate),
        "newRebate": _money(new_rebate),
        "newMarginalRelief": _money(new_relief),
        "oldSurcharge": _money(old_surcharge),
        "newSurcharge": _money(new_surcharge),
        "oldCess": _money(old_cess),
        "newCess": _money(new_cess),
        "oldTax": _money(old_tax),
        "newTax": _money(new_tax),
        "preferredRegime": "Old" if old_tax < new_tax else "New",
        "savingsVsOther": _money(abs(old_tax - new_tax)),
        "totalTaxPaid": _money(tax_paid),
        "oldRefundOrNeedToPay": _money(tax_paid - old_tax),
        "newRefundOrNeedToPay": _money(tax_paid - new_tax),
        "oldTaxPercent": round((old_tax / gross * 100) if gross else 0, 2),
        "newTaxPercent": round((new_tax / gross * 100) if gross else 0, 2),
        "hraCalculation": {"actualHra": _money(hra), "rentMinus10PctBasic": _money(max(0, rent - 0.10 * basic)), "basicLimit": _money(city_ratio * basic), "hraExemption": _money(hra_exemption), "formula": "Minimum of actual HRA, rent paid minus 10% basic, and 50% basic for metro / 40% for non-metro."},
        "oldRegimeRows": old_regime_rows,
        "newRegimeRows": [
            {"description": "Gross Salary", "formula": _money(gross)},
            {"description": "Standard Deduction", "formula": 75000},
            {"description": "Employer NPS 80CCD(2)", "formula": _money(d80ccd2_new)},
            {"description": "Taxable Income", "formula": _money(new_taxable)},
            {"description": "Total Tax Before Rebate", "formula": _money(new_before)},
            {"description": "Rebate", "formula": _money(new_rebate)},
            {"description": "Marginal Relief", "formula": _money(new_relief)},
            {"description": "Surcharge", "formula": _money(new_surcharge)},
            {"description": "Cess (4%)", "formula": _money(new_cess)},
            {"description": "Total Tax Payable", "formula": _money(new_tax)},
        ],
    }


def project_investments(investments, years, goal=None):
    total, monthly = 0, 0
    for inv in investments:
        if goal and inv.get("goal") not in {goal, "wealth", None, ""}:
            continue
        rate = (_num(inv.get("expectedReturnPct")) or DEFAULT_RETURNS.get(inv.get("category"), 8)) / 100
        total += _num(inv.get("currentValue")) * ((1 + rate) ** max(0, years))
        total += _fv_monthly(inv.get("monthlyAmount"), rate, years)
        monthly += _num(inv.get("monthlyAmount"))
    return _money_pos(total), _money_pos(monthly)


def add_goal(goals, name, category, priority, years, today, future, existing, target_sip, notes):
    gap = max(0, _num(future) - _num(existing))
    goals.append({"name": name, "category": category, "priority": priority, "timeline": f"{years} years", "years": years, "presentCost": _money(today), "futureCost": _money_pos(future), "existingAllocation": _money_pos(existing), "gap": _money_pos(gap), "targetMonthlyInvestment": _money_pos(target_sip), "recommendedMonthlyInvestment": 0, "fundingStatus": "Fully funded" if gap <= 0 else "Not funded", "notes": notes})


def insurance_need(p, cf, goals):
    b = p.get("basics", {}) or {}
    liabilities = p.get("liabilities", {}) or {}
    ins = p.get("insurance", {}) or {}
    annual_expenses = _num(cf.get("monthlyExpenses")) * 12
    dependents = (1 if b.get("maritalStatus") == "married" else 0) + len(b.get("kids", [])) + _int(b.get("dependentParentsCount"))
    debt = sum(_num(v) for v in liabilities.values()) if isinstance(liabilities, dict) else 0
    goal_gap = sum(_num(g.get("gap")) for g in goals if g.get("priority") in {"Critical", "High"})
    liquid_assets = sum(_num(i.get("currentValue")) for i in p.get("investments", []) if i.get("category") in {"fdRd", "liquidFund", "debtFund"})
    if dependents <= 0:
        required_life = max(0, debt - liquid_assets)
        note = "No dependents: term cover is good-to-have unless liabilities exist."
    else:
        required_life = max(0, annual_expenses * 15 + debt + goal_gap - liquid_assets)
        note = "Life cover uses income replacement, liabilities, dependents and priority goal gaps."
    health_required = 1000000 * (1.2 if b.get("cityTier") in {"Metro", "Tier 1"} else 1.0)
    if b.get("maritalStatus") == "married":
        health_required += 500000
    health_required += len(b.get("kids", [])) * 300000 + _int(b.get("dependentParentsCount")) * 500000
    existing_life, existing_health = _num(ins.get("life")), _num(ins.get("health"))
    return {"existingLifeCover": _money(existing_life), "requiredLifeCover": _money_pos(required_life), "lifeCoverGap": _money_pos(required_life - existing_life), "existingHealthCover": _money(existing_health), "requiredHealthCover": _money_pos(health_required), "healthCoverGap": _money_pos(health_required - existing_health), "priority": "High" if required_life > existing_life or health_required > existing_health else "Low", "notes": note}


def build_plan(p, cf):
    b = p.get("basics", {}) or {}
    investments = p.get("investments", [])
    goals = []
    age, retire_age = _int(b.get("age")), _int(b.get("desiredRetirementAge"))
    years_to_retire = max(1, retire_age - age)
    retirement_expense = _num(cf.get("monthlyExpenses")) * 0.85 * 12 * ((1 + ASSUMPTIONS["retirementExpenseInflation"]) ** years_to_retire)
    retirement_corpus = retirement_expense / ASSUMPTIONS["safeWithdrawalRate"]
    existing_retirement, _ = project_investments(investments, years_to_retire, "retirement")
    add_goal(goals, "Retirement Corpus", "retirement", "Critical", years_to_retire, retirement_corpus / ((1 + ASSUMPTIONS["retirementExpenseInflation"]) ** years_to_retire), retirement_corpus, existing_retirement, _sip_required(max(0, retirement_corpus - existing_retirement), 0.09, years_to_retire), "Retirement corpus uses safe withdrawal and projected expenses.")

    emergency_need = _num(cf.get("monthlyExpenses")) * ASSUMPTIONS["emergencyFundMonths"]
    emergency_existing = _num(p.get("emergencyFund"))
    add_goal(goals, "Emergency Fund", "emergency", "Critical", 1, emergency_need, emergency_need, emergency_existing, max(0, emergency_need - emergency_existing) / 12, "Emergency fund target is six months of expenses.")

    for kid in b.get("kids", []):
        child_age, name = _int(kid.get("age")), kid.get("name") or "Child"
        if child_age < 17:
            years = max(1, 17 - child_age)
            today, future = 2500000, _fv_lumpsum(2500000, 0.10, years)
            existing, _ = project_investments(investments, years, "childEducation")
            add_goal(goals, f"{name} Higher Education", "childEducation", "High", years, today, future, existing, _sip_required(max(0, future - existing), 0.09, years), "Auto-created at child age 17.")
        if child_age < 22:
            years = max(1, 22 - child_age)
            today, future = 1500000, _fv_lumpsum(1500000, 0.07, years)
            existing, _ = project_investments(investments, years, "marriage")
            add_goal(goals, f"{name} Marriage", "marriage", "Medium", years, today, future, existing, _sip_required(max(0, future - existing), 0.09, years), "Auto-created at child age 22.")

    for user_goal in p.get("goals", []):
        years, today = _int(user_goal.get("years")), _num(user_goal.get("presentCost"))
        inflation = (_num(user_goal.get("inflationPct")) or 6) / 100
        expected = (_num(user_goal.get("expectedReturnPct")) or 9) / 100
        future = _fv_lumpsum(today, inflation, years)
        existing, _ = project_investments(investments, years, user_goal.get("category"))
        add_goal(goals, user_goal.get("name", "Goal"), user_goal.get("category", "wealth"), user_goal.get("priority", "Medium"), years, today, future, existing, _sip_required(max(0, future - existing), expected, years), "User-entered goal.")

    remaining = max(0, _num(cf.get("remainingSurplusAfterExistingInvestments")))
    total_target = sum(_num(g.get("targetMonthlyInvestment")) for g in goals)
    scale = min(1, remaining / total_target) if total_target > 0 else 0
    for g in goals:
        target = _num(g.get("targetMonthlyInvestment"))
        rec = target * scale
        g["recommendedMonthlyInvestment"] = _money_pos(rec)
        g["fundingStatus"] = "Fully funded" if rec >= target * 0.98 else "Partially funded" if rec > 0 else "Not funded"

    ins = insurance_need(p, cf, goals)
    actions = []
    if _num(cf.get("monthlySurplus")) <= 0:
        actions.append("Fix cash-flow before starting new investments.")
    if _num(ins.get("lifeCoverGap")) > 0:
        actions.append(f"Review life cover gap of {_fmt_money(ins.get('lifeCoverGap'))}.")
    if _num(ins.get("healthCoverGap")) > 0:
        actions.append(f"Review health cover gap of {_fmt_money(ins.get('healthCoverGap'))}.")
    actions.append(f"Keep new investments within available surplus of {_fmt_money(remaining)}.")
    return {"goals": goals, "insurance": ins, "actionPlan": actions}


def risk_profile(p, goals, cf):
    age = _int(p.get("basics", {}).get("age"))
    min_years = min([_num(g.get("years")) for g in goals if _num(g.get("years")) > 0] or [10])
    if _num(cf.get("remainingSurplusAfterExistingInvestments")) <= 0 or min_years <= 3 or age >= 55:
        return {"label": "Conservative", "equity": 35, "debt": 55, "gold": 10, "reason": "Short goal timeline, low surplus or higher age requires lower volatility."}
    if age < 35 and min_years >= 7:
        return {"label": "Growth", "equity": 70, "debt": 20, "gold": 10, "reason": "Young age and longer goal timelines allow higher growth allocation."}
    return {"label": "Balanced", "equity": 55, "debt": 35, "gold": 10, "reason": "Balanced allocation based on age, goals and surplus."}


def build_summary(p, cf, tax, plan):
    assets = sum(_num(i.get("currentValue")) for i in p.get("investments", [])) + _num(p.get("emergencyFund"))
    liab = p.get("liabilities", {}) or {}
    debt = sum(_num(v) for v in liab.values()) if isinstance(liab, dict) else 0
    warnings = []
    if _num(cf.get("monthlySurplus")) <= 0:
        warnings.append("Monthly surplus is zero or negative.")
    if _num(cf.get("currentMonthlyInvestments")) > _num(cf.get("monthlySurplus")):
        warnings.append("Existing investments exceed monthly surplus; verify expenses and SIP data.")
    return {**cf, "netWorth": _money(assets - debt), "assets": _money(assets), "liabilities": _money(debt), "tax": tax, "riskProfile": risk_profile(p, plan.get("goals", []), cf), "oneLineDiagnosis": "SmartFinly AI reviewed cash-flow, tax, goals, insurance and investments using guardrails.", "topPriorities": plan.get("actionPlan", [])[:5], "warnings": warnings, "aiGeneratedWithGuardrails": True, "trustMessage": "AI-generated plan with affordability, tax, insurance and compliance guardrails."}


def truth_sheet(summary, plan):
    goals = []
    for g in plan.get("goals", []):
        goals.append({"name": g.get("name"), "priority": g.get("priority"), "years": g.get("years"), "todayNeed": _money(g.get("presentCost")), "futureNeed": _money(g.get("futureCost")), "existingAllocation": _money(g.get("existingAllocation")), "gap": _money(g.get("gap")), "targetMonthlyInvestment": _money(g.get("targetMonthlyInvestment")), "recommendedMonthlyInvestment": _money(g.get("recommendedMonthlyInvestment")), "fundingStatus": g.get("fundingStatus"), "notes": g.get("notes", "")})
    return {"fyLabel": "FY 2026-27", "cashflow": {k: summary.get(k) for k in ["monthlyIncome", "monthlyExpenses", "monthlySurplus", "currentMonthlyInvestments", "remainingSurplusAfterExistingInvestments"]}, "goals": goals, "goalTotals": {"todayNeed": _money(sum(_num(g.get("todayNeed")) for g in goals)), "futureNeed": _money(sum(_num(g.get("futureNeed")) for g in goals)), "targetMonthlyInvestment": _money(sum(_num(g.get("targetMonthlyInvestment")) for g in goals)), "recommendedMonthlyInvestment": _money(sum(_num(g.get("recommendedMonthlyInvestment")) for g in goals))}, "tax": summary.get("tax", {}), "insurance": plan.get("insurance", {}), "aiGuardrails": {"aiGenerated": True, "guardrailChecked": True, "educationalOnly": True, "noGuaranteedReturns": True}}


def build_report(summary, plan, truth):
    tax, ins = summary.get("tax", {}), plan.get("insurance", {})
    lines = ["# SmartFinly AI Financial Plan", "", "> **AI generated with guardrails:** recommendations are checked against affordability, tax facts, insurance base numbers and compliance rules.", "", f"**Financial year:** {tax.get('fyLabel', 'FY 2026-27')}", "", "## 1. AI Diagnosis", "", summary.get("oneLineDiagnosis", ""), "", "### Top priorities"]
    for i, item in enumerate(summary.get("topPriorities", [])[:5], 1):
        lines.append(f"{i}. {item}")
    lines += ["", "## 2. Cash-flow Guardrail", "", "| Item | Amount |", "|---|---:|", f"| Monthly income | {_fmt_money(summary.get('monthlyIncome'))} |", f"| Monthly expenses including EMI | {_fmt_money(summary.get('monthlyExpenses'))} |", f"| Monthly surplus | {_fmt_money(summary.get('monthlySurplus'))} |", f"| Current monthly investments | {_fmt_money(summary.get('currentMonthlyInvestments'))} |", f"| Maximum new monthly investment allowed | {_fmt_money(summary.get('remainingSurplusAfterExistingInvestments'))} |", "", "## 3. Goal Summary", "", "| Goal | Priority | Years | Today need | Future need | Gap | Target SIP | AI recommended SIP | Status |", "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for g in truth.get("goals", []):
        lines.append(f"| {g.get('name')} | {g.get('priority')} | {g.get('years')} | {_fmt_money(g.get('todayNeed'))} | {_fmt_money(g.get('futureNeed'))} | {_fmt_money(g.get('gap'))} | {_fmt_money(g.get('targetMonthlyInvestment'))} | {_fmt_money(g.get('recommendedMonthlyInvestment'))} | {g.get('fundingStatus')} |")
    lines += ["", "## 4. Tax Calculation", "", f"- Suggested regime: **{tax.get('preferredRegime')}**", f"- Old tax: **{_fmt_money(tax.get('oldTax'))}**", f"- New tax: **{_fmt_money(tax.get('newTax'))}**", "", "### Old regime slab-wise calculation", "", "| Slab | Rate | Taxable amount | Tax |", "|---|---:|---:|---:|"]
    for r in tax.get("oldSlabBreakdown", []):
        lines.append(f"| {r.get('range')} | {r.get('ratePct')}% | {_fmt_money(r.get('taxableAmount'))} | {_fmt_money(r.get('tax'))} |")
    lines += ["", "### New regime slab-wise calculation", "", "| Slab | Rate | Taxable amount | Tax |", "|---|---:|---:|---:|"]
    for r in tax.get("newSlabBreakdown", []):
        lines.append(f"| {r.get('range')} | {r.get('ratePct')}% | {_fmt_money(r.get('taxableAmount'))} | {_fmt_money(r.get('tax'))} |")
    risk = summary.get("riskProfile", {})
    lines += ["", "## 5. Insurance Calculation", "", "| Cover | Existing | Required | Gap | Assumption |", "|---|---:|---:|---:|---|", f"| Life cover | {_fmt_money(ins.get('existingLifeCover'))} | {_fmt_money(ins.get('requiredLifeCover'))} | {_fmt_money(ins.get('lifeCoverGap'))} | Income replacement + liabilities + priority goal gaps |", f"| Health cover | {_fmt_money(ins.get('existingHealthCover'))} | {_fmt_money(ins.get('requiredHealthCover'))} | {_fmt_money(ins.get('healthCoverGap'))} | Family size + dependent parents + city cost |", "", "## 6. Investment Mapping", "", f"- AI risk profile: **{risk.get('label')}**", f"- Suggested allocation: **{risk.get('equity')}% equity / {risk.get('debt')}% debt / {risk.get('gold')}% gold**", f"- Reason: {risk.get('reason')}", "", "## 7. Action Plan"]
    for i, item in enumerate(plan.get("actionPlan", [])[:8], 1):
        lines.append(f"{i}. {item}")
    lines += ["", "## 8. Trust & Compliance Note", "", "- Educational/sampling output only.", "- Not SEBI/RBI/IRDAI-registered advice.", "- No guaranteed returns.", "- No product execution.", "- Verify with qualified professionals."]
    return "\n".join(lines)


def ai_overlay(p, body):
    if not AI_PLANNER_MODE:
        return body
    try:
        prompt = "You are SmartFinly AI Planner. Return JSON only with summary.oneLineDiagnosis, summary.topPriorities, and plan.actionPlan. Do not change numbers or recommend SIP above surplus. " + json.dumps({"profile": p, "calculated": body}, ensure_ascii=False)
        response = bedrock.converse(modelId=MODEL_ID, messages=[{"role": "user", "content": [{"text": prompt}]}], inferenceConfig={"maxTokens": 1400, "temperature": 0.2, "topP": 0.9})
        text = response["output"]["message"]["content"][0]["text"]
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            ai = json.loads(text[start:end + 1])
            if isinstance(ai.get("summary"), dict):
                body["summary"]["oneLineDiagnosis"] = ai["summary"].get("oneLineDiagnosis") or body["summary"]["oneLineDiagnosis"]
                if isinstance(ai["summary"].get("topPriorities"), list):
                    body["summary"]["topPriorities"] = ai["summary"]["topPriorities"][:5]
            if isinstance(ai.get("plan"), dict) and isinstance(ai["plan"].get("actionPlan"), list):
                body["plan"]["actionPlan"] = ai["plan"]["actionPlan"][:8]
            body["truthSheet"] = truth_sheet(body["summary"], body["plan"])
            body["report"] = build_report(body["summary"], body["plan"], body["truthSheet"])
    except Exception as exc:
        print("AI overlay failed:", exc.__class__.__name__)
    return body


def analyze_profile(profile):
    p = normalize_profile(profile)
    validate_profile(p)
    cf = cashflow(p)
    tax = compute_tax(p)
    plan = build_plan(p, cf)
    summary = build_summary(p, cf, tax, plan)
    truth = truth_sheet(summary, plan)
    body = {"summary": summary, "plan": plan, "truthSheet": truth, "report": build_report(summary, plan, truth)}
    return ai_overlay(p, body)


def lambda_handler(event, context):
    try:
        payload = _parse_event(event)
        _security_scan(payload)
        return _json_response(200, analyze_profile(payload))
    except UserInputError as exc:
        if str(exc) == "__OPTIONS__":
            return {"statusCode": 204, "headers": CORS_HEADERS, "body": ""}
        return _json_response(400, {"error": str(exc)})
    except Exception as exc:
        print("Unhandled SmartFinly error:", exc.__class__.__name__, str(exc)[:300])
        return _json_response(500, {"error": "Internal error. Please try again later."})

# SAM template uses Handler: app.handler.
# Keep this wrapper so Lambda Function URL can call the expected symbol.
def handler(event, context):
    return lambda_handler(event, context)
