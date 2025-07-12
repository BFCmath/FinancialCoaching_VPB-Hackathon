"""
Fee Manager Agent - Main Logic
==============================

Core fee management system, using tools directly.
"""
import os
import sys
import traceback
from typing import List, Optional, Dict, Any

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# LLM imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Local imports
from .config import config
from .tools import get_all_fee_tools
from .prompt import build_fee_manager_prompt
from database import ConversationTurn
from utils import (
    add_conversation_turn, get_all_recurring_fees, get_all_jars,
    get_active_agent_context
)

class FeeManager:
    """Fee manager that uses tools directly based on LLM decisions."""
    
    def __init__(self):
        """Initialize the agent with LLM and tools."""
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.temperature
        )
        self.tools = get_all_fee_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def process_request(self, user_query: str, conversation_history: List = None) -> tuple[str, list, bool]:
        """
        Process user request by directly calling appropriate tools.
        
        Args:
            user_query: The latest query from the user
            conversation_history: Previous conversation turns for context
            
        Returns:
            Tuple of (tool_result, tool_calls_made, requires_follow_up)
        """
        tool_calls_made = []
        
        try:
            # Get fresh data
            existing_fees = get_all_recurring_fees()
            available_jars = get_all_jars()
            
            # Build prompt with history context for follow-ups
            system_prompt = build_fee_manager_prompt(
                user_input=user_query,
                existing_fees=existing_fees,
                available_jars=available_jars,
                conversation_history=conversation_history,
                is_follow_up=get_active_agent_context() == 'fee_manager'
            )
            
            # Get LLM's tool decision
            response = self.llm_with_tools.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ])

            if not response.tool_calls:
                if config.debug_mode:
                    print("🤖 Agent failed to call a tool.")
                return "Error: No action was taken.", [], False

            # Execute the chosen tool
            tool_call = response.tool_calls[0]  # Take first tool call
            tool_name = tool_call['name']
            tool_args = tool_call['args']

            if config.debug_mode:
                print(f"🛠️ Using tool: {tool_name}")

            # Find and execute tool
            for tool in self.tools:
                if tool.name == tool_name:
                    tool_calls_made.append(f"{tool_name}(args={tool_args})")
                    result = tool.invoke(tool_args)
                    
                    # If clarification needed, return result and set follow-up flag
                    if tool_name == "request_clarification":
                        return result, tool_calls_made, True
                        
                    # Otherwise return the tool result directly
                    return result, tool_calls_made, False

            return f"Error: Tool {tool_name} not found.", tool_calls_made, False

        except Exception as e:
            if config.debug_mode:
                traceback.print_exc()
            return f"Error: {str(e)}", tool_calls_made, False

def manage_fees(task: str, conversation_history: Optional[List[ConversationTurn]] = None) -> Dict[str, Any]:
    """
    Main orchestrator interface for the Fee Manager agent.
    
    Args:
        task: The user's request or clarification response
        conversation_history: Previous conversation turns for context
        
    Returns:
        Dict containing response and metadata
    """
    agent = FeeManager()
    
    try:
        # Process request and get tool result
        result, tool_calls_made, requires_follow_up = agent.process_request(task, conversation_history)

        # Log the interaction
        add_conversation_turn(
            user_input=task,
            agent_output=result,
            agent_list=['fee_manager'],
            tool_call_list=tool_calls_made
        )

        if config.verbose_logging:
            print(f"📝 Logged conversation turn for fee_manager. Follow-up: {requires_follow_up}")

        return {
            "response": result,  # Direct tool result
            "requires_follow_up": requires_follow_up,
            "agent": "fee_manager",
            "tool_calls": tool_calls_made,
            "success": True
        }

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        if config.debug_mode:
            error_msg += f"\n{traceback.format_exc()}"
            
        # Log the error
        add_conversation_turn(
            user_input=task,
            agent_output=error_msg,
            agent_list=['fee_manager'],
            tool_call_list=[]
        )
        
        return {
            "response": error_msg,
            "requires_follow_up": False,
            "agent": "fee_manager",
            "tool_calls": [],
            "success": False
        }
