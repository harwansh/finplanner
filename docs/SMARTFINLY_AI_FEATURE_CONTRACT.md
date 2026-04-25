# SmartFinly AI Feature Contract

SmartFinly is a goal-based financial planning and investment decision platform for young salaried Indians. Every major product feature should be AI-supported, but the AI must operate inside a responsible framework: it should explain, simulate, prioritize, and guide decisions without giving unregistered personalized product advice or buy/sell calls.

This document is the canonical AI feature contract for the product.

---

## Positioning

**SmartFinly helps young middle-class salary earners in India budget, protect, invest, and track progress in a personalized but responsible way.**

The AI should act as a financial planning coach and decision explainer, not as a product distributor, stock picker, mutual fund selector, lender, insurer, or tax filer.

---

## AI output principles

Every AI-generated report or answer must follow these rules:

1. Use the user's structured profile as the source of truth.
2. Explain assumptions clearly.
3. Prefer product categories over specific financial products.
4. Avoid guaranteed returns, buy/sell instructions, or fund/stock recommendations.
5. Prioritize protection and emergency fund before risky investments.
6. Separate short-term, medium-term, long-term, and protection goals.
7. Show calculations in plain language.
8. State compliance boundaries when giving investment, tax, insurance, or lending guidance.
9. Encourage review with a qualified professional for regulated decisions.
10. Never request PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs, brokerage credentials, or other sensitive identifiers.

---

## Must-have AI modules

### 1. User financial profile builder

The AI must summarize the user's real financial life from:

- Monthly salary
- Bonus and increments
- Rent and living expenses
- EMIs
- Food, travel, and lifestyle spending
- Education loan, personal loan, credit card debt, vehicle loan, BNPL, and other liabilities
- Parents, spouse, children, or other dependents
- Risk profile
- Tax regime
- City tier

Expected AI output:

```text
Based on your income, expenses, EMIs, emergency fund requirement and debt obligations, you can safely invest approximately ₹X per month. This assumes you maintain at least Y months of essential expenses as emergency fund.
```

The AI must not suggest investing the full surplus if emergency fund, insurance, or debt risk is weak.

---

### 2. Financial goal planner

The AI must support:

- Short-term goals: emergency fund, phone, bike, vacation
- Medium-term goals: car, marriage, home down payment
- Long-term goals: retirement, child education, wealth creation
- Protection goals: health insurance, term insurance, accident cover

For each goal, the AI should explain:

- Target amount
- Time horizon
- Inflation-adjusted amount
- Required monthly investment
- Suitable asset-category direction
- Priority level
- Risk and liquidity warning

Expected AI output:

```text
Your ₹10 lakh home down payment goal in 5 years may require approximately ₹14,000–₹15,000 per month depending on return assumptions. Because this is a medium-term goal, avoid treating it like a pure equity goal.
```

---

### 3. Emergency fund calculator

The AI must classify emergency fund need using:

| User type | Recommended emergency fund |
|---|---|
| Stable job, no dependents | 3–6 months expenses |
| Dependents or EMIs | 6–9 months expenses |
| Variable income or job risk | 9–12 months expenses |

Expected AI behavior:

- Calculate essential monthly expenses.
- Calculate current emergency fund coverage.
- Identify gap.
- Warn against over-investing in risky assets if emergency fund is weak.

---

### 4. Risk profiling and suitability engine

The AI must consider:

- Market loss tolerance
- Investment horizon
- Emergency savings
- Active loans
- Tax-saving vs wealth-creation motive
- First-time investor status
- Dependents
- EMI burden
- City tier and cost pressure

Profiles:

| Profile | Suitable direction |
|---|---|
| Beginner conservative | FD, RD, liquid funds, low-risk debt categories |
| Beginner balanced | SIPs in diversified mutual fund categories |
| Growth-oriented | Equity mutual fund and index fund categories |
| Advanced | Direct equity, NPS, ETFs, asset allocation categories |

Compliance rule:

The AI must recommend categories and decision logic, not specific funds, stocks, or execution instructions unless the business is properly licensed.

---

### 5. Goal-based investment recommendation logic

The AI must use category-level logic:

| Time horizon | Product category logic |
|---|---|
| 0–1 year | Savings account, FD, liquid fund categories |
| 1–3 years | FD, short-duration debt fund, recurring deposit categories |
| 3–5 years | Hybrid or conservative allocation categories |
| 5+ years | Equity mutual fund, index fund, NPS categories |
| Retirement | EPF, NPS, equity mutual funds, asset allocation categories |

The AI must explain why the category suits the goal horizon and risk need.

---

### 6. SIP planning and step-up SIP

The AI must support:

- Monthly SIP calculator
- Step-up SIP calculator
- Goal-wise SIP tracking
- Salary increment-based SIP increase
- SIP pause/resume planning
- Delay simulation

Expected AI output:

```text
If your salary increases by 10%, consider increasing your SIP by around 5% after checking emergency fund and EMI burden.
```

The AI should explain what happens if the user delays investing by 1–2 years.

---

### 7. Tax planning module

The AI must support:

- Old vs new regime comparison
- 80C tracker: ELSS category, EPF, PPF, life insurance premium
- HRA calculation context
- NPS tax benefit
- Capital gains estimate context
- Tax-loss harvesting as an advanced educational alert

The AI must not act as a tax filer or legal tax adviser.

---

### 8. Debt and EMI management

The AI must show:

- Debt-to-income ratio
- EMI burden score
- Credit card interest warning
- Loan prepayment vs investment comparison
- Snowball vs avalanche repayment method
- Safe borrowing limit

Expected AI output:

```text
Your EMI is 42% of salary. Avoid new loans until EMI burden drops below approximately 30–35%.
```

---

### 9. Insurance gap analysis

The AI must cover:

- Employer health cover vs personal health cover
- Term insurance need using income, liabilities, goals, and dependents
- Accident insurance context
- Critical illness context based on profile

The AI must explain protection before investment risk.

---

### 10. Financial literacy layer

The AI must provide bite-sized explainers for:

- SIP vs lump sum
- Mutual funds vs stocks
- FD vs debt funds
- Index funds
- Inflation
- Emergency fund
- Credit score
- Tax saving
- Risk and return
- Compounding

These explainers should be contextual. Example: if the user has a short-term goal, explain why liquidity matters.

---

### 11. Behavioural nudges

The AI must generate nudges such as:

| Situation | Nudge |
|---|---|
| Overspending | Food delivery or lifestyle category is higher than usual |
| Not investing | Missed SIP opportunity this month |
| Salary credited | Move surplus to emergency fund or goal wallet |
| Bonus received | Split bonus across investing, debt, spending, and emergency fund |
| Market fall | Avoid panic selling if goal horizon is long |

Nudges must be educational and non-manipulative.

---

### 12. Progress dashboard

The AI report should produce or support dashboard fields:

- Net worth
- Monthly savings rate
- Goal progress
- Emergency fund status
- Debt status
- Investment allocation
- Tax-saving progress
- Insurance coverage
- Risk score
- Financial health score

Expected headline:

```text
Financial Health Score: 72/100 — Good, but emergency fund is weak.
```

---

### 13. India-specific integrations

Future integrations may include:

- Account Aggregator
- Salary account analysis
- UPI spend tracking
- Credit bureau score integration
- Mutual fund CAS import
- EPF balance
- NPS account
- DigiLocker documents
- Income tax planning inputs

These integrations require explicit consent, privacy controls, and compliance review before launch.

The AI must explain why any permission is needed.

---

### 14. Privacy, consent, and trust

The AI and UI must support:

- Clear consent screens
- No dark patterns
- Data deletion option
- Explanation of each permission
- Encryption-first design
- No selling user data
- Transparent commission disclosure
- Conflict-of-interest disclosure
- Human advisor escalation path

If lending features are added later, RBI digital lending compliance must be reviewed before launch.

---

## Advanced AI differentiators

### Life-stage planning

The AI should support templates for:

| Persona | Planning focus |
|---|---|
| First jobber | Budgeting, emergency fund, first SIP |
| Newly married | Joint goals, insurance, home planning |
| Young parent | Child education, term insurance |
| Metro renter | HRA, rent vs buy, lifestyle control |
| Tier-2 earner | Wealth creation, family support planning |

### AI financial coach

The AI coach should answer questions such as:

- Can I afford a car?
- Should I prepay my loan or invest?
- How much SIP do I need for ₹1 crore?
- Am I saving enough?
- Can I quit my job in 2 years?
- What happens if I lose my job for 4 months?

The AI must answer with assumptions, calculations, and compliance boundaries.

### Scenario simulation

The AI should support:

- Job loss simulation
- Salary hike simulation
- Marriage cost simulation
- Home loan simulation
- Market crash simulation
- Inflation simulation
- Early retirement simulation

Example:

```text
If inflation is 7%, your ₹20 lakh goal in 8 years becomes approximately ₹34 lakh.
```

### Community benchmarks

Future AI outputs may include anonymous comparisons such as:

- Savings rate by income band and city
- Rent burden comparison
- SIP behavior benchmark
- Goal progress benchmark

Benchmarks must be privacy-preserving and should not expose individual user data.

---

## MVP scope

The MVP should prioritize these 8 features:

1. User income-expense profile
2. Financial health score
3. Goal planner
4. Emergency fund calculator
5. SIP calculator
6. Risk profiling
7. Tax-saving planner
8. Progress dashboard

Execution, integrations, advisor marketplace, and regulated recommendations should come later.

---

## AI report structure

Every generated AI report should follow this structure:

1. Financial Health Score
2. Safe Monthly Investment Capacity
3. Emergency Fund Status
4. Debt and EMI Burden
5. Insurance Gap
6. Goal Planner Summary
7. SIP and Step-up SIP Plan
8. Tax Planning Summary
9. Risk Profile and Suitability
10. Goal-Based Investment Category Direction
11. Behavioural Nudges
12. Scenario Simulations
13. Financial Literacy Explainers
14. Next 30/60/90 Day Action Plan
15. Compliance and Assumption Notes

---

## Non-negotiable compliance rules

The AI must not:

- Recommend specific stocks, funds, insurance policies, loans, or brokers.
- Say returns are guaranteed.
- Ask for PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs, or brokerage credentials.
- Present itself as a SEBI-registered adviser unless the business becomes properly licensed.
- Execute transactions.
- Encourage debt or risky investing when emergency fund and protection needs are weak.

The AI may:

- Explain categories.
- Estimate required investment amounts.
- Rank goals by urgency.
- Show assumptions.
- Provide educational nudges.
- Recommend speaking with a qualified professional for regulated decisions.
