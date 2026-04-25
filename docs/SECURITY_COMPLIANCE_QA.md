# SmartFinly QA, Security, and Compliance Notes

## Scope
This is an educational / sample financial planning website. It should not claim SEBI registration, RBI regulation, guaranteed returns, or personalized regulated investment advice unless the business actually obtains the required registrations and operational controls.

## Security checks to run after deploy
1. HTTPS only.
2. Security headers present: HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, CSP.
3. API does not return duplicate CORS headers.
4. API allows only expected origin, not `*`, in production.
5. No PAN, Aadhaar, bank account, OTP, password, or document upload requested.
6. No data stored unless a clear privacy notice and consent flow exist.
7. Browser console has no CORS, CSP, or mixed-content errors.
8. Lambda logs do not print full user financial profile.
9. All numeric fields reject invalid values and preserve decimals.
10. Required fields block next-tab navigation.

## Regulatory positioning checks
- Add visible disclaimer: educational / sampling only.
- Avoid words like guaranteed, assured return, best fund, buy/sell, invest now.
- Do not collect money, execute orders, or handle securities/cash.
- If personalized investment advice for securities is offered commercially, review SEBI Investment Adviser registration requirements.
- If stock recommendations/research reports are offered for a fee, review SEBI Research Analyst registration requirements.
- If any lending/credit product flow is added, review RBI digital lending requirements and do not imply RBI approval.

## 20 profile regression scenarios
1. Single, 24, low income, no dependents.
2. Single, 30, high salary, rent + HRA.
3. Single, no dependents, high loan.
4. Married, spouse dependent, no kids.
5. Married, child age 2.
6. Married, child age 16.
7. Child age 22+ should not auto-create past child goals.
8. Parents dependent.
9. High home loan.
10. Credit-card/personal-loan heavy.
11. Negative monthly surplus.
12. Existing SIPs greater than surplus.
13. Salary EPF/NPS entered only in salary.
14. Salary EPF/NPS plus manual EPF/NPS investment entered.
15. New-regime taxable income around ₹12L.
16. Taxable income just above ₹12L.
17. Income above ₹50L surcharge case.
18. Freelance/business user.
19. Age 55, retirement at 60.
20. Invalid retirement age <= current age.

## Must-pass behavior
- No duplicate EPF/NPS from salary.
- Child education goal only before child age 17.
- Child marriage goal only before child age 22.
- Goal summary and detailed report use same backend plan goals.
- Life/health insurance cards use backend insurance output.
- Tax card shows slab-wise old/new calculation.
