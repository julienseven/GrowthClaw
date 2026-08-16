"""
$GROWTH: The Autonomous Marketing Growth Hacker
Main entry point for the FastAPI backend.

Orchestrates:
- Transaction Agent for Solana monitoring
- Result Manager for storing processed transactions
- API routes for agent management
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from agents.transaction_agent import TransactionAgent
from core.solana_client import SolanaClient
from core.ai_engine import AIEngine
from services import ResultManager
from routes import transactions as transaction_routes
from utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Global instances
_transaction_agent: TransactionAgent = None
_result_manager: ResultManager = None
_agent_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    
    Handles:
    - Starting transaction agent on startup
    - Graceful shutdown of agents
    """
    global _transaction_agent, _result_manager, _agent_task

    logger.info("Starting $GROWTH backend...")

    try:
        # Initialize services
        _result_manager = ResultManager()
        
        # Initialize Solana and AI clients
        solana_client = SolanaClient()
        
        try:
            ai_engine = AIEngine()
        except ValueError:
            logger.warning("OpenAI API key not configured - AI features disabled")
            ai_engine = None

        # Initialize transaction agent
        target_wallet = settings.target_token_address
        if target_wallet:
            logger.info(f"Initializing transaction agent for wallet: {target_wallet}")
            
            _transaction_agent = TransactionAgent(
                wallet_address=target_wallet,
                solana_client=solana_client,
                ai_engine=ai_engine,
                polling_interval=30,
            )
            
            # Register agent with routes
            transaction_routes.set_agent(_transaction_agent, _result_manager)
            
            # Start agent in background
            _agent_task = asyncio.create_task(_transaction_agent.start())
            logger.info("Transaction agent started")
        else:
            logger.warning("TARGET_TOKEN_ADDRESS not configured - agent not started")

        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    finally:
        logger.info("Shutting down $GROWTH backend...")
        
        # Stop agent
        if _transaction_agent:
            await _transaction_agent.stop()
            logger.info("Transaction agent stopped")
        
        # Cancel agent task
        if _agent_task:
            _agent_task.cancel()
            try:
                await _agent_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Backend shutdown complete")


# Initialize FastAPI application with lifespan
app = FastAPI(
    title="$GROWTH",
    description="The Autonomous Marketing Growth Hacker on Solana",
    version="0.2.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transaction_routes.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    agent_status = None
    if _transaction_agent:
        agent_status = _transaction_agent.get_statistics()
    
    return {
        "status": "healthy",
        "environment": settings.environment,
        "service": "$GROWTH Backend",
        "version": "0.2.0",
        "agent": agent_status,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "$GROWTH",
        "description": "The Autonomous Marketing Growth Hacker on Solana",
        "version": "0.2.0",
        "environment": settings.environment,
        "features": {
            "transaction_monitoring": _transaction_agent is not None,
            "ai_marketing": _transaction_agent and _transaction_agent.ai_engine is not None,
        },
    }


@app.get("/api/agent/info")
async def get_agent_info():
    """Get information about the running agent."""
    if not _transaction_agent:
        return {"error": "No agent running", "message": "TARGET_TOKEN_ADDRESS not configured"}
    
    return {
        "status": "running" if _transaction_agent.is_running else "stopped",
        "wallet": _transaction_agent.wallet_address,
        "polling_interval": _transaction_agent.polling_interval,
        "statistics": _transaction_agent.get_statistics(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.api_log_level,
    )
