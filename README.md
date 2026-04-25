# SmartFinly — Financial Goal Planning Framework for Young Salary Earners in India

SmartFinly is an educational framework and web application for **financial goal planning and investment decision-making among young middle-class salary earners in India**.

The project helps users structure decisions across salary, expenses, emergency fund, insurance, liabilities, tax context, investment capacity, goal hierarchy, and long-term planning. It uses deterministic calculations first, then AI-generated explanations through Amazon Bedrock to produce an educational planning report.

> **Current status:** this repository is an MVP/demo implementation of the SmartFinly framework. The default `infrastructure/template.yaml` deploys a simple demo backend using a Lambda Function URL. For production or real user financial data, use `infrastructure/template.authenticated.yaml`, which adds Cognito authentication, an HTTP API JWT authorizer, and throttling.

---

## Core idea

**A Framework for Financial Goal Planning and Investment Decision-Making among Young Middle-Class Salary Earners in India**

SmartFinly is not positioned as a product-selling financial adviser. It is a structured decision framework that helps salary earners answer questions such as:

- What is my real investible surplus after expenses, EMIs, tax, and obligations?
- Do I have enough emergency fund, life cover, and health cover before taking investment risk?
- Which goals are essential, important, or aspirational?
- How much monthly SIP or investment may be required for each goal?
- How do tax regime, EPF, NPS, 80C, 80D, HRA, and salary structure affect planning?
- What does my risk capacity look like given age, dependents, debt burden, time horizon, and job stability?
- What should I review periodically as income, family responsibilities, tax rules, and market conditions change?

---

## Framework modules

SmartFinly follows a six-part planning sequence:

1. **Income Reality**  
   Maps salary structure, take-home income, recurring expenses, EMIs, dependents, and monthly surplus.

2. **Protection First**  
   Reviews emergency fund, health insurance, life insurance, debt exposure, and family obligations before investment decisions.

3. **Goal Hierarchy**  
   Classifies goals into must-have, should-have, and aspirational goals across short, medium, and long horizons.

4. **Tax-Aware Allocation**  
   Connects old/new regime context, HRA, EPF, NPS, 80C, 80D, tax already paid, and available surplus.

5. **Risk Capacity**  
   Frames investment suitability using age, dependents, income stability, liabilities, horizon, liquidity need, and loss tolerance.

6. **Decision Rules and Review**  
   Converts the assessment into SIP gaps, goal priorities, insurance gaps, and review actions.

---

## What you get

- React + Vite frontend
- Framework-led landing page and planner routes
- Multi-step planner for Indian salary earners and families
- Profile, salary, tax, cash-flow, liabilities, insurance, investment, and goal inputs
- Sensitive-data rejection for PAN, Aadhaar, OTP, bank/account identifiers, UPI, passwords, tokens, and similar values
- Deterministic backend calculations before AI explanation
- Amazon Bedrock-powered educational report generation
- SEO pages for framework, goal planning, SIP goals, tax context, insurance gap, and investment decision-making
- Privacy, terms, disclaimer, and security pages
- AWS Amplify-ready frontend deployment
- Demo backend deployment template
- Authenticated production SAM template scaffold

---

## Important legal and safety notice

SmartFinly is an educational financial planning framework. It is **not** a SEBI-registered investment adviser, research analyst, portfolio manager, insurance broker, tax filing service, lending platform, or product execution platform.

SmartFinly does **not** provide buy/sell calls, guaranteed returns, tax filing, legal advice, insurance broking, lending decisions, or product execution.

Do **not** enter PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs, brokerage credentials, or other sensitive identifiers.

Do **not** use the unauthenticated demo deployment for real user financial data.

---

## Architecture options

### Demo / MVP deployment

The default template is optimized for controlled demos and sample data:

```text
React frontend ──► Lambda Function URL ──► Lambda ──► Bedrock
```

File:

```text
infrastructure/template.yaml
```

Use this only for demos, local testing, and controlled sample data.

### Authenticated production scaffold

The authenticated template adds Cognito and an HTTP API JWT authorizer:

```text
React frontend ──► HTTP API ──► Lambda ──► Bedrock
       │              ▲
       └─ Cognito JWT ┘
```

File:

```text
infrastructure/template.authenticated.yaml
```

This is the recommended starting point before collecting real user financial data. It includes:

- Cognito User Pool
- Cognito User Pool Client
- HTTP API JWT authorizer
- `Authorization: Bearer <token>` support in the frontend API client
- API throttling
- CORS for SmartFinly and localhost development origins

---

## Project layout

```text
finplanner/
├── backend/
│   └── src/
│       └── analyze/
│           └── app.py                 # Analyze endpoint, validation, calculations, Bedrock call
├── frontend/
│   ├── public/
│   │   ├── robots.txt
│   │   ├── sitemap.xml
│   │   └── _redirects
│   ├── src/
│   │   ├── api/client.js              # API client, optional bearer-token support
│   │   ├── pages/Home.jsx             # Main framework planner UI
│   │   ├── App.jsx                    # Framework landing, legal pages, routing
│   │   ├── trust.css
│   │   ├── ten.css
│   │   └── framework.css
│   └── package.json
├── infrastructure/
│   ├── template.yaml                  # Demo Lambda Function URL deployment
│   └── template.authenticated.yaml    # Authenticated Cognito + HTTP API deployment scaffold
├── amplify.yml                        # Amplify frontend build config
└── customHttp.yml                     # Amplify security headers and SPA rewrites
```

---

## Prerequisites

Install once:

1. AWS account with permissions for Lambda, IAM, Bedrock, Amplify, and optionally Cognito/API Gateway.
2. AWS CLI v2.
3. AWS SAM CLI.
4. Python 3.12 or 3.11.
5. Node.js 20+ and npm.
6. Docker, if your SAM build flow requires it.

---

## Enable Bedrock model access

1. Open AWS Console → **Bedrock** → **Model access**.
2. Enable access to your chosen model.
3. Use a region where that model is available. `us-east-1` is the default in this repo.
4. If Bedrock requires a first-time-use form, complete it in the AWS Console.

The current default model ID is:

```text
amazon.nova-pro-v1:0
```

You can change it with the `BedrockModelId` parameter in the SAM template.

---

## Deploy the demo backend

Use this for quick testing only.

```bash
cd infrastructure
sam build -t template.yaml
sam deploy --guided -t template.yaml
```

Suggested guided values:

| Prompt | Answer |
|---|---|
| Stack name | `smartfinly-demo` |
| AWS Region | `us-east-1` or your Bedrock-enabled region |
| Parameter BedrockModelId | keep default or use your available Bedrock model ID |
| Parameter BedrockRegion | `us-east-1` or your Bedrock region |
| Confirm changes before deploy | `y` |
| Allow IAM role creation | `Y` |
| Disable rollback | `N` |
| Save arguments to samconfig.toml | `Y` |

The output includes `ApiUrl`. Use that value as `VITE_API_URL` in the frontend.

---

## Deploy the authenticated backend

Use this before real users or real financial data.

```bash
cd infrastructure
sam build -t template.authenticated.yaml
sam deploy --guided -t template.authenticated.yaml
```

Suggested guided values:

| Prompt | Answer |
|---|---|
| Stack name | `smartfinly-prod` |
| AWS Region | `us-east-1` or your Bedrock-enabled region |
| Parameter BedrockModelId | keep default or use your available Bedrock model ID |
| Parameter BedrockRegion | `us-east-1` or your Bedrock region |
| Parameter AllowedOrigin | `https://www.smartfinly.com` |
| Confirm changes before deploy | `y` |
| Allow IAM role creation | `Y` |
| Disable rollback | `N` |
| Save arguments to samconfig.toml | `Y` |

Outputs:

```text
ApiUrl
UserPoolId
UserPoolClientId
Region
```

The frontend API client supports an optional Cognito access token:

```js
await analyze(profile, accessToken)
```

If no token is passed, the demo deployment still works. The authenticated deployment requires the frontend to pass `Authorization: Bearer <token>`.

---

## Configure and run the frontend locally

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Set `.env` for demo mode:

```env
VITE_API_URL=https://your-demo-lambda-url.lambda-url.us-east-1.on.aws/
```

Set `.env` for authenticated mode:

```env
VITE_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/analyze
VITE_AWS_REGION=us-east-1
VITE_USER_POOL_ID=your-user-pool-id
VITE_USER_POOL_CLIENT_ID=your-user-pool-client-id
```

Open:

```text
http://localhost:5173
```

---

## Frontend deployment

### Production path: AWS Amplify Hosting

This repo includes `amplify.yml` and `customHttp.yml` for Amplify hosting.

Recommended Amplify settings:

| Setting | Value |
|---|---|
| Repository | `harwansh/finplanner` |
| Branch | `main` |
| App root | `frontend` |
| Build command | `npm run build` |
| Output directory | `dist` |
| Canonical domain | `https://www.smartfinly.com/` |

Required environment variable:

```text
VITE_API_URL=<backend ApiUrl output>
```

Optional authenticated-mode variables:

```text
VITE_AWS_REGION=us-east-1
VITE_USER_POOL_ID=<Cognito User Pool ID>
VITE_USER_POOL_CLIENT_ID=<Cognito User Pool Client ID>
```

Manual Amplify redeploy:

```bash
aws amplify start-job \
  --app-id d30bhr0ymvaqw3 \
  --branch-name main \
  --job-type RELEASE \
  --region us-east-1
```

### Preview / backup path: S3 website bucket

A simple S3 website deployment can be used for preview or backup builds:

```bash
cd frontend
npm ci
npm run build
aws s3 sync dist s3://smartfinly-web-<account-id> --delete
```

The production domain should remain on Amplify unless intentionally migrated.

---

## Public routes

The frontend includes SPA routing and Amplify rewrite support for:

```text
/
/planner
/learn
/privacy
/terms
/disclaimer
/security
/financial-goal-planning-framework-india
/investment-decision-making-salary-earners
/salary-tax-planner-india
/sip-goal-planner
/insurance-gap-calculator
/sitemap.xml
/robots.txt
```

Legacy or earlier routes such as `/home`, `/ai-financial-planner-india`, and `/retirement-planner-india` are redirected or normalized to the framework-led route structure.

---

## Data flow

### Demo mode

1. User fills the framework planner form.
2. Frontend posts the structured profile to the Lambda Function URL.
3. Lambda validates and normalizes the payload.
4. Lambda computes finance summaries deterministically.
5. Lambda sends the sanitized planning context to Bedrock.
6. Lambda returns an educational framework report.

### Authenticated mode

1. User signs in with Cognito.
2. Frontend sends `Authorization: Bearer <accessToken>` with the request.
3. HTTP API validates the JWT.
4. Lambda receives the authenticated request.
5. Lambda validates, computes, invokes Bedrock, and returns the framework report.

---

## Security notes

Before collecting real user financial data:

- Use `template.authenticated.yaml`, not the unauthenticated demo Function URL.
- Confirm production logs do not include full financial payloads.
- Keep Privacy, Terms, Disclaimer, and Security pages visible.
- Add request throttling and/or WAF rules.
- Add app-level rate limits for Bedrock usage.
- Add unit tests for tax, cash-flow, goal projections, insurance gap, risk capacity, and sensitive-data rejection.
- Define data retention, deletion, and export policies.
- Use a customer-managed KMS key if storing personal financial data.

---

## Cost expectations

For light demo use:

- Lambda: usually low or free-tier covered
- Bedrock: depends on model and token volume
- Amplify hosting: usually low for low traffic
- HTTP API / Cognito: low for small usage

Bedrock is the main variable cost. Add rate limits before public launch.

---

## Customization

- Change the model: update `BedrockModelId` in the SAM template.
- Change framework assumptions: edit constants and logic in `backend/src/analyze/app.py`.
- Add charts: use a charting library in the frontend dashboard.
- Add persistence: introduce a profile table keyed by Cognito `sub`.
- Add PDF export: convert the framework report into a downloadable plan.
- Add research content: expand `/learn` and SEO pages around Indian salary-earner planning behaviors.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Amplify site shows old copy | Redeploy branch `main` and confirm the latest commit is deployed. |
| Direct `/planner` or `/privacy` route returns 404 | Confirm Amplify custom rules rewrite SPA routes to `/index.html`. |
| `smartfinly.com` apex returns 405 | Use `https://www.smartfinly.com/` as canonical, or configure apex forwarding/DNS correctly in GoDaddy. |
| `AccessDeniedException` calling Bedrock | Enable model access in Bedrock console and redeploy if needed. |
| `ValidationException: model not found` | Use a Bedrock model ID available in your selected region. |
| CORS error | Confirm `VITE_API_URL` and allowed origins in the SAM template. |
| 401/403 in authenticated mode | Sign in again and make sure the frontend sends the Cognito access token. |
| Missing API URL | Set `VITE_API_URL` in `frontend/.env` or Amplify environment variables. |
| Bedrock cost spike | Add API throttling, WAF, and app-level per-user limits. |

---

## Teardown

Demo stack:

```bash
cd infrastructure
sam delete --stack-name smartfinly-demo
```

Authenticated stack:

```bash
cd infrastructure
sam delete --stack-name smartfinly-prod
```

Also delete any Amplify apps, CloudFront distributions, S3 buckets, or IAM users you created for hosting/deployment.
