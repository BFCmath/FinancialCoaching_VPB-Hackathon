"""
Fee Manager Agent Interface
===========================

A clean interface for the orchestrator to call the Fee Manager agent.
"""

from typing import Dict, Any, List
from . import main as fee_main

# --- Agent Interface Definition ---

class FeeManagerInterface:
    """Interface for the Fee Manager Agent."""

    agent_name = "fee_manager"

    def process_task(self, task: str, conversation_history: List) -> Dict[str, Any]:
        """
        Processes a recurring fee management task.
        
        Args:
            task: The user's request.
            conversation_history: The history of the conversation.
                
        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        return fee_main.manage_fees(task, conversation_history)

def get_agent_interface() -> FeeManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return FeeManagerInterface() 