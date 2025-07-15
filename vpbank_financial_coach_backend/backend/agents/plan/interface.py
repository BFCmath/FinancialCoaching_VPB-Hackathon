"""
Budget Advisor Agent Interface for Orchestrator - Enhanced Pattern 2
==================================================================

Clean interface for the orchestrator to call the budget advisor agent with production-ready multi-user support.

Usage:
    from agents.plan.interface import get_agent_interface
    
    plan_agent = get_agent_interface()
    result = await plan_agent.process_task(task="I want to save for vacation", db=db, user_id="user123")
"""

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from .main import process_task
from backend.models.conversation import ConversationTurnInDB

class BudgetAdvisorInterface(BaseWorkerInterface):
    """Interface for the Budget Advisor Agent with Enhanced Pattern 2."""

    agent_name = "plan"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a financial planning task with Enhanced Pattern 2.

        Args:
            task: The user's budget planning request
            db: Database connection for user data (required)
            user_id: User identifier for data isolation (required)
            conversation_history: The history of the conversation

        Returns:
            A dictionary containing the response and metadata
            Example: {"response": "...", "requires_follow_up": False, "stage": "1"}
        """
        # Validate required parameters for production
        if db is None:
            raise ValueError("Database connection is required for production budget advisor agent")
        if user_id is None:
            raise ValueError("User ID is required for production budget advisor agent")
            
        if conversation_history is None:
            conversation_history = []
            
        return await process_task(task, db, user_id, conversation_history)

    def get_capabilities(self) -> Optional[List[str]]:
        """Returns list of agent capabilities."""
        return [
            "Financial planning and goal setting",
            "Multi-stage budget advisory process", 
            "Savings plans and jar adjustments",
            "Transaction analysis for spending insights",
            "Personalized budget recommendations",
            "Plan creation and adjustment"
        ]

def get_agent_interface() -> BudgetAdvisorInterface:
    """Factory function to get an instance of the agent interface."""
    return BudgetAdvisorInterface()