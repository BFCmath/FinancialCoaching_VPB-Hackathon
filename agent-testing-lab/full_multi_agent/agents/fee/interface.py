# agents/fee/interface.py (updated to inherit from BaseWorkerInterface and use process_task)

from typing import Dict, Any, List, Optional
from agents.base_worker import BaseWorkerInterface
from .main import process_task  # Import the unified process_task from main.py
from database import ConversationTurn

class FeeManagerInterface(BaseWorkerInterface):
    """Interface for the Fee Manager Agent."""

    agent_name = "fee"

    def process_task(self, task: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
        """
        Processes a recurring fee management task.
        
        Args:
            task: The user's request.
            conversation_history: The history of the conversation.
                
        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        return process_task(task, conversation_history)

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Manage recurring fees/subscriptions (create, update, delete, list)"
        ]

def get_agent_interface() -> FeeManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return FeeManagerInterface()