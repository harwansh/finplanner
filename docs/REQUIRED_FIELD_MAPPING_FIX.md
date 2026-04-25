# Required Field Mapping Fix

## Problem

The user can fill visible fields, but backend still says:

- Current age is required
- Desired retirement age greater than current age
- Monthly after-tax income is required

That means submit payload did not contain canonical backend keys:

- `basics.age`
- `basics.desiredRetirementAge`
- `income.monthlyAfterTax`

## Fix

Frontend now canonicalizes the submit payload immediately before `analyze()`.

Backend now also performs defensive alias normalization and removes comma/rupee formatting before validation.

## Retest

1. Fill Current age.
2. Fill Desired retirement age.
3. Fill Monthly income after tax.
4. Accept legal checkbox.
5. Generate.
6. If it still fails, check CloudWatch log line beginning:
   `Validation failed after alias normalization`
