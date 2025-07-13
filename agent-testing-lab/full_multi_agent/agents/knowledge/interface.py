"""
Knowledge Agent Interface for Orchestrator
==========================================

Clean interface for the orchestrator to call the knowledge agent.

Usage:
    from agents.knowledge.interface import get_agent_interface
    
    knowledge_agent = get_agent_interface()
    result = knowledge_agent.process_task(task="What is compound interest?")
"""

from typing import Dict, Any, List, Optional
from agents.base_worker import BaseWorkerInterface
from .main import get_knowledge
from database import ConversationTurn

class KnowledgeInterface(BaseWorkerInterface):
    """Interface for the Knowledge Agent."""

    agent_name = "knowledge"

    def process_task(self, task: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
        """
        Processes a knowledge request task.
        
        Args:
            task: User's knowledge question
            conversation_history: The history of the conversation (unused, as knowledge is stateless).
                
        Returns:
            A dictionary containing the response and a flag for follow-up (always False).
            Example: {"response": "...", "requires_follow_up": False}
        """
        response = get_knowledge(task)
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