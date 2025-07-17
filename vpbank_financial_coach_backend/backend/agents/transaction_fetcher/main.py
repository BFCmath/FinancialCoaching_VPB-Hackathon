"""
Transaction Fetcher Agent - Enhanced Pattern 2
==============================================

Main agent for retrieving transaction history using intelligent tool selection.
Pure data retrieval service with dependency injection for production-ready multi-user support.
"""

import sys
import os
import traceback
import inspect
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

from backend.core.config import settings
from .tools import get_all_transaction_tools, TransactionFetcherServiceContainer
from .prompt import build_history_fetcher_prompt

class TransactionFetcher:
    """Transaction fetcher with Enhanced Pattern 2 for production-ready multi-user support."""
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """Initialize the agent with LLM, tools, and database context."""
        self.db = db
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Create service container for dependency injection
        self.services = TransactionFetcherServiceContainer(db, user_id)
        self.tools = get_all_transaction_tools(self.services)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def process_request(self, user_query: str) -> tuple[str, list, bool]:
        """
        Process user request by calling the appropriate tool with backend context.
        
        Args:
            user_query: The latest query from the user
            
        Returns:
            Tuple of (tool_result, tool_calls_made, requires_follow_up)
        """
        # Validate user query
        if not user_query or not user_query.strip():
            return (
                "❌ Error: User query cannot be empty.",
                [],
                False
            )
        
        tool_calls_made = []
        
        try:
            # Build prompt with async database context
            system_prompt = await build_history_fetcher_prompt(user_query, self.db, self.user_id)
            
            # Get LLM's tool decision
            try:
                response = await self.llm_with_tools.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_query)
                ])
            except Exception as e:
                return f"❌ LLM call failed: {str(e)}", tool_calls_made, False

            if not response.tool_calls:
                if settings.DEBUG_MODE:
                    print("🤖 Agent failed to call a tool.")
                return "❌ Error: I couldn't determine which transactions to fetch. Could you be more specific?", tool_calls_made, False

            # Execute the chosen tool
            tool_call = response.tool_calls[0]
            tool_name = tool_call['name']
            tool_args = tool_call['args']

            if settings.DEBUG_MODE:
                print(f"🛠️ Using tool: {tool_name}")

            for tool in self.tools:
                if tool.name == tool_name:
                    tool_calls_made.append(f"{tool_name}(args={tool_args})")
                    
                    try:
                        # Use ainvoke for async tools
                        result = await tool.ainvoke(tool_args)
                        return result, tool_calls_made, False
                    
                    except Exception as e:
                        return f"❌ Tool {tool_name} failed: {str(e)}", tool_calls_made, False

            return f"❌ Error: Tool {tool_name} not found.", tool_calls_made, False

        except Exception as e:
            if settings.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            return f"❌ Error during processing: {str(e)}", tool_calls_made, False

async def process_task(task: str, db: AsyncIOMotorDatabase, user_id: str, 
                     conversation_history: Optional[List[ConversationTurnInDB]] = None) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Transaction Fetcher agent with standardized return format.
    
    Args:
        task: The user's request for transaction retrieval
        db: Database instance for backend integration (required for production use)
        user_id: User identifier for backend context (required for production use)
        conversation_history: Not used by this stateless agent, but kept for interface consistency
        
    Returns:
        Dict containing:
        - response: Agent response text (transaction data)
        - requires_follow_up: Boolean indicating if agent needs another turn  
        - tool_calls: List of tool calls made during processing
        - error: Boolean indicating if an error occurred
    """
    # Validate required parameters for production use
    if db is None or user_id is None:
        return {
            "response": "❌ Error: Database connection and user_id are required for transaction fetcher agent.",
            "requires_follow_up": False,
            "tool_calls": [],
            "error": True
        }
    
    # Validate task input
    if not task or not task.strip():
        return {
            "response": "❌ Error: Task cannot be empty.",
            "requires_follow_up": False,
            "tool_calls": [],
            "error": True
        }
    
    try:
        agent = TransactionFetcher(db=db, user_id=user_id)
        result, tool_calls_made, requires_follow_up = await agent.process_request(task)

        if settings.VERBOSE_LOGGING:
            print(f"📝 Transaction fetcher completed task. Follow-up: {requires_follow_up}")

        return {
            "response": result,
            "requires_follow_up": requires_follow_up,
            "tool_calls": tool_calls_made,
            "error": False
        }
    
    except ValueError as e:
        # Handle validation errors from services
        return {
            "response": f"❌ Validation error: {str(e)}",
            "requires_follow_up": False,
            "tool_calls": [],
            "error": True
        }
    
    except Exception as e:
        # Handle any unexpected errors
        if settings.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        
        return {
            "response": f"❌ Transaction fetcher failed with unexpected error: {str(e)}",
            "requires_follow_up": False,
            "tool_calls": [],
            "error": True
        }