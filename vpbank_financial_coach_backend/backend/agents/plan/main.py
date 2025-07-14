"""
Budget Advisor Agent - Enhanced Pattern 2
========================================

Main agent that handles budget planning and financial advice using a ReAct framework
with Enhanced Pattern 2 for production-ready multi-user support.
"""

import sys
import os
import traceback
import json
from typing import Dict, Any, List, Optional

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from motor.motor_asyncio import AsyncIOMotorDatabase

from .config import config
from .tools import get_stage1_tools, get_stage2_tools, get_stage3_tools, PlanServiceContainer
from .prompt import build_budget_advisor_prompt
from backend.models.conversation import ConversationTurnInDB
from backend.services.conversation_service import ConversationService

# Stage management - simplified for Enhanced Pattern 2
PLAN_STAGES = {
    "1": "information_gathering",
    "2": "plan_refinement", 
    "3": "plan_implementation"
}

TERMINATING_TOOLS = {
    "1": ["request_clarification", "propose_plan"],
    "2": ["propose_plan"],
    "3": ["create_plan", "adjust_plan"]
}


class BudgetAdvisorAgent:
    """Budget Advisor Agent using Enhanced Pattern 2 for production-ready multi-user support."""
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """
        Initialize the agent with database context and user ID.
        
        Args:
            db: Database connection for user data
            user_id: User identifier for data isolation
        """
        # Validate required parameters
        if not db:
            raise ValueError("Database connection is required for production plan agent")
        if not user_id:
            raise ValueError("User ID is required for production plan agent")
            
        self.db = db
        self.user_id = user_id
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            google_api_key=config.google_api_key
        )
        
        # Create service container with user context
        self.services = PlanServiceContainer(db, user_id)
        
        # Create conversation service for stateless stage management
        self.conversation_service = ConversationService(db, user_id)
    
    def _get_tools_for_stage(self, stage: str):
        """Get tools for the specified stage."""
        if stage == "1":
            return get_stage1_tools(self.services)
        elif stage == "2":
            return get_stage2_tools(self.services)
        elif stage == "3":
            return get_stage3_tools(self.services)
        else:
            return get_stage1_tools(self.services)  # Default to stage 1
    
    async def process_request(self, task: str, conversation_history: Optional[List[ConversationTurnInDB]] = None) -> Dict[str, Any]:
        """
        Process user request using ReAct framework with stateless stage management.
        
        Args:
            task: User's budget planning request
            conversation_history: Previous conversation context
            
        Returns:
            Dict with response and metadata including stage information for orchestrator
        """
        tool_calls_made = []
        
        try:
            # Get current stage from conversation history (stateless)
            current_stage = await self.conversation_service.get_current_plan_stage()
            
            # Handle special "ACCEPT" transition from Stage 2 to 3
            if current_stage == "2" and task.strip().upper() == "ACCEPT":
                current_stage = "3"
            
            # Get tools for current stage
            tools = self._get_tools_for_stage(current_stage)
            llm_with_tools = self.llm.bind_tools(tools)
            
            # Build prompt with stage context
            prompt = build_budget_advisor_prompt(
                task, 
                conversation_history or [], 
                True,  # agent_active
                current_stage
            )
            
            if config.debug_mode:
                print(f"🔍 Processing budget request (Stage {current_stage}): {task}")
            
            # Initialize conversation
            messages = [SystemMessage(content=prompt), HumanMessage(content=task)]
            
            # ReAct loop
            for i in range(config.max_react_iterations):
                response = await llm_with_tools.ainvoke(messages)
                # response = llm_with_tools.invoke(messages)
                
                # If no tool calls, return direct response
                if not response.tool_calls:
                    # Return response with stage metadata for orchestrator
                    return {
                        "response": response.content,
                        "requires_follow_up": False,
                        "tool_calls": tool_calls_made,
                        "stage": current_stage,
                        "metadata": ConversationService.create_plan_stage_metadata(current_stage)
                    }
                
                # Add AI message to conversation
                messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls))
                
                # Process tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_calls_made.append(f"{tool_name}(args={tool_args})")
                    
                    # Find and execute tool
                    tool_func = next((t for t in tools if t.name == tool_name), None)
                    if not tool_func:
                        continue
                    
                    try:
                        tool_result = tool_func.ainvoke(tool_args)
                        # tool_result = tool_func.invoke(tool_args)
                        
                        # Check if this is a terminating tool
                        if tool_name in TERMINATING_TOOLS.get(current_stage, []):
                            # Update stage based on tool result
                            new_stage = str(tool_result.get("stage", current_stage))
                            
                            # Format response
                            user_response = tool_result.get("response", "")
                            if "financial_plan" in tool_result:
                                user_response = f"**Proposed Financial Plan:**\n\n{tool_result['financial_plan']}"
                                if "jar_changes" in tool_result:
                                    user_response += f"\n\n**Jar Changes:** {tool_result['jar_changes']}"
                            
                            requires_follow_up = tool_result.get("requires_follow_up", False)
                            
                            # Return response with stage metadata for orchestrator to save
                            return {
                                "response": user_response,
                                "requires_follow_up": requires_follow_up,
                                "tool_calls": tool_calls_made,
                                "stage": new_stage,
                                "metadata": ConversationService.create_plan_stage_metadata(
                                    new_stage, 
                                    {"tool_result": tool_name, "stage_transition": f"{current_stage}->{new_stage}"}
                                )
                            }
                        
                        else:
                            # Informational tool - continue conversation
                            messages.append(ToolMessage(
                                content=str(tool_result), 
                                tool_call_id=tool_call.get('id')
                            ))
                    
                    except Exception as e:
                        messages.append(ToolMessage(
                            content=f"Tool {tool_name} failed: {e}",
                            tool_call_id=tool_call.get('id')
                        ))
            
            # Max iterations reached - return error with current stage
            error_response = "❌ Could not complete request within iteration limit."
            
            return {
                "response": error_response,
                "requires_follow_up": False,
                "tool_calls": tool_calls_made,
                "stage": current_stage,
                "metadata": ConversationService.create_plan_stage_metadata(current_stage, {"error": "max_iterations"})
            }
        
        except Exception as e:
            if config.debug_mode:
                traceback.print_exc()
            
            # Return error with stage info for orchestrator
            error_response = f"❌ Agent error: {str(e)}"
            try:
                current_stage = await self.conversation_service.get_current_plan_stage()
            except:
                current_stage = "1"  # Fallback to stage 1 on error
            
            return {
                "response": error_response,
                "requires_follow_up": False,
                "tool_calls": tool_calls_made,
                "stage": current_stage,
                "metadata": ConversationService.create_plan_stage_metadata(current_stage, {"error": str(e)})
            }


async def process_task(task: str, db: AsyncIOMotorDatabase, user_id: str,
                     conversation_history: Optional[List[ConversationTurnInDB]] = None) -> Dict[str, Any]:
    """
    MAIN ORCHESTRATOR INTERFACE - STATELESS VERSION
    
    Standalone function to process budget planning requests using Enhanced Pattern 2
    with stateless stage management based on conversation history.
    
    Args:
        task: User's budget planning request
        db: Database connection for user data
        user_id: User identifier for data isolation
        conversation_history: Previous conversation context
        
    Returns:
        Budget planning response with metadata including current stage
        
    Examples:
        process_task("I want to save for vacation", db, "user123")
        → {"response": "Let me help you create a vacation savings plan...", "stage": "1", ...}
        
    Note: Stage is now determined from conversation history, making this fully stateless.
    """
    # Validate required parameters for production
    if not db:
        return {
            "response": "❌ Error: Database connection is required for budget advisor agent.",
            "requires_follow_up": False,
            "tool_calls": [],
            "stage": "1"
        }
    
    if not user_id:
        return {
            "response": "❌ Error: User ID is required for budget advisor agent.",
            "requires_follow_up": False,
            "tool_calls": [],
            "stage": "1"
        }
    
    agent = BudgetAdvisorAgent(db, user_id)
    return await agent.process_request(task, conversation_history)


# Legacy function names for backward compatibility
def process_task_legacy(task: str, conversation_history: List = None) -> Dict[str, Any]:
    """
    Legacy function name for backward compatibility.
    Use process_task() for new integrations.
    """
    raise NotImplementedError("Enhanced Pattern 2 requires db and user_id parameters")

