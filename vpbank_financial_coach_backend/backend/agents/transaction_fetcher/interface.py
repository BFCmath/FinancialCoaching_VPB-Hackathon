"""
Transaction Fetcher Agent Interface
===================================

Clean interface for the orchestrator or other agents to call the transaction fetcher.
This is a stateless data retrieval service.
"""

from typing import Dict, Any, List
from . import main as fetcher_main

# --- Agent Interface Definition ---

class TransactionFetcherInterface:
    """Interface for the Transaction Fetcher Agent."""

    agent_name = "fetcher"

    def process_task(self, task: str, conversation_history: List) -> Dict[str, Any]:
        """
        Processes a transaction retrieval task.
        
        Args:
            task: The user's retrieval request.
            conversation_history: The history of the conversation (unused, for compatibility).

        Returns:
            A dictionary containing the response (transaction data) and a flag for follow-up (always False).
            Example: {"response": {"data": [...], "description": "..."}, "requires_follow_up": False}
        """
        # Delegate the call directly to the agent's main processing logic
        return fetcher_main.process_task(task, conversation_history)

def get_agent_interface() -> TransactionFetcherInterface:
    """Factory function to get an instance of the agent interface."""
    return TransactionFetcherInterface()

