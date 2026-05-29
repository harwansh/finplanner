# SmartFinly — Educational Finance Chatbot (Makeover)

This converts the SmartFinly planner site into a **conversational educational assistant**.
It answers from a curated PDF library first, then falls back to AI only when the
library has no good match.

## Hard rules (enforced in code, tested)

1. **Knowledge-base first.** Every question is matched against the PDF library
   (`knowledge/pdfs/`, indexed into `knowledge/index/index.json`). If a relevant
   passage is found, the answer is grounded in it. AI is used only to rephrase
   the retrieved passages into clean prose — it does not invent facts.
2. **AI fallback second.** If the library has no usable match, Bedrock answers
   the concept generically (still education-only, still brand-free).
3. **No brand names — ever.** All source PDFs were re-ingested with brand names,
   coaching-institute names, certification marks, and promotional watermark URLs
   stripped (`sanitize.py`). Every outgoing answer is scrubbed again before send.
4. **No buy / sell / product guidance — ever.** Requests for "should I buy/sell",
   "which fund/stock", price predictions, etc. are intercepted and redirected to a
   concept explanation plus a pointer to a SEBI-registered adviser. Outgoing answers
   are also checked for advice phrasing as a safety net.

## Layout

```
chatbot/
├── backend/
│   ├── sanitize.py        # brand / mark / watermark stripping (single source of truth)
│   ├── ingest.py          # PDF -> sanitized text -> chunks -> index.json + clean PDFs
│   ├── retrieval.py       # pure-Python TF-IDF cosine retrieval (no ML wheels)
│   ├── guardrails.py      # advice detection + answer scrubbing
│   ├── chat_handler.py    # Lambda: KB-first -> AI fallback -> scrub
│   └── knowledge/index/index.json   # bundled for packaging
├── frontend/
│   └── SmartFinlyChat.jsx # premium black/gold chat UI (React)
├── infrastructure/
│   └── template.yaml      # SAM: Function URL + scoped Bedrock permission
└── tests/
    └── test_chatbot.py    # 14 tests: stripping, guardrails, routing, scrubbing

knowledge/
├── pdfs/                  # 13 brand-free educational PDFs (one folder, as requested)
└── index/index.json       # search index
```

## Rebuild the knowledge base

```
cd chatbot/backend
pip install pypdf reportlab --break-system-packages
python ingest.py            # rewrites knowledge/pdfs/ and knowledge/index/index.json
cp ../../knowledge/index/index.json knowledge/index/index.json
```

## Run tests

```
cd chatbot
INDEX_PATH=$PWD/../knowledge/index/index.json python -m pytest tests/ -q
```

## Deploy

```
cd chatbot/infrastructure
sam build -t template.yaml
sam deploy --guided -t template.yaml
```

Then expose the Function URL to the site, e.g. in `index.html`:

```html
<script>window.SMARTFINLY_CHAT_API = "https://<id>.lambda-url.us-east-1.on.aws/";</script>
```

The frontend works without a backend too: with no API configured it serves a small
in-browser demo KB so the UI is fully interactive in preview.

## Notes / honest limitations

- The stored PDFs in `knowledge/pdfs/` are **rebuilt from sanitized text**, not the
  originals — the originals carry brand watermarks that must not be redistributed.
  Visual fidelity (images, tables) is lost; the educational text is preserved.
- Retrieval is keyword TF-IDF, chosen so the Lambda needs no heavy ML dependencies.
  It's solid for concept lookup; for higher recall, swap in embeddings + a vector DB.
- Bedrock IAM is scoped to the chosen model ARN, not `"*"`.
