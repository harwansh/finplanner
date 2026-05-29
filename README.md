# SmartFinly / finplanner

SmartFinly is an education-only finance planning and learning app for Indian users. The existing planner flow remains under the existing `/analyze` Lambda, and the finance education chatbot is implemented as a separate `/chat` Lambda.

## Chatbot

The chatbot is a RAG-style finance education assistant that fits the existing architecture:

```text
frontend/                    React + Vite frontend
backend/src/chat/app.py       Python AWS Lambda chatbot backend
backend/scripts/ingest.py     One-time PDF ingestion script
backend/src/chat/kb/          Local committed chatbot knowledge artifacts
infrastructure/template.yaml  SAM template with AnalyzeFunction and ChatFunction
```

### Flow

```text
User message
→ sensitive-data rejection
→ embed query with Amazon Titan Embeddings
→ search local FAISS knowledge base
→ if similarity >= threshold: answer from study-material context using Nova Pro
→ otherwise: answer with Bedrock general finance education knowledge
```

The chatbot is education-only. It is not a SEBI-registered investment adviser and must not provide personalized buy/sell advice, guaranteed returns, or product recommendations.

### Knowledge base ingestion

The source PDFs are the CFP study PDFs already committed at the repo root, including retirement planning, estate lectures, risk lectures, IPS/PMF, regulatory, IPAM, Indian markets, and tax planning.

Install local ingestion dependencies:

```bash
python -m pip install boto3 numpy pypdf faiss-cpu
```

Build the FAISS index and metadata:

```bash
python backend/scripts/ingest.py --force
```

The script writes:

```text
backend/src/chat/kb/index.faiss
backend/src/chat/kb/chunks.json
```

The script is idempotent. If both files already exist, it skips re-embedding unless `--force` is supplied.

### Backend environment variables

The SAM template exposes these configurable values:

```text
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_REGION=us-east-1
CHAT_TOP_K=4
CHAT_SIMILARITY_THRESHOLD=0.35
```

### Deploy

```bash
cd infrastructure
sam build -t template.yaml
sam deploy --guided -t template.yaml
```

The existing planner output remains:

```text
ApiUrl
```

The new chatbot output is:

```text
ChatApiUrl
```

### Frontend environment variables

Set these in Amplify / local `.env`:

```text
VITE_API_URL=<AnalyzeFunctionUrl>
VITE_CHAT_API_URL=<ChatFunctionUrl>
```

`VITE_API_URL` is for the existing planner flow. `VITE_CHAT_API_URL` is for the new education chatbot page.

### Frontend route

The chatbot page is available at:

```text
/learn-chat
```

It renders markdown answers, a subtle source badge, references when the answer is grounded in study material, keyboard submit, loading state, and auto-scroll.

### Demo privacy note

The demo Function URL is unauthenticated. Do not enter real PAN, Aadhaar, OTP, UPI, bank/account numbers, passwords, or other sensitive personal identifiers.
