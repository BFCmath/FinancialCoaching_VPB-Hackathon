"""
Jar Manager Agent Interface for Orchestrator - Enhanced Pattern 2
================================================================

Enhanced Pattern 2 interface for the orchestrator to call the jar manager agent.
"""

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from backend.models.conversation import ConversationTurnInDB
from .main import process_task_async

class JarManagerInterface(BaseWorkerInterface):
    """Enhanced Pattern 2 interface for the Jar Manager Agent."""

    agent_name = "jar"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a jar management task with Enhanced Pattern 2.

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
            
        # Delegate to the Enhanced Pattern 2 main function
        return await process_task_async(task, db, user_id, conversation_history)

    def get_capabilities(self) -> Optional[List[str]]:
        """Returns list of agent capabilities."""
        return [
            "Manage budget jars (create, update, delete, list)",
            "Jar rebalancing and adjustments", 
            "Calculate jar allocations and targets",
            "Track jar spending and remaining balances"
        ]

def get_agent_interface() -> JarManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return JarManagerInterface() 