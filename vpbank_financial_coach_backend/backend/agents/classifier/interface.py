# agents/classifier/interface.py (updated to inherit from BaseWorkerInterface)

from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from . import main as classifier_main
from backend.models.conversation import ConversationTurnInDB

class ClassifierInterface(BaseWorkerInterface):
    """Interface for the Transaction Classifier Agent with standardized return format."""

    agent_name = "classifier"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, 
                          conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a transaction classification task with standardized return format.
        
        Args:
            task: The user's request
            db: Database connection for user data (required)
            user_id: User identifier for data isolation (required)
            conversation_history: The history of the conversation
                
        Returns:
            Dict containing:
            - response: Agent response text
            - requires_follow_up: Boolean indicating if agent needs another turn
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
            # Call the classifier main process_task_async
            result = await classifier_main.process_task_async(task, conversation_history, db, user_id)
            
            # Validate result format
            if not isinstance(result, dict) or "response" not in result:
                raise ValueError("Classifier returned invalid response format")
            
            # Extract response and follow-up information
            agent_output = result["response"]
            requires_follow_up = result.get("requires_follow_up", False)
            
            # Determine agent lock based on follow-up requirement
            agent_lock = "classifier" if requires_follow_up else None
            
            # Return standardized dict format for orchestrator
            return {
                "response": agent_output,
                "agent_lock": agent_lock,
                "tool_calls": result.get("tool_calls", []),
                "error": False
            }
            
        except Exception as e:
            # Handle any classifier processing errors
            error_message = f"Classifier agent failed: {str(e)}"
            
            # Return error in standardized format
            return {
                "response": f"I encountered an error while classifying your transaction: {str(error_message)}",
                "agent_lock": None,
                "tool_calls": [],
                "error": True
            }

    def get_capabilities(self) -> Optional[List[str]]:
        return [
            "Categorize transactions into jars",
            "Handle ambiguous inputs with follow-up",
            "Fetch transaction history for context",
            "Provide confidence-based classifications"
        ]

def get_agent_interface() -> ClassifierInterface:
    """Factory function to get an instance of the agent interface."""
    return ClassifierInterface()