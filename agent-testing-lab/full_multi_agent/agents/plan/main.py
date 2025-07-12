"""
Budget Advisor Agent - ReAct Framework
======================================

Main agent that handles financial planning and advisory questions
using a ReAct (Reason-Act) framework with conversation lock and stages.

ORCHESTRATOR INTERFACE:
- process_task(task: str, conversation_history: List) -> Dict[str, Any]
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
from database import ConversationTurn, set_active_agent_context, get_active_agent_context

# Define terminating tools per stage
TERMINATING_TOOLS = {
    "1": ["request_clarification", "propose_plan"],
    "2": ["propose_plan"],
    "3": ["create_plan", "adjust_plan"]  # Terminate after plan tools in stage 3
}

def create_llm_with_tools(tools):
    """Create Gemini LLM instance with specified tools bound."""
    if not config.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required")
    
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=config.google_api_key
    )
    return llm.bind_tools(tools)

def get_current_stage(conversation_history: List[ConversationTurn]) -> str:
    """Parse current stage from last agent output in history."""
    if not conversation_history:
        return "1"
    last_output = conversation_history[-1].agent_output
    if isinstance(last_output, str):
        try:
            last_dict = json.loads(last_output)
            return last_dict.get("stage", "1")
        except json.JSONDecodeError:
            return "1"
    return "1"

def process_task(task: str, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Budget Advisor agent.
    
    Args:
        task: User's financial planning request.
        conversation_history: List of previous conversation turns for context.
            
    Returns:
        Dict with the agent's response and follow-up flag.
    """
    tool_calls_made = []
    
    try:
        # Get current stage
        current_stage = get_current_stage(conversation_history)
        
        # Stage 2 ACCEPT check: Transition to stage 3
        if current_stage == "2" and task.strip().upper() == "ACCEPT":
            current_stage = "3"
        
        # Select stage-specific tools
        if current_stage == "1":
            tools = get_stage1_tools()
        elif current_stage == "2":
            tools = get_stage2_tools()
        elif current_stage == "3":
            tools = get_stage3_tools()
        else:
            current_stage = "1"  # Reset invalid
            tools = get_stage1_tools()
        
        llm_with_tools = create_llm_with_tools(tools)
        
        is_follow_up = get_active_agent_context() == 'budget_advisor'
        
        prompt = build_budget_advisor_prompt(task, conversation_history, is_follow_up, current_stage)
        
        if config.debug_mode:
            print(f"🔍 Processing budget request (Stage {current_stage}): {task}")
            if is_follow_up:
                print("📝 This is a follow-up response")

        # Initialize messages for ReAct (separate from conversation_history)
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=task)
        ]

        # ReAct Loop: Continue until terminating tool is called
        max_iterations = config.max_react_iterations
        iteration = 0
        print("Stage:", current_stage)
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 ReAct Iteration {iteration}/{max_iterations}")
            
            # Reason: Invoke LLM
            response = llm_with_tools.invoke(messages)
            
            # If no tool calls, direct response (fallback, but prompt enforces tool call)
            response = llm_with_tools.invoke(messages)
            if not response.tool_calls:
                if config.debug_mode:
                    print("🤖 Agent failed to call a tool.")
                return {"response": response.content, "requires_follow_up": False, "tool_calls": tool_calls_made, "success": True} 
            
            print(f"🤖 LLM Response Type: {type(response)}")
            if response.content:
                print(f"💭 LLM Thinking: {response.content[:100]}...")
            if response.tool_calls:
                print(f"🔧 Tool Calls: {len(response.tool_calls)}")
                for call in response.tool_calls:
                    print(f"  - {call['name']}({call['args']})")
            # Add AI message (reasoning step)
            messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls))
            
            
            # Act and Observe: Process each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_call_id = tool_call.get('id', f'call_{iteration}')
                
                if config.debug_mode:
                    print(f"\n📞 Tool Call: {tool_name}()")
                    print(f"📋 Parameters: {tool_args}")
                
                # Record tool usage (separate from history)
                tool_calls_made.append(f"{tool_name}(args={tool_args})")
                
                # Find and execute tool
                tool_func = next((t for t in tools if t.name == tool_name), None)
                if not tool_func:
                    error_msg = f"❌ Tool {tool_name} not found"
                    messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                    if config.debug_mode:
                        print(f"❌ Error: {error_msg}")
                    continue
                
                try:
                    result = tool_func.invoke(tool_args)
                    
                    # Observe: Add tool result as ToolMessage (for non-terminating)
                    messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
                    
                    if config.debug_mode:
                        print(f"✅ Tool result: {str(result)[:150]}...")
                    
                    # Check if terminating tool - exit loop
                    if tool_name in TERMINATING_TOOLS.get(current_stage, []):
                        print(tool_name, current_stage)
                        final_response = result.get("financial_plan", result.get("response", "No response"))
                        if "jar_changes" in result:
                            final_response += f"\n\n**Jar Changes:** {result['jar_changes']}"
                        requires_follow_up = True
                        if current_stage == "3":
                            requires_follow_up = False
                        stage = result.get("stage")
                        if requires_follow_up:
                            set_active_agent_context("budget_advisor")
                        else:
                            set_active_agent_context(None)
                        if config.debug_mode:
                            print(f"✅ Terminating tool called: {tool_name}")
                            print(f"🏁 ReAct completed in {iteration} iterations")
                        return {
                            "response": final_response,
                            "requires_follow_up": requires_follow_up,
                            "tool_calls": tool_calls_made,
                            "success": True
                        }
                        
                except Exception as e:
                    error_msg = f"❌ Tool {tool_name} failed: {str(e)}"
                    messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                    if config.debug_mode:
                        print(f"❌ Error: {error_msg}")
        
        # Max iterations reached
        if config.debug_mode:
            print(f"⚠️ Max iterations ({max_iterations}) reached without terminating tool")
        
        return {
            "response": "❌ Could not provide a complete answer within reasoning steps. Please try a simpler question.",
            "requires_follow_up": False,
            "tool_calls": tool_calls_made,
            "success": False
        }
    
    except Exception as e:
        if config.debug_mode:
            traceback.print_exc()
        error_msg = f"❌ Error processing request: {str(e)}"
        return {
            "response": error_msg,
            "requires_follow_up": False,
            "tool_calls": tool_calls_made,
            "success": False
        }
    finally:
        # Log the interaction (conversation history separate from ReAct messages/tool results)
        log_dict = {
            "response": error_msg if 'error_msg' in locals() else final_response if 'final_response' in locals() else "No response",
            "stage": stage if 'stage' in locals() else current_stage
        }
        if 'result' in locals() and isinstance(result, dict) and "jar_changes" in result:
            log_dict["jar_changes"] = result["jar_changes"]
        log_output = json.dumps(log_dict)
        add_conversation_turn(
            user_input=task,
            agent_output=log_output,
            agent_list=['budget_advisor'],
            tool_call_list=tool_calls_made
        )
        if config.verbose_logging:
            print(f"📝 Logged budget advisor turn")