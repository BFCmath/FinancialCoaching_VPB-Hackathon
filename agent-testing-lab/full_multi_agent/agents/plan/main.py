# agents/plan/main.py (FINAL, ROBUST VERSION)

"""
Budget Advisor Agent - ReAct Framework (Independent State Management)
======================================================================
This agent manages its stage (`1`, `2`, `3`) using a dedicated state manager,
decoupling it from the conversation history log. This makes it robust against
any external logging behavior (like from the Orchestrator).
"""

import sys
import os
import traceback
import json
from typing import Dict, Any, List

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from .config import config
from .tools import get_stage1_tools, get_stage2_tools, get_stage3_tools
from .prompt import build_budget_advisor_prompt
from utils import add_conversation_turn
from database import (
    ConversationTurn, 
    set_active_agent_context, 
    get_active_agent_context,
    # IMPORTANT: Import the new state functions
    get_plan_stage,
    set_plan_stage
)

TERMINATING_TOOLS = {
    "1": ["request_clarification", "propose_plan"],
    "2": ["propose_plan"],
    "3": ["create_plan", "adjust_plan"]
}

def create_llm_with_tools(tools):
    if not config.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required")
    llm = ChatGoogleGenerativeAI(model=config.model_name, temperature=config.temperature, google_api_key=config.google_api_key)
    return llm.bind_tools(tools)

# The stage is no longer parsed from history, it's read directly from the state manager.
def get_current_stage() -> str:
    """Gets the stage directly from the independent state manager."""
    return get_plan_stage()

def process_task(task: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
    """
    Main agent interface. Manages its own stage and logging.
    """
    tool_calls_made = []

    # Helper to centralize logging before returning
    def log_and_return(result: Dict, log_data: Dict):
        add_conversation_turn(
            user_input=task,
            agent_output=json.dumps(log_data, default=str),
            agent_list=['plan'],
            tool_call_list=result.get("tool_calls", [])
        )
        return result

    try:
        # 1. Get current stage from the dedicated state manager
        current_stage = get_current_stage()
        
        # 2. Handle special "ACCEPT" transition from Stage 2 to 3
        if current_stage == "2" and task.strip().upper() == "ACCEPT":
            current_stage = "3"
            set_plan_stage("3") # Immediately update the persistent state
        
        # Select tools based on the now-reliable stage
        if current_stage == "1": tools = get_stage1_tools()
        elif current_stage == "2": tools = get_stage2_tools()
        elif current_stage == "3": tools = get_stage3_tools()
        else: # Should not happen, but as a fallback
            current_stage = "1"
            set_plan_stage("1")
            tools = get_stage1_tools()
        
        llm_with_tools = create_llm_with_tools(tools)
        prompt = build_budget_advisor_prompt(task, conversation_history, get_active_agent_context() == 'plan', current_stage)
        
        if config.debug_mode:
            print(f"🔍 Processing budget request (Stage {current_stage}): {task}")

        messages = [SystemMessage(content=prompt), HumanMessage(content=task)]
        
        for i in range(config.max_react_iterations):
            response = llm_with_tools.invoke(messages)
            
            if not response.tool_calls:
                final_result = {"response": response.content, "requires_follow_up": False, "tool_calls": []}
                log_data = {"response": response.content, "stage": current_stage}
                return log_and_return(final_result, log_data)

            messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls))
            
            for tool_call in response.tool_calls:
                tool_name, tool_args = tool_call['name'], tool_call['args']
                tool_calls_made.append(f"{tool_name}(args={tool_args})")
                tool_func = next((t for t in tools if t.name == tool_name), None)

                if not tool_func: continue

                try:
                    tool_result = tool_func.invoke(tool_args)
                    
                    if tool_name in TERMINATING_TOOLS.get(current_stage, []):
                        
                        # 3. Update the stage based on the tool's result
                        new_stage = str(tool_result.get("stage", current_stage))
                        set_plan_stage(new_stage)
                        
                        user_response = tool_result.get("response")
                        if "financial_plan" in tool_result:
                            user_response = f"**Proposed Financial Plan:**\n\n{tool_result['financial_plan']}"
                            if "jar_changes" in tool_result:
                                user_response += f"\n\n**Jar Changes:** {tool_result['jar_changes']}"

                        requires_follow_up = tool_result.get("requires_follow_up", False)
                        set_active_agent_context("plan" if requires_follow_up else None)

                        # 4. If the plan is finalized (Stage 3), reset for the next conversation
                        if new_stage == "3":
                            set_plan_stage("1") # Reset for next time
                            set_active_agent_context(None) # Clear context
                            
                        final_result = {
                            "response": user_response, "requires_follow_up": requires_follow_up, "tool_calls": tool_calls_made
                        }
                        # The tool result is the perfect log data. Log and exit.
                        return log_and_return(final_result, tool_result)
                    
                    else: # Informational tool
                        messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call.get('id')))

                except Exception as e:
                    messages.append(ToolMessage(content=f"Tool {tool_name} failed: {e}", tool_call_id=tool_call.get('id')))
        
        # Max iterations reached
        final_result = {"response": "❌ Could not complete request.", "requires_follow_up": False, "tool_calls": tool_calls_made}
        log_data = {"response": final_result["response"], "stage": current_stage, "error": "max_iterations"}
        return log_and_return(final_result, log_data)

    except Exception as e:
        if config.debug_mode: traceback.print_exc()
        error_msg = f"❌ Agent error: {str(e)}"
        final_result = {"response": error_msg, "requires_follow_up": False, "tool_calls": []}
        log_data = {"response": error_msg, "stage": "unknown", "error": "exception"}
        # Reset state on critical error
        set_plan_stage("1")
        set_active_agent_context(None)
        return log_and_return(final_result, log_data)