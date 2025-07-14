# agents/plan/interface.py (updated to inherit from BaseWorkerInterface)

from typing import Dict, Any, List, Optional
from agents.base_worker import BaseWorkerInterface
from . import main as advisor_main
from database import ConversationTurn

class BudgetAdvisorInterface(BaseWorkerInterface):
    """Interface for the Budget Advisor Agent."""

    agent_name = "plan"

    def process_task(self, task: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
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

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Financial planning and goals",
            "Savings plans and jar adjustments",
            "Multi-stage advisory process"
        ]

def get_agent_interface() -> BudgetAdvisorInterface:
    """Factory function to get an instance of the agent interface."""
    return BudgetAdvisorInterface()