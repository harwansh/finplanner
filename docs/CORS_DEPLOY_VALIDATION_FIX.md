# CORS Deploy Validation Fix

## Problem

CloudFormation EarlyValidation failed because `OPTIONS` was added under Lambda Function URL `Cors.AllowMethods`.

For Lambda Function URLs, `OPTIONS` is not a valid configured `AllowMethods` value. Lambda handles browser preflight automatically from the CORS config.

Valid Lambda Function URL CORS methods are:

- `GET`
- `PUT`
- `HEAD`
- `POST`
- `PATCH`
- `DELETE`
- `*`

## Fix

`infrastructure/template.yaml` now uses:

```yaml
AllowMethods:
  - POST
```

Do not add `OPTIONS` there.

## Retest

```bash
sam validate
sam build
sam deploy
```

Then test preflight:

```bash
curl -i -X OPTIONS https://gsekzmc5h6vadln6vxx2mwvst40ihoxy.lambda-url.us-east-1.on.aws/ \
  -H "Origin: https://www.smartfinly.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```
