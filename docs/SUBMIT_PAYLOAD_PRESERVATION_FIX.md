# Submit Payload Preservation Fix

## Problem

The UI review tab showed real values, but backend output showed:

- Net worth = 0
- Expenses = 0
- Existing SIPs = 0
- Insurance existing cover = 0
- Goals = 0

This means the frontend submit pipeline was losing sections before API call.

## Fix

The frontend now uses `buildSubmitPayload(data)` directly from full form state instead of lossy `cleanProfile(data)`.

The submit payload now preserves and canonicalizes:

- basics
- salary
- income
- expenses
- liabilities
- insurance
- investments
- goals
- tax

## Retest

```bash
python3 backend/tests/test_full_payload_preservation.py
python3 ~/Downloads/frontend_backend_mapping_qa.py
```

Then deploy and test investor demo profile.
