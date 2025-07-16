"""
Jar Manager Agent Interface for Orchestrator - Standardized Format
================================================================

Standardized interface for the orchestrator to call the jar manager agent.
"""

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from backend.models.conversation import ConversationTurnInDB
from .main import process_task_async

class JarManagerInterface(BaseWorkerInterface):
    """Interface for the Jar Manager Agent with standardized return format."""

    agent_name = "jar"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, 
                          conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a jar management task with standardized return format.
        
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
            # Call the jar main process_task_async
            result = await process_task_async(task, db, user_id, conversation_history)
            
            # Validate result format
            if not isinstance(result, dict) or "response" not in result:
                raise ValueError("Jar manager returned invalid response format")
            
            # Extract response and follow-up information
            agent_output = result["response"]
            requires_follow_up = result.get("requires_follow_up", False)
            
            # Determine agent lock based on follow-up requirement
            agent_lock = "jar" if requires_follow_up else None
            
            # Return standardized dict format for orchestrator
            return {
                "response": agent_output,
                "agent_lock": agent_lock,
                "tool_calls": result.get("tool_calls", []),
                "error": False
            }
            
        except Exception as e:
            # Handle any jar manager processing errors
            error_message = f"Jar manager agent failed: {str(e)}"
            
            # Return error in standardized format
            return {
                "response": f"I encountered an error while managing your jars: {str(error_message)}",
                "agent_lock": None,
                "tool_calls": [],
                "error": True
            }

    def get_capabilities(self) -> Optional[List[str]]:
        """Returns list of agent capabilities."""
        return [
            "Manage budget jars (create, update, delete, list)",
            "Jar rebalancing and adjustments", 
            "Calculate jar allocations and targets",
            "Track jar spending and remaining balances"
        ]

def get_agent_interface() -> JarManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return JarManagerInterface() 