
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
                                        "oneLineDiagnosis": "Local smoke-test AI response.",
                                        "topPriorities": ["Validate field aliases", "Generate stable plan"],
                                    },
                                    "plan": {
                                        "actionPlan": ["Local smoke test passed."]
                                    },
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


def test_minimal_alias_profile_works():
    payload = {
        "currentAge": 34,
        "retirementAge": 60,
        "monthlyIncome": 210000,
        "expenses": {"fixed": 80000, "variable": 30000, "annual": 120000},
        "basics": {"employment": "salaried", "cityType": "Metro", "maritalStatus": "single"},
    }
    res = invoke(payload)
    assert res["statusCode"] == 200, res["body"]
    body = json.loads(res["body"])
    assert "summary" in body
    assert "plan" in body
    assert "truthSheet" in body
    assert body["summary"]["monthlyIncome"] == 210000


def test_missing_core_fields_returns_400():
    res = invoke({"basics": {"employmentType": "salaried"}})
    assert res["statusCode"] == 400
    body = json.loads(res["body"])
    assert body["code"] == "INPUT_VALIDATION_ERROR"
    assert "Missing required fields" in body["error"]


if __name__ == "__main__":
    test_minimal_alias_profile_works()
    test_missing_core_fields_returns_400()
    print("lambda smoke tests passed")
