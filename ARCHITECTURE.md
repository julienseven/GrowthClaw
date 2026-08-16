# $GROWTH Architecture Overview

## Project Separation Strategy

This monorepo contains two distinct applications with separate configuration:

### Frontend: Next.js 14+ (App Router)
- **Location**: `/src/*`
- **Build Tool**: Next.js
- **Port**: 3000 (dev), 3000 (prod)
- **Configuration**: `tsconfig.json`, `next.config.ts`
- **Environment**: `.env.local` (NEXT_PUBLIC_* only)
- **Dependencies**: React, TailwindCSS, Solana Web3.js, Lucide Icons

### Backend: Python FastAPI
- **Location**: `/backend/*`
- **Runtime**: Python 3.11+
- **Framework**: FastAPI + Uvicorn
- **Port**: 8000
- **Configuration**: `config/settings.py` (Pydantic Settings)
- **Environment**: `/backend/.env`
- **Dependencies**: FastAPI, OpenAI, Solana Libraries, Redis

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Dashboard  │  │ Market Stats │  │ Strategies   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ▲                 ▲                    ▲             │
│         │                 │                    │             │
│    @solana/web3.js   API Client (lib/api.ts)  │             │
│         │                 │                    │             │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          │                 └────────────────────┤
          │                                      │
          ▼                                      ▼
    ┌────────────────────────────────────────────────┐
    │     FastAPI Backend (Python)                   │
    │  ┌─────────────┐  ┌──────────────────────┐    │
    │  │   Routes    │  │   Core Services      │    │
    │  │ /api/market │  │ - SolanaClient       │    │
    │  │ /api/token  │  │ - AIEngine (OpenAI)  │    │
    │  └─────────────┘  └──────────────────────┘    │
    │         ▲                      ▲               │
    │         │                      │               │
    │         └──────────┬───────────┘               │
    │                    │                           │
    │  ┌─────────────────┴──────────────┐            │
    │  ▼                                 ▼            │
    │ ┌───────────────┐ ┌──────────────┐            │
    │ │Workers (Async)│ │Config/Setup  │            │
    │ │-MarketMonitor │ │-Settings     │            │
    │ │-GrowthAgent   │ │-Validators   │            │
    │ └───────────────┘ └──────────────┘            │
    └────────────────────────────────────────────────┘
          │                     │
          └────────────┬────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                              ▼
    ┌──────────────┐          ┌──────────────┐
    │   Solana     │          │    OpenAI    │
    │   Blockchain │          │     API      │
    │  (RPC/Web3)  │          │ (GPT-4o-mini)│
    └──────────────┘          └──────────────┘
```

## Configuration Management Strategy

### Frontend Configuration (Environment Variables)
- **File**: `.env.local`
- **Prefix**: `NEXT_PUBLIC_` for client-side vars
- **Loaded**: At build time via Next.js
- **Access**: `process.env.NEXT_PUBLIC_*` in browser

**Example:**
```
NEXT_PUBLIC_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Configuration (Pydantic Settings)
- **File**: `/backend/.env`
- **Loader**: `pydantic-settings` with `python-dotenv`
- **Type Safety**: Pydantic v2 validation
- **Access**: `from config import settings`

**Example:**
```python
from config import settings

# Access any setting with type hints
rpc_url = settings.solana_rpc_url  # str
openai_key = settings.openai_api_key  # str
debug = settings.debug  # bool
```

## Module Responsibilities

### Backend Modules

#### config/
**Responsibility**: Environment variable management and validation
- Centralized settings object
- Type-safe access to env vars
- Default values and validation
- Support for multiple environments (dev/prod)

#### core/
**Responsibility**: External service integrations
- **solana_client.py**: Blockchain interactions via solders/solana-py
- **ai_engine.py**: OpenAI API integration for GPT-4o-mini

#### models/
**Responsibility**: Data schema definitions
- Pydantic schemas for API request/response validation
- Type hints for all endpoints
- Automatic OpenAPI documentation

#### routes/
**Responsibility**: API endpoint definitions
- Market data endpoints
- Strategy management endpoints
- Token information endpoints
- Each route file handles specific domain

#### workers/
**Responsibility**: Background asynchronous agents
- **market_monitor.py**: Continuous market surveillance using asyncio
- **growth_agent.py**: AI-powered autonomous growth optimization

#### utils/
**Responsibility**: Helper functions and validation
- Logging configuration
- Input validators for Solana addresses
- Reusable utility functions

### Frontend Modules

#### lib/
**Responsibility**: Utilities and integrations
- **solana.ts**: Web3.js helpers and validators
- **api.ts**: Backend API client with typed responses

#### components/
**Responsibility**: React UI components
- Header, Footer, Layout
- Feature-specific components
- Reusable UI elements

#### hooks/
**Responsibility**: Custom React hooks
- API data fetching with state
- Wallet connection management
- Custom business logic

#### types/
**Responsibility**: TypeScript definitions
- Global interfaces and types
- Shared type definitions
- Type safety across app

## Deployment Architecture

### Frontend Deployment
- Built as static Next.js app
- Hosted on Vercel/Netlify or standalone server
- Environment variables via platform secrets
- Client-side: Solana Web3.js for wallet interactions

### Backend Deployment
- Docker containerized FastAPI app
- Runs with Uvicorn (production server)
- Environment variables via secrets manager
- Can scale with multiple worker processes
- Background workers run in same process (asyncio)

### Integration Points
- Frontend calls Backend API at `NEXT_PUBLIC_API_URL`
- Backend reads Solana blockchain via `SOLANA_RPC_URL`
- Backend calls OpenAI API with `OPENAI_API_KEY`
- Workers operate independently with asyncio

## Security Considerations

### Frontend
- Only `NEXT_PUBLIC_*` variables exposed to browser
- No secrets in client code
- Solana transactions validated by user wallet

### Backend
- All secrets in environment variables (not committed)
- OpenAI API key server-side only
- Pydantic validation on all inputs
- CORS configured appropriately

### API Communication
- HTTPS in production
- Request validation via Pydantic
- Rate limiting (to be added)
- Authentication (to be added)

## Scaling Strategy

### Horizontal Scaling
- Frontend: Static site on CDN
- Backend: Multiple Uvicorn workers behind load balancer
- Workers: Can run on separate processes/machines

### Vertical Scaling
- Increase `workers` in uvicorn config
- Optimize database queries
- Cache frequently accessed data in Redis

### Monitoring
- FastAPI health endpoint: `/health`
- Worker health checks
- Error logging via Python logging
- API response metrics

## Development Workflow

### Local Development
1. Start Backend: `cd backend && uvicorn main:app --reload`
2. Start Frontend: `npm run dev`
3. Frontend calls backend at `localhost:8000`
4. Both services have hot-reload enabled

### Production Build
1. Frontend: `npm run build && npm start`
2. Backend: `pip install -r requirements.txt && uvicorn main:app --workers 4`

### Environment Management
- Development: `.env.local` and `/backend/.env`
- Production: Platform secrets (GitHub Secrets, etc.)

---

**This architecture prioritizes:**
- Clear separation of concerns
- Type safety (TypeScript + Pydantic)
- Scalability
- Autonomous operation (asyncio workers)
- Web3/Solana integration
- AI/OpenAI integration
