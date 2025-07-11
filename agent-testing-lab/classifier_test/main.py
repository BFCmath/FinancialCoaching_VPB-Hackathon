"""
Main LLM-Powered Transaction Classifier
========================================

Core function that uses Gemini to classify transactions and call appropriate tools.
Supports multiple transactions with multiple tool calls in a single response.
"""

import json
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from config import config
from tools import CLASSIFICATION_TOOLS
from prompt import build_classification_prompt


def create_llm_with_tools():
    """Create Gemini LLM instance with classification tools bound."""
    if not config.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required")
    
    # Create Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=config.google_api_key
    )
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(CLASSIFICATION_TOOLS)
    
    return llm_with_tools


def classify_and_add_transaction(user_input: str) -> str:
    """
    Main classification function - analyzes transaction and takes appropriate action.
    Supports multiple transactions in a single input with multiple tool calls.
    
    Args:
        user_input: User's transaction input (e.g., "meal 20 dollar", "coffee 5, gas 50")
        
    Returns:
        Result message from all executed tool calls
    """
    try:
        # Create LLM with tools
        llm_with_tools = create_llm_with_tools()
        
        # Build complete prompt with context
        prompt = build_classification_prompt(user_input, number_of_transactions=50)
        
        if config.debug_mode:
            print(f"🔍 Prompt sent to LLM:\n{prompt}\n")
        
        # Get LLM response with tool calls
        response = llm_with_tools.invoke(prompt)
        
        if config.debug_mode:
            print(f"🤖 LLM Response: {response}")
            print(f"🛠️  Tool calls: {response.tool_calls}")
        
        # Check if LLM made tool calls
        if not response.tool_calls:
            return "❌ Error: LLM did not call any classification tool. Please try again."
        
        # Process ALL tool calls from LLM
        results = []
        for i, tool_call in enumerate(response.tool_calls, 1):
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            if config.debug_mode:
                print(f"🔧 Executing tool {i}: {tool_name} with args: {tool_args}")
            
            # Find and execute the tool
            tool_result = None
            for tool in CLASSIFICATION_TOOLS:
                if tool.name == tool_name:
                    tool_result = tool.invoke(tool_args)
                    break
            
            if tool_result is None:
                tool_result = f"❌ Unknown tool '{tool_name}'"
            
            # Format result with tool name for clarity
            formatted_result = f"🔧 {tool_name}() → {tool_result}"
            results.append(f"{i}. {formatted_result}")
        
        # Return combined results
        if len(results) == 1:
            return results[0].replace("1. ", "")  # Remove numbering for single result
        else:
            return "🔄 Multiple Transactions Processed:\n" + "\n".join(results)
        
    except Exception as e:
        if config.debug_mode:
            import traceback
            traceback.print_exc()
        return f"❌ Error during classification: {str(e)}"


def classify_simple(user_input: str) -> str:
    """
    Simplified classification for basic testing without full context.
    
    Args:
        user_input: Simple transaction input
        
    Returns:
        Classification result
    """
    try:
        from prompt import build_simple_prompt
        
        llm_with_tools = create_llm_with_tools()
        prompt = build_simple_prompt(user_input)
        
        response = llm_with_tools.invoke(prompt)
        
        if not response.tool_calls:
            return "❌ No tool called"
        
        # Handle multiple tool calls in simple mode too
        results = []
        for i, tool_call in enumerate(response.tool_calls, 1):
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            # Execute tool
            for tool in CLASSIFICATION_TOOLS:
                if tool.name == tool_name:
                    result = tool.invoke(tool_args)
                    formatted_result = f"🔧 {tool_name}() → {result}"
                    results.append(f"{i}. {formatted_result}")
                    break
        
        if len(results) == 1:
            return results[0].replace("1. ", "")
        else:
            return "\n".join(results)
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


if __name__ == "__main__":
    # Test with both single and multiple transactions
    test_inputs = [
        "meal 20 dollar",
        "coffee 5, gas 50",
        "snack 10 dollar",  # Should have lower confidence
        "tôi ăn cơm 25k, mua xăng 100k", 
        "chicken rice 10, youtube subscription 100, medicine bill 100"
    ]
    
    print("🧪 Testing Transaction Classifier with Confidence Scores")
    print("=" * 60)
    
    for test_input in test_inputs:
        print(f"\n📝 Input: '{test_input}'")
        result = classify_and_add_transaction(test_input)
        print(f"🎯 Result: {result}")
        print("-" * 60)
