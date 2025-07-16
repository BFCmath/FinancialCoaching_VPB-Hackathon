# agents/base_worker.py (shared base class, place in agents/ directory or appropriate shared location)

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.models.conversation import ConversationTurnInDB

class BaseWorkerInterface(ABC):
    """
    Base interface for all worker agents.
    
    All worker agents must inherit from this class and implement process_task.
    This ensures consistent API for the orchestrator (polymorphism).
    
    STANDARDIZED RETURN FORMAT:
    All agents must return Dict[str, Any] with response data.
    The orchestrator will create ConversationTurnInDB objects based on this data.
    """
    
    agent_name: str  # Must be set in subclass as class attribute

    @abstractmethod
    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str,
                          conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes the task and returns data for orchestrator to create conversation turn.
        
        Args:
            task: User request or sub-task
            db: Database connection (required for all agents)
            user_id: User identifier (required for data isolation)
            conversation_history: Filtered or full history for context
            
        Returns:
            Dict containing:
            - response: The agent's response text
            - requires_follow_up: Boolean indicating if agent needs another turn
            - agent_lock: Optional agent name to lock conversation to
            - plan_stage: Optional plan stage for multi-stage workflows
            - tool_calls: List of tool calls made during processing
            - error: Optional boolean indicating if an error occurred
            
        Raises:
            ValueError: For invalid input parameters or processing errors
        """
        pass

    def get_capabilities(self) -> Optional[List[str]]:
        """
        Optional: Returns list of agent capabilities for orchestrator discovery.
        """
        return None
    
    def validate_inputs(self, task: str, db: AsyncIOMotorDatabase, user_id: str) -> None:
        """
        Common input validation for all agents.
        
        Raises:
            ValueError: For invalid input parameters
        """
        if not task or not task.strip():
            raise ValueError("Task cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")