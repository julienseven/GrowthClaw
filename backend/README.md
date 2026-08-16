# $GROWTH Backend

FastAPI-based backend for the $GROWTH autonomous marketing growth hacker.

## Quick Start

### Installation

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Server

```bash
# Development with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── config/
│   ├── __init__.py
│   └── settings.py              # Pydantic Settings (environment vars)
├── core/
│   ├── __init__.py
│   ├── solana_client.py         # Solana RPC wrapper
│   └── ai_engine.py             # OpenAI wrapper
├── models/
│   ├── __init__.py
│   └── schemas.py               # Pydantic schemas
├── routes/
│   ├── __init__.py
│   ├── market.py                # Market endpoints
│   ├── strategies.py            # Strategy endpoints
│   └── token.py                 # Token endpoints
├── workers/
│   ├── __init__.py
│   ├── market_monitor.py        # Market surveillance agent
│   └── growth_agent.py          # Growth optimization agent
├── utils/
│   ├── __init__.py
│   ├── logger.py                # Logging
│   └── validators.py            # Input validators
├── main.py                      # FastAPI app entry point
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment template
```

## Core Modules

### config/settings.py
Centralized environment configuration using Pydantic Settings v2.

**Key Settings:**
- Solana RPC configuration
- OpenAI API configuration
- Target token addresses
- Redis connection
- API server settings

### core/solana_client.py
Wrapper around Solana Web3 libraries for blockchain interactions.

**Methods (Placeholders):**
- `get_balance(address)` - Get SOL balance
- `get_token_balance(token_address, owner_address)` - Get SPL token balance
- `get_account_info(address)` - Get account metadata

### core/ai_engine.py
Wrapper around OpenAI API for marketing intelligence.

**Methods (Placeholders):**
- `analyze_market_sentiment(data)` - Sentiment analysis
- `generate_marketing_strategy(token_info, market_data)` - Strategy generation
- `evaluate_growth_opportunities(data)` - Growth analysis

### workers/market_monitor.py
Asyncio-based background worker for continuous market monitoring.

**Features:**
- Continuous market data collection
- Market metrics processing
- Configurable update intervals
- Error handling and resilience

### workers/growth_agent.py
AI-powered autonomous agent for strategy generation.

**Features:**
- Market analysis and optimization
- Strategy recommendation generation
- Performance evaluation
- Asyncio-based autonomous operation

## API Endpoints (Placeholder Structure)

### Health & Status
```
GET /health
GET /
```

### Market Data
```
GET /api/market/data/{token_address}
GET /api/market/analysis/{token_address}
GET /api/market/trends
```

### Strategies
```
GET /api/strategies/{token_address}
GET /api/strategies/{token_address}/latest
GET /api/strategies/performance/{strategy_id}
```

### Token Information
```
GET /api/token/{token_address}
GET /api/token/{token_address}/holders
GET /api/token/{token_address}/metrics
```

## Environment Variables

See `.env.example` for complete configuration.

### Critical Variables
- `OPENAI_API_KEY` - Your OpenAI API key
- `SOLANA_RPC_URL` - Solana RPC endpoint
- `TARGET_TOKEN_ADDRESS` - Token to monitor
- `REDIS_URL` - Redis connection string

## Dependencies Overview

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic v2** - Data validation
- **python-dotenv** - Environment management
- **OpenAI** - GPT-4o-mini integration
- **solders/solana-py** - Solana blockchain
- **aioredis** - Async Redis client
- **httpx** - Async HTTP client

## Running Background Workers

Workers use asyncio and are started from the main application:

```python
# Start market monitor
monitor = MarketMonitor()
await monitor.start()

# Start growth agent
agent = GrowthAgent()
await agent.start()
```

## Development Notes

- All async functions use Python's `asyncio` library
- Pydantic v2 settings for validation
- Type hints throughout for IDE support
- Placeholder implementations for phase 2 development

## Next Steps

1. Implement Solana client methods using solders/solana-py
2. Implement OpenAI API calls for AI features
3. Connect Redis for caching and task management
4. Integrate market data sources (Magic Eden, Jupiter, etc.)
5. Deploy to production environment

---

**Part of $GROWTH: The Autonomous Marketing Growth Hacker**
