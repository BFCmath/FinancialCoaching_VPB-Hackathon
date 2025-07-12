"""
Transaction Fetcher Agent - Direct Flow
======================================

Main agent for retrieving transaction history using intelligent tool selection.
Pure data retrieval service - no analysis or conversation state.

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> Dict[str, Any]
"""

import sys
import os
import traceback
from typing import Dict, Any, List

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from .config import config
from .tools import get_all_transaction_tools, fetch_available_jars
from .prompt import build_history_fetcher_prompt
from utils import add_conversation_turn
from database import TOTAL_INCOME  # For potential future use, though not needed here

def create_llm_with_tools():
    """Create Gemini LLM instance with transaction tools bound."""
    if not config.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required")
    
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=config.google_api_key
    )
    return llm.bind_tools(get_all_transaction_tools())

def process_task(task: str, conversation_history: List) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Transaction Fetcher agent.
    
    Args:
        task: User's transaction retrieval request (e.g., "show me groceries spending last month").
        conversation_history: Previous conversation turns (unused, for compatibility).
            
    Returns:
        Dict with the agent's response (transaction data) and metadata.
    """
    tool_calls_made = []
    
    try:
        # Initialize LLM and get fresh data
        llm_with_tools = create_llm_with_tools()
        available_jars = fetch_available_jars()  # From tools.py
        
        # Build prompt (no history usage - stateless)
        prompt = build_history_fetcher_prompt(
            user_query=task,
            available_jars=available_jars
        )
        
        if config.debug_mode:
            print(f"🔍 Processing transaction request: {task}")

        # Get LLM's tool decision
        response = llm_with_tools.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=task)
        ])

        if not response.tool_calls:
            return {"response": "I'm not sure how to retrieve those transactions. Could you be more specific?", "requires_follow_up": False}

        # Take first tool call only (direct flow)
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']

        if config.debug_mode:
            print(f"🛠️ Using tool: {tool_name}")

        # Find and execute tool
        tool_to_call = next((t for t in get_all_transaction_tools() if t.name == tool_name), None)
        if not tool_to_call:
            return {"response": f"Error: Unknown tool '{tool_name}' called.", "requires_follow_up": False}

        # Record tool usage
        tool_calls_made.append(f"{tool_name}(args={tool_args})")

        # Execute tool and get result (dict from service)
        result = tool_to_call.invoke(tool_args)

        # Log the interaction (stateless, but log for system consistency)
        add_conversation_turn(
            user_input=task,
            agent_output=str(result),  # Convert dict to string for logging
            agent_list=['transaction_fetcher'],
            tool_call_list=tool_calls_made
        )

        if config.verbose_logging:
            print(f"📝 Logged transaction fetcher turn")

        return {
            "response": result,  # Direct service dict (data + description)
            "requires_follow_up": False,  # Always False - stateless
            "tool_calls": tool_calls_made,
            "success": True
        }

    except Exception as e:
        if config.debug_mode:
            traceback.print_exc()
        error_msg = f"❌ Error during transaction retrieval: {str(e)}"
        return {
            "response": error_msg,
            "requires_follow_up": False,
            "tool_calls": tool_calls_made,
            "success": False
        }