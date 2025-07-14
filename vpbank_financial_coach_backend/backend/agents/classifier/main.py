"""
Main ReAct-based Transaction Classifier
=======================================

Core function that uses a ReAct framework to classify transactions,
proactively fetching information for ambiguous inputs.

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> Dict[str, Any]
"""

import asyncio
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from motor.motor_asyncio import AsyncIOMotorDatabase

from .config import config
from .tools import get_all_classifier_tools
from .prompt import build_react_classifier_prompt
from backend.models.conversation import ConversationTurnInDB
from backend.services.financial_services import configure_classifier_services

# Define final action tools that end the loop
FINAL_ACTION_TOOLS = [
    "add_money_to_jar_with_confidence",
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
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.temperature
        )
        self.tools = get_all_classifier_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Configure services if database context is provided
        if db and user_id:
            configure_classifier_services(db, user_id)

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
        tool_calls_made = []
        requires_follow_up = False
        final_response = "Error: Agent loop completed without a final answer."
        try:
            # Build prompt with database context if available
            if self.db and self.user_id:
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

            if config.debug_mode:
                print(f"🔍 Processing query: {user_query}")
                print(f"🧠 System prompt length: {len(system_prompt)} chars")

            for iteration in range(config.max_react_iterations):
                if config.debug_mode:
                    print(f"🔄 ReAct Iteration {iteration + 1}/{config.max_react_iterations}")

                response = self.llm_with_tools.invoke(messages)
                messages.append(AIMessage(content=str(response.content), tool_calls=response.tool_calls))

                if not response.tool_calls:
                    if config.debug_mode:
                        print("🤖 Agent failed to call a tool. Returning error.")
                    final_response = "Error: The agent did not select a tool to respond."
                    return final_response, tool_calls_made, False

                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_call_id = tool_call['id']


                    tool_calls_made.append(f"{tool_name}(args={tool_args})")

                    if config.debug_mode:
                        print(f"📞 Calling Tool: {tool_name} with args: {tool_args}")

                    tool_func = self._find_tool(tool_name)
                    if not tool_func:
                        error_msg = f"❌ Tool '{tool_name}' not found."
                        messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                        continue

                    try:
                        result = tool_func.invoke(tool_args)
                        
                        # If "respond" for clarification, set follow-up
                        if tool_name == "respond":
                            if config.debug_mode:
                                print(f"🔒 ReAct loop paused by '{tool_name}' for user input.")
                            requires_follow_up = True
                            final_response = str(result)
                            return final_response, tool_calls_made, requires_follow_up

                        # If final classification tool, end without follow-up
                        if tool_name in ["add_money_to_jar_with_confidence", "report_no_suitable_jar"]:
                            if config.debug_mode:
                                print(f"🏁 ReAct loop finished by final action tool: '{tool_name}'.")
                            final_response = str(result)
                            return final_response, tool_calls_made, False
                        
                        # Add observation for non-final tools
                        messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
                    except Exception as e:
                        error_msg = f"❌ Tool {tool_name} failed: {e}"
                        messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                        if config.debug_mode:
                            print(error_msg)

            final_response = "❌ Classifier could not provide a complete answer within the allowed steps."
            return final_response, tool_calls_made, False

        except Exception as e:
            if config.debug_mode:
                import traceback
                traceback.print_exc()
            final_response = f"❌ An error occurred: {e}"
            return final_response, tool_calls_made, False


async def process_task_async(task: str, conversation_history: List[ConversationTurnInDB] = None, 
                           db: AsyncIOMotorDatabase = None, user_id: str = None) -> Dict[str, Any]:
    """
    Main async orchestrator interface for the ReAct Classifier agent.

    Args:
        task: The user's current request (e.g., "lunch" or "coffee 2 dollars").
        conversation_history: List of previous turns for follow-up context.
        db: Database connection (optional for compatibility).
        user_id: User ID (optional for compatibility).

    Returns:
        Dict with response and requires_follow_up flag.
    """
    agent = ReActClassifierAgent(db, user_id)
    
    # Process the request
    final_response, tool_calls_made, requires_follow_up = await agent.process_request(task, conversation_history)

    if config.verbose_logging:
        print(f"📝 Logged conversation turn for transaction_classifier. Follow-up: {requires_follow_up}")

    return {"response": final_response, "requires_follow_up": requires_follow_up}


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