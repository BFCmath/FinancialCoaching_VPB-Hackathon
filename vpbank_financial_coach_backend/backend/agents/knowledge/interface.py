"""
Knowledge Agent Interface for Orchestrator - Enhanced Pattern 2
================================================================

Clean interface for the orchestrator to call the knowledge agent with production-ready multi-user support.

Usage:
    from agents.knowledge.interface import get_agent_interface
    
    knowledge_agent = get_agent_interface()
    result = knowledge_agent.process_task(task="What is compound interest?", db=db, user_id="user123")
"""

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.agents.base_worker import BaseWorkerInterface
from .main import process_task
from backend.models.conversation import ConversationTurnInDB

class KnowledgeInterface(BaseWorkerInterface):
    """Interface for the Knowledge Agent with Enhanced Pattern 2."""

    agent_name = "knowledge"

    async def process_task(self, task: str, db: AsyncIOMotorDatabase, user_id: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
        """
        Processes a knowledge request task with Enhanced Pattern 2.
        
        Args:
            task: User's knowledge question
            db: Database connection for user data (required)
            user_id: User identifier for data isolation (required)
            conversation_history: The history of the conversation (unused, as knowledge is stateless)
                
        Returns:
            A dictionary containing the response and a flag for follow-up (always False).
            Example: {"response": "...", "requires_follow_up": False}
        """
        # Validate required parameters for production
        if not db:
            raise ValueError("Database connection is required for production knowledge agent")
        if not user_id:
            raise ValueError("User ID is required for production knowledge agent")
            
        if conversation_history is None:
            conversation_history = []
            
        response = await process_task(task, db, user_id)
        return {"response": response, "requires_follow_up": False}

    def get_capabilities(self) -> Optional[List[str]]:
        """Returns list of agent capabilities."""
        return [
            "Financial knowledge questions",
            "App documentation and features",
            "Online search for financial concepts",
            "ReAct reasoning framework",
            "Multi-step information gathering",
            "Comprehensive answer synthesis"
        ]

def get_agent_interface() -> KnowledgeInterface:
    """Factory function to get an instance of the agent interface."""
    return KnowledgeInterface()