# SmartFinly Security and Compliance Hardening

## Security posture

SmartFinly is positioned as an educational / sampling financial planner. The application must not collect high-risk identifiers or regulated credentials.

### Do not collect

- PAN
- Aadhaar
- OTPs
- Passwords
- Bank account numbers
- IFSC / UPI IDs
- Access tokens
- Uploaded financial documents until a full privacy and storage design exists

## Server-side controls added

- Maximum request body size: 64 KB by default.
- Rejects sensitive identifiers by key name and common PAN/Aadhaar/OTP patterns.
- Rejects negative numeric inputs.
- Rejects unrealistically large numeric values.
- Caps row counts:
  - 50 goals
  - 100 investment rows
  - 10 children
- Adds security response headers:
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `Referrer-Policy`
  - `Cache-Control`
  - `Permissions-Policy`
  - API CSP
  - `X-Robots-Tag`

## CORS note

The backend does **not** add `Access-Control-Allow-Origin` by default. This avoids the previous production bug where both Lambda Function URL and application code returned CORS headers.

Only enable application-owned CORS if Function URL / CloudFront CORS is disabled:

```bash
APP_OWNS_CORS=true
ALLOWED_ORIGINS=https://www.smartfinly.com,https://smartfinly.com
```

## Frontend controls added

- Form disables browser autocomplete.
- Client-side sensitive-data warning blocks PAN/Aadhaar/OTP/bank-style data before API call.
- Client-side row count caps mirror backend caps.

## Compliance positioning

SmartFinly copy should remain:

> Educational / sampling planner only. Not SEBI-registered investment advice. No guaranteed returns. No product execution. Verify with qualified professionals before acting.

Avoid:

- “Guaranteed”
- “Assured returns”
- “Buy this fund/stock”
- “SEBI approved”
- “RBI approved”
- “We manage your money”
- “Personalized registered advice”

## Security regression tests

1. Submit normal profile: should work.
2. Submit PAN-like string `ABCDE1234F` in any text field: should be blocked.
3. Submit Aadhaar-like string `2345 6789 1234`: should be blocked.
4. Submit field named `bankAccount`: should be blocked.
5. Submit negative salary/expense: should be blocked.
6. Add >100 investment rows: should be blocked.
7. Add >50 goals: should be blocked.
8. Add >10 children: should be blocked.
9. Send invalid JSON: should return 400.
10. Send body >64 KB: should return 400.
11. Verify production response does not duplicate `Access-Control-Allow-Origin`.
12. Verify browser console has no CSP/CORS/mixed content errors.
