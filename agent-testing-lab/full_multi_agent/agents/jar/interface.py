"""
Jar Manager Agent Interface for Orchestrator
===========================================

Clean interface for the orchestrator to call the jar manager agent.
"""

from typing import Dict, Any, List
from . import main as jar_main

# --- Agent Interface Definition ---

class JarManagerInterface:
    """Interface for the Jar Manager Agent."""

    agent_name = "jar_manager"

    def process_task(self, task: str, conversation_history: List) -> Dict[str, Any]:
        """
        Processes a jar management task.

        Args:
            task: The user's request.
            conversation_history: The history of the conversation.

        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        # Delegate the call directly to the agent's main processing logic
        return jar_main.process_task(task, conversation_history)

def get_agent_interface() -> JarManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return JarManagerInterface() 