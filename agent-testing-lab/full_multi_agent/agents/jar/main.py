"""
Main Jar Manager Agent
======================

LLM-powered jar management system with multi-jar operations support.
Handles jar creation, updates, deletion, and listing with automatic rebalancing.

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
from .tools import JAR_TOOLS
from .prompt import build_jar_manager_prompt
from utils import get_all_jars, add_conversation_turn
from database import TOTAL_INCOME, get_active_agent_context

def create_llm_with_tools():
    """Create Gemini LLM instance with jar management tools bound."""
    if not config.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required")
    
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=config.google_api_key
    )
    return llm.bind_tools(JAR_TOOLS)

def process_task(task: str, conversation_history: List) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Jar Manager agent.
    
    Args:
        task: User's jar management request.
        conversation_history: A list of previous conversation turns for context.
            
    Returns:
        A dictionary with the agent's response and a follow-up flag.
    """
    tool_calls_made = []
    
    try:
        # Initialize LLM and get fresh data
        llm_with_tools = create_llm_with_tools()
        existing_jars = get_all_jars()
        
        # Build prompt with context for follow-ups
        is_follow_up = get_active_agent_context() == 'jar'
        prompt = build_jar_manager_prompt(
            user_input=task,
            existing_jars=existing_jars,
            total_income=TOTAL_INCOME,
            conversation_history=conversation_history,
            is_follow_up=is_follow_up
        )
        
        if config.debug_mode:
            print(f"🔍 Processing jar request: {task}")
            if is_follow_up:
                print("📝 This is a follow-up response")

        # Get LLM's tool decision
        response = llm_with_tools.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=task)
        ])

        if not response.tool_calls:
            return {"response": "I'm not sure how to handle that jar request. Could you be more specific?", "requires_follow_up": False}

        # Take first tool call only
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']

        if config.debug_mode:
            print(f"🛠️ Using tool: {tool_name}")

        # Find and execute tool
        tool_to_call = next((t for t in JAR_TOOLS if t.name == tool_name), None)
        if not tool_to_call:
            return {"response": f"Error: Unknown tool '{tool_name}' called.", "requires_follow_up": False}

        # Record tool usage
        tool_calls_made.append(f"{tool_name}(args={tool_args})")

        # Execute tool and get result
        result = str(tool_to_call.invoke(tool_args))

        # Log the interaction
        add_conversation_turn(
            user_input=task,
            agent_output=result,
            agent_list=['jar'],
            tool_call_list=tool_calls_made
        )

        if config.verbose_logging:
            print(f"📝 Logged jar manager turn")
            print(f"🔄 Follow-up needed: {tool_name == 'request_clarification'}")

        return {
            "response": result,
            "requires_follow_up": tool_name == 'request_clarification',
            "tool_calls": tool_calls_made,
            "success": True
        }

    except Exception as e:
        if config.debug_mode:
            traceback.print_exc()
        error_msg = f"❌ Error during jar management: {str(e)}"
        return {
            "response": error_msg,
            "requires_follow_up": False,
            "tool_calls": tool_calls_made,
            "success": False
        }
