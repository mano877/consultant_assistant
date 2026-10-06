# Consultancy AI Assistant Frontend

The Next.js frontend for a generic education-consultancy AI assistant demo, using an Australian study enquiry scenario. This is a demonstration project, not a real education consultancy.

## Stack and features

- Next.js 16 App Router and React 19, with JavaScript, custom CSS, and Tailwind CSS 4.
- Responsive consultancy landing page with Australian destination sections, optimized local images through `next/image`, and reduced-motion support.
- Student Adviser chat with quick actions, Markdown and table rendering through `react-markdown` and `remark-gfm`, loading states, and error recovery with Retry.
- Automatic conversation session IDs and a consultation lead form connected to the backend qualification flow.
- ESLint 9 and Node.js built-in regression tests.

## Local setup

From the repository root:

```bash
cd frontend
npm install
```

Create `.env.local` in this directory:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`NEXT_PUBLIC_API_URL` is the base URL of the separately deployed FastAPI backend, without a trailing slash. The frontend calls its `/chat` and `/lead` endpoints. For local development, run the backend separately and allow the frontend origin in its CORS configuration.

This variable is public and included in the browser bundle; never place secrets in it. Set it before building for production and rebuild when it changes.

```bash
npm run dev
```

Open [localhost:3000](http://localhost:3000). See the root README for backend setup.

## Checks and production build

Run from `frontend/`:

```bash
npm run lint
node --test lib/api.test.mjs components/chat/MessageBubble.test.mjs
npm run build
npm run start
```

The six regression tests cover API session payloads, errors, timeout/retry behavior, and safe Markdown rendering. They use mocked requests and server-rendered components; they are not browser end-to-end tests. `npm run start` serves the completed production build.

## Demo scope

Study guidance and provider information use demonstration data and are not official university or provider advice. AI responses, qualification, and lead storage are handled by the separate FastAPI backend.
