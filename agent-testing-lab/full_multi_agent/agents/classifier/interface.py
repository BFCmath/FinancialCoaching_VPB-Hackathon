"""
Transaction Classifier Agent Interface
======================================

A clean interface for the orchestrator to call the Transaction Classifier agent.
"""

from typing import Dict, Any, List
from . import main as classifier_main

# --- Agent Interface Definition ---

class ClassifierInterface:
    """Interface for the Transaction Classifier Agent."""

    agent_name = "transaction_classifier"

    def process_task(self, task: str, conversation_history: List) -> Dict[str, Any]:
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

def get_agent_interface() -> ClassifierInterface:
    """Factory function to get an instance of the agent interface."""
    return ClassifierInterface() 