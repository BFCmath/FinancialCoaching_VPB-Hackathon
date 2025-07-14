# agents/classifier/interface.py (updated to inherit from BaseWorkerInterface)

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from . import main as classifier_main
from backend.models.conversation import ConversationTurnInDB

class ClassifierInterface(BaseWorkerInterface):
    """Interface for the Transaction Classifier Agent with Enhanced Pattern 2."""

    agent_name = "classifier"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a transaction classification task with Enhanced Pattern 2.
        
        Args:
            task: The user's request.
            db: Database connection for user data (required)
            user_id: User identifier for data isolation (required)
            conversation_history: The history of the conversation.
                
        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        # Validate required parameters for production
        if not db:
            raise ValueError("Database connection is required for production classifier agent")
        if not user_id:
            raise ValueError("User ID is required for production classifier agent")
            
        if conversation_history is None:
            conversation_history = []
            
        return await classifier_main.process_task_async(task, conversation_history, db, user_id)

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Categorize transactions into jars",
            "Handle ambiguous inputs with follow-up",
            "Fetch transaction history for context",
            "Provide confidence-based classifications"
        ]

def get_agent_interface() -> ClassifierInterface:
    """Factory function to get an instance of the agent interface."""
    return ClassifierInterface()