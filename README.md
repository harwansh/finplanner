# SmartFinly / FinPlanner — AI Personal Finance Planner on AWS

SmartFinly is an AI-assisted personal finance planning app for Indian users. It collects structured inputs across profile, salary, tax, liabilities, insurance, investments, goals, and cash flow, then generates an educational financial plan using deterministic Python calculations plus Amazon Bedrock.

> **Current status:** this repository is an MVP/demo build. The default `infrastructure/template.yaml` deploys a simple analysis Lambda URL for demos. For production or real user financial data, use `infrastructure/template.authenticated.yaml`, which adds Cognito authentication, an HTTP API JWT authorizer, and throttling.

---

## What you get

- React + Vite frontend
- Multi-step finance form for Indian salaried/family planning use cases
- Salary, tax, cash-flow, liabilities, insurance, investment, and goal inputs
- Backend validation and sensitive-data rejection for PAN, Aadhaar, OTP, bank/account identifiers, UPI, passwords, tokens, and similar values
- Deterministic backend finance calculations before AI generation
- Amazon Bedrock-powered educational planning output
- Demo deployment template for quick testing
- Authenticated production-ready SAM template scaffold

---

## Important legal and safety notice

SmartFinly is an educational AI financial planning sample. It is **not** a SEBI-registered investment adviser, research analyst, portfolio manager, insurance broker, tax filing service, lending platform, or product execution platform.

Do **not** enter PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs, brokerage credentials, or other sensitive identifiers.

Do **not** use the unauthenticated demo deployment for real user financial data.

---

## Architecture options

### Demo / MVP deployment

The default template is optimized for fast testing:

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
- `Authorization: Bearer <token>` support
- API throttling
- CORS for SmartFinly and localhost development origins

---

## Project layout

```text
finplanner/
├── backend/
│   └── src/
│       └── analyze/
│           └── app.py                 # POST analyze endpoint, validation, calculations, Bedrock call
├── frontend/
│   ├── src/
│   │   ├── api/client.js              # API client, optional bearer-token support
│   │   ├── pages/Home.jsx             # Main planner UI
│   │   └── App.jsx
│   └── package.json
└── infrastructure/
    ├── template.yaml                  # Demo Lambda Function URL deployment
    └── template.authenticated.yaml    # Authenticated Cognito + HTTP API deployment scaffold
```

---

## Prerequisites

Install once:

1. AWS account with permissions for Lambda, IAM, Bedrock, and optionally Cognito/API Gateway.
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

The output includes `ApiUrl`. Use that as `VITE_API_URL` in the frontend.

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

The frontend API client already supports an optional Cognito access token:

```js
await analyze(profile, accessToken)
```

If no token is passed, the demo deployment still works. The authenticated deployment requires the frontend to pass `Authorization: Bearer <token>`.

---

## Configure and run the frontend

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

### Option A: AWS Amplify Hosting

1. Push this repo to GitHub.
2. AWS Console → Amplify → Host web app.
3. Choose the repo.
4. Set app root to `frontend`.
5. Build command: `npm run build`.
6. Output directory: `dist`.
7. Add the environment variables from the backend deployment outputs.
8. Deploy.

### Option B: S3 + CloudFront

```bash
cd frontend
npm run build
aws s3 mb s3://smartfinly-web-<your-unique-suffix>
aws s3 sync dist s3://smartfinly-web-<your-unique-suffix>
```

Then create a CloudFront distribution pointing at the bucket.

---

## Data flow

### Demo mode

1. User fills the planner form.
2. Frontend posts the structured profile to the Lambda Function URL.
3. Lambda validates and normalizes the payload.
4. Lambda computes finance summaries deterministically.
5. Lambda sends the sanitized planning context to Bedrock.
6. Lambda returns the educational plan.

### Authenticated mode

1. User signs in with Cognito.
2. Frontend sends `Authorization: Bearer <accessToken>` with the request.
3. HTTP API validates the JWT.
4. Lambda receives the authenticated request.
5. Lambda validates, computes, invokes Bedrock, and returns the plan.

---

## Security notes

Before production launch:

- Use `template.authenticated.yaml`, not the unauthenticated demo Function URL.
- Remove any production logs that include full financial payloads.
- Add a Privacy Policy, Terms, Disclaimer, and Security page.
- Add request throttling and/or WAF rules.
- Add app-level rate limits for Bedrock usage.
- Add unit tests for tax, cash-flow, goal projections, insurance gap, and sensitive-data rejection.
- Define data retention and deletion policies.
- Use a customer-managed KMS key if storing personal financial data.

---

## Cost expectations

For light demo use:

- Lambda: usually low or free-tier covered
- Bedrock: depends on model and token volume
- HTTP API / Cognito: low for small usage
- S3 + CloudFront or Amplify: usually low for low traffic

Bedrock is the main variable cost. Add rate limits before public launch.

---

## Customization

- Change the model: update `BedrockModelId` in the SAM template.
- Change assumptions: edit constants in `backend/src/analyze/app.py`.
- Add charts: use a charting library in the frontend dashboard.
- Add persistence: introduce a profile table keyed by Cognito `sub`.
- Add exports: generate PDF reports from the final educational plan.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `AccessDeniedException` calling Bedrock | Enable model access in Bedrock console and redeploy if needed. |
| `ValidationException: model not found` | Use a Bedrock model ID available in your selected region. |
| CORS error | Confirm `VITE_API_URL` and allowed origins in the SAM template. |
| 401/403 in authenticated mode | Sign in again and make sure the frontend sends the Cognito access token. |
| Missing API URL | Set `VITE_API_URL` in `frontend/.env` or hosting environment variables. |
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

Also delete any Amplify apps, CloudFront distributions, or S3 buckets you created for frontend hosting.
