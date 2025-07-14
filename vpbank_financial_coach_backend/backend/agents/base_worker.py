# agents/base_worker.py (shared base class, place in agents/ directory or appropriate shared location)

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.models.conversation import ConversationTurnInDB

class BaseWorkerInterface(ABC):
    """
    Base interface for all worker agents.
    
    All worker agents must inherit from this class and implement process_task.
    This ensures consistent API for the orchestrator (polymorphism).
    """
    
    agent_name: str  # Must be set in subclass as class attribute

    @abstractmethod
    def process_task(self, task: str, conversation_history: List[ConversationTurnInDB]) -> Dict[str, Any]:
        """
        Processes the task and returns a standardized result.
        
        Args:
            task: User request or sub-task.
            conversation_history: Filtered or full history for context.
            
        Returns:
            Dict with 'response' (str), 'requires_follow_up' (bool), and optional extras.
        """
        pass

    def get_capabilities(self) -> Optional[List[str]]:
        """
        Optional: Returns list of agent capabilities for orchestrator discovery.
        """
        return None