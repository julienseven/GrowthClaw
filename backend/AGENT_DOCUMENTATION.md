# $GROWTH Transaction Agent Documentation

## Overview

The Transaction Agent is the core autonomous system that monitors Solana wallets, processes incoming transactions, extracts project metadata from memo instructions, and generates viral marketing content.

### Key Capabilities

- **Real-time Monitoring**: Continuously polls target wallet for new transactions
- **Smart Filtering**: Only processes SOL transfers meeting minimum threshold (0.05 SOL)
- **Memo Parsing**: Robust extraction of "ProjectName | Description" from Solana Memo Program
- **AI Marketing**: Generates viral, high-energy marketing posts under 280 characters
- **Error Resilience**: Comprehensive error handling with automatic recovery
- **Production Ready**: Async/await with rate limiting, timeouts, and monitoring

---

## Architecture

### Component Hierarchy

```
TransactionAgent (Main Orchestrator)
├── SolanaClient (Blockchain Interaction)
│   ├── RPC Connection Management
│   ├── Transaction Fetching
│   └── Rate Limiting
│
├── AIEngine (Marketing Generation)
│   ├── Marketing Post Generation
│   ├── Sentiment Analysis
│   └── Strategy Recommendations
│
├── MemoProcessor (Data Parsing)
│   ├── Memo Extraction
│   ├── Format Validation
│   └── Size Constraints
│
└── ResultManager (Storage & Analytics)
    ├── Result Caching
    ├── Statistics
    └── Persistence Layer
```

### Data Flow

```
Wallet Polling
    ↓
Transaction Signature Retrieval
    ↓
Transaction Fetch & Validation
    ↓
Memo Extraction
    ↓
Format Parsing (ProjectName | Description)
    ↓
AI Marketing Post Generation
    ↓
Result Storage & Analytics
```

---

## Configuration

### Required Environment Variables

```bash
# Wallet to monitor (REQUIRED for agent to run)
TARGET_TOKEN_ADDRESS=<solana_wallet_address>

# OpenAI API Key (REQUIRED for marketing posts)
OPENAI_API_KEY=sk-<your_key>

# Solana RPC Endpoint
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### Optional Configuration

```bash
# Polling interval in seconds (default: 30)
AGENT_POLLING_INTERVAL=30

# Minimum SOL transfer to process (default: 0.05)
AGENT_MIN_SOL_TRANSFER=0.05

# Max cached results in memory (default: 10000)
AGENT_MAX_CACHED_RESULTS=10000

# Solana network
SOLANA_NETWORK=mainnet-beta  # or devnet, testnet

# OpenAI model and settings
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=200
OPENAI_TEMPERATURE=0.7
```

---

## Usage Guide

### 1. Basic Usage

```python
import asyncio
from config import settings
from agents.transaction_agent import TransactionAgent
from core.solana_client import SolanaClient
from core.ai_engine import AIEngine

async def main():
    # Initialize clients
    solana_client = SolanaClient()
    ai_engine = AIEngine()
    
    # Create agent
    agent = TransactionAgent(
        wallet_address="<target_wallet>",
        solana_client=solana_client,
        ai_engine=ai_engine,
        polling_interval=30,
    )
    
    # Run agent
    await agent.start()

asyncio.run(main())
```

### 2. With Result Manager

```python
from services import ResultManager

result_manager = ResultManager()

# Agent processes transactions
# Results are stored and accessible
results = result_manager.get_results(limit=100)
stats = result_manager.get_statistics()

# Get marketing posts
posts = result_manager.get_marketing_posts(limit=50)

# Filter by project
project_results = result_manager.get_results_by_project("ProjectName")
```

### 3. Integration with FastAPI

```python
# In main.py - the lifespan context manager handles:
# 1. Initializing the agent on startup
# 2. Running it in background
# 3. Graceful shutdown on exit

# Results accessible via API:
# GET /api/transactions/results
# GET /api/transactions/agent/status
# GET /api/transactions/statistics
```

---

## Memo Format Specification

### Required Format

```
ProjectName | ProjectDescription
```

### Format Rules

- **Delimiter**: Pipe character `|` (required, appears once)
- **Project Name**: 2-100 characters
- **Description**: 5-1000 characters
- **Total Memo**: Maximum 566 bytes (Solana limit)

### Examples

✓ **Valid**:
```
SolanaAI | AI-powered trading bot for Solana blockchain
DeFiProtocol | Decentralized finance with yield farming
GameToken | Play-to-earn gaming on Solana
```

✗ **Invalid**:
```
NoDelimiter  # Missing |
| EmptyName  # Empty project name
ProjectOnly | # Empty description
```

---

## Solana Integration

### Transaction Polling

The agent uses the Solana RPC API to:

1. **Get Signatures**: Fetch recent transaction signatures for wallet
2. **Fetch Transactions**: Retrieve full transaction data
3. **Parse Instructions**: Extract Memo Program instructions

### Key RPC Calls

```python
# Get recent signatures
await solana_client.get_signatures_for_address(
    address="wallet_address",
    limit=10,
)

# Get full transaction with memo
await solana_client.get_transaction(signature)
```

### Rate Limiting

The client implements rate limiting:
- Max 40 requests per 10 seconds (public RPC limit)
- Automatic backoff when approaching limit
- Resumable polling after rate limit

---

## AI Marketing Post Generation

### Generation Process

1. **Input Validation**: Check project name/description
2. **Prompt Construction**: Build detailed OpenAI prompt
3. **API Call**: Request gpt-4o-mini response
4. **Output Validation**: Ensure under 280 characters
5. **Trimming**: Automatically truncate if needed

### Post Characteristics

- **Length**: Under 280 characters (tweet-like)
- **Tone**: Viral, high-energy, crypto-native
- **Style**: Authentic marketing without sounding like bot
- **Emojis**: 1-2 relevant emojis
- **No Hashtags**: Unless essential

### Example Output

Input:
```
Name: SolanaAI
Description: AI-powered trading bot for Solana blockchain
```

Output:
```
🤖 Meet SolanaAI - the trading bot that thinks faster than the market moves. 
ML-powered analysis on Solana = next-level gains. Time to let AI do the work 🚀
```

---

## Error Handling

### Transaction Processing Errors

The agent handles:

| Error | Handling | Result |
|-------|----------|--------|
| Invalid address | Validation before use | Logged, skipped |
| RPC timeout | Exponential backoff | Retry next cycle |
| Rate limit | Automatic delay | Resume after window |
| Missing memo | Skip transaction | No error recorded |
| Invalid memo format | Parse error logged | Stored as error |
| SOL below minimum | Filtered out | Not processed |
| Memo too large | Size validation | Rejected |
| Null bytes in memo | Character validation | Rejected |

### API Error Handling

OpenAI API errors:
- **RateLimitError**: Automatic retry with exponential backoff
- **APIConnectionError**: Logged, graceful degradation
- **APIError**: Detailed logging, transaction still stored

---

## Memo Parsing Implementation

### Parsing Steps

```python
# 1. Extract memo from instructions
memo_text = MemoProcessor.extract_memo_from_instructions(instructions)

# 2. Parse format
parsed = MemoProcessor.parse_memo(memo_text)

# 3. Validate extracted data
is_valid, error = MemoProcessor.validate_project_data(name, description)

# 4. Proceed to AI generation
if is_valid:
    post = await ai_engine.generate_viral_marketing_post(name, description)
```

### Validation Constraints

- **Empty Check**: Both name and description required
- **Length Check**: Name 2-100 chars, description 5-1000 chars
- **Character Check**: No null bytes or suspicious patterns
- **Format Check**: Delimiter found and properly split

---

## Result Storage

### Processed Transaction Result

Each result includes:

```python
@dataclass
class ProcessedTransaction:
    signature: str                          # Transaction ID
    timestamp: str                          # Block time (ISO format)
    payer: str                              # Transaction initiator
    lamports_transferred: int               # Amount in lamports
    project_name: str                       # Extracted project name
    project_description: str                # Extracted description
    marketing_post: str                     # Generated marketing post
    post_length: int                        # Length of post
    sentiment: Optional[Dict]               # AI sentiment analysis
    error: Optional[str]                    # Error message if failed
```

### ResultManager Features

```python
# Get paginated results
results = result_manager.get_results(limit=100, offset=0)

# Get recent results
recent = result_manager.get_recent_results(hours=24)

# Get only successful results
successful = result_manager.get_successful_results(limit=50)

# Filter by project
project = result_manager.get_results_by_project("ProjectName")

# Get marketing posts
posts = result_manager.get_marketing_posts(limit=50)

# Get statistics
stats = result_manager.get_statistics()
```

### Statistics

```python
{
    "total_processed": 150,
    "total_successful": 145,
    "total_errors": 5,
    "success_rate": 96.67,
    "avg_post_length": 145,
    "last_processed_time": "2024-01-15T10:30:00"
}
```

---

## API Endpoints

### Agent Status

```
GET /api/transactions/agent/status

Response:
{
    "is_running": true,
    "processed_count": 42,
    "error_count": 2,
    "wallet_address": "11111111111111111111111111111111",
    "last_processed_signature": "5Jk...xyz"
}
```

### Get Results

```
GET /api/transactions/results?limit=100&offset=0

Response:
{
    "results": [...],
    "count": 100,
    "total_processed": 500,
    "success_rate": 94.5
}
```

### Get Recent Results

```
GET /api/transactions/results/recent?hours=24

Response:
{
    "results": [...],
    "count": 42,
    "hours": 24
}
```

### Get Marketing Posts

```
GET /api/transactions/results/marketing-posts?limit=50

Response:
{
    "posts": [
        "🚀 SolanaAI is revolutionizing trading...",
        "💎 DeFiProtocol offers 30% APY...",
        ...
    ],
    "count": 50
}
```

### Get Project Results

```
GET /api/transactions/results/project/ProjectName

Response:
{
    "project": "ProjectName",
    "results": [...],
    "count": 5
}
```

### Get Statistics

```
GET /api/transactions/statistics

Response:
{
    "total_processed": 500,
    "total_successful": 475,
    "total_errors": 25,
    "success_rate": 95.0,
    "avg_post_length": 142,
    "last_processed_time": "2024-01-15T10:30:00"
}
```

---

## Monitoring & Logging

### Log Levels

```
DEBUG: Detailed polling information
INFO: Transaction processing, agent status
WARNING: Rate limits, parsing issues
ERROR: Failed transactions, API errors
```

### Example Log Output

```
2024-01-15 10:30:00 - INFO - Polling wallet: 11111111111...
2024-01-15 10:30:01 - INFO - Found 5 signatures
2024-01-15 10:30:02 - INFO - Processing transaction: 5Jk...xyz
2024-01-15 10:30:03 - INFO - Extracted project: SolanaAI
2024-01-15 10:30:05 - INFO - Generated post: 🚀 SolanaAI is...
2024-01-15 10:30:06 - INFO - ✓ Transaction processed successfully
```

---

## Performance Considerations

### Rate Limiting

- **Solana RPC**: 40 req/10s (public endpoint)
- **OpenAI API**: Varies by plan (handle 429s)
- **Memory**: 10,000 cached results by default

### Optimization Tips

1. **Polling Interval**: Increase for slow networks, decrease for fast markets
2. **Batch Size**: Keep signature fetch at 10-20 per cycle
3. **Caching**: Enable Redis for persistent storage across restarts
4. **Workers**: Use multiple worker processes for production

### Benchmarks

- **Transaction Fetch**: ~500ms per transaction (with RPC latency)
- **Memo Parsing**: <1ms per transaction
- **AI Post Generation**: 1-3 seconds per request
- **Full Pipeline**: ~5 seconds per transaction

---

## Troubleshooting

### Agent Not Starting

```python
# Check configuration
if not settings.target_token_address:
    print("ERROR: TARGET_TOKEN_ADDRESS not configured")

if not settings.openai_api_key:
    print("WARNING: OpenAI disabled, AI features unavailable")

# Check connections
await solana_client.connect()
await ai_engine.validate()
```

### No Transactions Found

```python
# Check wallet has recent activity
signatures = await solana_client.get_signatures_for_address(wallet)

# Verify wallet address format
from utils.validators import is_valid_solana_address
assert is_valid_solana_address(wallet)

# Check network selection
assert settings.solana_network in ["mainnet-beta", "devnet"]
```

### Memo Not Parsing

```python
# Test memo parsing
from agents.transaction_agent import ProjectMetadata
result = ProjectMetadata.from_memo("MyProject | Description")
print(f"Parsed: {result.name if result else 'Failed'}")

# Check memo format
assert "|" in memo_text
assert len(memo_text) <= 566
```

### Slow Performance

```python
# Check rate limiting
if solana_client.request_count >= 40:
    print("Rate limit reached, sleeping...")

# Increase polling interval
agent.polling_interval = 60  # Slower polling

# Enable Redis caching
redis_client = aioredis.from_url(settings.redis_url)
```

---

## Advanced Usage

### Custom Solana Network

```python
# Use devnet for testing
client = SolanaClient(rpc_url="https://api.devnet.solana.com")
agent = TransactionAgent(
    wallet_address=test_wallet,
    solana_client=client,
)
```

### Custom Polling Logic

```python
# Subclass agent for custom behavior
class CustomAgent(TransactionAgent):
    async def _process_transaction(self, signature):
        # Custom processing logic
        result = await super()._process_transaction(signature)
        # Additional processing
        return result
```

### Redis Persistence

```python
# Store results in Redis
await result_manager.persist_to_storage()

# Load from Redis on startup
await result_manager.load_from_storage()
```

---

## Testing

### Example Script

```bash
# Run the example with test data
python -m examples.run_agent_example

# Run with specific wallet (dev)
export TARGET_TOKEN_ADDRESS=<wallet>
export OPENAI_API_KEY=<key>
python -m examples.run_agent_example
```

### Unit Testing

```python
# Test memo parsing
test_memo = "TestProject | This is a test project"
result = ProjectMetadata.from_memo(test_memo)
assert result.name == "TestProject"
assert result.description == "This is a test project"

# Test validation
is_valid, error = validate_project_metadata("Name", "Description")
assert is_valid
```

---

## Future Enhancements

- [ ] Database persistence (PostgreSQL, MongoDB)
- [ ] Redis caching for scalability
- [ ] Multi-wallet monitoring
- [ ] Custom memo formats
- [ ] Transaction execution (responding to transfers)
- [ ] Discord/Twitter bot integration
- [ ] Advanced sentiment analysis
- [ ] Historical analytics dashboard

---

## Support & Debugging

For issues:
1. Check logs: `API_LOG_LEVEL=debug`
2. Verify configuration: `env | grep -E "SOLANA|OPENAI|TARGET"`
3. Test components independently
4. Review error stack traces
5. Check RPC endpoint status

---

**Last Updated**: 2024-01-15  
**Version**: 0.2.0  
**Status**: Production Ready
