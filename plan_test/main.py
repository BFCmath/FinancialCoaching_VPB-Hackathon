"""
Budget Advisor Agent - Main Logic
=================================

Core LLM-powered financial advisory system using ReAct framework.
"""

import sys
from typing import List, Optional, Dict, Any

# LLM imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

# Local imports
from config import config
from tools import (
    transaction_fetcher,
    get_plan,
    adjust_plan,
    create_plan,
    get_jar,
    respond,
    BUDGET_PLANS_STORAGE
)
from prompt import build_budget_advisor_prompt

# All Budget Advisor tools
BUDGET_ADVISOR_TOOLS = [
    transaction_fetcher,
    get_plan,
    adjust_plan,
    create_plan,
    get_jar,
    respond
]

def setup_llm():
    """Initialize Gemini LLM with Budget Advisor tools"""
    
    if not config.google_api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment")
        print("Please set your Gemini API key in .env file")
        return None
    
    try:
        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.temperature
        )
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(BUDGET_ADVISOR_TOOLS)
        
        if config.debug_mode:
            print(f"✅ LLM initialized: {config.model_name}")
            print(f"🔧 Tools bound: {len(BUDGET_ADVISOR_TOOLS)} tools")
        
        return llm_with_tools
    
    except Exception as e:
        print(f"❌ Error setting up LLM: {e}")
        return None

def get_financial_context() -> Dict[str, Any]:
    """Get minimal financial context - only active plans"""
    
    context = {}
    
    # Get current budget plans - only active ones for context
    if BUDGET_PLANS_STORAGE:
        active_plans = [p for p in BUDGET_PLANS_STORAGE.values() if p.get("status") == "active"]
        if active_plans:
            context["current_plans"] = active_plans
    
    return context

def provide_budget_advice(user_input: str, llm_with_tools, conversation_history=None) -> str:
    """
    Provide financial advice using ReAct framework.
    
    Args:
        user_input: User's financial question or request
        llm_with_tools: LLM with bound tools
        conversation_history: Optional list of (user_input, agent_response) tuples for memory
        
    Returns:
        Final advisory response
    """
    # Get context and build prompt
    context = get_financial_context()
    system_prompt = build_budget_advisor_prompt(user_input, context, conversation_history)
    
    # Initialize conversation
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    
    if config.debug_mode:
        print(f"\n🧠 System Prompt Length: {len(system_prompt)} chars")
        print(f"📝 User Input: {user_input}")
    
    # ReAct Loop: Continue until respond() is called
    max_iterations = config.max_react_iterations
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        if config.debug_mode:
            print(f"\n🔄 ReAct Iteration {iteration}/{max_iterations}")
            print("=" * 40)
        
        # Get LLM response with tools
        response = llm_with_tools.invoke(messages)
        
        if config.debug_mode:
            print(f"🤖 LLM Response Type: {type(response)}")
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"🔧 Tool Calls: {len(response.tool_calls)}")
        
        # Add AI message to conversation
        messages.append(AIMessage(
            content=response.content if hasattr(response, 'content') else "",
            tool_calls=response.tool_calls if hasattr(response, 'tool_calls') else []
        ))
        
        # Process tool calls if any
        if hasattr(response, 'tool_calls') and response.tool_calls:
            
            # Header for function calls
            print(f"\n🔧 Budget Advisor Actions ({len(response.tool_calls)} call(s)):")
            print("=" * 50)
            
            for i, tool_call in enumerate(response.tool_calls, 1):
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                tool_call_id = tool_call.get('id', f'call_{i}')
                
                # Show function call details
                print(f"\n📞 Action {i}: {tool_name}()")
                print(f"📋 Parameters:")
                for param, value in tool_args.items():
                    print(f"   • {param}: {repr(value)}")
                
                # Find and execute tool
                tool_func = None
                for tool in BUDGET_ADVISOR_TOOLS:
                    if tool.name == tool_name:
                        tool_func = tool
                        break
                
                if tool_func:
                    print(f"🔧 Invoking tool: {tool_name}")
                    result = tool_func.invoke(tool_args)
                    print(f"✅ Result: {result}")
                    
                    # Special handling for respond() tool - completion check
                    if tool_name == "respond" and isinstance(result, dict):
                        data = result.get("data", {})
                        if data.get("summary"):
                            print("🎯 Budget Advisory session completed")
                            response_parts = [data.get("summary", "")]
                            if data.get("advice"):
                                response_parts.append(f"\n\nRecommendations:\n{data.get('advice')}")
                            if data.get("question_ask_user"):
                                response_parts.append(f"\n\nQuestion for you:\n{data.get('question_ask_user')}")
                            return "".join(response_parts)
                    
                    # Add tool result to conversation
                    messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call_id
                    ))
                    
                    print(f"🔧 Debug: Tool {tool_name} executed successfully")
                else:
                    error_msg = f"❌ Tool {tool_name} not found"
                    print(f"❌ Error: {error_msg}")
                    messages.append(ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call_id
                    ))
                    print(error_msg)
            
            print("=" * 50)
            # Continue the loop to let LLM process tool results
            continue
        
        else:
            # No tool calls - LLM provided direct response
            if config.debug_mode:
                print("💬 Direct LLM response (no tool calls)")
            return response.content if hasattr(response, 'content') else str(response)
    
    # If we reach here, max iterations exceeded
    if config.debug_mode:
        print(f"⚠️ Max iterations ({max_iterations}) reached without respond() call")
    
    return f"❌ Could not provide a complete answer within {max_iterations} reasoning steps. Please try a simpler question."

def get_budget_summary() -> str:
    """Get a summary of current financial status"""
    
    plan_count = len(BUDGET_PLANS_STORAGE)
    active_plans = len([p for p in BUDGET_PLANS_STORAGE.values() if p.get("status") == "active"])
    
    summary_parts = [
        f"📋 Budget Plans: {plan_count} total ({active_plans} active)"
    ]
    
    # Get jar information
    from tool_agent.jar.tools import fetch_existing_jars
    jars = fetch_existing_jars()
    summary_parts.append(f"🏺 Budget Jars: {len(jars)} configured")
    
    return "\n".join(summary_parts)

def main():
    """Main entry point for Budget Advisor testing"""
    
    print("💰 Budget Advisor Development Test")
    print("=" * 40)
    
    # Setup LLM
    llm_with_tools = setup_llm()
    if not llm_with_tools:
        print("❌ Failed to setup LLM. Exiting.")
        return
    
    # Show financial summary
    print("\n📊 Financial Status:")
    print(get_budget_summary())
    
    # Interactive testing
    print(f"\n🤖 Budget Advisor ready! (Max {config.max_react_iterations} iterations)")
    print("Type 'quit' to exit, 'examples' to see example queries")
    
    while True:
        try:
            user_input = input("\n💬 Your financial question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for using Budget Advisor!")
                break
            
            if user_input.lower() in ['examples', 'help']:
                print("\n📝 Example queries:")
                examples = [
                    "How is my spending this month compared to my budget?",
                    "I want to save for a vacation to Japan",
                    "Can you optimize my budget allocation?",
                    "Where am I overspending the most?",
                    "Help me create an emergency fund plan",
                    "Tôi muốn tiết kiệm tiền cho kỳ nghỉ"
                ]
                for i, example in enumerate(examples, 1):
                    print(f"   {i}. {example}")
                continue
            
            if not user_input:
                print("Please enter a financial question or request.")
                continue
            
            # Provide financial advice
            print(f"\n🤖 Analyzing your request...")
            result = provide_budget_advice(user_input, llm_with_tools)
            
            if config.verbose_logging:
                print(f"\n🔍 Full result:\n{result}")
            
        except KeyboardInterrupt:
            print("\n👋 Budget Advisor session ended.")
            break

# Convenience function for external usage
def get_budget_advice(user_query: str) -> str:
    """
    Simple function to get budget advice programmatically.
    
    Args:
        user_query: User's financial question
        
    Returns:
        Advisory response
    """
    llm_with_tools = setup_llm()
    if not llm_with_tools:
        return "❌ Error: Could not initialize Budget Advisor"
    
    return provide_budget_advice(user_query, llm_with_tools)

if __name__ == "__main__":
    main()
