"""
Example script demonstrating the TransactionAgent in action.

This shows:
1. How to initialize the agent
2. How to run it with real Solana transactions
3. How to handle results
4. Error handling and recovery

Run with:
    python -m examples.run_agent_example
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from core.solana_client import SolanaClient
from core.ai_engine import AIEngine
from agents.transaction_agent import TransactionAgent, ProjectMetadata
from services import ResultManager
from utils.logger import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = get_logger(__name__)


async def main():
    """Run the example transaction agent."""
    
    # Check configuration
    if not settings.target_token_address:
        logger.error("TARGET_TOKEN_ADDRESS not configured in .env")
        logger.info("Set TARGET_TOKEN_ADDRESS=<your_wallet_address> to run agent")
        return

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not configured - AI features disabled")

    logger.info("=" * 80)
    logger.info("$GROWTH Transaction Agent Example")
    logger.info("=" * 80)

    # Initialize services
    logger.info("\nInitializing services...")
    
    try:
        solana_client = SolanaClient()
        ai_engine = AIEngine() if settings.openai_api_key else None
        result_manager = ResultManager()

        # Initialize agent
        agent = TransactionAgent(
            wallet_address=settings.target_token_address,
            solana_client=solana_client,
            ai_engine=ai_engine,
            polling_interval=10,  # 10 seconds for example
        )

        logger.info(f"Agent initialized for wallet: {settings.target_token_address}")

        # Run agent for a limited time (30 seconds in this example)
        logger.info("\nStarting agent (will run for 30 seconds)...")
        
        agent_task = asyncio.create_task(agent.start())
        
        try:
            # Let it run for 30 seconds
            await asyncio.wait_for(agent_task, timeout=30)
        except asyncio.TimeoutError:
            logger.info("Time limit reached, stopping agent...")
            await agent.stop()
        except asyncio.CancelledError:
            logger.info("Agent cancelled")

        # Get and display results
        logger.info("\n" + "=" * 80)
        logger.info("Agent Execution Results")
        logger.info("=" * 80)

        stats = agent.get_statistics()
        logger.info(f"\nAgent Statistics:")
        logger.info(f"  - Processed Transactions: {stats['processed_count']}")
        logger.info(f"  - Errors: {stats['error_count']}")
        logger.info(f"  - Last Signature: {stats['last_processed_signature']}")

        # Display processed transactions
        if agent.results:
            logger.info(f"\nProcessed {len(agent.results)} transactions:")
            
            for result in agent.results[-5:]:  # Show last 5
                logger.info(f"\n  Transaction: {result.signature[:16]}...")
                logger.info(f"    Project: {result.project_name}")
                logger.info(f"    Description: {result.project_description[:50]}...")
                
                if result.marketing_post:
                    logger.info(f"    Post: {result.marketing_post}")
                    logger.info(f"    Length: {result.post_length} chars")
                
                if result.error:
                    logger.info(f"    Error: {result.error}")
        else:
            logger.info("\nNo transactions processed (may need to check wallet activity)")

    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)


async def test_memo_parsing():
    """Test memo parsing with example memos."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Memo Parsing")
    logger.info("=" * 80)

    test_memos = [
        "MyToken | A revolutionary blockchain-based social platform",
        "DeFiProtocol | Decentralized finance protocol with yield farming",
        "GameToken | Play-to-earn gaming token with NFT integration",
        "Invalid Memo No Delimiter",  # Should fail
        "",  # Should fail
    ]

    for memo in test_memos:
        result = ProjectMetadata.from_memo(memo)
        if result:
            logger.info(f"\n✓ Valid: {memo}")
            logger.info(f"  Name: {result.name}")
            logger.info(f"  Description: {result.description}")
        else:
            logger.info(f"\n✗ Invalid: {memo}")


async def test_marketing_post_generation():
    """Test marketing post generation."""
    if not settings.openai_api_key:
        logger.warning("Skipping post generation test - OpenAI API key not configured")
        return

    logger.info("\n" + "=" * 80)
    logger.info("Testing Marketing Post Generation")
    logger.info("=" * 80)

    try:
        ai_engine = AIEngine()

        test_projects = [
            (
                "SolanaAI",
                "AI-powered trading bot for Solana blockchain with machine learning predictions",
            ),
            (
                "CryptoLend",
                "Decentralized lending protocol offering up to 30% APY on stablecoins",
            ),
            (
                "NFTMarket",
                "Peer-to-peer NFT marketplace with zero fees and instant settlement",
            ),
        ]

        for project_name, description in test_projects:
            logger.info(f"\nGenerating post for: {project_name}")
            
            post = await ai_engine.generate_viral_marketing_post(
                project_name=project_name,
                project_description=description,
                max_length=280,
            )
            
            if post:
                logger.info(f"✓ Post ({len(post)} chars): {post}")
            else:
                logger.info(f"✗ Failed to generate post")

    except Exception as e:
        logger.error(f"Error generating posts: {e}")


async def run_all_examples():
    """Run all example demonstrations."""
    
    # Test memo parsing
    await test_memo_parsing()

    # Test marketing post generation
    await test_marketing_post_generation()

    # Run agent if wallet configured
    if settings.target_token_address:
        logger.info("\nRunning transaction agent with real Solana data...")
        await main()
    else:
        logger.info("\nSkipping agent example - TARGET_TOKEN_ADDRESS not configured")


if __name__ == "__main__":
    logger.info("Starting $GROWTH Agent Examples\n")
    
    try:
        asyncio.run(run_all_examples())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    
    logger.info("\nExample complete!")
