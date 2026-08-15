# ManobalAI 🧠💪

A mental-health support web app with a RAG-powered chatbot, emotion detection,
and mental-health quotes.

- **Frontend**: React 18 + Vite + Tailwind CSS, authentication via Clerk.
- **Backend**: FastAPI with a retrieval-augmented generation (RAG) chatbot
  (LLM + FAISS vector search), a Hugging Face emotion classifier, and a
  SQLite persistence layer.

The chatbot LLM can be either a **local model via Ollama** (default) or the
**hosted Groq API** — switch with `LLM_PROVIDER`.

---

## How the system works

```
┌──────────────────────┐        ┌─────────────────────────────────────┐
│  React SPA (Vite)    │  HTTP  │  FastAPI backend (port 8000)        │
│  - Clerk sign-in     │ ─────► │  - /prompt          RAG chatbot      │
│  - chat UI           │        │  - /analyze-emotion emotion analysis │
│  - emotion graph     │        │  - /emotion-graph   aggregated counts │
│  - random quote      │        │  - /random-quote    quote service    │
└──────────────────────┘        │  - /health          liveness         │
                                └───────────┬─────────────────────────┘
                                            │
                ┌───────────────────────────┼───────────────────────────┐
                ▼                           ▼                           ▼
      ┌─────────────────┐         ┌──────────────────┐        ┌─────────────────┐
      │  FAISS vector   │         │  SQLite (WAL)    │        │  Groq LLM       │
      │  index (disk)   │         │  sessions        │        │  + HF emotion   │
      │  embeddings via │         │  messages        │        │  classifier     │
      │  MiniLM         │         │  emotion_events  │        │                 │
      └─────────────────┘         └──────────────────┘        └─────────────────┘
```

### Chatbot (`/prompt`)

1. The request is authenticated (Clerk JWT) and tied to a per-user session.
2. The **latest user question only** is used to retrieve the top `RETRIEVER_K`
   most similar documents from a **cosine-similarity FAISS index** built over
   `data/combined_mental_health_dataset.csv` (~1,350 unique Q&A pairs).
   - Retrieval is filtered by a `RETRIEVER_MIN_SCORE` similarity threshold so
     unrelated questions are not force-grounded in the dataset.
3. Recent conversation history is injected into the prompt separately, while
   the retriever only searches on the current question — keeping retrieval
   accurate as conversations grow.
4. The configured LLM generates the answer, which is returned and persisted to
   the user's session.

   - `LLM_PROVIDER=ollama` (default) calls a local model through Ollama at
     `OLLAMA_BASE_URL` (e.g. `qwen2.5-coder:1.5b`).
   - `LLM_PROVIDER=groq` calls the hosted Groq API (`ChatGroq`).

Key properties:

- **Persistent vector store**: embeddings are computed once and cached on disk
  (`data/vector_store`), so restarts do not re-embed the whole dataset.
- **Lazy heavy imports**: the Groq client, embeddings, FAISS index, and the
  transformers emotion pipeline are all built on first use, keeping cold start
  and test runs fast.
- **Per-user isolation**: conversations and emotion analytics are scoped to the
  authenticated user id in SQLite; a session id from one user can never be
  claimed by another.
- **Async LLM calls**: the chain is invoked with `ainvoke`, so long generations
  do not block the event loop.

### Adding data

The chat corpus is a single CSV, `data/combined_mental_health_dataset.csv`,
rebuilt from the raw sources in `data/raw/`:

```bash
cd ava/backend
./.venv/bin/python data/build_dataset.py
```

- Drop new Q&A CSVs into `data/raw/` with any supported schema — `Questions,Answers`,
  `Human,Bot`, `Context,Response`, or `questionTitle,questionText,answerText`
  (counselchat) — and rerun the script.
- The existing combined file is preserved verbatim (the dataset only ever
  grows); new rows are deduplicated (by question and exact pair) and filtered
  (short/thin rows and HTML/training-template artifacts dropped).
- After rebuilding, delete `data/vector_store/` and restart the backend so the
  FAISS index is rebuilt from the new corpus (first request takes ~10-90s).
- `common_concerns.csv` and `coping_strategies.csv` ship pre-made with curated
  content covering everyday phrasings ("i don't feel well") and coping skills
  (grounding, breathing, boundaries, etc.).

### Emotion analysis (`/analyze-emotion`, `/emotion-graph`)

- A `j-hartmann/emotion-english-distilroberta-base` pipeline returns the
  dominant emotion and its confidence, plus a supportive suggestion.
- Results are stored per user in SQLite. `/emotion-graph` returns aggregated
  emotion counts as JSON (the frontend renders the bar chart), instead of
  generating PNG images on every request.

### Security

- Clerk RS256 session tokens are verified server-side against Clerk's JWKS
  endpoint (`PyJWKClient`, cached). When `AUTH_ENABLED=false` (local dev/tests)
  a dummy user is used.
- CORS is locked to the origins listed in `CORS_ORIGINS`.
- Bot responses are HTML-escaped on the client before the typewriter renders
  them, preventing stored XSS from LLM output.

---

## Project layout

```
ava/
├── backend/
│   ├── app/
│   │   ├── config.py        # env-driven settings
│   │   ├── db.py            # SQLite sessions/messages/emotion events
│   │   ├── security.py      # Clerk JWT verification
│   │   ├── emotion.py       # emotion classifier (lazy)
│   │   ├── quotes.py        # cached quote loader
│   │   ├── chat.py          # RAG chain + response generation
│   │   ├── routers/         # FastAPI routers
│   │   └── main.py          # app factory
│   ├── data/                # dataset + quotes (raw sources in data/raw/)
│   │   └── build_dataset.py # rebuild combined CSV from data/raw/*.csv
│   ├── tests/               # pytest suite (backend)
│   ├── main.py              # runnable entrypoint
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api.js           # typed API client (axios)
    │   ├── utils/sanitize.js# XSS-safe message rendering
    │   ├── component/       # chat, graph, sign-in components
    │   ├── main.jsx         # router + Clerk provider (lazy GraphPage)
    │   └── App.jsx          # chat UI
    ├── .env.example
    └── vitest.config.js
```

---

## Prerequisites

- Python 3.10+ and `pip`
- Node.js 18+ and npm
- A [Groq](https://console.groq.com) API key — only if `LLM_PROVIDER=groq`
- [Ollama](https://ollama.com) with a local model — only if
  `LLM_PROVIDER=ollama` (default)
- A [Clerk](https://clerk.com) application (for authentication)

---

## Running the backend

```bash
cd ava/backend

# 1. Create a virtual environment and install dependencies (with uv)
uv venv --python 3.12
uv pip install torch --index-url https://download.pytorch.org/whl/cpu   # optional, CPU-only torch
uv pip install -r requirements.txt

# 2. Start Ollama (only needed for LLM_PROVIDER=ollama, the default)
ollama serve                       # in another terminal
ollama pull qwen2.5-coder:1.5b     # first time only

# 3. Configure environment
cp .env.example .env
#   - default LLM_PROVIDER=ollama is fine for local testing
#   - set GROQ_API_KEY + LLM_PROVIDER=groq to use the hosted Groq API
#   - set CLERK_ISSUER, CLERK_JWKS_URL, CLERK_AUDIENCE (or AUTH_ENABLED=false for local dev)
#   - optionally adjust CORS_ORIGINS

# 4. Start the server
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The first `/prompt` request builds the embeddings and FAISS index (and caches it
on disk), so expect a one-time delay.

> **Local LLM note**: `qwen2.5-coder:1.5b` is a small coding-focused model. It
> is great for verifying the pipeline works but is not ideal for final
> mental-health answer quality — pull a larger chat model (e.g.
> `ollama pull qwen2.5:7b`) and set `OLLAMA_MODEL` accordingly for better
> answers.

### Backend configuration

| Variable              | Default                                      | Description                          |
| --------------------- | -------------------------------------------- | ------------------------------------ |
| `LLM_PROVIDER`        | `ollama`                                     | `ollama` (local) or `groq` (hosted)  |
| `OLLAMA_BASE_URL`     | `http://localhost:11434`                     | Ollama server URL                    |
| `OLLAMA_MODEL`        | `qwen2.5-coder:1.5b`                         | Local model to use                   |
| `GROQ_API_KEY`        | –                                            | Groq API key (for `groq` provider)   |
| `LLM_MODEL`           | `mixtral-8x7b-32768`                         | Groq model                           |
| `LLM_TEMPERATURE`     | `0.3`                                        | LLM sampling temperature             |
| `LLM_MAX_TOKENS`      | `512`                                        | Max output tokens                    |
| `EMBEDDING_MODEL`     | `all-MiniLM-L6-v2`                           | Embedding model                      |
| `RETRIEVER_K`         | `4`                                          | Documents retrieved per query        |
| `RETRIEVER_MIN_SCORE` | `0.35`                                       | Minimum cosine similarity to ground  |
| `MAX_CONVERSATIONS`   | `30`                                         | History exchanges kept per session   |
| `MAX_INPUT_CHARS`     | `2000`                                       | Max user input length                |
| `DATABASE_PATH`       | `./data/manobal.db`                          | SQLite database file                 |
| `VECTOR_STORE_DIR`    | `./data/vector_store`                        | FAISS index directory                |
| `CORS_ORIGINS`        | – (defaults to `http://localhost:5173`)      | Comma-separated allowed origins      |
| `AUTH_ENABLED`        | `true`                                       | Require Clerk tokens                 |
| `CLERK_ISSUER`        | –                                            | Clerk issuer URL                     |
| `CLERK_JWKS_URL`      | –                                            | Clerk JWKS endpoint                  |
| `CLERK_AUDIENCE`      | `manobal-frontend`                           | Expected JWT audience                |
| `EMOTION_MODEL`       | `j-hartmann/emotion-english-distilroberta-base` | Emotion classifier               |
| `EMOTION_DEVICE`      | `cpu`                                        | `cpu` or `cuda`                      |
| `QUOTES_FILE`         | `./data/mental_health_quotes.txt`            | Quotes source file                   |

---

## Running the frontend

```bash
cd ava/frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
#   - set VITE_CLERK_PUBLISHABLE_KEY (from your Clerk app)
#   - set VITE_API_BASE_URL (http://127.0.0.1:8000 for local dev)
#   - set VITE_AUTH_DISABLED=true to run without Clerk (local dev)

# 3. Start the dev server
npm run dev
```

Open http://localhost:5173 and sign in with Clerk.

In development, Vite proxies `/prompt`, `/analyze-emotion`, `/emotion-graph`
and `/random-quote` to the backend on `http://127.0.0.1:8000`. In production,
point `VITE_API_BASE_URL` at the deployed backend origin.

```bash
npm run build   # production bundle (GraphPage is code-split)
npm run preview
```

---

## Running the tests

Backend (`pytest`):

```bash
cd ava/backend
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest            # 39 tests: config, db, auth, emotion, quotes, chat, API
```

Frontend (`vitest`):

```bash
cd ava/frontend
npm test                    # 14 tests: API client, XSS-safe message rendering, auth-disabled smoke tests
```

Tests mock the heavy components (Groq, embeddings, emotion pipeline), so they
run fast and offline.

---

## API reference

| Method | Endpoint            | Auth    | Description                              |
| ------ | ------------------- | ------- | ---------------------------------------- |
| GET    | `/health`           | no      | Liveness check                           |
| POST   | `/prompt`           | yes*    | Chat with the RAG bot                    |
| POST   | `/analyze-emotion`  | yes*    | Detect dominant emotion + suggestion     |
| GET    | `/emotion-graph`    | yes*    | Emotion counts for the current user      |
| GET    | `/random-quote`     | no      | A random mental-health quote             |

\* `yes` when `AUTH_ENABLED=true`.

---

## Troubleshooting local dev

- **Quote/chat fails in the browser but backend logs show 200** — almost always
  CORS: the browser blocks the response because the page origin isn't in
  `CORS_ORIGINS`. If Vite auto-incremented the port (e.g. you're on
  `:5174` because another instance holds `:5173`), add that origin to
  `CORS_ORIGINS` and restart the backend.
- **Connection refused from the browser only** — Vite binds to IPv6
  (`[::1]`) while uvicorn binds IPv4 (`0.0.0.0`); the browser resolves
  `localhost` to `::1` and the API call dies. Point `VITE_API_BASE_URL` at
  explicit IPv4 (`http://127.0.0.1:8000`) or run uvicorn with `--host ::`.
- **Backend dies with your terminal** — `uv run uvicorn --reload` stops when the
  terminal closes; run it with `nohup ... &` (log to a file) for a persistent
  instance.
- **"Looks like there might have been a typo…" on real questions** — the small
  `qwen2.5-coder:1.5b` model is unreliable at following the fallback rules; pull
  a larger model (`ollama pull qwen2.5:7b`) and set `OLLAMA_MODEL`.
- **`&#39;` shown literally in chat** — the typewriter inserts escaped HTML
  strings without re-parsing entities; apostrophes are no longer escaped by
  `toSafeMessageHtml` (single quotes are only used inside double-quoted
  attributes, so this is XSS-safe).

---

## Security note

A previous commit accidentally included API keys in tracked files
(`ManobalAI/x.py`, `ManobalAI/temp.yaml`). Those files have been removed and the
keys rotated are **still considered compromised** — if you ever used the keys
from this repository, revoke them in the Groq and Clerk dashboards. The keys
were also present in git history, so the history should be rewritten (or the
repository treated as internal) before any public release.