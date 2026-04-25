# Bad Gateway QA Checklist

This patch replaces `backend/src/analyze/app.py` with a clean compiled Lambda handler.

## Retest

1. `cd ../frontend && npm run build`
2. `cd ../infrastructure && sam build`
3. `sam deploy`
4. Open SmartFinly and submit a normal profile.
5. If you still see 502/Bad Gateway, check CloudWatch Lambda logs.
6. Confirm Lambda has Bedrock model permission if AI mode is enabled.
7. Backend intentionally does not emit Access-Control-Allow-Origin to avoid duplicate CORS.

## Expected
- Validation errors return HTTP 400 JSON.
- Server errors return HTTP 500 JSON, not Lambda import failure.
- Normal profiles return summary, plan, truthSheet and report.
