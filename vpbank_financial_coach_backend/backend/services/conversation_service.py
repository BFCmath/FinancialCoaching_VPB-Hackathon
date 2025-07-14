"""
Conversation Service - User-scoped conversation management
========================================================

This service manages user conversations and agent locks for the orchestrator system.
It bridges backend user data with lab orchestrator expectations.
"""

from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from backend.models.conversation import ConversationTurnBase, ConversationTurnCreate, ConversationTurnInDB
from backend.utils import db_utils


class ConversationService:
    """Service for managing user conversations and agent context."""
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """Initialize conversation service for a specific user."""
        self.db = db
        self.user_id = user_id
    
    async def get_conversation_history(self, limit: int = 10) -> List[ConversationTurnInDB]:
        """Get user's conversation history, limited to recent turns."""
        try:
            # Get conversation history from database using correct function name
            conversations = await db_utils.get_conversation_history_for_user(self.db, self.user_id, limit)
            return conversations
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    async def add_conversation_turn(self, turn_data: ConversationTurnCreate) -> ConversationTurnInDB:
        """Add new conversation turn to user's history."""
        try:
            # Save conversation turn to database using correct function name
            saved_turn = await db_utils.add_conversation_turn_for_user(
                self.db, 
                self.user_id, 
                turn_data
            )
            return saved_turn
        except Exception as e:
            print(f"Error adding conversation turn: {e}")
            raise
    
    async def get_agent_lock(self) -> Optional[str]:
        """Get current agent lock for user."""
        try:
            lock = await db_utils.get_agent_lock_for_user(self.db, self.user_id)
            return lock
        except Exception as e:
            print(f"Error getting agent lock: {e}")
            return None
    
    async def set_agent_lock(self, agent_name: Optional[str]) -> None:
        """Set agent lock for user."""
        try:
            await db_utils.set_agent_lock_for_user(self.db, self.user_id, agent_name)
        except Exception as e:
            print(f"Error setting agent lock: {e}")
            raise
    
    async def filter_agent_history(self, agent_name: str, max_turns: int = 10) -> List[ConversationTurnInDB]:
        """Get conversation history for specific agent."""
        try:
            # Get full history first
            full_history = await self.get_conversation_history(limit=max_turns * 2)  # Get more to filter
            
            # Filter for turns involving the specific agent
            filtered_turns = [
                turn for turn in full_history 
                if agent_name in turn.agent_list
            ]
            
            # Return limited results
            return filtered_turns[:max_turns]
        except Exception as e:
            print(f"Error filtering agent history: {e}")
            return []
    
    async def convert_to_lab_format(self, backend_conversations: List[ConversationTurnInDB]) -> List[Dict[str, Any]]:
        """Convert backend conversation format to lab format."""
        lab_format = []
        
        for conv in backend_conversations:
            lab_turn = {
                "user_input": conv.user_input,
                "agent_output": conv.agent_output,
                "agent_list": conv.agent_list,
                "tool_call_list": conv.tool_call_list,
                "timestamp": conv.timestamp
            }
            lab_format.append(lab_turn)
        
        return lab_format
    
    async def create_conversation_turn_from_result(self, user_input: str, agent_result: Dict[str, Any]) -> ConversationTurnCreate:
        """Create conversation turn from agent result."""
        return ConversationTurnCreate(
            user_input=user_input,
            agent_output=agent_result.get("response", ""),
            agent_list=agent_result.get("agent_list", ["orchestrator"]),
            tool_call_list=agent_result.get("tool_call_list", [])
        )
