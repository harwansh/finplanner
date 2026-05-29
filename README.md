# SmartFinly — Educational Finance Chatbot Site

SmartFinly is now a working education-only finance chatbot site. It includes a Vite/React frontend, reusable chat safety logic, a small demo knowledge base, a Python Lambda-style backend handler, guardrails, tests, and a SAM deployment template.

The current implementation is intentionally conservative: it explains finance concepts and blocks buy/sell/product-selection advice.

## What is included

```text
chatbot/
├── index.html
├── package.json
├── vite.config.js
├── .env.example
├── src/
│   ├── main.js
│   ├── App.js
│   ├── chat.js
│   ├── chat.test.js
│   └── styles.css
├── backend/
│   ├── chat_handler.py
│   ├── guardrails.py
│   └── requirements.txt
├── infrastructure/
│   └── template.yaml
└── tests/
    └── test_chatbot.py
```

## Hard rules

1. Education only.
2. No buy, sell, timing, stock, fund, SIP, or product recommendations.
3. No guaranteed-return or price-prediction responses.
4. No PAN, Aadhaar, OTP, password, bank-detail, or sensitive-identifier collection.
5. Unknown topics are handled as safe educational fallback prompts.

## Run the chatbot site locally

```bash
cd chatbot
npm install
npm run dev
```

Then open the local Vite URL shown in the terminal.

The frontend works without a backend. It uses the in-browser demo knowledge base in `src/chat.js`.

## Run frontend tests

```bash
cd chatbot
npm install
npm test
```

## Run backend tests

```bash
cd chatbot
python -m pytest tests/ -q
```

The backend has no runtime package dependencies for the demo handler.

## Backend API shape

`chatbot/backend/chat_handler.py` exposes a Lambda-compatible `handler(event, context)` and a pure `answer_question(message)` function.

Request body:

```json
{
  "message": "What is SIP?"
}
```

Response body:

```json
{
  "blocked": false,
  "source": "demo_knowledge_base",
  "answer": "...",
  "citations": []
}
```

## Deploy the backend with SAM

```bash
cd chatbot/infrastructure
sam build -t template.yaml
sam deploy --guided -t template.yaml
```

The output `ChatApiUrl` is the Lambda Function URL.

## Production next steps

- Wire the frontend to `VITE_CHAT_API_URL` for live backend calls.
- Replace the demo topic matcher with real retrieval over `knowledge/index/index.json`.
- Add Bedrock or another model only after retrieval and guardrails run first.
- Add rate limiting, authentication, structured logs, and narrower CORS before using real users.
- Keep the education-only disclaimer visible on every page.

## Legal and safety notice

SmartFinly is not a SEBI-registered investment adviser, research analyst, portfolio manager, insurance broker, tax filing service, lending platform, or product execution platform. It provides education-only explanations and does not provide personalized financial, tax, legal, insurance, or investment advice.
