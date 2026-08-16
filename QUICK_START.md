# $GROWTH Quick Start Guide

Get $GROWTH up and running in 5 minutes.

## Prerequisites Check

```bash
# Verify Node.js 18+
node --version

# Verify Python 3.11+
python --version

# Verify npm 9+
npm --version
```

---

## Option 1: Simplest Setup (2 Terminals)

### Terminal 1: Backend
```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Copy environment (first time only)
cp .env.example .env
# ⚠️ Edit .env: Add your OPENAI_API_KEY

# Start backend
uvicorn main:app --reload
```

Backend runs at: **http://localhost:8000**

### Terminal 2: Frontend
```bash
# Install dependencies (first time only)
npm install

# Start frontend
npm run dev
```

Frontend runs at: **http://localhost:3000**

### Done! ✅
Visit http://localhost:3000 in your browser.

---

## Option 2: Docker Setup (1 Command)

```bash
cd backend

# Create .env file
cp .env.example .env
# ⚠️ Edit .env: Add your OPENAI_API_KEY

# Start all services (Backend + Redis)
docker-compose up
```

Services:
- API: http://localhost:8000
- Redis: localhost:6379
- Frontend: npm run dev (in another terminal)

---

## Configuration

### Minimum Required
You **MUST** set one variable in `backend/.env`:

```bash
# Your OpenAI API key (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key-here
```

### Optional But Recommended
```bash
# Which token to analyze (Solana mint address)
TARGET_TOKEN_ADDRESS=your-token-mint

# Solana network to use
SOLANA_NETWORK=mainnet-beta  # or devnet

# Debugging
DEBUG=true
ENVIRONMENT=development
```

See `backend/.env.example` for all options.

---

## Verify It Works

### Health Check
```bash
# Terminal: Check backend is running
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "environment": "development",
#   "service": "$GROWTH Backend"
# }
```

### API Documentation
```
Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
```

### Frontend
```
http://localhost:3000
```

---

## Common Tasks

### Run Type Checks
```bash
# Frontend
npm run lint

# Backend
cd backend && python -m py_compile *.py
```

### Stop Services
```bash
# Backend: Ctrl+C in terminal
# Frontend: Ctrl+C in terminal
# Docker: docker-compose down
```

### Clear Cache & Reinstall
```bash
# Frontend
rm -rf node_modules package-lock.json .next
npm install

# Backend
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## File Locations to Know

| File | Purpose | Edit? |
|------|---------|-------|
| `backend/.env` | Backend configuration | ✏️ YES (API keys) |
| `.env.local` | Frontend configuration | ✏️ Rarely needed |
| `backend/main.py` | Backend entry point | 📖 Reference |
| `src/app/page.tsx` | Frontend home page | ✏️ YES (UI) |
| `backend/config/settings.py` | All settings | 📖 Reference |
| `backend/requirements.txt` | Python packages | ⚠️ Add new packages |
| `package.json` | Node packages | ⚠️ Add new packages |

---

## Project Structure (High Level)

```
growth/
├── backend/              # Python FastAPI
│   ├── main.py          # Start here!
│   ├── config/          # Settings
│   ├── core/            # Solana & OpenAI wrappers
│   ├── routes/          # API endpoints
│   ├── workers/         # Background agents
│   ├── .env.example     # Config template
│   └── requirements.txt # Dependencies
│
├── src/                 # Next.js Frontend
│   ├── app/            # Pages
│   ├── components/     # UI components
│   ├── lib/            # Utilities
│   ├── hooks/          # Custom hooks
│   └── types/          # TypeScript types
│
├── package.json        # Frontend config
└── .env.local         # Frontend env (dev)
```

---

## API Quick Reference

### Health Check
```bash
GET http://localhost:8000/health
```

### Get Market Data (Placeholder)
```bash
GET http://localhost:8000/api/market/data/{token_address}
```

### Get Strategies (Placeholder)
```bash
GET http://localhost:8000/api/strategies/{token_address}
```

### Get Token Info (Placeholder)
```bash
GET http://localhost:8000/api/token/{token_address}
```

See [README.md](./README.md) for complete API reference.

---

## Next Steps

### 1. Explore the Code
- Backend: `backend/main.py`
- Frontend: `src/app/page.tsx`
- API Docs: http://localhost:8000/docs

### 2. Read Documentation
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Development**: [DEVELOPMENT.md](./DEVELOPMENT.md)
- **Deployment**: [DEPLOYMENT.md](./DEPLOYMENT.md)

### 3. Add Your API Key
- Get OpenAI key: https://platform.openai.com/api-keys
- Add to `backend/.env`

### 4. Start Development
- Follow [DEVELOPMENT.md](./DEVELOPMENT.md) for guides
- See [CONTRIBUTING.md](./CONTRIBUTING.md) for code style

---

## Troubleshooting

### "ModuleNotFoundError" in Backend
```bash
# Solution: Install dependencies
cd backend
pip install -r requirements.txt
```

### "Cannot find module" in Frontend
```bash
# Solution: Install dependencies
npm install
```

### "Port 8000 already in use"
```bash
# Solution: Change port
uvicorn main:app --port 8001 --reload
```

### "OPENAI_API_KEY not set"
```bash
# Solution: Edit backend/.env and add your key
OPENAI_API_KEY=sk-your-api-key
```

### Frontend can't reach backend
```bash
# Check NEXT_PUBLIC_API_URL in .env.local
# Should be: http://localhost:8000
```

### Docker containers won't start
```bash
# Solution: Check logs
docker-compose logs

# Or rebuild
docker-compose up --build
```

---

## Key Files to Understand

### Backend Entry Point
**File**: `backend/main.py`
- FastAPI application
- Route registration
- CORS configuration
- Health check endpoint

### Configuration
**File**: `backend/config/settings.py`
- All environment variables
- Type-safe settings with Pydantic
- Easy to add new config options

### API Routes
**Directory**: `backend/routes/`
- `market.py` - Market data endpoints
- `strategies.py` - Strategy endpoints
- `token.py` - Token information endpoints

### Background Workers
**Directory**: `backend/workers/`
- `market_monitor.py` - Market surveillance
- `growth_agent.py` - AI-powered analysis

### Frontend Components
**Directory**: `src/components/`
- `header.tsx` - Page header
- `footer.tsx` - Page footer

### Frontend Utilities
**Directory**: `src/lib/`
- `solana.ts` - Solana Web3.js helpers
- `api.ts` - Backend API client

---

## Environment Variables

### Most Important (Backend)
```bash
OPENAI_API_KEY=sk-your-key-from-openai
```

### Useful (Backend)
```bash
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
TARGET_TOKEN_ADDRESS=your-token-mint
ENVIRONMENT=development
DEBUG=true
```

### Frontend
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

See `backend/.env.example` for all options.

---

## Common Commands

### Frontend
```bash
npm install              # Install dependencies
npm run dev             # Start dev server
npm run build           # Build for production
npm start               # Start production server
npm run lint            # Check code style
npm test                # Run tests
```

### Backend
```bash
pip install -r requirements.txt  # Install dependencies
uvicorn main:app --reload        # Start dev server
python -m pytest                 # Run tests
python -c "import main"          # Check syntax
```

### Git
```bash
git clone <repo>        # Clone repository
git checkout -b feature-name  # Create branch
git add .              # Stage changes
git commit -m "message"  # Commit
git push origin branch-name  # Push
```

---

## Getting Help

### Documentation
- Full docs: [README.md](./README.md)
- Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Development: [DEVELOPMENT.md](./DEVELOPMENT.md)
- Deployment: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)

### API Documentation
- Swagger UI: http://localhost:8000/docs (while running)
- ReDoc: http://localhost:8000/redoc

### External Links
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Solana Docs](https://docs.solana.com/)
- [OpenAI Docs](https://platform.openai.com/docs)

---

## Success Checklist

- [ ] Backend running: `http://localhost:8000/health`
- [ ] Frontend running: `http://localhost:3000`
- [ ] Can see API docs: `http://localhost:8000/docs`
- [ ] OPENAI_API_KEY set in `backend/.env`
- [ ] No errors in console/terminal

**If all checked ✓, you're ready to start developing!**

---

## What's Next?

1. **Explore**: Browse http://localhost:3000
2. **Review**: Read [DEVELOPMENT.md](./DEVELOPMENT.md)
3. **Implement**: Start building Phase 2 features
4. **Deploy**: Follow [DEPLOYMENT.md](./DEPLOYMENT.md) when ready

---

## Quick Links

| Purpose | Link |
|---------|------|
| Full README | [README.md](./README.md) |
| Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Development | [DEVELOPMENT.md](./DEVELOPMENT.md) |
| Deployment | [DEPLOYMENT.md](./DEPLOYMENT.md) |
| Contributing | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| Project Overview | [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) |
| Backend Docs | [backend/README.md](./backend/README.md) |
| API Docs | http://localhost:8000/docs |

---

**Ready to build? Let's go! 🚀**

Questions? Check [DEVELOPMENT.md](./DEVELOPMENT.md) or the full [README.md](./README.md).
