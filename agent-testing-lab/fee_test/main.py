"""
Fee Manager Agent - Main Logic
==============================

Core LLM-powered fee management system.
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
    FEE_MANAGER_TOOLS,
    
    # Utility functions
    fetch_existing_fees,
    fetch_available_jars,
    RecurringFee,
    FEES_STORAGE
)
from prompt import build_fee_manager_prompt

def setup_llm():
    """Initialize Gemini LLM with tools"""
    
    if not config.google_api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment")
        print("Please set your Gemini API key in .env file")
        sys.exit(1)
    
    try:
        # Initialize Gemini
        llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=config.temperature
        )
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(FEE_MANAGER_TOOLS)
        
        if config.debug_mode:
            print(f"✅ LLM initialized: {config.model_name}")
            print(f"🔧 Tools bound: {len(FEE_MANAGER_TOOLS)} tools")
        
        return llm_with_tools
        
    except Exception as e:
        # During development, show full error details
        import traceback
        error_details = traceback.format_exc()
        print(f"\n🐛 LLM SETUP ERROR:\n{error_details}")
        raise e  # Re-raise instead of sys.exit

def process_fee_request(user_input: str, llm_with_tools) -> str:
    """
    Main function: Process user fee request using LLM + tools
    
    Args:
        user_input: User's natural language fee description
        llm_with_tools: LLM instance with bound tools
        
    Returns:
        Response string from tool execution
    """
    
    try:
        # 1. Fetch context data
        existing_fees = fetch_existing_fees()
        available_jars = fetch_available_jars()
        
        # 2. Build complete prompt
        full_prompt = build_fee_manager_prompt(user_input, existing_fees, available_jars)
        
        if config.debug_mode:
            print(f"\n🧠 LLM Input:")
            print(f"User: {user_input}")
            print(f"Existing fees: {len(existing_fees)}")
            print(f"Available jars: {available_jars}")
        
        # 3. Send to LLM
        response = llm_with_tools.invoke([HumanMessage(content=full_prompt)])
        
        # 4. Execute tool calls (handle multiple tool calls like classifier)
        if response.tool_calls:
            results = []
            for i, tool_call in enumerate(response.tool_calls, 1):
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if config.debug_mode:
                    print(f"🔧 Executing tool {i}: {tool_name}")
                    print(f"📝 Tool args: {tool_args}")
                
                # Execute the tool function
                tool_function = None
                for tool in FEE_MANAGER_TOOLS:
                    if tool.name == tool_name:
                        tool_function = tool.func
                        break
                
                if tool_function:
                    result = tool_function(**tool_args)
                    
                    if config.debug_mode:
                        print(f"✅ Tool {i} result: {result}")
                    
                    # Format result with tool name for clarity (if multiple tools)
                    if len(response.tool_calls) > 1:
                        formatted_result = f"🔧 {tool_name}() → {result}"
                        results.append(f"{i}. {formatted_result}")
                    else:
                        results.append(result)
                else:
                    error_msg = f"❌ Unknown tool '{tool_name}'"
                    results.append(f"{i}. {error_msg}")
            
            # Return combined results
            if len(results) == 1:
                return results[0].replace("1. ", "") if results[0].startswith("1. ") else results[0]
            else:
                return "🔄 Multiple Operations:\n" + "\n".join(results)
        
        else:
            # LLM responded without tool call
            return f"❌ Error: LLM did not use any tools. Response: {response.content}"
            
    except Exception as e:
        # During development, show full error details
        import traceback
        error_details = traceback.format_exc()
        print(f"\n🐛 DEVELOPMENT ERROR:\n{error_details}")
        raise e  # Re-raise the exception instead of returning a string

def handle_confidence_flow(user_input: str, llm_with_tools) -> str:
    """
    Handle the confidence-based flow for fee management
    
    This function processes the initial request and may trigger
    confirmation or clarification flows based on LLM confidence.
    """
    
    result = process_fee_request(user_input, llm_with_tools)
    
    # Check if result is a confirmation request
    if result.startswith("❓") and "Confidence:" in result:
        # This is a confidence-based confirmation
        print(f"\n{result}")
        
        # In a real system, this would wait for user input
        # For testing, we'll return the confirmation request
        return result
    
    # Check if result is a clarification request  
    elif result.startswith("❓") and "Confidence:" not in result:
        # This is a clarification request
        print(f"\n{result}")
        return result
    
    # Direct action was taken
    return result

def get_fee_summary() -> str:
    """Get a detailed summary of all current fees for development tracking"""
    
    fees = fetch_existing_fees()
    active_fees = [f for f in fees if f.is_active]
    inactive_fees = [f for f in fees if not f.is_active]
    
    print(f"\n🔍 DEBUG: Total fees in storage: {len(fees)}")
    print(f"🔍 DEBUG: Active fees: {len(active_fees)}")
    print(f"🔍 DEBUG: Inactive fees: {len(inactive_fees)}")
    
    if not active_fees:
        return "📋 No active recurring fees"
    
    summary = f"📋 Fee Summary ({len(active_fees)} active fees):\n"
    
    # Group by jar
    by_jar = {}
    total_monthly = 0.0
    
    for i, fee in enumerate(active_fees):
        print(f"\n🔍 DEBUG Fee {i+1}: {fee.name}")
        print(f"   Type: {type(fee.pattern_details)} = {fee.pattern_details}")
        print(f"   Pattern: {fee.pattern_type}")
        print(f"   Amount: ${fee.amount}")
        print(f"   Jar: {fee.target_jar}")
        
        if fee.target_jar not in by_jar:
            by_jar[fee.target_jar] = []
        by_jar[fee.target_jar].append(fee)
        
        # Rough monthly calculation for summary
        if fee.pattern_type == "daily":
            monthly_amount = fee.amount * 30
            print(f"   Monthly calc (daily): ${fee.amount} * 30 = ${monthly_amount}")
            total_monthly += monthly_amount
        elif fee.pattern_type == "weekly":
            # Handle pattern_details as list or None
            pattern_details = fee.pattern_details
            print(f"   Raw pattern_details: {type(pattern_details)} = {pattern_details}")
            
            if pattern_details is None:
                days_count = 7  # Every day of the week
                print(f"   Days count: {days_count} (every day)")
            else:
                days_count = len(pattern_details)
                print(f"   Days count: {days_count} (specific days: {pattern_details})")
            
            monthly_amount = fee.amount * days_count * 4
            print(f"   Monthly calc (weekly): ${fee.amount} * {days_count} * 4 = ${monthly_amount}")
            total_monthly += monthly_amount
        elif fee.pattern_type == "monthly":
            # Handle pattern_details as list or None
            pattern_details = fee.pattern_details
            if pattern_details is None:
                days_count = 30  # Every day of the month
                monthly_amount = fee.amount * days_count
                print(f"   Monthly calc (monthly, every day): ${fee.amount} * {days_count} = ${monthly_amount}")
            else:
                days_count = len(pattern_details)
                monthly_amount = fee.amount * days_count
                print(f"   Monthly calc (monthly, specific days): ${fee.amount} * {days_count} = ${monthly_amount}")
            total_monthly += monthly_amount
    
    print(f"\n🔍 DEBUG: Calculated total monthly: ${total_monthly}")
    
    for jar, jar_fees in by_jar.items():
        summary += f"\n{jar.upper()} JAR ({len(jar_fees)} fees):\n"
        for fee in jar_fees:
            summary += f"  • {fee.name}: {fee.description} - ${fee.amount} {fee.pattern_type}"
            summary += f" | Next: {fee.next_occurrence.strftime('%Y-%m-%d')}\n"
    
    summary += f"\n💰 Estimated monthly total: ${total_monthly:.2f}"
    
    # Also show inactive fees if any
    if inactive_fees:
        summary += f"\n\n❌ INACTIVE FEES ({len(inactive_fees)}):\n"
        for fee in inactive_fees:
            summary += f"  • {fee.name} - ${fee.amount} {fee.pattern_type} (disabled)\n"
    
    return summary

# === TEST HELPERS ===

def run_test_scenarios():
    """Run some test scenarios to validate the system"""
    
    print("🧪 Running Fee Manager Test Scenarios")
    print("=" * 50)
    
    llm_with_tools = setup_llm()
    
    test_cases = [
        "5 dollar daily for coffee",
        "10 dollar every Monday and Friday for commute", 
        "YouTube Premium 15.99 monthly",
        "list my fees",
        "stop my coffee fee",
        "change bus fare to 12 dollars",
        "30k mỗi thứ hai cho xe buýt",  # Vietnamese
        "subscription for stuff",  # Ambiguous - should ask for clarification
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_input} ---")
        
        result = handle_confidence_flow(test_input, llm_with_tools)
        print(f"Result: {result}")
        
        if i == len(test_cases) // 2:
            print(f"\n{get_fee_summary()}")

if __name__ == "__main__":
    # Run test scenarios when called directly
    run_test_scenarios()
