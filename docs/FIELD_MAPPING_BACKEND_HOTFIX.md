# Field Mapping Backend Hotfix v2

## Problem

Previous patch file was corrupted during download at `patch_block = r`.

## Backend issues fixed

- `_missing_core_fields` missing caused Lambda 500.
- `children` did not map into `basics.kids`.
- `totalMonthlyEMI` did not map into `monthlyEmi`.

## Retest

```bash
python3 ~/Downloads/frontend_backend_mapping_qa.py
python3 backend/tests/test_lambda_smoke.py
```
