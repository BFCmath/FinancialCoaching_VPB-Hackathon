"""
Budget Advisor Agent Interface
==============================

Clean interface for the orchestrator to call the Budget Advisor agent.
"""

from typing import Dict, Any, List
from . import main as advisor_main

class BudgetAdvisorInterface:
    """Interface for the Budget Advisor Agent."""

    agent_name = "budget_advisor"

    def process_task(self, task: str, conversation_history: List) -> Dict[str, Any]:
        """
        Processes a financial planning task.

        Args:
            task: The user's request.
            conversation_history: The history of the conversation.

        Returns:
            A dictionary containing the response and a flag for follow-up.
            Example: {"response": "...", "requires_follow_up": False}
        """
        return advisor_main.process_task(task, conversation_history)

def get_agent_interface() -> BudgetAdvisorInterface:
    """Factory function to get an instance of the agent interface."""
    return BudgetAdvisorInterface()