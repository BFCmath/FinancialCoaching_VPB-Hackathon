"""
Interactive Test for Fee Manager Agent
======================================

This script allows you to interactively test the Fee Manager agent,
including its follow-up and conversation lock capabilities.

Usage:
    python -m agents.fee.test

    (Run from the `full_multi_agent` directory)
"""

import os
import sys

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(grandparent_dir)

# Import the agent interface and history/lock utilities
from agents.fee.interface import get_agent_interface
from utils import (
    get_conversation_history, add_conversation_turn, get_all_jars
)
from database import set_active_agent_context, get_active_agent_context

def display_context():
    """Display current fees and jars context."""
    print("\n📊 CURRENT CONTEXT")
    print("=" * 50)
    
    # Show active fees
    print("\n💰 Active Recurring Fees:")
    fee_response = get_agent_interface().process_task("list my fees", None)
    print(fee_response.get("response", "No fees found"))
    
    # Show available jars
    jars = get_all_jars()
    print("\n🏺 Available Jars:")
    for jar in jars:
        print(f"  • {jar.name}: ${jar.current_amount:.2f}/${jar.amount:.2f}")
    print()

def test_predefined_scenarios():
    """Test with predefined scenarios covering different fee operations."""
    agent_interface = get_agent_interface()
    scenarios = [
        # Basic fee creation (Should work directly)
        ("create a monthly netflix fee of $15 for the entertainment jar", 
         "Should create fee without clarification"),
        ("set up my rent payment, $1200 monthly from necessities jar", 
         "Should create fee without clarification"),
        
        # Complex fee creation (May need clarification)
        ("create a gym membership fee", 
         "Should ask for amount and jar"),
        ("set up spotify payment", 
         "Should ask for details"),
         
        # Vietnamese inputs
        ("tạo khoản phí Netflix 15 đô hàng tháng từ jar giải trí", 
         "Should handle Vietnamese input"),
        
        # Fee adjustments
        ("increase my netflix fee to $20", 
         "Should adjust existing fee"),
        ("change my gym membership to weekly payments", 
         "Should ask for confirmation"),
         
        # Fee listing and querying
        ("what fees do I have?", 
         "Should list all active fees"),
        ("show me fees for entertainment jar", 
         "Should filter by jar"),
         
        # Fee deletion/disabling
        ("cancel my netflix subscription", 
         "Should disable netflix fee"),
        ("delete spotify fee", 
         "Should remove spotify fee"),
         
        # Multi-operation (Should handle one at a time)
        ("create netflix $15 monthly and spotify $10 monthly for entertainment", 
         "Should handle multiple fees"),
         
        # Error cases
        ("create fee for non-existent jar", 
         "Should report invalid jar"),
        ("", 
         "Should handle empty input"),
    ]
    
    print("🧪 PREDEFINED TEST SCENARIOS")
    print("=" * 60)
    
    # Start with clean state
    set_active_agent_context(None)
    
    for i, (user_input, expected) in enumerate(scenarios, 1):
        print(f"\n{i:2d}. Input: '{user_input}'")
        print(f"    Expected: {expected}")
        
        try:
            history = get_conversation_history()
            result = agent_interface.process_task(user_input, history)
            print(f"    Result: {result['response']}")
            if result.get("requires_follow_up"):
                print(f"    🔒 Conversation locked for follow-up")
            display_context()
        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)
        input("Press Enter to continue...")

def run_interactive_session():
    """
    Starts an interactive command-line session to test the Fee Manager agent.
    """
    agent_interface = get_agent_interface()
    print("========================================")
    print("         Fee Manager Agent Test")
    print("========================================")
    print("Manage your recurring fees (subscriptions, bills, etc.).")
    print("Commands:")
    print("  - create : 'create a monthly $15 netflix fee for entertainment jar'")
    print("  - list   : 'list all my subscriptions'")
    print("  - adjust : 'change netflix fee to $20'")
    print("  - delete : 'cancel my gym membership'")
    print("Options:")
    print("  - 'test'  : Run predefined test scenarios")
    print("  - 'show'  : Display current context")
    print("  - 'exit'  : End session")
    print("========================================")
    
    # Start with a clean slate
    set_active_agent_context(None)
    add_conversation_turn("system", "User started a new fee manager test session.", ["system"], [])

    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            # Handle special commands
            if user_input.lower() in ["exit", "quit"]:
                print("Ending session. Goodbye!")
                break
            
            if not user_input:
                continue
                
            if user_input.lower() == "test":
                test_predefined_scenarios()
                continue
                
            if user_input.lower() == "show":
                display_context()
                continue

            # Process normal input
            print("\nAgent is thinking...")
            history = get_conversation_history()
            result_dict = agent_interface.process_task(user_input, history)
            response = result_dict.get("response", "Error: No response from agent.")
            requires_follow_up = result_dict.get("requires_follow_up", False)

            # Show response and lock status
            print(f"\nAgent: {response}")
            if requires_follow_up:
                print("🔒 Agent has locked the conversation and is waiting for your response.")
            else:
                # Release any existing lock when done
                if get_active_agent_context() == agent_interface.agent_name:
                    print(f"🔓 Lock released from {agent_interface.agent_name}")
                    set_active_agent_context(None)
                
                # Show updated context after successful operations
                display_context()
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
 