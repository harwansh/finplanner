
import json
import importlib.util
import sys
import types
from pathlib import Path


class _FakeBedrockClient:
    def converse(self, *args, **kwargs):
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps(
                                {
                                    "summary": {
                                        "oneLineDiagnosis": "Full payload preservation smoke test.",
                                        "topPriorities": ["Verify all sections are preserved"],
                                    },
                                    "plan": {"actionPlan": ["Full payload preservation passed."]},
                                }
                            )
                        }
                    ]
                }
            }
        }


fake_boto3 = types.ModuleType("boto3")
fake_boto3.client = lambda *args, **kwargs: _FakeBedrockClient()
sys.modules.setdefault("boto3", fake_boto3)

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "analyze" / "app.py"
spec = importlib.util.spec_from_file_location("app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def invoke(payload):
    return app.lambda_handler({"body": json.dumps(payload)}, None)


def test_full_payload_not_zero():
    payload = {
        "basics": {
            "age": 34,
            "desiredRetirementAge": 60,
            "country": "India",
            "cityTier": "Metro",
            "maritalStatus": "married",
            "employmentType": "salaried",
            "kids": [{"name": "Aarav", "age": 5}],
            "parentsDependent": True,
            "dependentParentsCount": 2,
        },
        "salary": {
            "basicSalary": 1200000,
            "hraReceived": 480000,
            "grossEarning": 3018000,
            "epfContribution": 144000,
            "npsEmployer": 120000,
            "rentPaid": 720000,
            "profTax": 2400,
            "incomeTax": 300000,
        },
        "income": {"monthlyAfterTax": 210000, "bonusAnnual": 200000, "otherMonthly": 10000},
        "expenses": {"fixed": 80000, "variable": 35000, "annual": 240000},
        "monthlyEmi": 25000,
        "emergencyFund": 800000,
        "liabilities": {"personalLoan": 250000, "creditCard": 50000},
        "insurance": {"life": 5000000, "health": 1000000},
        "tax": {"deduction80C": 50000, "nps80CCD1B": 50000, "health80D": 25000, "health80DParents": 50000, "taxPaid": 300000},
        "investments": [
            {"name": "EPF corpus", "category": "epf", "currentValue": 900000, "monthlyAmount": 0, "expectedReturnPct": 8.25, "goal": "retirement"},
            {"name": "NPS Tier 1", "category": "nps", "currentValue": 350000, "monthlyAmount": 5000, "expectedReturnPct": 10, "goal": "retirement"},
            {"name": "Flexicap SIP", "category": "equityFlexiCap", "currentValue": 600000, "monthlyAmount": 20000, "expectedReturnPct": 11, "goal": "wealth"},
            {"name": "Child education SIP", "category": "childEducation", "currentValue": 250000, "monthlyAmount": 10000, "expectedReturnPct": 10, "goal": "childEducation"},
        ],
        "goals": [{"name": "Home", "category": "home", "presentCost": 2500000, "years": 5, "inflationPct": 6, "expectedReturnPct": 9, "priority": "High"}],
    }

    res = invoke(payload)
    assert res["statusCode"] == 200, res["body"]
    body = json.loads(res["body"])
    summary = body["summary"]
    plan = body["plan"]

    assert summary["monthlyExpenses"] == 160000.0, summary
    assert summary["currentMonthlyInvestments"] >= 45000.0, summary
    assert summary["assets"] >= 2800000.0, summary
    assert summary["netWorth"] > 0, summary
    assert plan["insurance"]["existingLifeCover"] == 5000000.0, plan["insurance"]
    assert plan["insurance"]["existingHealthCover"] == 1000000.0, plan["insurance"]
    assert len(plan["goals"]) >= 5, plan["goals"]
    assert any(float(g.get("futureCost") or 0) > 0 for g in plan["goals"]), plan["goals"]


if __name__ == "__main__":
    test_full_payload_not_zero()
    print("full payload preservation smoke test passed")
