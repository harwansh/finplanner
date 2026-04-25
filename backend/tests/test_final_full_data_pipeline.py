
import json
import importlib.util
import sys
import types
from pathlib import Path


class _FakeBedrockClient:
    def converse(self, *args, **kwargs):
        return {"output": {"message": {"content": [{"text": json.dumps({"summary": {"oneLineDiagnosis": "test", "topPriorities": ["ok"]}, "plan": {"actionPlan": ["ok"]}})}]}}}


fake_boto3 = types.ModuleType("boto3")
fake_boto3.client = lambda *args, **kwargs: _FakeBedrockClient()
sys.modules.setdefault("boto3", fake_boto3)

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "analyze" / "app.py"
spec = importlib.util.spec_from_file_location("app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

payload = {
    "basics": {"age": "34", "desiredRetirementAge": "60", "country": "India", "cityTier": "Metro", "maritalStatus": "married", "employmentType": "salaried", "kids": [{"name": "Aarav", "age": "5"}], "parentsDependent": True, "dependentParentsCount": "2"},
    "salary": {"basicSalary": "12,00,000", "hraReceived": "4,80,000", "grossEarning": "30,18,000", "epfContribution": "1,44,000", "npsEmployer": "1,20,000", "rentPaid": "7,20,000", "profTax": "2,400", "incomeTax": "3,00,000"},
    "income": {"monthlyAfterTax": "2,10,000", "bonusAnnual": "2,00,000", "otherMonthly": "10,000"},
    "expenses": {"fixed": "80,000", "variable": "35,000", "annual": "2,40,000"},
    "monthlyEmi": "25,000",
    "emergencyFund": "8,00,000",
    "liabilities": {"personalLoan": "2,50,000", "creditCard": "50,000"},
    "insurance": {"life": "50,00,000", "health": "10,00,000"},
    "tax": {"deduction80C": "50,000", "nps80CCD1B": "50,000", "health80D": "25,000", "health80DParents": "50,000", "taxPaid": "3,00,000"},
    "investments": [
        {"name": "EPF corpus", "category": "epf", "currentValue": "9,00,000", "monthlyAmount": "0", "expectedReturnPct": "8.25", "goal": "retirement"},
        {"name": "NPS Tier 1", "category": "nps", "currentValue": "3,50,000", "monthlyAmount": "5,000", "expectedReturnPct": "10", "goal": "retirement"},
        {"name": "Flexicap SIP", "category": "equityFlexiCap", "currentValue": "6,00,000", "monthlyAmount": "20,000", "expectedReturnPct": "11", "goal": "wealth"},
        {"name": "Child education SIP", "category": "childEducation", "currentValue": "2,50,000", "monthlyAmount": "10,000", "expectedReturnPct": "10", "goal": "childEducation"},
    ],
    "goals": [{"name": "Home", "category": "home", "presentCost": "25,00,000", "years": "5", "inflationPct": "6", "expectedReturnPct": "9", "priority": "High"}],
}

if __name__ == "__main__":
    res = app.lambda_handler({"body": json.dumps(payload)}, None)
    assert res["statusCode"] == 200, res["body"]
    body = json.loads(res["body"])
    s = body["summary"]
    p = body["plan"]
    assert s["monthlyExpenses"] == 160000.0, s
    assert s["currentMonthlyInvestments"] >= 45000.0, s
    assert s["assets"] >= 2800000.0, s
    assert s["netWorth"] > 0, s
    assert p["insurance"]["existingLifeCover"] == 5000000.0, p["insurance"]
    assert p["insurance"]["existingHealthCover"] == 1000000.0, p["insurance"]
    assert len(p["goals"]) >= 5, p["goals"]
    print("FINAL FULL DATA TEST PASSED")
