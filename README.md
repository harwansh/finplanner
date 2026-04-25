# FinPlanner — AI Personal Finance Planner on AWS

A complete starter app you can deploy to your AWS account.

**What you get:**
- Sign up / sign in via **Cognito**
- Multi-step profile form covering all 11 categories from your spec
- Profile data stored in **DynamoDB**
- **Bedrock (Claude)** generates net worth, plus 5 must-have / 5 good-to-have / 5 optional financial goals tailored to the user
- React frontend hosted on **S3 + CloudFront** (or run locally)
- Deployed via **AWS SAM** — one command

---

## Architecture

```
React (S3+CloudFront)  ──►  API Gateway  ──►  Lambda (Python)
       │                         │                    │
       └── Cognito JWT ──────────┘                    ├─► DynamoDB (profiles)
                                                       └─► Bedrock (Claude Sonnet)
```

---

## 1. Prerequisites

Install once on your machine:

1. **AWS account** with admin or sufficient privileges (Cognito, IAM, Lambda, API Gateway, DynamoDB, Bedrock, S3, CloudFront).
2. **AWS CLI v2** — `aws --version` should show 2.x. Configure with `aws configure`.
3. **AWS SAM CLI** — install from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
4. **Python 3.12** (or 3.11)
5. **Node.js 20+** and npm
6. **Docker** (SAM uses it for builds; Docker Desktop is fine)

---

## 2. Enable Bedrock model access (one-time)

This is the step people most often miss.

1. Open AWS Console → **Bedrock** → **Model access** (left nav).
2. Click **Modify model access** and request access to **Anthropic Claude** models. Approval is usually instant.
3. Pick a region where the Claude model is enabled. Recommended: `us-east-1`.
4. The first time you invoke an Anthropic model, you may need to fill out a one-time **First Time Use (FTU)** form at AWS Console → Bedrock → first invocation prompt.

The default model id used in this project is `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. If your account doesn't have that one, edit the `BedrockModelId` parameter in `infrastructure/template.yaml` to whatever model id is shown for Anthropic Claude in your Bedrock console (Models → Anthropic).

---

## 3. Project layout

```
finplanner/
├── backend/
│   └── src/
│       ├── common/utils.py
│       ├── profile/app.py        # GET/PUT /profile
│       └── analyze/app.py        # POST /analyze (Bedrock)
├── frontend/                     # React + Vite
└── infrastructure/template.yaml  # SAM (Cognito, DynamoDB, Lambda, API GW)
```

---

## 4. Deploy the backend

```bash
cd infrastructure
sam build
sam deploy --guided
```

When prompted by `--guided`:

| Prompt | Answer |
|---|---|
| Stack name | `finplanner` |
| AWS Region | `us-east-1` (or your choice with Bedrock enabled) |
| Parameter AppName | `finplanner` |
| Parameter BedrockModelId | (keep default or your chosen model id) |
| Parameter BedrockRegion | `us-east-1` |
| Confirm changes before deploy | `y` |
| Allow IAM role creation | `Y` |
| Disable rollback | `N` |
| Save arguments to samconfig.toml | `Y` |

After deploy completes, you'll see **Outputs**:

```
ApiUrl              https://abcd1234.execute-api.us-east-1.amazonaws.com/prod
UserPoolId          us-east-1_AbCdEfGhI
UserPoolClientId    1a2b3c4d5e6f7g8h9i0j
Region              us-east-1
```

Copy these. You'll paste them into the frontend in the next step.

For future deploys, just run `sam build && sam deploy` (no `--guided`).

---

## 5. Configure & run the frontend

```bash
cd ../frontend
cp .env.example .env
# Edit .env and fill in the four values from the SAM outputs above
npm install
npm run dev
```

Open `http://localhost:5173`.

Test the full flow locally:

1. Click **Sign in** → switch to **Sign up** → register an email.
2. Cognito emails you a 6-digit code → enter it on the confirm screen.
3. You're auto-logged in and routed to **Onboarding**.
4. Fill the 9 steps, hit **Save & analyze**.
5. Dashboard shows your computed net worth + the 15 AI-generated goals.

---

## 6. Deploy the frontend to AWS

Two easy options.

### Option A: AWS Amplify Hosting (simplest)

1. Push your code to GitHub.
2. AWS Console → **Amplify** → **Host a web app** → connect your repo.
3. Build settings: monorepo. App root = `frontend`. Build command `npm run build`, output directory `dist`.
4. Add environment variables (`VITE_AWS_REGION`, `VITE_USER_POOL_ID`, `VITE_USER_POOL_CLIENT_ID`, `VITE_API_URL`) from SAM outputs.
5. Deploy. Amplify gives you a URL like `https://main.d1234.amplifyapp.com`.

### Option B: S3 + CloudFront (manual)

```bash
cd frontend
npm run build
aws s3 mb s3://finplanner-web-<your-unique-suffix>
aws s3 sync dist s3://finplanner-web-<your-unique-suffix>
# then create a CloudFront distribution pointing at the bucket
```

After hosting, update CORS if needed by tightening `AllowOrigin` in `template.yaml` from `'*'` to your real domain and redeploying.

---

## 7. How it works (data flow)

1. User signs up → Cognito creates a user, emails confirmation code, returns JWT on sign in.
2. Frontend attaches the JWT in the `Authorization` header on every API call.
3. API Gateway's Cognito authorizer validates the JWT and injects `claims.sub` (the user id) into the Lambda event.
4. **`profile` Lambda** uses `sub` as the DynamoDB partition key → each user only ever sees their own data.
5. **`analyze` Lambda**:
   - Reads the user's profile from DynamoDB.
   - Computes net worth, surplus, savings rate, emergency-fund months **deterministically in Python** (no AI hallucinations on math).
   - Sends the profile + summary to Bedrock with a strict system prompt asking for exactly 15 goals in JSON.
   - Returns `{summary, goals}`.

---

## 8. Cost expectations

For a single user testing:
- DynamoDB on-demand: ~$0
- Lambda + API Gateway: ~$0 (free tier covers it)
- Cognito: free up to 50,000 MAUs
- **Bedrock**: this is the main variable. Each `/analyze` call sends ~1–2k input tokens and gets ~2–3k output tokens. At Sonnet 4.5 rates that's roughly $0.01–$0.04 per analysis.
- S3 + CloudFront: pennies/month for low traffic.

---

## 9. Customization & next steps

- **Swap the model:** edit `BedrockModelId` in `template.yaml` (e.g. to Haiku for cheaper, Opus 4.7 for highest quality) and redeploy.
- **Add more goals:** change the count and bucket names in the `SYSTEM_PROMPT` inside `backend/src/analyze/app.py`.
- **Lock down CORS:** in `template.yaml`, change `AllowOrigin: "'*'"` to your real domain.
- **Encrypt at rest:** DynamoDB uses AWS-owned keys by default. For PII like financial data in production, switch to a customer-managed KMS key.
- **Add email alerts** on big plan changes via SNS + EventBridge.
- **Charts:** the dashboard is plain numbers — drop in Recharts to visualize asset allocation and goal progress.

---

## 10. Tearing it down

When you're done testing and don't want to be charged:

```bash
cd infrastructure
sam delete --stack-name finplanner
```

Then in the Amplify console, delete the app (if you used Option A), or empty + delete the S3 bucket (Option B).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `AccessDeniedException` calling Bedrock | Enable model access in Bedrock console (step 2). Wait 1–2 min. |
| `ValidationException: model not found` | The model ID isn't in your region. Pick the model id shown in your Bedrock console. |
| Confirmation email never arrives | Check spam. Cognito's free tier sends from a generic AWS sender; for production, wire it to SES. |
| CORS error in browser | Make sure `VITE_API_URL` matches the deployed `ApiUrl` exactly, including `/prod`. |
| `model returned non-JSON` in /analyze response | Lower `temperature` further (already 0.2) or shorten the system prompt. Larger / smarter models are more reliable here. |

---

That's it. Code is intentionally minimal and documented — easy to read, easy to extend.
