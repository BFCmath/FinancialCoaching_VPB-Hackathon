"""
Knowledge Base Agent - Enhanced Pattern 2
========================================

Main agent that handles financial knowledge and app documentation questions
using a ReAct (Reason-Act) framework with Enhanced Pattern 2 for production-ready multi-user support.

ORCHESTRATOR INTERFACE:
- process_task(task: str, db: AsyncIOMotorDatabase, user_id: str) -> str
"""

import traceback
import inspect
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from motor.motor_asyncio import AsyncIOMotorDatabase

from .tools import get_all_knowledge_tools, KnowledgeServiceContainer
from .prompt import build_react_prompt
from backend.core.config import settings


class KnowledgeBaseAgent:
    """Knowledge Base Agent using ReAct framework with Enhanced Pattern 2"""
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """
        Initialize the agent with database context and user ID.
        
        Args:
            db: Database connection for user data
            user_id: User identifier for data isolation
        """
        # Validate required parameters
        if db is None:
            raise ValueError("Database connection is required for production knowledge agent")
        if user_id is None:
            raise ValueError("User ID is required for production knowledge agent")
            
        self.db = db
        self.user_id = user_id
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.LLM_TEMPERATURE
        )
        
        # Create service container with user context
        self.services = KnowledgeServiceContainer(db, user_id)
        
        # Bind tools to LLM for intelligent selection
        self.tools = get_all_knowledge_tools(self.services)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Track conversation for ReAct
        self.conversation_history = []
    
    async def process_task(self, task: str) -> str:
        """
        MAIN ORCHESTRATOR INTERFACE
        
        Process knowledge request using ReAct framework.
        This is the primary function that the orchestrator should call.
        
        Args:
            task: User's question about financial concepts or app features
                Examples:
                - "What is compound interest?"
                - "How does the jar system work?"
                - "What budgeting features does the app have?"
                - "How do I track my subscriptions?"
                
        Returns:
            Final formatted answer from ReAct reasoning process
            
        Examples:
            process_task("What is compound interest?")
            → "Compound interest is the interest calculated on..."
            
            process_task("How does the jar system work?")
            → "The jar system helps you organize your budget..."
        """
        
        try:
            # Build ReAct system prompt  
            system_prompt = build_react_prompt()
            
            # Initialize conversation
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task)
            ]
            
            if settings.DEBUG_MODE:
                print(f"🔍 Processing query: {task}")
                print(f"🧠 System prompt length: {len(system_prompt)} chars")
            
            # ReAct Loop: Continue until respond() is called
            max_iterations = settings.MAX_REACT_ITERATIONS  
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1

                if settings.DEBUG_MODE:
                    print(f"\n🔄 ReAct Iteration {iteration}/{max_iterations}")
                    print("=" * 40)
                
                # Get LLM response with tools
                response = await self.llm_with_tools.ainvoke(messages)

                if settings.DEBUG_MODE:
                    print(f"🤖 LLM Response Type: {type(response)}")
                    if hasattr(response, 'content') and response.content:
                        print(f"💭 LLM Thinking: {response.content[:100]}...")
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        print(f"🔧 Tool Calls: {len(response.tool_calls)}")
                
                # Add AI message to conversation
                messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls if hasattr(response, 'tool_calls') else []))
                
                # Process tool calls if any
                if hasattr(response, 'tool_calls') and response.tool_calls:

                    if settings.DEBUG_MODE:
                        print(f"\n🔧 Processing {len(response.tool_calls)} tool call(s):")
                    
                    for i, tool_call in enumerate(response.tool_calls, 1):
                        tool_name = tool_call['name']
                        tool_args = tool_call.get('args', {})
                        tool_call_id = tool_call.get('id', f'call_{i}')

                        if settings.DEBUG_MODE:
                            print(f"\n📞 Call {i}: {tool_name}()")
                            print(f"📋 Parameters: {tool_args}")
                        
                        # Find and execute tool
                        tool_func = None
                        for tool in self.tools:
                            if tool.name == tool_name:
                                tool_func = tool
                                break
                        
                        if tool_func:
                            try:
                                result = await tool_func.ainvoke(tool_args)

                                
                                # Special handling for respond() tool - THIS IS THE KEY FIX
                                if tool_name == "respond" and isinstance(result, dict):
                                    final_answer = result.get("data", {}).get("final_answer", "")
                                    if settings.DEBUG_MODE:
                                        print(f"✅ Final answer received: {final_answer[:100]}...")
                                        print(f"🏁 ReAct completed in {iteration} iterations")
                                    return final_answer
                                
                                # Add tool result to conversation
                                messages.append(ToolMessage(
                                    content=str(result),
                                    tool_call_id=tool_call_id
                                ))

                                if settings.DEBUG_MODE:
                                    print(f"✅ Tool result: {str(result)[:150]}...")
                                    
                            except Exception as e:
                                error_msg = f"❌ Tool {tool_name} failed: {str(e)}"
                                messages.append(ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_call_id
                                ))
                                print(f"❌ Error: {error_msg}")
                        else:
                            error_msg = f"❌ Tool {tool_name} not found"
                            messages.append(ToolMessage(
                                content=error_msg,
                                tool_call_id=tool_call_id
                            ))
                            print(f"❌ Error: {error_msg}")
                    
                    # Continue the loop to let LLM process tool results and potentially call respond()
                    continue
                
                else:
                    # No tool calls - LLM provided direct response without tools
                    print("🤖 No tool calls - direct response")
                    return response.content if hasattr(response, 'content') else str(response)
            
            # If we reach here, max iterations exceeded without respond() being called
            print(f"⚠️ Max iterations ({max_iterations}) reached without respond() call")
            
            return f"❌ Could not provide a complete answer within {max_iterations} reasoning steps. Please try a simpler question."
                
        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
            print(f"🐛 Full error traceback:\n{traceback.format_exc()}")
            return error_msg


async def process_task(task: str, db: AsyncIOMotorDatabase, user_id: str) -> str:
    """
    MAIN ORCHESTRATOR INTERFACE
    
    Standalone function to process knowledge requests using Enhanced Pattern 2.
    This is the primary function that the orchestrator should call.
    
    Args:
        task: User's question about financial concepts or app features
        db: Database connection for user data
        user_id: User identifier for data isolation
        
    Returns:
        Knowledge response from ReAct reasoning process
        
    Examples:
        process_task("What is compound interest?", db, "user123")
        → "Compound interest is the interest calculated on..."
        
        process_task("How does the jar system work?", db, "user123")
        → "The jar system helps you organize your budget by..."
    """
    agent = KnowledgeBaseAgent(db, user_id)
    return await agent.process_task(task)


# Legacy function names for backward compatibility
def get_knowledge(user_query: str, db: AsyncIOMotorDatabase = None, user_id: str = None) -> str:
    """
    Legacy function name for backward compatibility.
    Use process_task() for new integrations.
    """
    if db is None or user_id is None:
        raise ValueError("Enhanced Pattern 2 requires db and user_id parameters")
    return process_task(user_query, db, user_id)


def get_knowledge_response(user_query: str, db: AsyncIOMotorDatabase = None, user_id: str = None) -> str:
    """
    Legacy function name for backward compatibility.
    Use process_task() for new integrations.
    """
    return get_knowledge(user_query, db, user_id)



# ============================================================================
# ORCHESTRATOR INTEGRATION INTERFACE  
# ============================================================================

# For orchestrator: Use process_task(task, db, user_id) as primary interface



