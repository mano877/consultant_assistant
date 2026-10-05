# Education Consultancy AI Assistant Demo

A full-stack AI-powered student enquiry and lead qualification demo for education consultancies, using an Australian study consultancy scenario. It combines a responsive consultancy website with a conversational assistant that helps visitors explore demo course information and request a consultation.

**GlobalPath Consulting is the fictional brand used in the demo UI.** This project is not built for, affiliated with, or endorsed by a specific real consultancy.

## Key features

- AI student enquiry assistant with session-based conversation context.
- Grounded responses rendered from the supplied FAQ and provider dataset, with a fallback when information is unavailable.
- Course/provider guidance based on study interests, location, and available English-test information.
- Student qualification flow covering education, course preferences, English tests, location, budget, intake, and contact details.
- Consultation form and persistent lead capture linked to the chat session.
- Separate budget and intake extraction, including common month/year and relative intake expressions.
- Server-calculated `LOW_INTENT`, `MEDIUM_INTENT`, and `HIGH_INTENT` lead status.
- Protected admin lead-list endpoint using a backend bearer token.
- Responsive consultancy website with Sydney, Melbourne, Brisbane, and Adelaide destination sections.
- Restricted Markdown rendering, request timeouts, and a Retry flow for chat failures.

## Tech stack

| Area | Current implementation |
| --- | --- |
| Frontend | Next.js 16 App Router, React 19, JavaScript/JSX |
| Styling and images | Custom CSS, Tailwind CSS 4/PostCSS, Next.js Image |
| Chat formatting | `react-markdown` and `remark-gfm` |
| Backend | Python 3.12+, FastAPI, Uvicorn, Pydantic 2, `email-validator` |
| LLM integration | Groq through LangChain and `langchain-groq`; currently configured for `openai/gpt-oss-120b` |
| Persistence | PostgreSQL, using Neon for the demo database; SQLAlchemy 2 and `psycopg2-binary` |
| Migrations | Alembic |
| Configuration | Environment variables and `python-dotenv` |
| Verification | pytest, FastAPI TestClient/HTTPX, Node.js built-in test runner, ESLint |
| Dependency management | `pyproject.toml` / `uv.lock`, `requirements.txt`, npm / `package-lock.json` |

## How it works

1. The frontend generates a session ID automatically and reuses it for the conversation and lead submission. Students never enter it manually.
2. The backend extracts student details before matching records from the demo provider dataset.
3. The LLM selects relevant references; factual response content is rendered from those records rather than unrestricted generated prose. Reference selection is still model-based and can be imperfect.
4. The conversation gathers qualification details and offers a consultation form. The form can also be opened through the website's adviser buttons.
5. Submitted leads are stored in PostgreSQL. The backend calculates their status from completed English-test evidence and intake timing: both signals produce `HIGH_INTENT`, one produces `MEDIUM_INTENT`, and neither produces `LOW_INTENT`. A budget amount alone is not intake timing.

Budget and intake are stored separately. The combined `budget_intake` field remains for API compatibility. Relative intake wording is retained without guessing a year.

Conversation state is held in backend process memory and is lost on restart; it is not shared across multiple workers. Lead records persist in the database. The browser session ID is retained for the mounted chat widget, not as a persistent visitor account.

## Project structure

```text
.
├── README.md
├── .env.example                 # Backend variable template; no credentials
├── main.py                      # FastAPI application and CORS configuration
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── alembic.ini
├── alembic/
│   ├── env.py                   # Environment-based migration connection
│   └── versions/                # Baseline and budget/intake revisions
├── app/
│   ├── config.py
│   ├── database.py
│   ├── models.py                # Lead persistence model
│   ├── schemas.py               # Request/response validation
│   ├── routes/                  # Chat and lead endpoints
│   ├── services/                # Agent, matching, intake, scoring, sessions, escalation
│   └── data/                    # Demo providers, FAQs, and escalation phrases
├── tests/
│   ├── test_api.py
│   ├── test_predeployment.py
│   ├── test_intake.py
│   ├── test_migrations.py
│   └── manual_conversation.py
└── frontend/
    ├── app/                     # Page, layout, and global styles
    ├── components/              # Website sections and chat/form components
    ├── config/brandConfig.js    # Fictional UI branding and copy
    ├── context/                 # Chat widget state
    ├── lib/                     # API client and its regression tests
    ├── public/images/           # Local hero and destination images
    ├── package.json
    ├── package-lock.json
    └── next.config.mjs
```

## Local setup

Prerequisites: Python 3.12 or later, Node.js 20.9 or later with npm, a PostgreSQL database (local or Neon), and Groq API access.

### Backend

From the repository root:

```sh
python -m venv .venv
```

Activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell, or `source .venv/bin/activate` on macOS/Linux. Then install dependencies:

```sh
python -m pip install -r requirements.txt
```

Alternatively, `uv sync --locked` installs the locked backend dependencies and default development dependencies; activate the resulting `.venv` before the commands below.

Copy the root `.env.example` to `.env` and configure the backend variables described below. Apply the migrations before starting the server:

```sh
alembic upgrade head
uvicorn main:app --reload
```

The backend runs locally on port 8000. Interactive API documentation is available at `/docs`.

### Frontend

In a second terminal:

```sh
cd frontend
npm ci
```

Create `frontend/.env.local` and configure `NEXT_PUBLIC_API_URL` to point to the local backend origin on port 8000, without a trailing slash. Then run:

```sh
npm run dev
```

The website runs locally on port 3000. Use a frontend origin allowed by the backend CORS configuration. The project currently has no frontend `.env.example`; the public API variable is read by `frontend/lib/api.js`.

## Environment variables

The root [.env.example](.env.example) is the source of truth for backend variable names. Configure values locally or through the hosting platform; never commit credentials.

| Variable | Scope | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Backend | Authenticates requests to Groq |
| `DATABASE_URL` | Backend | Connects SQLAlchemy and Alembic to PostgreSQL |
| `LEADS_ADMIN_TOKEN` | Backend only | Authorizes lead-list access; missing configuration denies access |
| `ALLOWED_ORIGINS` | Backend | Comma-separated exact frontend origins; local defaults are provided in the template, and wildcard origins are rejected |
| `NEXT_PUBLIC_API_URL` | Frontend | Public backend base URL used by the browser API client |

Only `NEXT_PUBLIC_API_URL` belongs in the frontend configuration. API credentials, database credentials, and the admin token must remain on the backend. Next.js public variables are included in the client build.

## Database migrations

Run from the repository root with the backend environment activated and the intended database configured:

```sh
alembic upgrade head
alembic current
alembic history
alembic check
```

The revision chain is:

- `20261003_01`: creates the legacy `leads` table on an empty database or adopts the existing table without rewriting rows.
- `20261003_02`: adds nullable string columns for `budget` and `intake` only when missing. Compatible manually added columns are retained. The legacy `budget_intake` column remains intact.

These adoption migrations require an online database connection and do not support `--sql`. Automatic downgrade is intentionally blocked to prevent deletion of pre-existing data; rollback requires a reviewed data-preserving migration. The earlier raw SQL migration has been replaced by Alembic. Run migrations before starting a release; application table creation does not replace schema migrations.

## Main API endpoints

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| `POST` | `/chat` | Accepts a session ID and message; returns a reply, collected fields, lead readiness, and optional lead status | Public |
| `POST` | `/lead` | Validates and stores consultation details with the session ID; calculates lead status on the server | Public |
| `GET` | `/leads` | Returns saved leads, newest first | Protected: bearer authentication using `LEADS_ADMIN_TOKEN` |
| `GET` | `/health` | Returns application health status | Public |

Consult `/docs` for the current request and response schemas. `GET /leads` returns unauthorized when the bearer token is missing or invalid, or the backend token is not configured. There is no admin dashboard or user account system.

## Testing and verification

Run the complete backend suite from the repository root:

```sh
python -m pytest -p no:cacheprovider -q
```

Backend tests use pytest, FastAPI TestClient/HTTPX, isolated in-memory SQLite databases, test-only configuration, and mocked LLM calls. Coverage includes API validation, lead access, CORS, grounding behavior, scoring, intake extraction, session behavior, retryable errors, and migration adoption/data preservation. These tests do not validate live Groq responses or replace PostgreSQL migration verification.

Frontend automated regression tests do exist: `lib/api.test.mjs` and `components/chat/MessageBubble.test.mjs` use Node's built-in test runner. They check API transport/session IDs, timeout/error handling, Markdown rendering, and unsafe-content restrictions. They are focused regressions, not a browser end-to-end suite.

From `frontend/`:

```sh
node --test lib/api.test.mjs components/chat/MessageBubble.test.mjs
npm run lint
npm run build
```

For a local production preview, run `npm run start` after building. Verify the real conversation, consultation submission, responsive layout, and failure/retry flow separately with the configured backend.

## Deployment architecture

The Next.js frontend, FastAPI backend, and PostgreSQL database are separate services. The browser calls the backend; the backend calls Groq and persists leads in PostgreSQL. Neon can provide the hosted PostgreSQL database.

A deployment needs the public backend origin configured in the frontend build, the exact frontend origin allowed by backend CORS, backend secrets configured privately, and Alembic migrations applied to the target database. Serve public traffic over HTTPS. Review dependency security advisories before release.

The current in-memory conversation store assumes a single backend process. Rate limiting, persistent/shared conversation storage, and a full admin authentication system are not implemented. This repository demonstrates an enquiry workflow; it is not a production admissions platform.

## Demo disclaimer

GlobalPath Consulting is a fictional demo brand. The provider records, fees, entry requirements, FAQs, and recommendations are demonstration data, not official university/provider advice or verified current admissions or migration guidance. Campus imagery does not imply a partnership or endorsement. The assistant does not determine admission eligibility or guarantee a visa, offer, or outcome.
