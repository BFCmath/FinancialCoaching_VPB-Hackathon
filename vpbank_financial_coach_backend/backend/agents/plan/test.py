"""
Interactive Test for Budget Advisor Agent
=========================================

This script allows you to interactively test the Budget Advisor agent,
focusing on financial planning and advisory with ReAct, stages, and follow-up.

Usage:
    python -m agents.plan.test

    (Run from the `full_multi_agent` directory)
"""

import os
import sys
import json

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(grandparent_dir)

# Import the agent interface and utilities
from agents.plan.interface import get_agent_interface
from utils import get_conversation_history, add_conversation_turn, get_all_jars, get_database_stats, get_all_budget_plans
from database import get_active_agent_context, set_active_agent_context

def display_context():
    """Display current jars, plans, and database stats context."""
    print("\n📊 CURRENT CONTEXT")
    # print("=" * 50)
    
    # # Show available jars
    # jars = get_all_jars()
    # print("\n🏺 Available Jars:")
    # for jar in jars:
    #     print(f"  • {jar.name}: ${jar.current_amount:.2f}/${jar.amount:.2f} - {jar.description}")
    
    # # Show budget plans
    # plans = get_all_budget_plans()
    # print("\n📋 Budget Plans:")
    # if plans:
    #     table_data = []
    #     for plan in plans:
    #         table_data.append([
    #             plan.name,
    #             plan.status,
    #             plan.detail_description[:50] + "..." if len(plan.detail_description) > 50 else plan.detail_description,
    #             plan.jar_recommendations[:50] + "..." if plan.jar_recommendations and len(plan.jar_recommendations) > 50 else plan.jar_recommendations or "N/A"
    #         ])
    #     headers = ["Name", "Status", "Description", "Jar Recommendations"]
    #     print(table_data)
    # else:
    #     print("No budget plans found.")
    
    # Show transaction stats
    stats = get_database_stats()
    print("\n💳 Transaction Stats:")
    print(f"  • Total Transactions: {stats['transactions']['count']}")
    print(f"  • Total Amount: {stats['transactions']['total_amount']}")
    print(f"  • Sources: {', '.join(stats['transactions']['sources'])}")
    print()

def test_predefined_scenarios():
    """Test with predefined scenarios covering different advisory operations and stages."""
    agent_interface = get_agent_interface()
    scenarios = [
        # Stage 1: Understanding and initial proposal
        ("help me save for a vacation", 
         "Stage 1: Gather info and propose"),
        # Simulate Stage 2: Feedback and refine
        ("make it for $2000 in 6 months", 
         "Stage 2: Refine proposal"),
        # Stage 2 to 3: Acceptance
        ("ACCEPT", 
         "Stage 3: Finalize and apply"),
        # Other scenarios
        ("analyze my spending last month", 
         "Stage 1: Analyze and propose adjustments"),
        ("update my vacation plan to $3000", 
         "Stage 1-3: Adjust existing plan"),
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
            print("\nRaw Agent Result:")
            print(json.dumps(result, indent=2))  # Print full raw result_dict
            
            response = result.get("response", "No response")
            requires_follow_up = result.get("requires_follow_up", False)
            print(f"\nResponse:\n{response}")
            if requires_follow_up:
                print("🔒 Conversation locked for follow-up")
            display_context()
        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)
        input("Press Enter to continue...")

def run_interactive_session():
    """
    Starts an interactive command-line session to test the Budget Advisor agent.
    """
    agent_interface = get_agent_interface()
    print("========================================")
    print("       Budget Advisor Agent Test")
    print("========================================")
    print("Get personalized financial advice and plans.")
    print("In stage 2, type 'ACCEPT' to finalize.")
    print("Examples:")
    print("  - 'help me save for a vacation'")
    print("  - 'analyze my spending last month'")
    print("  - 'update my car savings plan'")
    print("  - 'list active plans'")
    print("  - Vietnamese: 'tôi muốn tiết kiệm cho chuyến du lịch'")
    print("Options:")
    print("  - 'test'  : Run predefined test scenarios")
    print("  - 'show'  : Display current context")
    print("  - 'exit'  : End session")
    print("========================================")
    
    # Start with clean state
    set_active_agent_context(None)

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
            print("\nRaw Agent Result:")
            print(json.dumps(result_dict, indent=2))  # Print full raw result_dict
            
            response = result_dict.get("response", "Error: No response from agent.")
            requires_follow_up = result_dict.get("requires_follow_up", False)
            print(f"\nAgent:\n{response}")
            if requires_follow_up:
                print("🔒 Agent has locked the conversation and is waiting for your response.")
            else:
                if get_active_agent_context() == agent_interface.agent_name:
                    print(f"🔓 Lock released from {agent_interface.agent_name}")
                    set_active_agent_context(None)
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