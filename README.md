# Achievement Education & Visa Services — Demo AI Chatbot

A conversational AI student-assistant chatbot for qualification and lead generation. Built for a pitch demo — all data is dummy and can be swapped without touching application logic.

## Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI (Python 3.12) |
| LLM | Groq API via `langchain-groq` (Llama 3.3 70B) |
| Database | PostgreSQL (Neon) via SQLAlchemy |
| Session state | In-memory Python dict (no persistence across restarts) |

## Project Structure

```
achievement-demo-bot/
├── main.py                          # FastAPI app entry point
├── requirements.txt                 # Python dependencies
├── .env                             # Secrets (not committed)
├── app/
│   ├── config.py                    # Loads env vars
│   ├── database.py                  # SQLAlchemy engine + session
│   ├── models.py                    # Lead ORM model
│   ├── schemas.py                   # Pydantic request/response models
│   ├── routes/
│   │   ├── chat.py                  # POST /chat
│   │   └── lead.py                  # POST /lead, GET /leads
│   ├── services/
│   │   ├── agent.py                 # LangChain Groq conversational agent
│   │   ├── session_store.py         # In-memory session dict
│   │   ├── escalation.py            # Pre-LLM escalation phrase detection
│   │   └── provider_matcher.py      # Filter providers by student preferences
│   └── data/
│       ├── providers.json           # 8 dummy IT course entries
│       ├── escalation_phrases.json  # 13 trigger phrases for escalation
│       └── faq.json                 # 10 Q&A pairs
```

## Setup

### 1. Clone and install

```bash
git clone <repo-url> && cd achievement-demo-bot

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create `.env`

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://user:password@ep-xxxx.us-east-2.aws.neon.tech/dbname?sslmode=require
```

> Get a free Groq API key at [console.groq.com](https://console.groq.com).
> Get a free Postgres database at [neon.tech](https://neon.tech).

### 3. Apply database migrations

```bash
alembic upgrade head
alembic current
alembic history
```

Alembic reads `DATABASE_URL` from the same environment / `.env` as the backend.
Revision `20261003_01` creates the legacy `leads` table on an empty database or
adopts the existing table. Revision `20261003_02` adds nullable `budget` and
`intake` string columns only when missing, preserving `budget_intake` and all
existing data. Already-applied manual columns are validated and adopted; do not
manually stamp or run the former raw SQL script.

These adoption revisions require an online connection (no `--sql`). Automatic
downgrade is deliberately blocked because it could delete data that predates
Alembic; any rollback requires a reviewed data-preserving migration. Application
startup behavior is unchanged, but run migrations before starting each release.

### 4. Run the server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## How It Works

```
User sends message
        │
        ▼
  ┌─────────────┐
  │ /chat POST  │
  └──────┬──────┘
         │
         ▼
  ┌──────────────────┐     yes     ┌─────────────────────┐
  │ Escalation check ├────────────►│ Fixed reply + continue│
  │ (pre-LLM)        │            │ collecting lead info  │
  └──────┬───────────┘            └─────────────────────┘
         │ no
         ▼
  ┌──────────────────┐
  │ LangChain Agent  │◄── session history + provider matches + FAQ
  │ (Groq / Llama)   │
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ ChatResponse     │  reply + collected_fields + lead_ready
  └──────────────────┘
         │
    lead_ready == true?
         │
    yes  │  no → wait for next message
         ▼
  ┌──────────────────┐
  │ /lead POST       │  save to Postgres
  └──────────────────┘
```

**Qualification flow:** The agent converses naturally to collect 6 qualification fields + 3 contact fields. It never asks like a form — one question at a time, acknowledging what the student shares.

**Provider matching:** Once `course_interest`, `preferred_location`, and `english_test_status` are collected, matching providers are injected into the LLM prompt as context for personalised recommendations.

**Lead status inference:**
- `HIGH_INTENT` — IELTS score provided + clear intake timing
- `MEDIUM_INTENT` — one of the above present
- `LOW_INTENT` — neither present yet

## API Reference

### `POST /chat`

Send a message and get a conversational reply.

**Request:**
```json
{
  "session_id": "sess-abc-123",
  "message": "I want to study cybersecurity in Brisbane"
}
```

**Response:**
```json
{
  "reply": "Great choice! Brisbane has some excellent cybersecurity programs...",
  "collected_fields": {
    "course_interest": "cybersecurity",
    "preferred_location": "Brisbane",
    "current_education": "Bachelor of Computer Science",
    "english_test_status": "IELTS 6.5",
    "budget_intake": null,
    "budget_intake": null,
    "current_country_status": null,
    "name": null,
    "email": null,
    "phone_whatsapp": null
  },
  "lead_ready": false
}
```

| Field | Description |
|---|---|
| `session_id` | Client-generated unique session identifier |
| `message` | The user's message |
| `reply` | The AI assistant's response |
| `collected_fields` | Fields collected so far (null = not yet asked) |
| `lead_ready` | `true` when all fields are collected and student shows interest |

### `POST /lead`

Save a qualified lead to the database. Only call this when `lead_ready` is `true`.

**Request:**
```json
{
  "session_id": "sess-abc-123",
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "phone_whatsapp": "+91-9876543210",
  "course_interest": "Master of Cybersecurity",
  "preferred_location": "Brisbane",
  "current_education": "Bachelor of Computer Science",
  "english_test_status": "IELTS 6.5 overall",
  "budget_intake": "AUD 35k/year, starting July 2026",
  "current_country_status": "Currently in India, student visa",
  "lead_status": "HIGH_INTENT"
}
```

**Response:** Returns the created lead with `id` and `created_at` timestamp.

### `GET /leads`

List all captured leads (for demo review).

**Response:** Array of lead objects, ordered by most recent first.

### `GET /health`

Health check endpoint.

**Response:** `{ "status": "ok" }`

## Escalation

Certain phrases trigger an automatic escalation response before the LLM is called. These include "visa refused", "complex case", "onshore application", etc. When triggered:

- The user gets a fixed response noting a consultant will follow up
- Lead info collection continues as normal
- The conversation remains in session history for context

Trigger phrases are defined in `app/data/escalation_phrases.json`.

## Customising Data

All domain-specific data lives in `app/data/`:

| File | What it controls |
|---|---|
| `providers.json` | Course/institution data for provider matching |
| `escalation_phrases.json` | Trigger phrases for consultant escalation |
| `faq.json` | FAQ knowledge base the agent references |

To swap in real data, replace the JSON files — no code changes needed.

## Notes

- This is a **demo** — lead review requires a backend admin token; rate limiting is not implemented.
- Session state is **in-memory** — lost on server restart
- `GET /leads` requires `Authorization: Bearer <LEADS_ADMIN_TOKEN>`; missing configuration fails closed.
- The LLM is called on every `/chat` request — watch your Groq usage during demos

## Pre-deployment configuration and verification

Backend `.env` (never copy the admin token into the frontend):

```env
LEADS_ADMIN_TOKEN=<random secret generated with secrets.token_urlsafe(32)>
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Add the exact Vercel HTTPS origin to `ALLOWED_ORIGINS` when deploying; wildcards
are rejected. CORS governs browser access, not API authentication. Review leads
using a trusted API client with the bearer token over HTTPS outside localhost.
Keep `GROQ_API_KEY` and `DATABASE_URL` on the backend. The frontend only needs
`NEXT_PUBLIC_API_URL` pointing to the backend (HTTPS in production).

Lead requests trim and validate required fields, email, phone, lengths, and the
status enum. The server computes the stored status from completed English-test
evidence and intake timing; budget alone does not count as timing. The existing
`lead_status` request field remains accepted for compatibility.

Chat extracts current-message fields before matching. Factual replies are
rendered directly from supplied FAQ/provider records selected by a second model
pass; generated draft prose never reaches the student. Invalid references fail
closed, and missing information gets an information-gap response. Reference
selection is model-based, so relevance and the demo data itself still need
domain review before real admissions use. There are now three model
calls per normal turn, each with a 15-second network timeout and no SDK retry.
AI failures return HTTP 503 with `detail.code=AI_UNAVAILABLE` and
`detail.retryable=true`, without internal error details. Frontend requests abort
after 60 seconds and use the existing error/Retry UI.

Verification commands:

```text
python -m pytest -p no:cacheprovider -q
cd frontend
npm run lint
node --test lib/api.test.mjs components/chat/MessageBubble.test.mjs
npm run build
```

The tests use an isolated in-memory database and a test-only admin token.
Markdown rendering uses a restricted element allowlist, ignores raw HTML,
blocks images and unsafe link schemes, and wraps long words and tables.
