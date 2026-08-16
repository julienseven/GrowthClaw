# $GROWTH Development Guide

Complete guide for developing the $GROWTH autonomous marketing platform locally.

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-repo/growth.git
cd growth
```

### 2. Backend Setup (Terminal 1)
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Start development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup (Terminal 2)
```bash
# From project root
npm install

# Start development server
npm run dev
```

### 4. Visit Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend Docs: http://localhost:8000/docs

---

## Development Environment

### Required Tools
- **Node.js 18+**: `node --version`
- **Python 3.11+**: `python --version`
- **npm 9+**: `npm --version`
- **Git**: `git --version`

### Optional Tools (Recommended)
- **Redis CLI**: For debugging Redis connections
- **curl**: For testing API endpoints
- **VS Code**: With Python and ESLint extensions
- **Postman**: For API testing

### VS Code Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-vscode.makefile-tools",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss"
  ]
}
```

---

## Project Structure Review

```
growth/
├── backend/                          # Python FastAPI
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # Pydantic Settings
│   ├── core/
│   │   ├── solana_client.py          # Solana integration
│   │   └── ai_engine.py              # OpenAI integration
│   ├── models/
│   │   └── schemas.py                # Pydantic schemas
│   ├── routes/
│   │   ├── market.py
│   │   ├── strategies.py
│   │   └── token.py
│   ├── workers/
│   │   ├── market_monitor.py         # Market surveillance
│   │   └── growth_agent.py           # AI agent
│   ├── utils/
│   │   ├── logger.py
│   │   └── validators.py
│   ├── main.py                       # FastAPI app
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── src/                              # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx                  # Home page
│   │   ├── layout.tsx                # Root layout
│   │   └── globals.css               # Global styles
│   ├── components/
│   │   ├── header.tsx
│   │   └── footer.tsx
│   ├── hooks/
│   │   └── useApi.ts
│   ├── lib/
│   │   ├── solana.ts                 # Web3.js utilities
│   │   └── api.ts                    # Backend client
│   ├── types/
│   │   └── index.ts                  # TypeScript definitions
│   └── public/
│
├── package.json                      # Frontend dependencies
├── tsconfig.json                     # TypeScript config
├── tailwind.config.ts                # Tailwind CSS config
├── next.config.ts                    # Next.js config
├── .env.local                        # Frontend env (dev)
├── .env                              # (Not in repo)
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── DEPLOYMENT.md
└── DEVELOPMENT.md                    # This file
```

---

## Backend Development

### Adding a New API Endpoint

1. **Create route file** (`backend/routes/example.py`):
```python
from fastapi import APIRouter
from models.schemas import TokenInfo

router = APIRouter(prefix="/api/example", tags=["example"])

@router.get("/data/{id}")
async def get_example(id: str) -> TokenInfo:
    """Get example data."""
    # Implementation
    return TokenInfo(
        mintAddress=id,
        name="Example",
        symbol="EX",
        decimals=6
    )
```

2. **Register route in `main.py`**:
```python
from routes import example

app.include_router(example.router)
```

3. **Test endpoint**:
```bash
curl http://localhost:8000/api/example/data/test123
```

### Adding a New Pydantic Schema

1. **Add to `models/schemas.py`**:
```python
class ExampleData(BaseModel):
    field1: str = Field(..., description="Field description")
    field2: int = Field(..., description="Another field")
    field3: Optional[float] = None
```

2. **Use in routes**:
```python
@router.post("/create")
async def create_example(data: ExampleData) -> dict:
    return {"status": "created", "data": data}
```

### Working with Background Workers

#### Market Monitor Example
```python
from workers.market_monitor import MarketMonitor

# In your route
@app.get("/start-monitor")
async def start_monitoring():
    monitor = MarketMonitor()
    # Start in background
    asyncio.create_task(monitor.start())
    return {"status": "monitoring started"}
```

#### Growth Agent Example
```python
from workers.growth_agent import GrowthAgent

@app.post("/trigger-analysis")
async def trigger_analysis():
    agent = GrowthAgent()
    analysis = await agent._analyze_and_optimize()
    return {"analysis": analysis}
```

### Integration with Solana

```python
from core.solana_client import SolanaClient

@router.get("/balance/{address}")
async def get_balance(address: str):
    client = SolanaClient()
    balance = await client.get_balance(address)
    return {"address": address, "balance": balance}
```

### Integration with OpenAI

```python
from core.ai_engine import AIEngine

@router.post("/analyze")
async def analyze_data(data: dict):
    engine = AIEngine()
    analysis = await engine.analyze_market_sentiment(data)
    return {"analysis": analysis}
```

### Logging

```python
from utils.logger import get_logger

logger = get_logger(__name__)

@router.get("/example")
async def example_endpoint():
    logger.info("Processing example endpoint")
    try:
        # Your code
        pass
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise
```

---

## Frontend Development

### Creating a New Component

1. **Create component file** (`src/components/example.tsx`):
```typescript
import { AlertCircle } from "lucide-react";

interface ExampleProps {
  title: string;
  description?: string;
}

export function Example({ title, description }: ExampleProps) {
  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-5 w-5 text-blue-600" />
        <h2 className="font-semibold">{title}</h2>
      </div>
      {description && (
        <p className="mt-2 text-sm text-gray-600">{description}</p>
      )}
    </div>
  );
}
```

2. **Use in page**:
```typescript
import { Example } from "@/components/example";

export default function Page() {
  return (
    <Example title="Example" description="This is an example component" />
  );
}
```

### Creating a Custom Hook

1. **Create hook file** (`src/hooks/useExample.ts`):
```typescript
import { useState, useCallback } from "react";

interface UseExampleOptions {
  initialValue?: string;
}

export function useExample(options: UseExampleOptions = {}) {
  const [value, setValue] = useState(options.initialValue || "");
  const [loading, setLoading] = useState(false);

  const process = useCallback(async (input: string) => {
    setLoading(true);
    try {
      // Your logic
      setValue(input);
    } finally {
      setLoading(false);
    }
  }, []);

  return { value, loading, process };
}
```

### Using the API Client

```typescript
import { useApi } from "@/hooks/useApi";
import { apiPost } from "@/lib/api";

export default function Example() {
  // Auto-fetch on mount
  const { data, loading, error } = useApi("/api/example/data", true);

  const handleSubmit = async () => {
    const response = await apiPost("/api/example/create", {
      field1: "value",
      field2: 42
    });
    
    if (response.success) {
      console.log("Created:", response.data);
    } else {
      console.error("Error:", response.error);
    }
  };

  return (
    <div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">Error: {error}</p>}
      {data && <p>Data: {JSON.stringify(data)}</p>}
      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}
```

### Working with Solana Web3.js

```typescript
import { 
  getSolanaConnection, 
  isValidSolanaAddress,
  getAccountBalance 
} from "@/lib/solana";

export default function WalletInfo() {
  const [balance, setBalance] = useState<number | null>(null);

  const handleCheckBalance = async (address: string) => {
    if (!isValidSolanaAddress(address)) {
      console.error("Invalid address");
      return;
    }

    const balance = await getAccountBalance(address);
    setBalance(balance);
  };

  return (
    <div>
      {balance !== null && (
        <p>Balance: {balance} SOL</p>
      )}
      <button onClick={() => handleCheckBalance("...")}>
        Check Balance
      </button>
    </div>
  );
}
```

### Styling with Tailwind CSS

```typescript
export function StyledComponent() {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-bold text-gray-900">Title</h2>
      
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-md bg-blue-50 p-4">
          <p className="text-sm font-medium text-blue-900">Section 1</p>
        </div>
        <div className="rounded-md bg-green-50 p-4">
          <p className="text-sm font-medium text-green-900">Section 2</p>
        </div>
      </div>

      <button className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
        Action
      </button>
    </div>
  );
}
```

### Using Lucide React Icons

```typescript
import { 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  TrendingUp,
  Zap 
} from "lucide-react";

export function IconExample() {
  return (
    <div className="flex gap-4">
      <AlertCircle className="h-5 w-5 text-red-600" />
      <CheckCircle className="h-5 w-5 text-green-600" />
      <Clock className="h-5 w-5 text-yellow-600" />
      <TrendingUp className="h-5 w-5 text-blue-600" />
      <Zap className="h-5 w-5 text-purple-600" />
    </div>
  );
}
```

---

## Testing

### Backend Unit Tests

```python
# backend/tests/test_routes.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_market_data():
    response = client.get("/api/market/data/test-token")
    assert response.status_code in [200, 404]
```

Run tests:
```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/
```

### Frontend Component Tests

```typescript
// src/__tests__/example.test.tsx
import { render, screen } from "@testing-library/react";
import { Example } from "@/components/example";

describe("Example Component", () => {
  it("renders title", () => {
    render(<Example title="Test Title" />);
    expect(screen.getByText("Test Title")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(<Example title="Title" description="Test desc" />);
    expect(screen.getByText("Test desc")).toBeInTheDocument();
  });
});
```

Run tests:
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest
npm test
```

---

## Debugging

### Backend Debugging

#### Using print debugging:
```python
logger.debug(f"Variable value: {variable}")
```

#### Using Python debugger:
```python
import pdb
pdb.set_trace()  # Execution will pause here
```

#### VS Code debugger:
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend Debugging

#### Browser DevTools:
```typescript
console.log("Debug:", variable);
console.error("Error:", error);
console.time("operation");
// ... code ...
console.timeEnd("operation");
```

#### VS Code debugger:
```json
// .vscode/launch.json
{
  "type": "chrome",
  "request": "launch",
  "name": "Next.js",
  "url": "http://localhost:3000",
  "webRoot": "${workspaceFolder}",
  "sourceMapPathOverride": {
    "webpack://_N_E/*": "${webRoot}/.next/*"
  }
}
```

---

## Code Style & Linting

### Backend (Python)

```bash
# Install linters
pip install black flake8 isort

# Format code
black backend/

# Check style
flake8 backend/

# Sort imports
isort backend/
```

### Frontend (TypeScript/JavaScript)

```bash
# Format code
npm run format

# Lint code
npm run lint

# Fix linting errors
npm run lint -- --fix
```

---

## Git Workflow

### Branch Naming
```
feature/add-market-analysis
fix/solana-connection-error
docs/update-readme
refactor/optimize-api-client
```

### Commit Messages
```
feat: Add market data endpoint
fix: Resolve Solana RPC timeout
docs: Update deployment guide
refactor: Simplify AI engine wrapper
```

### Creating a Pull Request
```bash
git checkout -b feature/new-feature
# Make changes
git add .
git commit -m "feat: Add new feature"
git push origin feature/new-feature
# Create PR on GitHub
```

---

## Common Tasks

### Adding a New API Key

1. Add to `.env.example`:
```bash
NEW_API_KEY=your-key-here
```

2. Add to `config/settings.py`:
```python
new_api_key: str = ""
```

3. Use in code:
```python
from config import settings
api_key = settings.new_api_key
```

### Running Backend with Different Settings

```bash
# Development
ENVIRONMENT=development DEBUG=true uvicorn main:app --reload

# Production
ENVIRONMENT=production DEBUG=false uvicorn main:app --workers 4
```

### Building Frontend for Production

```bash
npm run build
npm start  # Local production server
```

---

## Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Solana Docs](https://docs.solana.com/)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)

### Learning Resources
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [React Hooks](https://react.dev/reference/react/hooks)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for syntax errors
python -m py_compile backend/main.py
```

### Frontend build errors
```bash
# Clear cache
rm -rf .next node_modules package-lock.json

# Reinstall dependencies
npm install

# Run build
npm run build
```

### API connection issues
```bash
# Backend running?
curl http://localhost:8000/health

# CORS enabled?
curl -H "Origin: http://localhost:3000" http://localhost:8000/health -v

# Check env vars
echo $NEXT_PUBLIC_API_URL
```

---

**Happy Developing! 🚀**

For issues, questions, or contributions, please open an issue or PR on GitHub.
