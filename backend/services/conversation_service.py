"""
Conversation Service - Complete Implementation with Error Handling
=================================================================

This module implements the conversation management service with static methods
and comprehensive error handling following the same pattern as other services.
Covers essential conversation operations:
- add_conversation_turn: Add new conversation turns to history
- get_conversation_history: Retrieve conversation history with limits
- get_agent_lock: Check current agent lock status  
- get_plan_stage: Get current plan stage from latest turn
All methods use proper input validation and raise ValueError for errors.
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import conversation_utils
from backend.models.conversation import ConversationTurnInDB

class ConversationService:
    """
    Conversation management service with static methods.
    """
    
    @staticmethod
    async def add_conversation_turn(db: AsyncIOMotorDatabase, user_id: str, 
                                   user_input: str, agent_output: str,
                                   agent_list: Optional[List[str]] = None,
                                   tool_call_list: Optional[List[str]] = None,
                                   agent_lock: Optional[str] = None,
                                   plan_stage: Optional[str] = None) -> ConversationTurnInDB:
        """
        Add a new conversation turn to the database.
        
        Args:
            db: Database connection
            user_id: User identifier
            user_input: User's message
            agent_output: Agent's response
            agent_list: List of agents involved (optional)
            tool_call_list: List of tools called (optional)
            agent_lock: Agent that should lock the conversation (optional)
            plan_stage: Current plan stage (optional)
            
        Returns:
            Created conversation turn
            
        Raises:
            ValueError: For invalid input parameters
        """
        print('agent output:', agent_output)
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not user_input or not user_input.strip():
            raise ValueError("User input cannot be empty")
        if not agent_output:
            raise ValueError("Agent output cannot be empty")
        try: 
            agent_output = str(agent_output).strip()
        except Exception as e:
            raise ValueError(f"Agent output must be a string: {str(e)}")
        
        # Validate agent_list if provided
        if agent_list is not None and not isinstance(agent_list, list):
            raise ValueError("Agent list must be a list")
        
        # Validate tool_call_list if provided
        if tool_call_list is not None and not isinstance(tool_call_list, list):
            raise ValueError("Tool call list must be a list")
        
        # Validate agent_lock if provided
        if agent_lock is not None:
            valid_agents = ["classifier", "jar", "fee", "plan", "fetcher", "knowledge", "orchestrator"]
            if agent_lock not in valid_agents:
                raise ValueError(f"Invalid agent lock '{agent_lock}'. Must be one of: {', '.join(valid_agents)}")
        
        # Validate plan_stage if provided
        if plan_stage is not None and not plan_stage.strip():
            raise ValueError("Plan stage cannot be empty when provided")
        
        # Create turn dictionary
        turn_dict = {
            "user_input": user_input.strip(),
            "agent_output": agent_output,
            "agent_list": agent_list or [],
            "tool_call_list": tool_call_list or []
        }
        
        # Add optional fields
        if agent_lock is not None:
            turn_dict["agent_lock"] = agent_lock
        if plan_stage is not None:
            turn_dict["plan_stage"] = plan_stage.strip()
        
        return await conversation_utils.add_conversation_turn_for_user(db, user_id, turn_dict)
    
    @staticmethod
    async def get_conversation_history(db: AsyncIOMotorDatabase, user_id: str, 
                                     limit: int = 10) -> List[ConversationTurnInDB]:
        """
        Get conversation history for a user.
        
        Args:
            db: Database connection
            user_id: User identifier
            limit: Maximum number of turns to retrieve (default: 10)
            
        Returns:
            List of conversation turns (oldest first)
            
        Raises:
            ValueError: For invalid input parameters
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if limit <= 0:
            raise ValueError("Limit must be greater than 0")
        if limit > 100:
            raise ValueError("Limit cannot exceed 100 turns")
        print("PASS 1.5")
        return await conversation_utils.get_conversation_history_for_user(db, user_id, limit)
    
    @staticmethod
    async def get_agent_lock(db: AsyncIOMotorDatabase, user_id: str) -> Optional[str]:
        """
        Get the current agent lock for a user.
        
        Args:
            db: Database connection
            user_id: User identifier
            
        Returns:
            Agent name that has the lock, or None if no lock
            
        Raises:
            ValueError: For invalid input parameters
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        
        return await conversation_utils.get_agent_lock_for_user(db, user_id)
    
    @staticmethod
    async def get_plan_stage(db: AsyncIOMotorDatabase, user_id: str) -> Optional[str]:
        """
        Get the current plan stage for a user.
        
        Args:
            db: Database connection
            user_id: User identifier
            
        Returns:
            Current plan stage string, or None if no stage set
            
        Raises:
            ValueError: For invalid input parameters
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        
        return await conversation_utils.get_plan_stage_for_user(db, user_id)
    
    @staticmethod
    async def get_latest_turn(db: AsyncIOMotorDatabase, user_id: str) -> Optional[ConversationTurnInDB]:
        """
        Get the most recent conversation turn for a user.
        
        Args:
            db: Database connection
            user_id: User identifier
            
        Returns:
            Latest conversation turn, or None if no turns exist
            
        Raises:
            ValueError: For invalid input parameters
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        
        return await conversation_utils.get_latest_conversation_turn_for_user(db, user_id)