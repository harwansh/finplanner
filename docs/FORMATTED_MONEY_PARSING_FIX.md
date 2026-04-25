# Formatted Money Parsing Fix

## Problem

Visible form values were present, but output showed:

- Net worth ₹0
- Monthly expenses ₹0
- Existing SIPs ₹0
- Goal values ₹0

Root cause: backend `_num()` could not parse formatted Indian money strings like:

- `9,00,000`
- `₹80,000`
- `5,000`

So many values silently became zero.

## Fix

Backend `_num()` now parses:

- raw numbers
- comma-formatted Indian currency
- rupee symbol
- percent values
- strings with spaces

## Retest

```bash
python3 -m py_compile backend/src/analyze/app.py
python3 backend/tests/test_formatted_money_parsing.py
python3 ~/Downloads/frontend_backend_mapping_qa.py
```

Then deploy and test the demo profile again.
