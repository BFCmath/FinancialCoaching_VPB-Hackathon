"""
Main ReAct-based Transaction Classifier
=======================================

Core function that uses a ReAct framework to classify transactions,
proactively fetching information for ambiguous inputs.

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> str
"""

import sys
import os
from typing import List, Dict, Any
import json
from datetime import datetime

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from .config import config
from .tools import get_all_classifier_tools
from .prompt import build_react_classifier_prompt
from utils import add_conversation_turn

# Define which tools are considered "final actions" that end the ReAct loop
FINAL_ACTION_TOOLS = [
    "add_money_to_jar_with_confidence",
    "report_no_suitable_jar",
]

class ReActClassifierAgent:
    """A ReAct-based agent for intelligent transaction classification."""

    def __init__(self):
        """Initialize the agent with LLM and tools."""
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.temperature
        )
        self.tools = get_all_classifier_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _find_tool(self, tool_name: str):
        """Finds a tool function by its name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

    def process_request(self, user_query: str, conversation_history: List = None) -> tuple[str, list, bool]:
        """
        Processes the user's request using the ReAct framework.

        Args:
            user_query: The latest query from the user.
            conversation_history: A list of previous conversation turns for context.

        Returns:
            A tuple containing the final response, tool calls, and a follow-up flag.
        """
        tool_calls_made = []
        requires_follow_up = False
        final_response = "Error: Agent loop completed without a final answer."
        try:
            system_prompt = build_react_classifier_prompt(user_query, conversation_history)
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
                    # If the LLM fails to call a tool, it's a failure.
                    # The agent should not be able to respond directly.
                    final_response = "Error: The agent did not select a tool to respond."
                    return final_response, tool_calls_made, False

                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_call_id = tool_call['id']
                    
                    # Log the tool call to log.txt
                    log_file_path = os.path.join(current_dir, "log.txt")
                    with open(log_file_path, "a", encoding="utf-8") as f:
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "tool_name": tool_name,
                            "arguments": tool_args
                        }
                        f.write(json.dumps(log_entry, indent=2) + "\n")

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
                        
                        # If the agent needs to ask a question, it requires a follow-up.
                        if tool_name == "respond":
                             if config.debug_mode:
                                print(f"🔒 ReAct loop paused by '{tool_name}' for user input.")
                             return str(result), tool_calls_made, True

                        # If a final action tool was called, the loop is over.
                        if tool_name in FINAL_ACTION_TOOLS:
                            if config.debug_mode:
                                print(f"🏁 ReAct loop finished by final action tool: '{tool_name}'.")
                            return str(result), tool_calls_made, False
                        
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


def process_task(task: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Main orchestrator interface for the ReAct Classifier agent.

    Args:
        task: The user's current request (e.g., "lunch" or "coffee 2 dollars").
        conversation_history: Not used by this agent but kept for interface consistency.

    Returns:
        The agent's final response string.
    """
    agent = ReActClassifierAgent()
    
    # Process the request to get the response, tool calls, and follow-up status.
    final_response, tool_calls_made, requires_follow_up = agent.process_request(task, conversation_history)

    # Log the completed turn to the central conversation history
    add_conversation_turn(
        user_input=task,
        agent_output=final_response,
        agent_list=['transaction_classifier'],
        tool_call_list=tool_calls_made
    )
    print(conversation_history)
    if config.verbose_logging:
        print(f"📝 Logged conversation turn for transaction_classifier. Follow-up: {requires_follow_up}")

    return {"response": final_response, "requires_follow_up": requires_follow_up}


if __name__ == "__main__":
    # Test with both ambiguous and clear inputs
    test_inputs = [
        "meal 20 dollar",
        "went out for lunch", # Ambiguous
        "coffee 5, gas 50", 
        "mua ít đồ ăn vặt", # Ambiguous Vietnamese ("buy some snacks")
        "tôi ăn cơm 25k, mua xăng 100k",
    ]
    
    print("🧪 Testing ReAct Transaction Classifier")
    print("=" * 70)
    
    for test_input in test_inputs:
        print(f"\n📝 Input: '{test_input}'")
        result = process_task(test_input)
        print(f"🎯 Final Result: {result}")
        print("-" * 70)
