# agents/fee/interface.py (updated for backend migration with database context)

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from backend.models.conversation import ConversationTurnInDB
from .main import process_task  # Import the unified async process_task

class FeeManagerInterface(BaseWorkerInterface):
    """Interface for the Fee Manager Agent with backend database integration."""

    agent_name = "fee"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a recurring fee management task with backend database context.
        
        Args:
            task: The user's request.
            db: Database instance for backend integration
            user_id: User identifier for database context
            conversation_history: The history of the conversation.
                
        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        if conversation_history is None:
            conversation_history = []
        return await process_task(task, db, user_id, conversation_history)

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Manage recurring fees/subscriptions (create, update, delete, list)"
        ]

def get_agent_interface() -> FeeManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return FeeManagerInterface()