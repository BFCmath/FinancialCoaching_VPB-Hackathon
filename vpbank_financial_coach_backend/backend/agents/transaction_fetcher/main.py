"""
Transaction Fetcher Agent - Backend Migration
============================================

Main agent for retrieving transaction history using intelligent tool selection.
Pure data retrieval service - no analysis or conversation state.
Migrated from lab to backend with database integration following classifier pattern.

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> Dict[str, Any]
"""

import sys
import os
import traceback
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Backend imports (following classifier pattern)
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.models.conversation import ConversationTurnInDB
from backend.services.adapters import configure_transaction_fetcher_services

from .config import config
from .tools import get_all_transaction_tools
from .prompt import build_history_fetcher_prompt

class TransactionFetcher:
    """Transaction fetcher with backend database integration following classifier pattern."""
    
    def __init__(self, db: AsyncIOMotorDatabase = None, user_id: str = None):
        """Initialize the agent with LLM, tools, and optional database context."""
        self.db = db
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            google_api_key=config.google_api_key
        )
        self.tools = get_all_transaction_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Configure services if database context is provided (following classifier pattern)
        if db and user_id:
            configure_transaction_fetcher_services(db, user_id)

    async def process_request(self, user_query: str, conversation_history: List[ConversationTurnInDB] = None) -> tuple[str, list, bool]:
        """
        Process user request by directly calling appropriate tools with backend database context.
        
        Args:
            user_query: The latest query from the user
            conversation_history: Previous conversation turns for context
            
        Returns:
            Tuple of (tool_result, tool_calls_made, requires_follow_up)
        """
        tool_calls_made = []
        
        try:
            # Build prompt with database context (async following classifier pattern)
            if conversation_history is None:
                conversation_history = []
                
            system_prompt = await build_history_fetcher_prompt(
                user_query,
                conversation_history,
                self.db,
                self.user_id
            )
            
            # Get LLM's tool decision
            response = self.llm_with_tools.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ])

            if not response.tool_calls:
                if config.debug_mode:
                    print("🤖 Agent failed to call a tool.")
                return "I couldn't find specific transaction data. Could you be more specific about what transactions you're looking for?", [], False

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
                    result = tool.invoke(tool_args)
                    
                    # Transaction fetcher typically doesn't need follow-up
                    return result, tool_calls_made, False

            return f"Error: Tool {tool_name} not found.", tool_calls_made, False

        except Exception as e:
            if config.debug_mode:
                traceback.print_exc()
            return f"Error: {str(e)}", tool_calls_made, False

async def process_task_async(task: str, db: AsyncIOMotorDatabase = None, user_id: str = None, 
                           conversation_history: Optional[List[ConversationTurnInDB]] = None) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Transaction Fetcher agent with backend database context.
    
    Args:
        task: The user's request for transaction retrieval
        db: Database instance for backend integration
        user_id: User identifier for backend context
        conversation_history: Previous conversation turns for context
        
    Returns:
        Dict containing response and metadata
    """
    agent = TransactionFetcher(db=db, user_id=user_id)
    
    # Process request and get tool result
    result, tool_calls_made, requires_follow_up = await agent.process_request(task, conversation_history)

    # Note: Conversation logging handled at API level in backend pattern
    if config.verbose_logging:
        print(f"📝 Transaction fetcher completed task. Follow-up: {requires_follow_up}")

    return {
        "response": result,  # Direct tool result
        "requires_follow_up": requires_follow_up,
        "tool_calls": tool_calls_made,
        "success": "Error" not in result
    }

def process_task(task: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for backward compatibility following classifier pattern.
    
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