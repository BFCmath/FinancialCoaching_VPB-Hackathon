"""
Jar Manager Agent - Main Logic
==============================

Core LLM-powered jar management system.
"""

import sys
from typing import List, Optional

# LLM imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Local imports
from config import config
from tools import (
    # LLM Tools list
    JAR_MANAGER_TOOLS,
    
    # Utility functions
    fetch_existing_jars,
    JARS_STORAGE
)
from prompt import build_jar_manager_prompt

def setup_llm():
    """Initialize Gemini LLM with tools"""
    
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
        llm_with_tools = llm.bind_tools(JAR_MANAGER_TOOLS)
        
        if config.debug_mode:
            print(f"✅ LLM initialized: {config.model_name}")
            print(f"🔧 Tools bound: {len(JAR_MANAGER_TOOLS)} tools")
        
        return llm_with_tools
    
    except Exception as e:
        print(f"❌ Error setting up LLM: {e}")
        return None

def handle_confidence_flow(user_input: str, llm_with_tools) -> str:
    """Handle confidence-based jar operations flow"""
    
    try:
        # Get current context
        existing_jars = fetch_existing_jars()
        from tools import TOTAL_INCOME
        
        # Build prompt with context including total income
        system_prompt = build_jar_manager_prompt(user_input, existing_jars, TOTAL_INCOME)
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]
        
        if config.debug_mode:
            print(f"\n🧠 System Prompt Length: {len(system_prompt)} chars")
            print(f"📝 User Input: {user_input}")
        
        # Invoke LLM with tools
        response = llm_with_tools.invoke(messages)
        
        if config.debug_mode:
            print(f"🤖 LLM Response Type: {type(response)}")
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"🔧 Tool Calls: {len(response.tool_calls)}")
                for i, call in enumerate(response.tool_calls):
                    print(f"   {i+1}. {call['name']} with {len(call.get('args', {}))} args")
        
        # Process response and tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            results = []
            
            # Header to show what function(s) were called
            print(f"\n🔧 AI Function Calls ({len(response.tool_calls)} call(s)):")
            print("=" * 50)
            
            for i, tool_call in enumerate(response.tool_calls, 1):
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                
                # Show function call details
                print(f"\n📞 Call {i}: {tool_name}()")
                print(f"📋 Parameters:")
                for param, value in tool_args.items():
                    if isinstance(value, list):
                        print(f"   • {param}: {value}")
                    else:
                        print(f"   • {param}: {repr(value)}")
                
                # Find and execute tool
                tool_func = None
                for tool in JAR_MANAGER_TOOLS:
                    if tool.name == tool_name:
                        tool_func = tool
                        break
                
                if tool_func:
                    try:
                        result = tool_func.invoke(tool_args)
                        results.append(result)
                        print(f"✅ Result: {result}")
                        if config.debug_mode:
                            print(f"🔧 Debug: Tool {tool_name} executed successfully")
                    except Exception as e:
                        error_msg = f"❌ Tool {tool_name} failed: {str(e)}"
                        results.append(error_msg)
                        print(f"❌ Error: {error_msg}")
                        if config.debug_mode:
                            print(error_msg)
                else:
                    error_msg = f"❌ Tool {tool_name} not found"
                    results.append(error_msg)
                    print(f"❌ Error: {error_msg}")
                    if config.debug_mode:
                        print(error_msg)
            
            print("=" * 50)
            return "\n".join(results)
        
        else:
            # No tool calls - return LLM's direct response
            return response.content if hasattr(response, 'content') else str(response)
    
    except Exception as e:
        error_msg = f"❌ Error processing request: {str(e)}"
        if config.debug_mode:
            import traceback
            print(f"🐛 Full error traceback:\n{traceback.format_exc()}")
        return error_msg

def get_jar_summary() -> str:
    """Get a summary of current jar status with multi-jar system support"""
    
    jars = fetch_existing_jars()
    
    if not jars:
        return f"📋 No jars found. Total income: ${TOTAL_INCOME:,.2f}"
    
    # Import TOTAL_INCOME for calculations
    from tools import TOTAL_INCOME, calculate_budget_from_percent, calculate_current_amount_from_percent, format_percent_display
    
    # Sort by percentage allocation (descending)
    jars.sort(key=lambda j: j["percent"], reverse=True)
    
    # Format jar list
    jar_list = []
    total_current_percent = 0.0
    total_percent = 0.0
    
    for jar in jars:
        # Calculate dollar amounts from percentages
        current_amount = calculate_current_amount_from_percent(jar['current_percent'])
        budget_amount = calculate_budget_from_percent(jar['percent'])
        
        # Format display
        current_display = format_percent_display(jar['current_percent'])
        percent_display = format_percent_display(jar['percent'])
        
        jar_list.append(
            f"• {jar['name']}: ${current_amount:.2f}/${budget_amount:.2f} "
            f"({current_display}/{percent_display}) - {jar['description']}"
        )
        
        total_current_percent += jar["current_percent"]
        total_percent += jar["percent"]
    
    # Calculate total amounts
    total_current_amount = calculate_current_amount_from_percent(total_current_percent)
    total_budget_amount = calculate_budget_from_percent(total_percent)
    
    header = f"📋 Budget Jars ({len(jars)} jars) - Total Income: ${TOTAL_INCOME:,.2f}"
    footer = (f"\n💰 Totals: ${total_current_amount:.2f}/${total_budget_amount:.2f} "
              f"({format_percent_display(total_current_percent)}/{format_percent_display(total_percent)})")
    
    return header + "\n" + "\n".join(jar_list) + footer

def main():
    """Main entry point for testing jar manager functionality"""
    
    print("🧪 Jar Manager Development Test")
    print("=" * 40)
    
    # Setup LLM
    llm_with_tools = setup_llm()
    if not llm_with_tools:
        sys.exit(1)
    
    # Show current jar status
    print("\n" + get_jar_summary())
    
    # Test examples for multi-jar system
    test_inputs = [
        "list my jars",
        "create vacation jar with 15%",
        "create emergency fund with $1000",
        "show jar summary"
    ]
    
    print(f"\n🧪 Running {len(test_inputs)} test scenarios...")
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n--- Test {i}: {test_input} ---")
        result = handle_confidence_flow(test_input, llm_with_tools)
        print(result)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
