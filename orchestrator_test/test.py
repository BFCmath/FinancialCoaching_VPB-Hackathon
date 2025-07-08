"""
Multi-Worker Prompt Testing Interface
====================================

Interactive tool to test orchestrator parallel tool calling prompts.
Focus: Can the prompt call multiple worker tools directly in parallel?
"""

from typing import Dict, Any

from main import MultiWorkerOrchestrator
from config import config


class MultiWorkerPromptTester:
    """Interactive interface for testing parallel tool calling prompts."""
    
    def __init__(self):
        """Initialize the prompt tester."""
        self.orchestrator = MultiWorkerOrchestrator()
        
    def run_interactive_test(self):
        """Interactive test loop."""
        self.show_welcome()
        
        while True:
            try:
                user_input = input("\n👤 Test input: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() in ['help', 'h']:
                    self.show_help()
                elif user_input.lower() in ['examples', 'e']:
                    self.show_examples()
                elif user_input.lower() in ['multi', 'm']:
                    self.test_multi_tool_examples()
                elif user_input.lower() in ['simple', 'single']:
                    self.test_simple_examples()
                elif user_input:
                    # Test the user input
                    result = self.orchestrator.analyze_request(user_input)
                    self.orchestrator.display_result(user_input, result)
                    self.evaluate_result(user_input, result)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_welcome(self):
        """Show welcome message and instructions."""
        print("🚀 Multi-Worker Orchestrator Prompt Tester")
        print("=" * 60)
        print(f"🤖 Model: {config.model_name}")
        print("=" * 60)
        print()
        print("This tool tests if prompts can:")
        print("  • Call single tools for simple requests")
        print("  • Call multiple tools in parallel for complex requests")
        print("  • Handle unclear requests with clarification")
        print()
        print("Commands:")
        print("  help (h)      - Show help")
        print("  examples (e)  - Show example inputs")
        print("  multi (m)     - Test parallel tool examples")
        print("  simple        - Test single tool examples")
        print("  quit (q)      - Exit")
        print()
        print("Just type any request to test tool calling!")
    
    def show_help(self):
        """Show help message."""
        print("\n📚 HELP - How to Test Parallel Tool Calling")
        print("=" * 50)
        print()
        print("🎯 SIMPLE REQUESTS (should call 1 tool):")
        print("  • Add vacation jar 10%")
        print("  • I spent $50 on groceries")
        print("  • Help me save for a car")
        print("  • What is compound interest?")
        print("  • Hello")
        print()
        print("🎯 COMPLEX REQUESTS (should call multiple tools):")
        print("  • I spent $100 on groceries and want to add a vacation jar with 15%")
        print("  • Log my $200 car repair and help me plan to save for future repairs")
        print("  • Create emergency fund jar with 20%, explain emergency funds, and log my $150 medical bill")
        print()
        print("🎯 UNCLEAR REQUESTS (should ask for clarification):")
        print("  • Help me with my finances - I spent money on dining and need a savings plan")
        print("  • I want to better manage my money and track my expenses")
        print()
        print("Look for:")
        print("  ✅ Correct tool selection")
        print("  ✅ Appropriate number of tools called")
        print("  ✅ Clear task descriptions")
        print("  ✅ Logical parallel execution")
    
    def show_examples(self):
        """Show example inputs organized by complexity."""
        print("\n📋 EXAMPLE INPUTS BY COMPLEXITY")
        print("=" * 50)
        
        print(f"\n🎯 SIMPLE REQUESTS (1 tool):")
        simple_examples = [
            "Add vacation jar 10%",
            "I spent $50 on groceries", 
            "Help me save for a car",
            "What is compound interest?",
            "Hello"
        ]
        for example in simple_examples:
            print(f"  • {example}")
        
        print(f"\n🎯 COMPLEX REQUESTS (multiple tools):")
        complex_examples = [
            "I spent $100 on groceries and want to add a vacation jar with 15%",
            "Log my $200 car repair and help me plan to save for future repairs",
            "Create emergency fund jar with 20%, explain emergency funds, and log my $150 medical bill",
            "I bought a laptop for $1500 and need to update my tech budget jar to 25%"
        ]
        for example in complex_examples:
            print(f"  • {example}")
        
        print(f"\n🎯 UNCLEAR REQUESTS (need clarification):")
        unclear_examples = [
            "Help me with my finances - I spent money on dining and need a savings plan",
            "I want to better manage my money and track my expenses"
        ]
        for example in unclear_examples:
            print(f"  • {example}")
    
    def test_multi_tool_examples(self):
        """Test multi-tool examples specifically."""
        print("\n🧪 TESTING PARALLEL TOOL EXAMPLES")
        print("=" * 60)
        
        multi_examples = [
            "I spent $100 on groceries and want to add a vacation jar with 15%",
            "Log my $200 car repair and help me plan to save for future repairs",
            "Create emergency fund jar with 20%, explain emergency funds, and log my $150 medical bill",
            "I bought a laptop for $1500 and need to update my tech budget jar to 25%"
        ]
        
        for i, example in enumerate(multi_examples, 1):
            print(f"\n🧪 Test {i}/4:")
            result = self.orchestrator.analyze_request(example)
            self.orchestrator.display_result(example, result)
            
            # Check if it's multi-tool
            if result["success"] and result["num_tools"] > 1:
                print(f"✅ Correctly identified as multi-tool ({result['num_tools']} tools)")
            else:
                print(f"❌ Should be multi-tool calling!")
            
            print("─" * 60)
    
    def test_simple_examples(self):
        """Test simple tool calling examples."""
        print("\n🧪 TESTING SIMPLE TOOL EXAMPLES")
        print("=" * 60)
        
        simple_examples = [
            "Add vacation jar 10%",
            "I spent $50 on groceries",
            "Help me save for a car",
            "What is compound interest?",
            "Hello"
        ]
        
        for i, example in enumerate(simple_examples, 1):
            print(f"\n🧪 Test {i}/5:")
            result = self.orchestrator.analyze_request(example)
            self.orchestrator.display_result(example, result)
            
            # Check if it's single tool
            if result["success"] and result["num_tools"] == 1:
                print(f"✅ Correctly identified as single tool")
            else:
                print(f"❌ Should be single tool calling!")
            
            print("─" * 60)
    
    def evaluate_result(self, user_input: str, result: Dict[str, Any]):
        """Provide quick evaluation of the result."""
        if not result["success"]:
            print(f"❌ Failed to route: {result.get('error', 'Unknown error')}")
            return
        
        num_tools = result["num_tools"]
        tool_calls = result["tool_calls"]
        
        # Quick evaluation hints
        print(f"\n💡 EVALUATION HINTS:")
        
        if num_tools == 1:
            tool_name = tool_calls[0]["tool_name"]
            print(f"✅ Single tool calling: {tool_name}")
            print(f"   Check: Is this the right tool for the request?")
        else:
            print(f"✅ Parallel tool calling with {num_tools} tools")
            tool_names = [tc["tool_name"] for tc in tool_calls]
            print(f"   Tools: {', '.join(tool_names)}")
            print(f"   Check: Are all tools appropriate and distinct?")


def main():
    """Main function for interactive testing."""
    tester = MultiWorkerPromptTester()
    tester.run_interactive_test()


if __name__ == "__main__":
    main()
