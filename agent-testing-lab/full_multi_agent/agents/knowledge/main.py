"""
Knowledge Base Agent - ReAct Framework
=====================================

Main agent that handles financial knowledge and app documentation questions
using a ReAct (Reason-Act) framework with proper LangChain tool calling.

ORCHESTRATOR INTERFACE:
- get_knowledge(user_query: str) -> str
"""

from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from tools import get_all_knowledge_tools
from prompt import build_react_prompt
import config


class KnowledgeBaseAgent:
    """Knowledge Base Agent using ReAct framework with proper LangChain tool calling"""
    
    def __init__(self):
        """Initialize the agent with LLM and tools"""
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.llm_temperature
        )
        
        # Bind all tools to LLM for intelligent selection
        self.tools = get_all_knowledge_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Track conversation for ReAct
        self.conversation_history = []
    
    def get_knowledge(self, user_query: str) -> str:
        """
        MAIN ORCHESTRATOR INTERFACE
        
        Get knowledge using proper ReAct framework.
        This is the primary function that the orchestrator should call.
        
        Args:
            user_query: User's question about financial concepts or app features
                Examples:
                - "What is compound interest?"
                - "How does the jar system work?"
                - "What budgeting features does the app have?"
                - "How do I track my subscriptions?"
                
        Returns:
            Final formatted answer from ReAct reasoning process
            
        Examples:
            get_knowledge("What is compound interest?")
            → "Compound interest is the interest calculated on..."
            
            get_knowledge("How does the jar system work?")
            → "The jar system helps you organize your budget..."
        """
        
        try:
            # Build ReAct system prompt  
            system_prompt = build_react_prompt()
            
            # Initialize conversation
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]
            
            if config.debug_mode:
                print(f"🔍 Processing query: {user_query}")
                print(f"🧠 System prompt length: {len(system_prompt)} chars")
            
            # ReAct Loop: Continue until respond() is called
            max_iterations = config.max_react_iterations
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                if config.debug_mode:
                    print(f"\n🔄 ReAct Iteration {iteration}/{max_iterations}")
                    print("=" * 40)
                
                # Get LLM response with tools
                response = self.llm_with_tools.invoke(messages)
                
                if config.debug_mode:
                    print(f"🤖 LLM Response Type: {type(response)}")
                    if hasattr(response, 'content') and response.content:
                        print(f"💭 LLM Thinking: {response.content[:100]}...")
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        print(f"🔧 Tool Calls: {len(response.tool_calls)}")
                
                # Add AI message to conversation
                messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls if hasattr(response, 'tool_calls') else []))
                
                # Process tool calls if any
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    
                    if config.debug_mode:
                        print(f"\n🔧 Processing {len(response.tool_calls)} tool call(s):")
                    
                    for i, tool_call in enumerate(response.tool_calls, 1):
                        tool_name = tool_call['name']
                        tool_args = tool_call.get('args', {})
                        tool_call_id = tool_call.get('id', f'call_{i}')
                        
                        if config.debug_mode:
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
                                result = tool_func.invoke(tool_args)
                                
                                # Special handling for respond() tool - THIS IS THE KEY FIX
                                if tool_name == "respond" and isinstance(result, dict):
                                    final_answer = result.get("data", {}).get("final_answer", "")
                                    if config.debug_mode:
                                        print(f"✅ Final answer received: {final_answer[:100]}...")
                                        print(f"🏁 ReAct completed in {iteration} iterations")
                                    return final_answer
                                
                                # Add tool result to conversation
                                messages.append(ToolMessage(
                                    content=str(result),
                                    tool_call_id=tool_call_id
                                ))
                                
                                if config.debug_mode:
                                    print(f"✅ Tool result: {str(result)[:150]}...")
                                    
                            except Exception as e:
                                error_msg = f"❌ Tool {tool_name} failed: {str(e)}"
                                messages.append(ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_call_id
                                ))
                                if config.debug_mode:
                                    print(f"❌ Error: {error_msg}")
                        else:
                            error_msg = f"❌ Tool {tool_name} not found"
                            messages.append(ToolMessage(
                                content=error_msg,
                                tool_call_id=tool_call_id
                            ))
                            if config.debug_mode:
                                print(f"❌ Error: {error_msg}")
                    
                    # Continue the loop to let LLM process tool results and potentially call respond()
                    continue
                
                else:
                    # No tool calls - LLM provided direct response without tools
                    if config.debug_mode:
                        print("🤖 No tool calls - direct response")
                    return response.content if hasattr(response, 'content') else str(response)
            
            # If we reach here, max iterations exceeded without respond() being called
            if config.debug_mode:
                print(f"⚠️ Max iterations ({max_iterations}) reached without respond() call")
            
            return f"❌ Could not provide a complete answer within {max_iterations} reasoning steps. Please try a simpler question."
                
        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
            if config.debug_mode:
                import traceback
                print(f"🐛 Full error traceback:\n{traceback.format_exc()}")
            return error_msg


def get_knowledge(user_query: str) -> str:
    """
    MAIN ORCHESTRATOR INTERFACE
    
    Standalone function to get knowledge using ReAct framework.
    This is the primary function that the orchestrator should call.
    
    Args:
        user_query: User's question about financial concepts or app features
        
    Returns:
        Knowledge response from ReAct reasoning process
        
    Examples:
        get_knowledge("What is compound interest?")
        → "Compound interest is the interest calculated on..."
        
        get_knowledge("How does the jar system work?")
        → "The jar system helps you organize your budget by..."
    """
    agent = KnowledgeBaseAgent()
    return agent.get_knowledge(user_query)


def get_knowledge_response(user_query: str) -> str:
    """
    Legacy function name for backward compatibility.
    Use get_knowledge() for new integrations.
    """
    return get_knowledge(user_query)


def quick_knowledge_test():
    """Quick test of knowledge agent functionality"""
    
    test_queries = [
        "What is compound interest?",
        "How does the jar system work?", 
        "What budgeting features does the app have?",
        "Tell me about subscription tracking"
    ]
    
    print("🧪 Testing Knowledge Agent with Service Integration")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        try:
            result = get_knowledge(query)
            print(f"🎯 Result: {result[:200]}...")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        print("-" * 60)


# ============================================================================
# ORCHESTRATOR INTEGRATION INTERFACE  
# ============================================================================

def process_task(task: str) -> str:
    """
    Simple interface for orchestrator to call this agent.
    
    Args:
        task: User's knowledge request task
        
    Returns:
        Knowledge response
    """
    return get_knowledge(task)


if __name__ == "__main__":
    quick_knowledge_test()
