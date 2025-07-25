from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from backend.models.conversation import ConversationTurnInDB
from .main import process_task

class TransactionFetcherInterface(BaseWorkerInterface):
    """Interface for the Transaction Fetcher Agent with standardized return format."""

    agent_name = "fetcher"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, 
                          conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a transaction retrieval task with standardized return format.
        
        Args:
            task: The user's request
            db: Database connection for user data (required)
            user_id: User identifier for data isolation (required)
            conversation_history: The history of the conversation (unused by this stateless agent)
                
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
            # Call the transaction fetcher main process_task
            result = await process_task(task, db, user_id, conversation_history)
            
            # Validate result format
            if not isinstance(result, dict) or "response" not in result:
                raise ValueError("Transaction fetcher returned invalid response format")
            
            # Extract response and follow-up information
            agent_output = result["response"]
            requires_follow_up = result.get("requires_follow_up", False)
            
            # Determine agent lock based on follow-up requirement (transaction fetcher is stateless, typically no follow-up)
            agent_lock = "fetcher" if requires_follow_up else None
            
            # Return standardized dict format for orchestrator
            return {
                "response": agent_output,
                "agent_lock": agent_lock,
                "tool_calls": result.get("tool_calls", []),
                "error": False
            }
            
        except Exception as e:
            # Handle any transaction fetcher processing errors
            error_message = f"Transaction fetcher agent failed: {str(e)}"
            
            # Return error in standardized format
            return {
                "response": f"I encountered an error while fetching your transaction data: {str(error_message)}",
                "agent_lock": None,
                "tool_calls": [],
                "error": True
            }

    def get_capabilities(self) -> Optional[List[str]]:
        """Returns list of agent capabilities."""
        return [
            "Retrieve transaction history with complex filters",
            "Filter transactions by jar, date, amount, time, or source",
            "Handle multilingual (Vietnamese) transaction queries"
        ]

def get_agent_interface() -> TransactionFetcherInterface:
    """Factory function to get an instance of the agent interface."""
    return TransactionFetcherInterface()