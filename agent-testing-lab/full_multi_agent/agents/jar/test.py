"""
Interactive Test for Jar Manager Agent
======================================

This script allows you to interactively test the Jar Manager agent,
including its multi-jar operations and conversation lock capabilities.

Usage:
    cd agent-testing-lab/full_multi_agent
    python -m agents.jar.test

Example inputs:
    'create a vacation jar with 15%'
    'set up the 6-jar system'
    'create vacation and emergency jars 10% each'
    'tạo hũ du lịch với 15%'
"""

import os
import sys

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(grandparent_dir)

# Import the agent interface and history/lock utilities
from agents.jar.interface import get_agent_interface
from utils import (
    get_conversation_history, add_conversation_turn, get_all_jars,
)
from database import set_active_agent_context, get_active_agent_context, TOTAL_INCOME

def display_context():
    """Display current jars and budget context."""
    print("\n📊 CURRENT SYSTEM STATE")
    print("=" * 60)
    
    # Show total income first
    print(f"💰 Monthly Income: ${TOTAL_INCOME:,.2f}")
    
    # Show active jars and their allocations
    print("\n🏺 Active Budget Jars:")
    jars = get_all_jars()
    if jars:
        total_percent = sum(jar.percent for jar in jars)
        total_current = sum(jar.current_percent for jar in jars)
        
        # Show each jar's details
        for jar in jars:
            current_amount = jar.current_percent * TOTAL_INCOME
            budget_amount = jar.percent * TOTAL_INCOME
            print(f"\n• {jar.name}:")
            print(f"  Current: ${current_amount:.2f} ({jar.current_percent*100:.1f}%)")
            print(f"  Budget:  ${budget_amount:.2f} ({jar.percent*100:.1f}%)")
            print(f"  Info:    {jar.description}")
            
        # Show totals
        print("\n� System Totals:")
        print(f"  Current: {total_current*100:.1f}% allocated")
        print(f"  Budget:  {total_percent*100:.1f}% allocated")
    else:
        print("No jars configured (Use 'set up the 6-jar system' to get started)")
    print()

def test_predefined_scenarios():
    """Test with predefined scenarios covering common jar management operations.
    
    This function runs through a series of carefully designed test cases that
    validate the jar manager's core functionality:
    - Single and multi-jar operations
    - Percentage and amount-based allocations
    - T. Harv Eker's 6-jar system setup
    - Vietnamese language support
    - Error handling and validation
    - Automatic rebalancing
    """
    agent_interface = get_agent_interface()
    scenarios = [
        # Single Jar Creation (Should work directly)
        ("create vacation jar with 15%", 
         "Should create jar without clarification"),
        ("set up emergency fund with $1000", 
         "Should create jar converting to percentage"),
        
        # Complex Multi-Jar Creation (May need clarification)
        ("create entertainment and education jars", 
         "Should ask for percentages"),
        ("set up jars for savings and bills", 
         "Should ask for details"),
         
        # Vietnamese inputs
        ("tạo hũ du lịch với 15%", 
         "Should handle Vietnamese input"),
        
        # Jar Updates
        ("change vacation jar to 20%", 
         "Should update percentage"),
        ("make emergency fund 10% of budget", 
         "Should update with rebalancing"),
         
        # Full System Setup
        ("set up the 6-jar system",
         "Should create T. Harv Eker's system"),
        
        # Multi-Jar Updates
        ("update vacation to 8% and emergency to 15%",
         "Should handle multiple updates"),
         
        # Jar Listing
        ("list all jars", 
         "Should show all jars with details"),
        
        # Jar Deletion
        ("delete vacation jar", 
         "Should delete and rebalance"),
         
        # Error cases
        ("create invalid jar with 150%", 
         "Should report invalid percentage"),
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
    Starts an interactive command-line session to test the Jar Manager agent.
    """
    agent_interface = get_agent_interface()
    print("=" * 60)
    print("                Jar Manager Agent Test")
    print("=" * 60)
    print("📊 T. Harv Eker's 6-Jar Money Management System")
    print("\nSingle Jar Operations:")
    print("  - create : 'create vacation jar with 15%'")
    print("  - update : 'update emergency to 20%'")
    print("  - amount : 'set up savings jar with $1000'")
    print("  - delete : 'delete vacation jar'")
    print("  - list   : 'show my jars'")
    print("\nMulti-Jar Operations:")
    print("  - 'create vacation and emergency jars 10% each'")
    print("  - 'update vacation to 8% and emergency to 15%'")
    print("\nFull System Setup:")
    print("  - 'set up the 6-jar system'")
    print("\nVietnamese Support:")
    print("  - 'tạo hũ du lịch với 15%'")
    print("  - 'cập nhật hũ khẩn cấp lên 20%'")
    print("\nTest Commands:")
    print("  - 'test'  : Run all test scenarios")
    print("  - 'show'  : Display current jars")
    print("  - 'exit'  : End session")
    print("=" * 60)
    
    # Start with a clean slate
    set_active_agent_context(None)
    add_conversation_turn("system", "User started a new jar manager test session.", ["system"], [])

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