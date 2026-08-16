# $GROWTH: The Autonomous Marketing Growth Hacker on Solana

An AnsemHack project for autonomous marketing strategy generation and execution on Solana.

## Project Overview

$GROWTH is a full-stack Web3 application that leverages AI (OpenAI GPT-4o-mini) and blockchain analysis to generate autonomous marketing strategies for tokens on Solana.

## Architecture

```
growth/
├── frontend/                 # Next.js 14+ App Router
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Utilities (Solana, API client)
│   │   └── types/           # TypeScript type definitions
│   ├── public/              # Static assets
│   ├── package.json
│   └── tsconfig.json
│
└── backend/                 # Python FastAPI
    ├── config/              # Settings and environment management
    ├── core/                # Core services (SolanaClient, AIEngine)
    ├── models/              # Pydantic schemas
    ├── routes/              # API endpoints
    ├── workers/             # Asyncio background workers
    ├── utils/               # Helpers and validators
    ├── main.py              # FastAPI application entry point
    ├── requirements.txt     # Python dependencies
    └── .env.example         # Environment variables template
```

## Tech Stack

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Blockchain**: @solana/web3.js
- **Language**: TypeScript

### Backend
- **Framework**: FastAPI 0.115.4
- **Language**: Python 3.11+
- **Runtime**: Asyncio for background workers
- **Solana Libraries**: solders, solana-py
- **AI**: OpenAI API (gpt-4o-mini)
- **Database**: Redis (caching and task management)
- **Validation**: Pydantic v2

## Configuration

### Environment Variables

#### Frontend (.env.local)
```
NEXT_PUBLIC_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Backend (.env)
```
# Solana Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_NETWORK=mainnet-beta
SOLANA_COMMITMENT_LEVEL=confirmed

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7

# Target Token Configuration
TARGET_TOKEN_ADDRESS=
TARGET_TOKEN_DECIMALS=6
TARGET_DEX_PROGRAM_ID=675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1xf

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=info

# Environment
ENVIRONMENT=development
DEBUG=true
```

## Backend Module Structure

### config/
- **settings.py**: Pydantic Settings for environment variable management
- Centralized configuration for all backend services

### core/
- **solana_client.py**: Solana RPC client wrapper
- **ai_engine.py**: OpenAI API wrapper for marketing insights

### workers/
- **market_monitor.py**: Autonomous agent for continuous market surveillance
- **growth_agent.py**: AI-powered growth optimization agent using asyncio

### models/
- **schemas.py**: Pydantic schemas for API request/response validation

### routes/
- **market.py**: Market data endpoints
- **strategies.py**: Strategy management endpoints
- **token.py**: Token information endpoints

### utils/
- **logger.py**: Logging configuration
- **validators.py**: Input validation utilities

## Frontend Components

- **Header**: Main navigation and branding
- **Footer**: Application footer
- **Custom Hooks**: `useApi` for API interactions with state management

## Frontend Libraries

- **lib/solana.ts**: Solana Web3.js utilities
- **lib/api.ts**: Backend API client with typed responses
- **types/index.ts**: Global TypeScript interfaces

## Getting Started (Setup Guide)

### Prerequisites
- Node.js 18+
- Python 3.11+
- Redis (for background task management)
- OpenAI API key
- Solana RPC endpoint access

### Backend Setup
```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
npm install
npm run dev
```

## API Endpoints (FastAPI)

### Health & Status
- `GET /health` - Service health check
- `GET /` - API information

### Market Data
- `GET /api/market/data/{token_address}` - Get market data
- `GET /api/market/analysis/{token_address}` - Get market analysis
- `GET /api/market/trends` - Get market trends

### Strategies
- `GET /api/strategies/{token_address}` - Get strategies for token
- `GET /api/strategies/{token_address}/latest` - Get latest strategy
- `GET /api/strategies/performance/{strategy_id}` - Get strategy performance

### Token Information
- `GET /api/token/{token_address}` - Get token info
- `GET /api/token/{token_address}/holders` - Get top holders
- `GET /api/token/{token_address}/metrics` - Get token metrics

## Background Workers

### MarketMonitor
- Continuous market surveillance
- Data collection from Solana DEX
- Metrics processing and analysis
- Update interval: 60 seconds

### GrowthAgent
- AI-powered strategy generation
- Market analysis and optimization
- Autonomous recommendation generation
- Update interval: 5 minutes

## Development Status

This is the foundational architecture and is ready for feature implementation:
- ✅ Project structure established
- ✅ Configuration management setup
- ✅ FastAPI framework configured with CORS
- ✅ Solana client wrapper abstraction
- ✅ OpenAI AI engine wrapper abstraction
- ✅ Asyncio background worker structure
- ✅ Pydantic schema definitions
- ✅ API route structure with placeholders
- ✅ Frontend component structure
- ✅ Type definitions and utilities
- ⏳ Functional implementations (next phase)

## Future Phases

### Phase 1: Core Implementation
- Implement Solana blockchain interactions
- Integrate OpenAI API for analysis
- Build market data collectors
- Implement AI strategy generation

### Phase 2: Advanced Features
- Autonomous strategy execution
- Real-time notifications
- Dashboard analytics
- Transaction history and tracking

### Phase 3: Optimization
- Performance tuning
- Mainnet deployment
- Advanced caching strategies
- ML model fine-tuning

## Notes for AnsemHack

This architecture is specifically designed for the AnsemHack competition:
- **Solana Integration**: Full Web3.js frontend and Solana Python support
- **AI Integration**: OpenAI GPT-4o-mini for autonomous decision making
- **Autonomy**: Background workers with asyncio for continuous operation
- **Growth Focus**: Autonomous marketing strategy generation and tracking

---

**Built with ❤️ for AnsemHack | The Autonomous Marketing Growth Hacker**
