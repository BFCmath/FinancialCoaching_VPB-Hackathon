"""
Main CLI interface for the AI Financial Coach multi-agent system.
Provides an interactive command-line interface to test the agent routing and execution.
"""

import os
from langchain_core.messages import HumanMessage
from graph import create_simple_routing_graph
from state import GraphState


def setup_environment():
    """Setup required environment variables."""
    
    # Check for Google API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY environment variable not set.")
        print("Please set your Google API key to use the LLM functionality.")
        print("You can get one from: https://makersuite.google.com/app/apikey")
        print()
        
        # For demo purposes, set a placeholder
        api_key = input("Enter your Google API key (or press Enter to continue with demo): ").strip()
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        else:
            os.environ["GOOGLE_API_KEY"] = "demo_key"
            print("Running in demo mode with mock responses.")


def create_initial_state(user_id: str = "demo_user") -> GraphState:
    """
    Create the initial state for the graph.
    
    Args:
        user_id: User identifier
        
    Returns:
        Initial graph state
    """
    return {
        "messages": [],
        "next_agent": None,
        "user_id": user_id,
        "task_complete": False,
        "agent_data": {}
    }


def process_user_input(graph, user_input: str, current_state: GraphState) -> GraphState:
    """
    Process user input through the multi-agent graph.
    
    Args:
        graph: Compiled LangGraph
        user_input: User's message
        current_state: Current graph state
        
    Returns:
        Updated graph state after processing
    """
    
    # Add user message to state
    user_message = HumanMessage(content=user_input)
    new_state = current_state.copy()
    new_state["messages"] = current_state["messages"] + [user_message]
    new_state["task_complete"] = False
    new_state["next_agent"] = None
    
    try:
        # Process through the graph
        result = graph.invoke(new_state)
        return result
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return current_state


def display_response(state: GraphState):
    """
    Display the agent's response to the user.
    
    Args:
        state: Graph state containing the response
    """
    
    if state["messages"]:
        latest_message = state["messages"][-1]
        if hasattr(latest_message, 'content'):
            print("\n🤖 AI Financial Coach:")
            print(latest_message.content)
        else:
            print("\n🤖 AI Financial Coach: Task completed!")
    else:
        print("\n🤖 AI Financial Coach: Hello! How can I help you manage your finances today?")


def run_demo_examples(graph):
    """
    Run the predefined demo examples to showcase agent routing.
    
    Args:
        graph: Compiled LangGraph
    """
    
    print("\n" + "="*60)
    print("DEMO: Testing Agent Routing with Example Inputs")
    print("="*60)
    
    examples = [
        ("dining 20 dollar", "Should route to TransactionClassifier"),
        ("add a 'Vacation' jar with 8% allocation", "Should route to JarManager"),
        ("what is compound interest?", "Should route to KnowledgeBase"),
        ("I want to save for a trip to Japan", "Should route to BudgetAdvisor")
    ]
    
    for i, (user_input, expected) in enumerate(examples, 1):
        print(f"\nExample {i}: {user_input}")
        print(f"Expected: {expected}")
        print("-" * 40)
        
        # Create fresh state for each example
        state = create_initial_state()
        
        # Process the input
        result_state = process_user_input(graph, user_input, state)
        
        # Display the response
        display_response(result_state)
        
        # Show routing information
        if result_state.get("next_agent"):
            print(f"✅ Routed to: {result_state['next_agent']}")
        
        print()


def interactive_mode(graph):
    """
    Run the interactive CLI mode.
    
    Args:
        graph: Compiled LangGraph
    """
    
    print("\n" + "="*60)
    print("INTERACTIVE MODE: AI Financial Coach")
    print("="*60)
    print("Commands:")
    print("  - Type your financial requests naturally")
    print("  - Type 'demo' to run demo examples")
    print("  - Type 'quit' or 'exit' to quit")
    print("  - Type 'help' for usage examples")
    print("-" * 60)
    
    # Initialize state
    state = create_initial_state()
    
    # Welcome message
    display_response(state)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Thanks for using AI Financial Coach!")
                break
            elif user_input.lower() == 'demo':
                run_demo_examples(graph)
                continue
            elif user_input.lower() == 'help':
                print_help()
                continue
            
            # Process the user input
            state = process_user_input(graph, user_input, state)
            
            # Display the response
            display_response(state)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using AI Financial Coach!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'help' for examples.")


def print_help():
    """Print usage examples and help information."""
    
    print("\n📚 AI Financial Coach - Usage Examples:")
    print("-" * 50)
    print("💰 Budget Jar Management:")
    print("  • 'Add a Vacation jar with 10% allocation'")
    print("  • 'Change my Play jar to 8%'")
    print("  • 'Show me all my jars'")
    print()
    print("💳 Transaction Logging:")
    print("  • 'dining 25 dollar'")
    print("  • 'I bought groceries for $75'")
    print("  • 'coffee 5 dollars at Starbucks'")
    print()
    print("🔄 Recurring Fees:")
    print("  • 'Set up Netflix subscription $15 monthly'")
    print("  • 'I have daily parking fee 2 dollars'")
    print("  • 'Monthly gym membership $50'")
    print()
    print("📊 Financial Planning:")
    print("  • 'I want to save for a trip to Japan'")
    print("  • 'Help me budget for a new car'")
    print("  • 'Analyze my spending habits'")
    print()
    print("📚 Financial Education:")
    print("  • 'What is compound interest?'")
    print("  • 'Explain the 50/30/20 rule'")
    print("  • 'What is an emergency fund?'")


def main():
    """Main application entry point."""
    
    print("🚀 Starting AI Financial Coach Multi-Agent System")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    try:
        # Create the graph
        print("📊 Initializing multi-agent system...")
        graph = create_simple_routing_graph()
        print("✅ Multi-agent system ready!")
        
        # Run interactive mode
        interactive_mode(graph)
        
    except Exception as e:
        print(f"❌ Failed to initialize the system: {str(e)}")
        print("Please check your environment setup and try again.")


if __name__ == "__main__":
    main() 