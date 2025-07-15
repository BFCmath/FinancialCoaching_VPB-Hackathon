"""
Fee Manager Agent - Main Logic
==============================

Core fee management system using Enhanced Pattern 2 with dependency injection
for production-ready multi-user support.
"""

import os
import sys
import traceback
import inspect
from typing import List, Optional, Dict, Any

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# LLM imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Backend imports
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.models.conversation import ConversationTurnInDB

# Local imports
from .config import config
from .tools import get_all_fee_tools, FeeServiceContainer
from .prompt import build_fee_manager_prompt

class FeeManager:
    """Fee manager that uses Enhanced Pattern 2 with dependency injection for production-ready multi-user support."""
    
    def __init__(self, db: AsyncIOMotorDatabase = None, user_id: str = None):
        """Initialize the agent with LLM, tools, and database context."""
        self.db = db
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.temperature
        )
        
        # Create service container for dependency injection
        if db and user_id:
            self.services = FeeServiceContainer(db, user_id)
            self.tools = get_all_fee_tools(self.services)
        else:
            # Fallback for cases without database context (testing/development)
            self.services = None
            self.tools = []  # Empty tools list for non-production use
            
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def process_request(self, user_query: str, conversation_history: List[ConversationTurnInDB] = None) -> tuple[str, list, bool]:
        """
        Process user request by directly calling appropriate tools with backend database context.
        
        Args:
            user_query: The latest query from the user
            conversation_history: Previous conversation turns for context
            
        Returns:
            Tuple of (tool_result, tool_calls_made, requires_follow_up)
        """
        # Validate that agent is properly configured for production use
        if not self.services or not self.db or not self.user_id:
            return (
                "❌ Error: Fee agent not properly configured. Database and user context required.",
                [],
                False
            )
        
        tool_calls_made = []
        
        try:
            # Build prompt with database context (async following classifier pattern)
            if conversation_history is None:
                conversation_history = []
                
            system_prompt = await build_fee_manager_prompt(
                user_query,
                conversation_history,
                self.db,
                self.user_id,
                is_follow_up=True  # Simplified context check for backend
            )
            
            # Get LLM's tool decision
            response = await self.llm_with_tools.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ])

            if not response.tool_calls:
                if config.debug_mode:
                    print("🤖 Agent failed to call a tool.")
                return "Error: No action was taken.", [], False

            # Execute the chosen tool
            tool_call = response.tool_calls[0]  # Take first tool call
            tool_name = tool_call['name']
            tool_args = tool_call['args']

            if config.debug_mode:
                print(f"🛠️ Using tool: {tool_name}")

            # Find and execute tool
            for tool in self.tools:
                if tool.name == tool_name:
                    tool_calls_made.append(f"{tool_name}(args={tool_args})")
                    if inspect.iscoroutinefunction(tool.func):
                        result = await tool.ainvoke(tool_args)
                    else:
                        result = tool.invoke(tool_args)
                    
                    # If clarification needed, return result and set follow-up flag
                    if tool_name == "request_clarification":
                        return result, tool_calls_made, True
                        
                    # Otherwise return the tool result directly
                    return result, tool_calls_made, False

            return f"Error: Tool {tool_name} not found.", tool_calls_made, False

        except Exception as e:
            if config.debug_mode:
                traceback.print_exc()
            return f"Error: {str(e)}", tool_calls_made, False

async def process_task(task: str, db: AsyncIOMotorDatabase = None, user_id: str = None, conversation_history: Optional[List[ConversationTurnInDB]] = None) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Fee Manager agent with backend database context.
    
    Args:
        task: The user's request or clarification response
        db: Database instance for backend integration (required for production use)
        user_id: User identifier for backend context (required for production use)
        conversation_history: Previous conversation turns for context
        
    Returns:
        Dict containing response and metadata
    """
    # Validate required parameters for production use
    if not db or not user_id:
        return {
            "response": "❌ Error: Database connection and user_id are required for fee agent.",
            "requires_follow_up": False,
            "tool_calls": [],
            "success": False
        }
    
    agent = FeeManager(db=db, user_id=user_id)
    
    # Process request and get tool result
    result, tool_calls_made, requires_follow_up = await agent.process_request(task, conversation_history)

    # Note: Conversation logging handled at API level in backend pattern
    if config.verbose_logging:
        print(f"📝 Fee manager completed task. Follow-up: {requires_follow_up}")

    return {
        "response": result,  # Direct tool result
        "requires_follow_up": requires_follow_up,
        "tool_calls": tool_calls_made,
        "success": "Error" not in result
    }