"""
Agent Orchestrator Service - Enhanced Pattern 2 Simplified Interface
==================================================================

Simplified service that directly calls the Enhanced Pattern 2 orchestrator.
"""

import logging
from typing import Dict, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase


class OrchestratorService:
    """Simplified orchestrator service using Enhanced Pattern 2."""
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """Initialize orchestrator service for specific user."""
        self.db = db
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
    
    async def process_chat_message(self, message: str) -> Dict[str, Any]:
        """
        Main chat processing function - direct interface to Enhanced Pattern 2 orchestrator.
        
        Args:
            message: User's chat message
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Import and call Enhanced Pattern 2 orchestrator directly
            from backend.agents.orchestrator.main import process_task_async
            
            # Call the orchestrator with Enhanced Pattern 2
            result = await process_task_async(message, self.user_id, self.db)
            
            # Check if the response indicates an error
            response_text = result["response"]
            is_error = self._is_error_response(response_text)
            
            return {
                "response": response_text,
                "requires_follow_up": result.get("requires_follow_up", False),
                "success": not is_error
            }
            
        except Exception as e:
            self.logger.error(f"Orchestrator error for user {self.user_id}: {str(e)}")
            return {
                "response": f"❌ I encountered an error processing your request: {str(e)}",
                "requires_follow_up": False,
                "success": False
            }
    
    def _is_error_response(self, response: str) -> bool:
        """
        Detect if a response indicates an error condition.
        
        Args:
            response: The agent response text
            
        Returns:
            True if the response indicates an error, False otherwise
        """
        if not response:
            return True
            
        error_indicators = [
            "❌",
            "Error",
            "could not provide a complete answer within the allowed steps",
            "Agent loop completed without a final answer",
            "Failed to process"
        ]
        
        response_lower = response.lower()
        for indicator in error_indicators:
            if indicator.lower() in response_lower:
                return True
                
        return False
