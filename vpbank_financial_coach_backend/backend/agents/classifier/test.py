"""
Interactive Test for Transaction Classifier Agent
===============================================

This script allows you to interactively test the Transaction Classifier agent,
including its multi-turn conversation capabilities.

Usage:
    python -m backend.agents.classifier.test

    (Run from the project root directory)
"""

import os
import sys

# Now we can import the agent interface
from backend.agents.classifier.interface import get_agent_interface

def run_interactive_session():
    """
    Starts an interactive command-line session to test the Classifier agent.
    """
    agent_interface = get_agent_interface()
    print("========================================")
    print("  Transaction Classifier Agent Test")
    print("========================================")
    print("Type your transaction to classify.")
    print("Examples: 'lunch 20 dollars', 'coffee', '15'")
    print("Type 'exit' or 'quit' to end the session.")
    print("========================================")
    
    # Start with a clean slate
    print("ℹ️  Starting new classifier test session")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Ending session. Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("Agent is thinking...")
            
            # Use empty conversation history for testing
            history = []
            
            # Process the task using the agent interface
            result_dict = agent_interface.process_task(user_input, history)
            
            response = result_dict.get("response", "Error: No response from agent.")
            requires_follow_up = result_dict.get("requires_follow_up", False)

            print(f"Agent: {response}")
            
            # Provide feedback to the user about follow-up
            if requires_follow_up:
                print("🔒 Agent is waiting for your response.")
            else:
                print("✅ Transaction classification complete.")
            
            print("--------------------")

        except KeyboardInterrupt:
            print("\nEnding session. Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_interactive_session() 