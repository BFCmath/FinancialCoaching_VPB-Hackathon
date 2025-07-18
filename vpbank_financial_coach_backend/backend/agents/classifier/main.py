"""
Main ReAct-based Transaction Classifier
=======================================

Core function that uses a ReAct framework to classify transactions,
proactively fetching information for ambiguous inputs.

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> Dict[str, Any]
"""

import asyncio
import traceback
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.core.config import settings
from .tools import get_all_classifier_tools, ClassifierServiceContainer
from .prompt import build_react_classifier_prompt
from backend.models.conversation import ConversationTurnInDB

# Define final action tools that end the loop
FINAL_ACTION_TOOLS = [
    "add_money_to_jar",
    "report_no_suitable_jar",
    "respond" 
]

class ReActClassifierAgent:
    """A ReAct-based agent for intelligent transaction classification."""

    def __init__(self, db: AsyncIOMotorDatabase = None, user_id: str = None):
        """Initialize the agent with LLM and tools."""
        self.db = db
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.LLM_TEMPERATURE
        )
        
        # Create service container for dependency injection
        if db is None and user_id is None:
            # Fallback for cases without database context (testing/development)
            self.services = None
            self.tools = []  # Empty tools list for non-production use
        else:
            self.services = ClassifierServiceContainer(db, user_id)
            self.tools = get_all_classifier_tools(self.services)
            
            
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _find_tool(self, tool_name: str):
        """Finds a tool function by its name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

    async def process_request(self, user_query: str, conversation_history: List[ConversationTurnInDB] = None) -> tuple[str, list, bool]:
        """
        Processes the user's request using the ReAct framework.

        Args:
            user_query: The latest query from the user.
            conversation_history: List of previous conversation turns for context (filtered for this agent).

        Returns:
            A tuple containing the final response, tool calls, and a follow-up flag.
        """
        # Validate that agent is properly configured for production use
        if self.services is None or self.db is None or self.user_id is None:
            return (
                "❌ Error: Classifier agent not properly configured. Database and user context required.",
                [],
                False
            )
        
        # Validate user query
        if not user_query or not user_query.strip():
            return (
                "❌ Error: User query cannot be empty.",
                [],
                False
            )
        
        tool_calls_made = []
        requires_follow_up = False
        final_response = "❌ Error: Agent loop completed without a final answer."
        
        try:
            # Build prompt with database context if available
            if self.db is not None and self.user_id is not None:
                system_prompt = await build_react_classifier_prompt(user_query, conversation_history, self.db, self.user_id)
            else:
                # Fallback for cases without database context
                system_prompt = f"""You are an intelligent transaction classifier. Your goal is to accurately categorize user expenses into the correct budget jar.

**CRITICAL RULE:** You MUST NOT ask the user for clarification in your direct content response. If you need to ask a question, you MUST use the respond tool.

**YOUR TASK:**
Analyze the user's request and classify the transaction.

THE ReAct FRAMEWORK: **Reason** -> **Act** -> **Observe** -> **Repeat or Finalize**

User: "{user_query}"
Assistant:
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]

            if settings.DEBUG_MODE:
                print(f"🔍 Processing query: {user_query}")
                print(f"🧠 System prompt length: {len(system_prompt)} chars")

            for iteration in range(settings.MAX_REACT_ITERATIONS):
                if settings.DEBUG_MODE:
                    print(f"🔄 ReAct Iteration {iteration + 1}/{settings.MAX_REACT_ITERATIONS}")

                try:
                    response = await self.llm_with_tools.ainvoke(messages)
                    messages.append(AIMessage(content=str(response.content), tool_calls=response.tool_calls))
                except Exception as e:
                    final_response = f"❌ LLM call failed: {str(e)}"
                    return final_response, tool_calls_made, False

                if not response.tool_calls:
                    if settings.DEBUG_MODE:
                        print("🤖 Agent failed to call a tool. Returning error.")
                    final_response = "❌ Error: The agent did not select a tool to respond."
                    return final_response, tool_calls_made, False

                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_call_id = tool_call['id']

                    tool_calls_made.append(f"{tool_name}(args={tool_args})")

                    if settings.DEBUG_MODE:
                        print(f"📞 Calling Tool: {tool_name} with args: {tool_args}")

                    tool_func = self._find_tool(tool_name)
                    if not tool_func:
                        error_msg = f"❌ Tool '{tool_name}' not found."
                        messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                        continue

                    try:
                        result = await tool_func.ainvoke(tool_args)
                        
                        # If "respond" for clarification, set follow-up
                        if tool_name == "respond":
                            if settings.DEBUG_MODE:
                                print(f"🔒 ReAct loop paused by '{tool_name}' for user input.")
                            requires_follow_up = True
                            final_response = str(result)
                            return final_response, tool_calls_made, requires_follow_up

                        # If final classification tool, end without follow-up
                        if tool_name in ["add_money_to_jar", "report_no_suitable_jar"]:
                            if settings.DEBUG_MODE:
                                print(f"🏁 ReAct loop finished by final action tool: '{tool_name}'.")
                            final_response = str(result)
                            return final_response, tool_calls_made, False
                        
                        # Add observation for non-final tools
                        messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
                        
                    except Exception as e:
                        error_msg = f"❌ Tool {tool_name} failed: {str(e)}"
                        messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                        if settings.DEBUG_MODE:
                            print(error_msg)

            final_response = "❌ Classifier could not provide a complete answer within the allowed steps."
            return final_response, tool_calls_made, False

        except Exception as e:
            if settings.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            final_response = f"❌ An error occurred during processing: {str(e)}"
            return final_response, tool_calls_made, False


async def process_task_async(task: str, conversation_history: List[ConversationTurnInDB] = None, 
                           db: AsyncIOMotorDatabase = None, user_id: str = None) -> Dict[str, Any]:
    """
    Main async orchestrator interface for the ReAct Classifier agent.

    Args:
        task: The user's current request (e.g., "lunch" or "coffee 2 dollars").
        conversation_history: List of previous turns for follow-up context.
        db: Database connection (required for production use).
        user_id: User ID (required for production use).

    Returns:
        Dict with response, requires_follow_up flag, and tool_calls list.
    """
    # Validate required parameters for production use
    if db is None or user_id is None:
        return {
            "response": "❌ Error: Database connection and user_id are required for classifier agent.",
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
        agent = ReActClassifierAgent(db, user_id)
        
        # Process the request
        final_response, tool_calls_made, requires_follow_up = await agent.process_request(task, conversation_history)

        if settings.VERBOSE_LOGGING:
            print(f"📝 Classifier agent completed. Follow-up: {requires_follow_up}")

        return {
            "response": final_response, 
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
        import traceback
        if settings.DEBUG_MODE:
            traceback.print_exc()
        
        return {
            "response": f"❌ Classifier agent failed with unexpected error: {str(e)}",
            "requires_follow_up": False,
            "tool_calls": [],
            "error": True
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
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(process_task_async(task, conversation_history))
                )
                return future.result()
        else:
            # Run in current loop
            return loop.run_until_complete(process_task_async(task, conversation_history))
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(process_task_async(task, conversation_history))