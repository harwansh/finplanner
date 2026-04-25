# Frontend Build Pipeline Verify

## Fixed

Removed duplicate `annualGross: ''` from the investor demo profile. It was overwriting the earlier demo value.

## Required verification

From frontend folder:

```bash
npm run build
grep -R "Duplicate key" dist/assets/*.js
grep -R "ps(data).replace\|buildSmartFinlyPayload(data).replace" dist/assets/*.js
grep -R "SmartFinly FINAL submit payload" dist/assets/*.js
```

Expected:

- Duplicate key warning should be gone.
- Bad parser grep should return no output.
- Final payload grep should show one result.

## Production note

`npm run build` only creates `frontend/dist`. It does not automatically update the live SmartFinly frontend unless Amplify/hosting redeploys from GitHub, or you upload `dist` to the hosting bucket/CDN.
