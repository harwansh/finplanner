# Validation and Children Panel Fix

## Problem

Users could reach Review and see a generic required-field error such as:

- Current age is required.
- Desired retirement age must be greater than current age.
- Monthly after-tax income is required.

The UI did not automatically guide the user back to the tab that needs correction.

Also, the Children section still rendered with a light background and pale text on the dark theme.

## Fix

- Validation errors now map to the likely tab.
- After an error, the app switches back to the relevant tab and scrolls to the error/invalid field.
- Children/kids panels are forced to dark readable styles.
- No backend, tax, insurance, AI, or calculation logic is changed.

## Retest

1. Leave Current age blank.
2. Go to Review.
3. Click Generate.
4. App should show the error and move back to Profile.
5. Fill Current age.
6. If salaried, fill Basic Salary, HRA received, and E-PF Contribution.
7. Children card should be readable in dark mode.
