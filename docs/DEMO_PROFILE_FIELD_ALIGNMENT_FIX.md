# Demo Profile Field Alignment Fix

## Root cause

The demo profile loaded visible values, but frontend/backend field names were not fully aligned after multiple upgrades.

Examples:
- `currentAge` should map to `basics.age`
- `retirementAge` should map to `basics.desiredRetirementAge`
- `monthlyIncomeAfterTax` should map to `income.monthlyAfterTax`

## Fix

Backend now normalizes aliases before validation.

Investor demo profile also includes canonical and alias keys where possible.

## Retest

1. Click Load investor demo profile.
2. Review Profile tab.
3. Continue through tabs or go to Review.
4. Generate plan.
5. The app should not complain that current age/monthly income is missing.
