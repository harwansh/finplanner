# SmartFinly Production Deployment

This repo now contains two frontend deployment paths:

1. **AWS Amplify Hosting** using `amplify.yml`
2. **S3 + CloudFront** using `.github/workflows/deploy-frontend.yml`

The upgraded SmartFinly product homepage is in `frontend/src/App.jsx` and `frontend/src/trust.css`.

---

## Option A: AWS Amplify Hosting

Use this if the domain is already managed through Amplify or you want the simplest deployment.

### Steps

1. Open AWS Amplify Console.
2. Connect this GitHub repo: `harwansh/finplanner`.
3. Choose branch: `main`.
4. Amplify should detect `amplify.yml`.
5. Confirm app root is `frontend`.
6. Add environment variables:

```text
VITE_API_URL=<backend API URL>
VITE_AWS_REGION=us-east-1
VITE_USER_POOL_ID=<optional Cognito User Pool ID>
VITE_USER_POOL_CLIENT_ID=<optional Cognito User Pool Client ID>
```

For demo mode, only `VITE_API_URL` is required.

7. Deploy.
8. In Amplify domain settings, connect:

```text
www.smartfinly.com
smartfinly.com
```

9. Set the canonical production domain to:

```text
https://www.smartfinly.com/
```

---

## Option B: S3 + CloudFront via GitHub Actions

Use this if the frontend is hosted by S3 and CloudFront.

### Required GitHub Actions secrets

Add these repository secrets in GitHub:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
SMARTFINLY_S3_BUCKET
CLOUDFRONT_DISTRIBUTION_ID
VITE_API_URL
VITE_AWS_REGION
VITE_USER_POOL_ID
VITE_USER_POOL_CLIENT_ID
```

For demo mode, Cognito values may be blank if the frontend does not require login yet.

### IAM permissions for deploy user

The deploy user needs permissions for:

```text
s3:ListBucket
s3:PutObject
s3:DeleteObject
s3:GetObject
cloudfront:CreateInvalidation
```

Restrict S3 permissions to the production frontend bucket.

### Deploy

The workflow deploys automatically when frontend files change on `main`.

You can also run it manually from:

```text
GitHub → Actions → Deploy SmartFinly Frontend → Run workflow
```

---

## Domain checklist

For a 9/10 public site, make sure these are true:

- `https://www.smartfinly.com/` serves the upgraded React app.
- `https://smartfinly.com/` redirects to `https://www.smartfinly.com/`.
- Old `/home/` pages redirect to the new homepage or become `/learn`.
- CloudFront or Amplify serves `index.html` with no-cache headers.
- Static assets are served with long-cache immutable headers.
- The root page title is `SmartFinly — AI Financial Planner for Salaried India`.
- The homepage hero says: `One financial plan for your salary, tax, SIPs, insurance and goals.`

---

## Post-deploy verification

After deployment, check:

```bash
curl -I https://www.smartfinly.com/
curl -I https://smartfinly.com/
```

Then open the site and verify:

- Premium SmartFinly hero appears.
- `Start free planner` scrolls to the planner.
- Trust/privacy sections appear above and below the planner.
- No production console log prints `SmartFinly FINAL submit payload`.
- The planner can call the configured `VITE_API_URL`.
