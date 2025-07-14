from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from backend.models.conversation import ConversationTurnInDB
from .main import process_task

class TransactionFetcherInterface(BaseWorkerInterface):
    """Interface for the Transaction Fetcher Agent with backend database integration."""

    agent_name = "fetcher"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, 
                         conversation_history: Optional[List[ConversationTurnInDB]] = None) -> Dict[str, Any]:
        """
        Processes a transaction retrieval task with backend database context.
        
        Args:
            task: The user's retrieval request.
            db: Database instance for backend integration.
            user_id: User identifier for database context.
            conversation_history: Unused by this stateless agent, kept for compatibility.

        Returns:
            A dictionary containing the response (transaction data) and metadata.
        """
        # Delegate the call directly to the agent's main async processing logic
        return await process_task(task, db, user_id, conversation_history)

    def get_capabilities(self) -> Optional[List[str]]:
        """Returns list of agent capabilities."""
        return [
            "Retrieve transaction history with complex filters",
            "Filter transactions by jar, date, amount, time, or source",
            "Handle multilingual (Vietnamese) transaction queries"
        ]

def get_agent_interface() -> TransactionFetcherInterface:
    """Factory function to get an instance of the agent interface."""
    return TransactionFetcherInterface()