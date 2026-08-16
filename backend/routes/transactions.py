"""
Transaction API routes.

Endpoints for managing and monitoring the transaction agent.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agents.transaction_agent import TransactionAgent
from services import ResultManager
from models.schemas import TransactionResult, AgentStatus

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

# Global agent instance (will be initialized via dependency injection)
_transaction_agent: Optional[TransactionAgent] = None
_result_manager: Optional[ResultManager] = None


def set_agent(agent: TransactionAgent, result_manager: ResultManager):
    """Set the global agent instance."""
    global _transaction_agent, _result_manager
    _transaction_agent = agent
    _result_manager = result_manager


@router.get("/agent/status")
async def get_agent_status() -> AgentStatus:
    """
    Get the current status of the transaction agent.

    Returns:
        Agent status including running state, statistics, etc.
    """
    if not _transaction_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    stats = _transaction_agent.get_statistics()
    return AgentStatus(
        is_running=stats["is_running"],
        processed_count=stats["processed_count"],
        error_count=stats["error_count"],
        wallet_address=stats["wallet"],
        last_processed_signature=stats["last_processed_signature"],
    )


@router.get("/results")
async def get_transaction_results(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    Get processed transaction results.

    Args:
        limit: Number of results to return (1-1000)
        offset: Starting offset for pagination

    Returns:
        List of processed transaction results
    """
    if not _result_manager:
        raise HTTPException(status_code=503, detail="Result manager not initialized")

    results = _result_manager.get_results(limit=limit, offset=offset)
    stats = _result_manager.get_statistics()

    return {
        "results": results,
        "count": len(results),
        "total_processed": stats.get("total_processed", 0),
        "success_rate": stats.get("success_rate", 0),
    }


@router.get("/results/recent")
async def get_recent_results(hours: int = Query(24, ge=1, le=720)) -> dict:
    """
    Get recently processed transactions.

    Args:
        hours: Look back N hours (1-720)

    Returns:
        Recent transaction results
    """
    if not _result_manager:
        raise HTTPException(status_code=503, detail="Result manager not initialized")

    results = _result_manager.get_recent_results(hours=hours)
    return {
        "results": results,
        "count": len(results),
        "hours": hours,
    }


@router.get("/results/marketing-posts")
async def get_marketing_posts(limit: int = Query(50, ge=1, le=500)) -> dict:
    """
    Get generated marketing posts.

    Args:
        limit: Maximum posts to return

    Returns:
        List of marketing posts
    """
    if not _result_manager:
        raise HTTPException(status_code=503, detail="Result manager not initialized")

    posts = _result_manager.get_marketing_posts(limit=limit)
    return {
        "posts": posts,
        "count": len(posts),
    }


@router.get("/results/project/{project_name}")
async def get_project_results(project_name: str) -> dict:
    """
    Get all results for a specific project.

    Args:
        project_name: Name of the project to filter

    Returns:
        Results for that project
    """
    if not _result_manager:
        raise HTTPException(status_code=503, detail="Result manager not initialized")

    results = _result_manager.get_results_by_project(project_name)
    return {
        "project": project_name,
        "results": results,
        "count": len(results),
    }


@router.get("/statistics")
async def get_statistics() -> dict:
    """
    Get aggregate statistics about transaction processing.

    Returns:
        Statistics dictionary
    """
    if not _result_manager:
        raise HTTPException(status_code=503, detail="Result manager not initialized")

    return _result_manager.get_statistics()


@router.post("/results/clear")
async def clear_results() -> dict:
    """
    Clear all cached results.

    WARNING: This deletes all in-memory results.

    Returns:
        Number of results cleared
    """
    if not _result_manager:
        raise HTTPException(status_code=503, detail="Result manager not initialized")

    count = _result_manager.clear_results()
    return {
        "cleared": count,
        "message": f"Cleared {count} results",
    }
