# agents/classifier/interface.py (updated to inherit from BaseWorkerInterface)

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from . import main as classifier_main
from backend.models.conversation import ConversationTurnInDB

class ClassifierInterface(BaseWorkerInterface):
    """Interface for the Transaction Classifier Agent."""

    agent_name = "classifier"

    def __init__(self, db: AsyncIOMotorDatabase = None, user_id: str = None):
        """Initialize with optional database context."""
        self.db = db
        self.user_id = user_id

    def process_task(self, task: str, conversation_history: List[ConversationTurnInDB]) -> Dict[str, Any]:
        """
        Processes a transaction classification task.
        
        Args:
            task: The user's request.
            conversation_history: The history of the conversation.
                
        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        # Use the synchronous wrapper that handles async internally
        return classifier_main.process_task(task, conversation_history)

    async def process_task_async(self, task: str, conversation_history: List[ConversationTurnInDB]) -> Dict[str, Any]:
        """
        Async version that provides full database functionality.
        
        Args:
            task: The user's request.
            conversation_history: The history of the conversation.
                
        Returns:
            A dictionary containing the response and a flag for follow-up.
        """
        return await classifier_main.process_task_async(task, conversation_history, self.db, self.user_id)

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Categorize transactions into jars",
            "Handle ambiguous inputs with follow-up",
            "Fetch transaction history for context",
            "Provide confidence-based classifications"
        ]

def get_agent_interface(db: AsyncIOMotorDatabase = None, user_id: str = None) -> ClassifierInterface:
    """Factory function to get an instance of the agent interface."""
    return ClassifierInterface(db, user_id)