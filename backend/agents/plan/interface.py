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

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, 
                          conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a financial planning task with standardized return format.

        Args:
            task: The user's budget planning request
            db: Database connection for user data (required)
            user_id: User identifier for data isolation (required)
            conversation_history: The history of the conversation

        Returns:
            Dict containing:
            - response: Agent response text
            - agent_lock: Agent name if lock required (plan agent typically requires lock during multi-stage process)
            - tool_calls: List of tool calls made during processing
            - plan_stage: Current stage of the plan process ("1", "2", "3")
            - error: Boolean indicating if an error occurred
            
        Raises:
            ValueError: For invalid input parameters or processing errors
        """
        # Validate inputs using base class validation
        self.validate_inputs(task, db, user_id)
        
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Call the plan agent main process_task
            result = await process_task(task, db, user_id, conversation_history)
            
            # Validate result format
            if not isinstance(result, dict) or "response" not in result:
                raise ValueError("Plan agent returned invalid response format")
            
            # Extract response and follow-up information
            agent_output = result["response"]
            requires_follow_up = result.get("requires_follow_up", False)
            current_plan_stage = result.get("plan_stage", "1")  # Get plan_stage from result, default to "1"
            
            # Plan agent typically requires lock during multi-stage process
            # Only release lock when plan is complete (stage 3 and no follow-up)
            agent_lock = "plan" if requires_follow_up or current_plan_stage in ["1", "2"] else None
            
            # Return standardized dict format for orchestrator
            return {
                "response": agent_output,
                "agent_lock": agent_lock,
                "tool_calls": result.get("tool_calls", []),
                "plan_stage": current_plan_stage,  # Renamed from stage
                "error": False
            }
            
        except Exception as e:
            # Handle any plan agent processing errors
            error_message = f"Plan agent failed: {str(e)}"
            
            # Return error in standardized format
            return {
                "response": f"I encountered an error while processing your financial planning request: {str(error_message)}",
                "agent_lock": None,
                "tool_calls": [],
                "plan_stage": "1",  # Default to stage 1 on error
                "error": True
            }

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