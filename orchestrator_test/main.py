"""
Multi-Worker Orchestrator Prompt Tester
=======================================

Tests if orchestrator prompts can correctly analyze, decompose, and route
user requests to multiple workers with specific task descriptions.

Goal: Test prompt quality for parallel tool calling and routing.
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Import simplified modules
from config import config
from tools import ALL_TOOLS
from prompt import ROUTING_PROMPT


class MultiWorkerOrchestrator:
    """Orchestrator for testing parallel tool calling prompts."""
    
    def __init__(self):
        if not config.google_api_key:
            print("❌ ERROR: GOOGLE_API_KEY not found!")
            exit(1)
        
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            google_api_key=config.google_api_key
        )
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        
        if config.debug_mode:
            print(f"🔧 Model: {config.model_name}")
            print(f"🌡️  Temperature: {config.temperature}")
    
    def analyze_request(self, user_input: str) -> Dict[str, Any]:
        """Analyze user request and route to appropriate workers."""
        
        try:
            # Create messages for LLM
            messages = [
                SystemMessage(content=ROUTING_PROMPT),
                HumanMessage(content=user_input)
            ]
            
            if config.debug_mode:
                print(f"🔍 DEBUG - Analyzing: {user_input}")
            
            # Get LLM response with tools
            response = self.llm_with_tools.invoke(messages)
            
            if config.debug_mode:
                print(f"🔍 DEBUG - Tool calls: {len(response.tool_calls) if response.tool_calls else 0}")
            
            # Process tool calls (can be multiple now)
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_calls = []
                for tool_call in response.tool_calls:
                    # LangChain tool call structure for Gemini
                    tool_calls.append({
                        "tool_name": tool_call['name'],
                        "arguments": tool_call['args']
                    })
                
                return {
                    "success": True,
                    "tool_calls": tool_calls,
                    "num_tools": len(tool_calls),
                    "raw_response": response.content
                }
            else:
                return {
                    "success": False,
                    "error": "No tool call generated",
                    "raw_response": response.content
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": None
            }

    def display_result(self, user_input: str, result: Dict[str, Any]) -> None:
        """Display the routing result in a clear format."""
        
        print(f"\n{'='*80}")
        print(f"📝 USER INPUT: {user_input}")
        print(f"{'='*80}")
        
        if not result["success"]:
            print(f"❌ ERROR: {result['error']}")
            if result["raw_response"]:
                print(f"💬 Raw response: {result['raw_response']}")
            return
        
        tool_calls = result["tool_calls"]
        num_tools = result["num_tools"]
        
        if num_tools == 1:
            print(f"🎯 SINGLE TOOL CALL")
        else:
            print(f"🔄 PARALLEL TOOL CALLS ({num_tools} tools)")
        
        print(f"{'─'*50}")
        
        # Display each tool call
        for i, tool_call in enumerate(tool_calls, 1):
            tool_name = tool_call["tool_name"]
            args = tool_call["arguments"]
            
            # Extract worker name for display
            if tool_name.startswith("route_to_"):
                worker = tool_name.replace("route_to_", "")
            elif tool_name == "provide_direct_response":
                worker = "direct_response"
            else:
                worker = tool_name
            
            print(f"  {i}. 🤖 {worker.upper()}")
            
            # Display relevant arguments
            if "task_description" in args:
                print(f"     📋 Task: {args['task_description']}")
            elif "query" in args:
                print(f"     ❓ Query: {args['query']}")
            elif "response_text" in args:
                print(f"     💬 Response: {args['response_text']}")
            else:
                print(f"     📄 Arguments: {args}")
            
            if i < num_tools:  # Add separator between tools
                print()
        
        if config.debug_mode and result["raw_response"]:
            print(f"\n🔍 DEBUG - Raw response: {result['raw_response']}")


def main():
    """Main function for testing orchestrator prompts."""
    
    # Initialize orchestrator
    orchestrator = MultiWorkerOrchestrator()
    
    print("🚀 Multi-Worker Orchestrator Test Lab")
    print("="*60)
    print(f"🤖 Model: {config.model_name}")
    print("="*60)
    
    # Test examples
    test_inputs = [
        "Add vacation jar 10%",
        "I spent $100 on groceries and want to add a vacation jar with 15%",
        "Help me with my finances - I spent money on dining and need a savings plan",
        "What is compound interest?",
        "Hello"
    ]
    
    print("\n🧪 RUNNING TEST EXAMPLES:")
    print("─" * 80)
    
    for test_input in test_inputs:
        result = orchestrator.analyze_request(test_input)
        orchestrator.display_result(test_input, result)
        print("\n" + "─" * 80)
    
    print(f"\n🎯 Ready for interactive testing! Run 'python test.py' to start.")
    print("\n✅ Multi-worker orchestrator test completed successfully!")


if __name__ == "__main__":
    main()
