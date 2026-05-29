# SmartFinly — Educational Finance Chatbot Site

SmartFinly is an education-only finance chatbot site. The deployed frontend lives in `frontend/`, and the backend lives in `chatbot/backend/`.

The production target flow is now implemented in the backend:

```text
User question
→ guardrails
→ PDF/knowledge index retrieval first
→ if no strong match, AI fallback
→ education-only response with citations when grounded
```

## What is included

```text
frontend/                    # Amplify builds this live site
├── src/App.jsx              # Chatbot UI wired to VITE_CHAT_API_URL or VITE_API_URL
├── src/styles.css
└── index.html

chatbot/
├── backend/
│   ├── chat_handler.py      # Lambda handler: guardrails → retrieval → AI fallback
│   ├── retrieval.py         # Pure-Python TF-IDF retrieval over index.json
│   ├── ai_fallback.py       # Bedrock-ready fallback
│   ├── guardrails.py
│   ├── ingest.py            # Build index.json from PDFs
│   ├── requirements.txt
│   └── knowledge/index/index.json
├── infrastructure/
│   └── template.yaml        # SAM Lambda Function URL deployment
└── tests/
    └── test_chatbot.py
```

## Hard rules

1. Education only.
2. No buy, sell, timing, stock, fund, SIP, or product recommendations.
3. No guaranteed-return or price-prediction responses.
4. No PAN, Aadhaar, OTP, password, bank-detail, or sensitive-identifier collection.
5. Search the PDF/knowledge index first.
6. Use AI fallback only when retrieval does not find a strong match.

## Build the knowledge index from PDFs

Place PDF files here:

```text
knowledge/pdfs/
```

Then run:

```bash
cd chatbot/backend
python -m pip install -r requirements.txt
python ingest.py
```

This writes:

```text
chatbot/backend/knowledge/index/index.json
```

The repo currently includes a small bundled index so the backend works before you upload real PDFs. Replace it by running `ingest.py` with your PDF library.

## Run backend tests

```bash
cd chatbot
python -m pip install pytest
python -m pytest tests/ -q
```

## Deploy backend with SAM

```bash
cd chatbot/infrastructure
sam build -t template.yaml
sam deploy --guided -t template.yaml
```

For PDF-first retrieval only, keep:

```text
EnableBedrockFallback=false
```

For AI fallback with Bedrock, set:

```text
EnableBedrockFallback=true
BedrockModelId=amazon.nova-lite-v1:0
BedrockRegion=us-east-1
```

The output `ChatApiUrl` is the Lambda Function URL.

## Connect the frontend to the backend

In AWS Amplify environment variables, set one of these to the SAM output URL:

```text
VITE_CHAT_API_URL=https://your-lambda-url.lambda-url.us-east-1.on.aws/
```

or:

```text
VITE_API_URL=https://your-lambda-url.lambda-url.us-east-1.on.aws/
```

Then redeploy Amplify. The frontend already calls that API first and falls back locally only if the API is unavailable.

## API response shape

```json
{
  "blocked": false,
  "source": "pdf_knowledge_base",
  "answer": "...",
  "citations": [
    {
      "id": "emi-001",
      "title": "EMI and Income Capacity",
      "source": "SmartFinly Education Notes",
      "score": 0.42,
      "text": "..."
    }
  ]
}
```

When no knowledge-base match is found:

```json
{
  "blocked": false,
  "source": "ai_fallback",
  "answer": "...",
  "citations": []
}
```

## Legal and safety notice

SmartFinly is not a SEBI-registered investment adviser, research analyst, portfolio manager, insurance broker, tax filing service, lending platform, or product execution platform. It provides education-only explanations and does not provide personalized financial, tax, legal, insurance, or investment advice.
