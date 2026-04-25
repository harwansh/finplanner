# Lambda 400 Deep Fix

## Finding

The production error is HTTP 400, not a Lambda crash. That means Lambda handler is alive and rejecting input.

The likely cause is field-name mismatch after multiple UI/backend patches:
- UI/demo may send `currentAge`
- backend expects `basics.age`
- UI/demo may send `monthlyIncome`
- backend expects `income.monthlyAfterTax`

## Fix

Backend now normalizes aliases before validation and calculation.

Also changed salaried tax validation:
- Basic Salary / HRA / EPF are required only if salary/tax details are being used.
- A simple demo/basic profile is no longer rejected just because employment defaults to salaried.

## Added

- Clearer 400 JSON:
  - `code: INPUT_VALIDATION_ERROR`
- Local smoke tests:
  - `backend/tests/test_lambda_smoke.py`

## Local test commands

From repo root:

```bash
python3 -m py_compile backend/src/analyze/app.py
python3 backend/tests/test_lambda_smoke.py
```

## Retest production

1. Deploy.
2. Click demo profile.
3. Generate plan.
4. If 400 remains, UI should show exact backend message.
