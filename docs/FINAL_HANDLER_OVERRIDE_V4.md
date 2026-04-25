# Final Handler Override v4

## Fix

The previous final handler relied on `_json_response` and `UserInputError`, but the local active `app.py` did not define them.

v4 is self-contained:

- Defines `_sf_response`
- Defines `_SmartFinlyInputError`
- Avoids `except UserInputError`
- Accepts raw profile and `{ profile: ... }`
- Logs payload shape
- Returns deterministic result even if AI overlay fails

## Verify

```bash
python3 backend/tests/test_payload_contract_raw_and_wrapped.py
```
