# $GROWTH — The Autonomous Marketing Growth Hacker

An autonomous marketing growth engine for the **AnsemHack on Solana**. `$GROWTH`
is an AI agent that continuously generates, schedules, and executes marketing
actions on behalf of a token — powered by **OpenAI (gpt-4o-mini)** and driven by
a **FastAPI + Asyncio** backend with a **Next.js (App Router)** frontend.

> **Status:** foundational architecture — directory scaffolding and environment
> configuration only. No functional business logic has been implemented yet.

---

## Tech Stack

| Layer      | Technology                                                        |
| ---------- | ----------------------------------------------------------------- |
| Frontend   | Next.js 16 (App Router), Tailwind CSS, Lucide React, `@solana/web3.js` |
| Backend    | Python 3.11, FastAPI, Asyncio                                     |
| Solana     | `solana-py` + `solders` (backend), `@solana/web3.js` (frontend)   |
| AI Engine  | OpenAI API — `gpt-4o-mini`                                        |
| Persistence| PostgreSQL (via the provided Drizzle ORM wiring in `src/db/`)     |

---

## Repository Layout

```
.
├── src/                     # Next.js frontend (App Router)
│   ├── app/                 #   routes / pages / API-route proxies
│   ├── lib/                 #   client helpers → env.ts (typed env)
│   │   └── env.ts
│   └── db/                  #   Drizzle schema + client (shared w/ backend)
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── core/            #   config.py (typed settings), logging, lifecycle
│   │   ├── api/             #   HTTP routes (deps, routers)
│   │   ├── domain/          #   business logic (Solana adapter, AI engine)
│   │   └── workers/         #   asyncio background workers
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
└── .env.example             # Next.js frontend env template
```

### Boundaries

- **`src/`** — the Next.js app. Never imports Python; talks to the backend via
  HTTP. Browser-safe secrets are limited to `NEXT_PUBLIC_*`.
- **`backend/`** — the FastAPI app. Owns all secrets (OpenAI key, RPC URLs) and
  runs the asyncio workers. It is the single writer to the database.
- **`src/lib/env.ts`** vs **`backend/app/core/config.py`** — twin typed
  configuration surfaces; each side validates its own env at startup.

---

## Getting Started

### 1. Frontend env

```bash
cp .env.example .env.local
```

### 2. Backend env

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in OPENAI_API_KEY, SOLANA_RPC_URL, SOLANA_TARGET_TOKENS
```

### 3. Validate configuration

```bash
cd backend
python -m app.infra.config   # exits non-zero if anything is misconfigured
```

---

## Configuration Reference

### Backend (`backend/.env`)

| Variable                     | Purpose                                        | Required |
| ---------------------------- | ---------------------------------------------- | -------- |
| `OPENAI_API_KEY`             | OpenAI API key (engine disabled when unset)    | prod     |
| `OPENAI_MODEL`               | Model to call (default `gpt-4o-mini`)          | no       |
| `SOLANA_RPC_URL`             | HTTPS RPC endpoint                             | yes      |
| `SOLANA_RPC_WS_URL`          | WebSocket RPC (optional)                       | no       |
| `SOLANA_TARGET_TOKENS`       | Comma-separated base58 mint addresses          | no       |
| `WORKER_MAX_CONCURRENT_TASKS`| Async worker concurrency cap                   | no       |
| `CORS_ALLOWED_ORIGINS`       | Allowed frontend origins                        | dev      |

### Frontend (`.env.local`)

| Variable                    | Purpose                                   | Required |
| --------------------------- | ----------------------------------------- | -------- |
| `NEXT_PUBLIC_API_URL`       | FastAPI backend origin                    | yes      |
| `NEXT_PUBLIC_SOLANA_RPC_URL`| Public RPC for `@solana/web3.js`          | yes      |
| `NEXT_PUBLIC_TARGET_TOKENS` | Comma-separated base58 mint addresses     | no       |

---

## Roadmap (implementation phases)

1. **API skeleton** — FastAPI app factory, `/api/health`, CORS wiring.
2. **Solana adapter** — RPC client wrapper around `solders` / `solana-py`.
3. **AI engine** — `AsyncOpenAI` client (gpt-4o-mini) with typed prompts.
4. **Workers** — asyncio task loop consuming marketing actions.
5. **Frontend** — page shell, Tailwind theme, wallet + token UI via `@solana/web3.js`.
