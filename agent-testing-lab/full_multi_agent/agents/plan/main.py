"""
Budget Advisor Agent - ReAct Framework
======================================

Main agent that handles financial planning and advisory questions
using a ReAct (Reason-Act) framework with conversation lock.

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
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from .config import config
from .tools import get_all_plan_tools
from .prompt import build_budget_advisor_prompt
from utils import add_conversation_turn
from database import ConversationTurn, set_active_agent_context, get_active_agent_context

class BudgetAdvisorAgent:
    """Budget Advisor Agent using ReAct framework with conversation lock."""
    
    def __init__(self):
        """Initialize the agent with LLM and tools."""
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.temperature
        )
        self.tools = get_all_plan_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

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
        # Initialize LLM
        agent = BudgetAdvisorAgent()
        llm_with_tools = agent.llm_with_tools
        
        # Check if follow-up
        is_follow_up = get_active_agent_context() == 'budget_advisor'
        
        # Build prompt with filtered history
        prompt = build_budget_advisor_prompt(task, conversation_history, is_follow_up)
        
        if config.debug_mode:
            print(f"🔍 Processing budget request: {task}")
            if is_follow_up:
                print("📝 This is a follow-up response")

        # Initialize messages
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=task)
        ]

        # ReAct Loop
        max_iterations = config.max_react_iterations
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if config.debug_mode:
                print(f"\n🔄 ReAct Iteration {iteration}/{max_iterations}")
            
            # Get LLM response
            response = llm_with_tools.invoke(messages)
            
            if config.debug_mode:
                print(f"🤖 LLM Response Type: {type(response)}")
                if response.content:
                    print(f"💭 LLM Thinking: {response.content[:100]}...")
                if response.tool_calls:
                    print(f"🔧 Tool Calls: {len(response.tool_calls)}")
            
            # Add AI message
            messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls))
            
            # If no tool calls, direct response (fallback)
            if not response.tool_calls:
                if config.debug_mode:
                    print("🤖 No tool calls - direct response")
                return {"response": response.content, "requires_follow_up": False}
            
            # Process tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_call_id = tool_call.get('id', f'call_{iteration}')
                
                if config.debug_mode:
                    print(f"\n📞 Tool Call: {tool_name}()")
                    print(f"📋 Parameters: {tool_args}")
                
                # Record tool usage
                tool_calls_made.append(f"{tool_name}(args={tool_args})")
                
                # Find and execute tool
                tool_func = next((t for t in agent.tools if t.name == tool_name), None)
                if not tool_func:
                    error_msg = f"❌ Tool {tool_name} not found"
                    messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                    if config.debug_mode:
                        print(f"❌ Error: {error_msg}")
                    continue
                
                try:
                    result = tool_func.invoke(tool_args)
                    
                    # Handle respond tool - exit condition
                    if tool_name == "respond" and isinstance(result, dict):
                        final_answer = result.get('advice', '')  # Use 'advice' as main response
                        if config.debug_mode:
                            print(f"✅ Final answer received: {final_answer[:100]}...")
                            print(f"🏁 ReAct completed in {iteration} iterations")
                        
                        # Set lock based on question_ask_user
                        requires_follow_up = bool(result.get('question_ask_user'))
                        if requires_follow_up:
                            set_active_agent_context("budget_advisor")
                        else:
                            set_active_agent_context(None)
                        
                        # Format full response
                        formatted_response = f"{result.get('summary', '')}\n{result.get('advice', '')}"
                        if result.get('question_ask_user'):
                            formatted_response += f"\n❓ {result['question_ask_user']}"
                        
                        return {
                            "response": formatted_response,
                            "requires_follow_up": requires_follow_up,
                            "tool_calls": tool_calls_made,
                            "success": True
                        }
                    
                    # Add tool result
                    messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
                    
                    if config.debug_mode:
                        print(f"✅ Tool result: {str(result)[:150]}...")
                        
                except Exception as e:
                    error_msg = f"❌ Tool {tool_name} failed: {str(e)}"
                    messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
                    if config.debug_mode:
                        print(f"❌ Error: {error_msg}")
        
        # Max iterations reached
        if config.debug_mode:
            print(f"⚠️ Max iterations ({max_iterations}) reached without respond() call")
        
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
        # Log the interaction
        add_conversation_turn(
            user_input=task,
            agent_output=error_msg if 'error_msg' in locals() else formatted_response if 'formatted_response' in locals() else "No response",
            agent_list=['budget_advisor'],
            tool_call_list=tool_calls_made
        )
        if config.verbose_logging:
            print(f"📝 Logged budget advisor turn")