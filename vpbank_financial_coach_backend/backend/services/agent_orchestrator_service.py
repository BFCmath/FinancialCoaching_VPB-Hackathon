"""
Agent Orchestrator Service - Main Interface for Orchestrator Integration
======================================================================

This service provides the main interface between the backend and the orchestrator,
handling async execution, conversation management, and error handling.
"""

import logging
from typing import Dict, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.services.conversation_service import ConversationService
from backend.services.orchestrator_context_adapter import OrchestratorContextAdapter
from backend.models.conversation import ConversationTurnCreate


class AgentOrchestratorService:
    """Main orchestrator service that bridges backend with backend orchestrator."""
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """Initialize orchestrator service for specific user."""
        self.db = db
        self.user_id = user_id
        self.conversation_service = ConversationService(db, user_id)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def process_chat_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main chat processing function - the primary interface.
        
        Args:
            message: User's chat message
            context: Optional context data
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Use context adapter to setup user context
            async with OrchestratorContextAdapter(self.db, self.user_id) as adapter:
                # Call backend orchestrator directly (no need for thread pool since it's async)
                from backend.agents.orchestrator import main as orchestrator_main
                
                # Call the async orchestrator method directly
                result = await orchestrator_main.process_task_async(message, self.user_id, self.db)
                
                # Format response for backend
                return self._format_response(result)
                
        except Exception as e:
            self.logger.error(f"Orchestrator error for user {self.user_id}: {str(e)}")
            return self._handle_error(e)
    
    def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format orchestrator result for backend response."""
        return {
            "response": result.get("response", ""),
            "success": True,
            "requires_follow_up": result.get("requires_follow_up", False),
            "context": {
                "agent_list": result.get("agent_list", ["orchestrator"]),
                "tool_call_list": result.get("tool_call_list", []),
                "error_type": result.get("error_type"),
                "error_details": result.get("error_details")
            }
        }
    
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors with production-appropriate responses."""
        error_response = {
            "response": "I apologize, I encountered an issue processing your request. Please try again.",
            "success": False,
            "requires_follow_up": False,
            "context": {
                "error_type": type(error).__name__,
                "error_details": str(error),
                "agent_list": ["orchestrator"],
                "tool_call_list": []
            }
        }
        
        return error_response
