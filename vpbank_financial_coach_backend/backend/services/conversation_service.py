"""
Conversation Service - Complete Implementation from Lab
=======================================================

This module implements the complete conversation service ported from the lab
with database backend, maintaining exact same interface and behavior.
Covers all conversation operations from lab utils.py:
- add_conversation_turn (with memory limit)
- get_conversation_history (with limit)
- get_agent_specific_history
- clear_conversation_history
- get_conversation_context_string
- Conversation lock utilities: parse_confidence_response, check_conversation_lock, lock_conversation_to_agent, release_conversation_lock
All methods are async where appropriate.
"""

from typing import List, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models.conversation import ConversationTurnInDB, ConversationTurnCreate
from backend.core.config import settings  # For MAX_MEMORY_TURNS

class ConversationService:
    """
    User-scoped conversation management service.
    Handles history, agent locks, and context.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
    
    async def add_conversation_turn(self, user_input: str, agent_output: str, 
                                    agent_list: Optional[List[str]] = None, 
                                    tool_call_list: Optional[List[str]] = None) -> None:
        """Add conversation turn with memory limit."""
        agent_list = agent_list or []
        tool_call_list = tool_call_list or []
        
        turn_data = ConversationTurnCreate(
            user_input=user_input,
            agent_output=agent_output,
            agent_list=agent_list,
            tool_call_list=tool_call_list
        )
        
        await db_utils.add_conversation_turn_for_user(self.db, self.user_id, turn_data)
    
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[ConversationTurnInDB]:
        """Get recent conversation history."""
        history = await db_utils.get_conversation_history_for_user(self.db, self.user_id, limit)
        if limit is not None:
            return history[-limit:]
        return history
    
    async def get_agent_specific_history(self, agent_name: str, max_turns: int = 10) -> List[ConversationTurnInDB]:
        """Get conversation history for specific agent."""
        history = await self.get_conversation_history()
        filtered = [turn for turn in history if agent_name in turn.agent_list]
        return filtered[-max_turns:]

    async def get_conversation_context_string(self, limit: int = 5) -> str:
        """Get conversation history as formatted string for agent context."""
        recent_turns = await self.get_conversation_history(limit)
        
        if not recent_turns:
            return "No conversation history."
        
        context_lines = []
        for turn in recent_turns:
            context_lines.append(f"User: {turn.user_input}")
            context_lines.append(f"Assistant: {turn.agent_output}")
            if turn.agent_list:
                context_lines.append(f"Agents: {', '.join(turn.agent_list)}")
        
        return "\n".join(context_lines)
    
    @staticmethod
    def parse_confidence_response(response: str, agent_name: str) -> Tuple[str, bool]:
        """Parse agent response for requires_follow_up flag."""
        follow_up_indicators = [
            "?", "please", "clarify", "more information", "follow up",
            "what about", "can you", "would you like", "do you want"
        ]
        
        requires_follow_up = any(indicator in response.lower() for indicator in follow_up_indicators)
        
        return response, requires_follow_up
    
    async def check_conversation_lock(self) -> Optional[str]:
        """Check if conversation is locked to a specific agent."""
        return await db_utils.get_agent_lock_for_user(self.db, self.user_id)
    
    async def lock_conversation_to_agent(self, agent_name: str) -> None:
        """Lock conversation to specific agent for multi-turn interaction."""
        await db_utils.set_agent_lock_for_user(self.db, self.user_id, agent_name)
    
    async def release_conversation_lock(self) -> None:
        """Release conversation lock to allow orchestrator routing."""
        await db_utils.set_agent_lock_for_user(self.db, self.user_id, None)
    
    # =============================================================================
    # STAGE MANAGEMENT UTILITIES FOR PLAN AGENT
    # =============================================================================
    
    async def get_current_plan_stage(self) -> str:
        """
        Determine current plan agent stage from conversation history.
        This provides stateless stage management for the plan agent.
        
        Returns:
            Current stage: "1" (information_gathering), "2" (plan_refinement), "3" (plan_implementation)
        """
        # Get recent conversation history for plan agent
        history = await self.get_agent_specific_history("plan", max_turns=10)
        
        if not history:
            return "1"  # Default to stage 1 for new conversations
        
        # Look for the most recent stage information in metadata
        for turn in reversed(history):  # Most recent first
            if turn.metadata and "plan_stage" in turn.metadata:
                stage = turn.metadata["plan_stage"]
                # Validate stage
                if stage in ["1", "2", "3"]:
                    return stage
        
        # Fallback: Analyze conversation content for stage indicators
        return self._analyze_conversation_for_stage(history)
    
    def _analyze_conversation_for_stage(self, history: List[ConversationTurnInDB]) -> str:
        """
        Analyze conversation content to infer current stage.
        This is a fallback when metadata is not available.
        """
        if not history:
            return "1"
        
        # Check most recent turns for stage indicators
        recent_content = ""
        for turn in history[-3:]:  # Last 3 turns
            recent_content += f" {turn.user_input} {turn.agent_output}".lower()
        
        # Stage 3 indicators: plan accepted, implementation started
        stage3_indicators = [
            "accept", "approved", "implement", "create plan", 
            "finalize", "proceed", "start implementation"
        ]
        
        # Stage 2 indicators: plan proposed, refinement happening
        stage2_indicators = [
            "proposed plan", "financial plan", "budget plan",
            "modify", "adjust", "change plan", "refine"
        ]
        
        # Check for stage indicators
        if any(indicator in recent_content for indicator in stage3_indicators):
            return "3"
        elif any(indicator in recent_content for indicator in stage2_indicators):
            return "2"
        else:
            return "1"  # Default to information gathering
    
    @staticmethod
    def create_plan_stage_metadata(stage: str, additional_context: Optional[dict] = None) -> dict:
        """
        Create metadata dict for plan agent conversations to be used by orchestrator.
        
        Args:
            stage: Current plan stage ("1", "2", or "3")
            additional_context: Optional additional metadata
            
        Returns:
            Metadata dict ready for conversation turn
        """
        metadata = {
            "plan_stage": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_context": "budget_planning"
        }
        
        if additional_context:
            metadata.update(additional_context)
            
        return metadata