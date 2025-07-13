# agents/classifier/interface.py (updated to inherit from BaseWorkerInterface)

from typing import Dict, Any, List, Optional
from agents.base_worker import BaseWorkerInterface
from . import main as classifier_main
from database import ConversationTurn

class ClassifierInterface(BaseWorkerInterface):
    """Interface for the Transaction Classifier Agent."""

    agent_name = "classifier"

    def process_task(self, task: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
        """
        Processes a transaction classification task.
        
        Args:
            task: The user's request.
            conversation_history: The history of the conversation.
                
        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        return classifier_main.process_task(task, conversation_history)

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Categorize transactions into jars",
            "Handle ambiguous inputs with follow-up"
        ]

def get_agent_interface() -> ClassifierInterface:
    """Factory function to get an instance of the agent interface."""
    return ClassifierInterface()