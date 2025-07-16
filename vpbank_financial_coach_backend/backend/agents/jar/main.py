"""
Main Jar Manager Agent - Enhanced Pattern 2 Implementation  
==========================================================

LLM-powered jar management system with multi-jar operations support.
Handles jar creation, updates, deletion, and listing with automatic rebalancing.
Enhanced Pattern 2 implementation with dependency injection for production-ready multi-user support.

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> Dict[str, Any]
"""

import sys
import os
import traceback
import inspect
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Backend imports
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.models.conversation import ConversationTurnInDB

from .config import config
from .tools import get_all_jar_tools, JarServiceContainer
from .prompt import build_jar_manager_prompt

class JarManager:
    """Jar manager with Enhanced Pattern 2 implementation for production-ready multi-user support."""
    
    def __init__(self, db: AsyncIOMotorDatabase = None, user_id: str = None):
        """Initialize the agent with LLM, tools, and optional database context."""
        self.db = db
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            google_api_key=config.google_api_key
        )
        
        # Create service container for dependency injection
        if db is None and user_id is None:
            # Fallback for cases without database context (testing/development)
            self.services = None
            self.tools = []  # Empty tools list for non-production use
        else:
            self.services = JarServiceContainer(db, user_id)
            self.tools = get_all_jar_tools(self.services)
            
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
        if self.services is None or self.db is None or self.user_id is None:
            return (
                "❌ Error: Jar agent not properly configured. Database and user context required.",
                [],
                False
            )
        
        tool_calls_made = []
        
        try:
            # Build prompt with database context (async following classifier pattern)
            if conversation_history is None:
                conversation_history = []
                
            system_prompt = await build_jar_manager_prompt(
                user_query,
                conversation_history,
                self.db,
                self.user_id,
                is_follow_up=len(conversation_history) > 0
            )
            
            # Get LLM's tool decision
            response = await self.llm_with_tools.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ])

            if not response.tool_calls:
                print("🤖 Agent failed to call a tool.")
                return "I'm not sure how to handle that jar request. Could you be more specific?", [], False

            # Execute the chosen tool
            tool_call = response.tool_calls[0]  # Take first tool call
            tool_name = tool_call['name']
            tool_args = tool_call['args']

            if config.debug_mode:
                print(f"🛠️ Using tool: {tool_name}")

            # Find and execute tool async
            for tool in self.tools:
                if tool.name == tool_name:
                    tool_calls_made.append(f"{tool_name}(args={tool_args})")
                    result = await tool.ainvoke(tool_args)
                    
                    # If clarification needed, return result and set follow-up flag
                    if tool_name == "request_clarification":
                        return result, tool_calls_made, True
                        
                    # Otherwise return the tool result directly
                    return result, tool_calls_made, False

            return f"Error: Tool {tool_name} not found.", tool_calls_made, False

        except Exception as e:
           
            traceback.print_exc()
            return f"Error: {str(e)}", tool_calls_made, False

async def process_task_async(task: str, db: AsyncIOMotorDatabase = None, user_id: str = None, 
                           conversation_history: Optional[List[ConversationTurnInDB]] = None) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Jar Manager agent with backend database context.
    
    Args:
        task: The user's request or clarification response
        db: Database instance for backend integration (required for production use)
        user_id: User identifier for backend context (required for production use)
        conversation_history: Previous conversation turns for context
        
    Returns:
        Dict containing response and metadata
    """
    # Validate required parameters for production use
    if db is None or user_id is None:
        return {
            "response": "❌ Error: Database connection and user_id are required for jar agent.",
            "requires_follow_up": False,
            "tool_calls": [],
            "success": False
        }
    
    agent = JarManager(db=db, user_id=user_id)
    
    # Process request and get tool result
    result, tool_calls_made, requires_follow_up = await agent.process_request(task, conversation_history)

    # Note: Conversation logging handled at API level in backend pattern
    if config.verbose_logging:
        print(f"📝 Jar manager completed task. Follow-up: {requires_follow_up}")

    return {
        "response": result,  # Direct tool result
        "requires_follow_up": requires_follow_up,
        "tool_calls": tool_calls_made,
        "success": "Error" not in result
    }

def process_task(task: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for backward compatibility.
    
    Note: This version won't have full database functionality.
    Use process_task_async for full features.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, create new thread
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(process_task_async(task, None, None, conversation_history))
                )
                return future.result()
        else:
            # Run in current loop
            return loop.run_until_complete(process_task_async(task, None, None, conversation_history))
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(process_task_async(task, None, None, conversation_history))


# Alias for backward compatibility
process_task = process_task_async
