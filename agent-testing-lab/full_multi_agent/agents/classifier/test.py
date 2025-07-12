"""
Interactive Test for Transaction Classifier Agent
===============================================

This script allows you to interactively test the Transaction Classifier agent,
including its multi-turn conversation capabilities.

Usage:
    python -m agents.classifier.test

    (Run from the `full_multi_agent` directory)
"""

import os
import sys

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(grandparent_dir)

# Now we can import the agent interface and history functions
from agents.classifier.interface import get_agent_interface
from utils import get_conversation_history, add_conversation_turn
from database import set_active_agent_context, get_active_agent_context

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
    set_active_agent_context(None)
    add_conversation_turn("system", "User started a new classifier test session.", ["system"], [])

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Ending session. Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("Agent is thinking...")
            
            # Use the full conversation history for context
            history = get_conversation_history()
            
            # Process the task using the agent interface
            result_dict = agent_interface.process_task(user_input, history)
            
            response = result_dict.get("response", "Error: No response from agent.")
            requires_follow_up = result_dict.get("requires_follow_up", False)

            print(f"Agent: {response}")
            
            # The agent itself sets the lock when it asks a question.
            # Here, we just provide feedback to the user.
            if requires_follow_up:
                print("🔒 Agent has locked the conversation and is waiting for your response.")
            else:
                # If the agent signals it's done, we can manually release the lock
                # if it's still set, as a safety measure.
                if get_active_agent_context() == agent_interface.agent_name:
                    print(f"🔓 Lock released from {agent_interface.agent_name}")
                    set_active_agent_context(None)
            
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