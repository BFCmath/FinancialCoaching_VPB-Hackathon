# agents/fee/interface.py (updated for backend migration with database context)

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from backend.models.conversation import ConversationTurnInDB
from .main import process_task  # Import the unified async process_task

class FeeManagerInterface(BaseWorkerInterface):
    """Interface for the Fee Manager Agent with standardized return format."""

    agent_name = "fee"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, 
                          conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a recurring fee management task with standardized return format.
        
        Args:
            task: The user's request
            db: Database connection for user data (required)
            user_id: User identifier for data isolation (required)
            conversation_history: The history of the conversation
                
        Returns:
            Dict containing:
            - response: Agent response text
            - agent_lock: Agent name if lock required, None otherwise  
            - tool_calls: List of tool calls made during processing
            - error: Boolean indicating if an error occurred
            
        Raises:
            ValueError: For invalid input parameters or processing errors
        """
        # Validate inputs using base class validation
        self.validate_inputs(task, db, user_id)
        
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Call the fee main process_task
            result = await process_task(task, db, user_id, conversation_history)
            
            # Validate result format
            if not isinstance(result, dict) or "response" not in result:
                raise ValueError("Fee manager returned invalid response format")
            
            # Extract response and follow-up information
            agent_output = result["response"]
            requires_follow_up = result.get("requires_follow_up", False)
            
            # Determine agent lock based on follow-up requirement
            agent_lock = "fee" if requires_follow_up else None
            
            # Return standardized dict format for orchestrator
            return {
                "response": agent_output,
                "agent_lock": agent_lock,
                "tool_calls": result.get("tool_calls", []),
                "error": False
            }
            
        except Exception as e:
            # Handle any fee manager processing errors
            error_message = f"Fee manager agent failed: {str(e)}"
            
            # Return error in standardized format
            return {
                "response": f"I encountered an error while managing your fees: {str(error_message)}",
                "agent_lock": None,
                "tool_calls": [],
                "error": True
            }

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Manage recurring fees/subscriptions (create, update, delete, list)"
        ]

def get_agent_interface() -> FeeManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return FeeManagerInterface()