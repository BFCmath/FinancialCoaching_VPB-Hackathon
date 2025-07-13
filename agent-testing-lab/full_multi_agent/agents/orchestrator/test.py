"""
Interactive Test for Orchestrator
=================================

Test the orchestrator with multi-agent routing.
"""

import os
import sys

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(grandparent_dir)

from agents.orchestrator.main import process_task
from utils import get_conversation_history

def run_interactive_session():
    print("========================================")
    print("     Orchestrator Interactive Test")
    print("========================================")
    print("Enter queries to test routing and responses.")
    print("Type 'exit' to quit.")
    print("Examples:")
    print("  - 'Categorize my lunch expense'")
    print("  - 'Create a monthly Netflix fee'")
    print("  - 'What is compound interest?'")
    print("  - 'Update my savings jar to 20%'")
    print("  - 'Show transactions last month'")
    print("  - 'Help me plan for vacation savings'")
    print("  - 'Hi' (direct greeting)")
    print("  - 'What's the weather?' (irrelevant)")
    print("========================================")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ["exit", "quit"]:
                print("Ending session. Goodbye!")
                break
            
            if not user_input:
                continue

            # Process input
            print("\nOrchestrator is thinking...")
            history = get_conversation_history()
            result_dict = process_task(user_input, history)
            print("\nResponse:\n", result_dict["response"])
            if result_dict["requires_follow_up"]:
                print("\n(Follow-up expected - enter next response)")

        except KeyboardInterrupt:
            print("\nEnding session. Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_interactive_session()