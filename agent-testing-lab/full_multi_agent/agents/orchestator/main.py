"""
Orchestrator - Central Router
=============================

Stateful router that classifies intents, handles locks, and uses tool calling for routing.
Single flow with LLM deciding direct response or tool calls (agent routes).

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> Dict[str, Any]
"""

import sys
import os
import json
from typing import Dict, Any, List

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from .config import config
from .prompt import build_orchestrator_prompt
from .tools import get_all_orchestrator_tools, AGENT_REGISTRY
from utils import add_conversation_turn, get_conversation_history
from database import ConversationTurn, set_active_agent_context, get_active_agent_context, MAX_MEMORY_TURNS



def create_llm_with_tools():
    """Create Gemini LLM with orchestrator tools bound."""
    if not config.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required")
    
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=config.google_api_key
    )
    return llm.bind_tools(get_all_orchestrator_tools())

def filter_agent_history(history: List[ConversationTurn], agent_name: str) -> List[ConversationTurn]:
    """Filter history to turns involving specific agent."""
    return [turn for turn in history if agent_name in turn.agent_list]

def process_task(task: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
    """
    Main entry point: Handle lock, build prompt with last 10 history, invoke LLM for direct/tool decision.
    
    Args:
        task: User input.
        conversation_history: Full history (last 10 used).
            
    Returns:
        Dict with response and follow-up flag.
    """
    try:
        llm_with_tools = create_llm_with_tools()
        
        # Check lock first (bypass LLM if locked)
        locked_agent = get_active_agent_context()
        if locked_agent:
            if config.debug_mode:
                print(f"🔒 Locked to {locked_agent} - routing directly")
            filtered_history = filter_agent_history(conversation_history, locked_agent)
            result = AGENT_REGISTRY[locked_agent].process_task(task, filtered_history)
            # If no follow-up, release lock
            if not result.get("requires_follow_up", False):
                set_active_agent_context(None)
            # Log turn
            add_conversation_turn(
                user_input=task,
                agent_output=result["response"],
                agent_list=[locked_agent],
                tool_call_list=[]
            )
            return result
        
        # Limit to last 10 turns for statefulness
        limited_history = conversation_history[-MAX_MEMORY_TURNS:]
        
        # Build prompt with history
        prompt = build_orchestrator_prompt(task, limited_history)
        
        # Invoke LLM with tools
        response = llm_with_tools.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=task)
        ])
        
        # If no tool calls, direct response from LLM
        if not response.tool_calls:
            direct_response = response.content
            add_conversation_turn(
                user_input=task,
                agent_output=direct_response,
                agent_list=['orchestrator'],
                tool_call_list=[]
            )
            return {"response": direct_response, "requires_follow_up": False}
        
        # Process tool calls (route to agents)
        responses = []
        requires_follow_up = False
        tool_calls_made = []
        
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_calls_made.append(f"{tool_name}(args={tool_args})")
            
            # Execute tool (agent call)
            tool_func = next((t for t in get_all_orchestrator_tools() if t.name == tool_name), None)
            if tool_func:
                result = tool_func.invoke(tool_args)
                responses.append(result["response"])
                if result.get("requires_follow_up", False):
                    requires_follow_up = True
            else:
                responses.append(f"❌ Tool {tool_name} not found")
        
        # Synthesize final response from tool results
        final_response = "\n\n".join(responses) if len(responses) > 1 else responses[0]
        
        # Log turn with tool calls
        add_conversation_turn(
            user_input=task,
            agent_output=final_response,
            agent_list=['orchestrator'],
            tool_call_list=tool_calls_made
        )
        
        return {"response": final_response, "requires_follow_up": requires_follow_up}
    
    except Exception as e:
        if config.debug_mode:
            traceback.print_exc()
        error_msg = f"❌ Orchestrator error: {str(e)}"
        return {"response": error_msg, "requires_follow_up": False}