# HTTP 400 Debug

## What changed

502 means backend crash/import/handler problem.  
400 means backend is alive and rejected the submitted input.

## Most common current cause

For salaried users, these fields are required for tax calculation:

- Basic Salary
- HRA received
- E-PF Contribution

The frontend now checks these before calling Lambda and shows the exact message.

## Browser extension warning

`A listener indicated an asynchronous response by returning true...`

This is usually from a Chrome extension. Test in incognito with extensions disabled.

## Retest

1. Open site in incognito.
2. Fill Profile tab.
3. If Employment Type = salaried, fill Basic Salary, HRA received, E-PF Contribution.
4. Submit again.
5. If error remains, the page should show the exact backend reason.
