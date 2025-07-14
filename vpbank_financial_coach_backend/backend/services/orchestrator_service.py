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
            
            return {
                "response": result["response"],
                "requires_follow_up": result.get("requires_follow_up", False),
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Orchestrator error for user {self.user_id}: {str(e)}")
            return {
                "response": f"❌ I encountered an error processing your request: {str(e)}",
                "requires_follow_up": False,
                "success": False
            }
