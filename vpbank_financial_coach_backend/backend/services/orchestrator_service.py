"""
Orchestrator Service - Unified Orchestrator Support
==================================================

Consolidated service that combines agent orchestration, context management,
and conversation handling for the orchestrator system.
"""

import logging
from typing import Dict, Optional, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from backend.models.conversation import ConversationTurnCreate, ConversationTurnInDB
from backend.utils import db_utils

class OrchestratorService:
    """
    Unified service for orchestrator support, combining functionality from:
    - agent_orchestrator_service.py
    - orchestrator_context_adapter.py
    - conversation_service.py
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """Initialize orchestrator service for specific user."""
        self.db = db
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
    
    async def process_chat_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main chat processing function - the primary interface for orchestrator.
        
        Args:
            message: User's chat message
            context: Optional context data
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Setup user context
            user_context = await self._setup_user_context(context)
            
            # Call backend orchestrator directly (async)
            from backend.agents.orchestrator import main as orchestrator_main
            
            # Get conversation history for context
            conversation_history = await self.get_conversation_history(limit=5)
            
            # Call the orchestrator with full context
            result = await orchestrator_main.process_task_async(
                task=message,
                user_id=self.user_id,
                db=self.db,
                conversation_history=conversation_history
            )
            
            # Store conversation turn
            await self._store_conversation_turn(
                user_input=message,
                agent_output=result.get("response", ""),
                agents_used=result.get("agents_used", []),
                tool_calls=result.get("tool_calls", [])
            )
            
            # Format response for API
            return {
                "response": result.get("response", "No response generated"),
                "success": result.get("success", False),
                "agents_used": result.get("agents_used", []),
                "requires_follow_up": result.get("requires_follow_up", False),
                "metadata": {
                    "user_id": self.user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": user_context
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing chat message: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "success": False,
                "error": str(e),
                "metadata": {
                    "user_id": self.user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _setup_user_context(self, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Setup comprehensive user context for orchestrator."""
        context = {
            "user_id": self.user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Get user's financial context
            jars = await db_utils.get_all_jars_for_user(self.db, self.user_id)
            recent_transactions = await db_utils.get_user_transactions(self.db, self.user_id, limit=5)
            recurring_fees = await db_utils.get_user_recurring_fees(self.db, self.user_id)
            
            context.update({
                "jars_count": len(jars),
                "jar_names": [j.name for j in jars] if jars else [],
                "recent_transactions_count": len(recent_transactions),
                "active_fees_count": len([f for f in recurring_fees if f.is_active])
            })
            
        except Exception as e:
            self.logger.warning(f"Could not load full user context: {e}")
            context["context_load_error"] = str(e)
        
        # Add any additional context provided
        if additional_context:
            context.update(additional_context)
        
        return context
    
    async def get_conversation_history(self, limit: int = 10) -> List[ConversationTurnInDB]:
        """Get recent conversation history for context."""
        try:
            return await db_utils.get_conversation_history(self.db, self.user_id, limit=limit)
        except Exception as e:
            self.logger.warning(f"Could not load conversation history: {e}")
            return []
    
    async def _store_conversation_turn(self, user_input: str, agent_output: str, 
                                     agents_used: List[str], tool_calls: List[str]) -> None:
        """Store conversation turn in database."""
        try:
            conversation_turn = ConversationTurnCreate(
                user_input=user_input,
                agent_output=agent_output,
                agent_list=agents_used,
                tool_call_list=tool_calls
            )
            
            await db_utils.add_conversation_turn(self.db, self.user_id, conversation_turn)
            
        except Exception as e:
            self.logger.error(f"Error storing conversation turn: {e}")
    
    async def clear_conversation_history(self) -> Dict[str, Any]:
        """Clear conversation history for user."""
        try:
            await db_utils.clear_conversation_history(self.db, self.user_id)
            return {
                "status": "success",
                "message": "Conversation history cleared"
            }
        except Exception as e:
            self.logger.error(f"Error clearing conversation history: {e}")
            return {
                "status": "error", 
                "message": f"Failed to clear conversation history: {e}"
            }
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get comprehensive user statistics for orchestrator context."""
        try:
            # Get all user data
            jars = await db_utils.get_all_jars_for_user(self.db, self.user_id)
            transactions = await db_utils.get_user_transactions(self.db, self.user_id, limit=100)
            fees = await db_utils.get_user_recurring_fees(self.db, self.user_id)
            conversation_history = await self.get_conversation_history(limit=50)
            
            # Calculate statistics
            total_jar_allocation = sum(j.percent for j in jars)
            total_spending = sum(t.amount for t in transactions)
            active_fees_total = sum(f.amount for f in fees if f.is_active)
            
            return {
                "user_id": self.user_id,
                "jars": {
                    "count": len(jars),
                    "total_allocation": f"{total_jar_allocation * 100:.1f}%",
                    "names": [j.name for j in jars]
                },
                "transactions": {
                    "count": len(transactions),
                    "total_amount": f"${total_spending:.2f}",
                    "recent_count": len([t for t in transactions if (datetime.utcnow() - t.created_at).days <= 30])
                },
                "fees": {
                    "total": len(fees),
                    "active": len([f for f in fees if f.is_active]),
                    "monthly_total": f"${active_fees_total:.2f}"
                },
                "conversation": {
                    "total_turns": len(conversation_history),
                    "recent_activity": len([t for t in conversation_history if (datetime.utcnow() - t.timestamp).days <= 7])
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            return {
                "user_id": self.user_id,
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
