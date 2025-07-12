"""
Interactive Test for Transaction Fetcher Agent
==============================================

This script allows you to interactively test the Transaction Fetcher agent,
focusing on data retrieval with various filters.

Usage:
    python -m agents.transaction_fetcher.test

    (Run from the `full_multi_agent` directory)
"""

import os
import sys
import json

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(grandparent_dir)

# Import the agent interface and history utilities
from agents.transaction_fetcher.interface import get_agent_interface
from utils import (
    get_conversation_history, add_conversation_turn, get_all_jars, get_database_stats
)
from database import get_active_agent_context  # For display, even if stateless

def display_context():
    """Display current jars and database stats context."""
    print("\n📊 CURRENT CONTEXT")
    print("=" * 50)
    
    # Show available jars
    jars = get_all_jars()
    print("\n🏺 Available Jars:")
    for jar in jars:
        print(f"  • {jar.name}: ${jar.current_amount:.2f}/${jar.amount:.2f} - {jar.description}")
    
    # Show transaction stats
    stats = get_database_stats()
    print("\n💳 Transaction Stats:")
    print(f"  • Total Transactions: {stats['transactions']['count']}")
    print(f"  • Total Amount: {stats['transactions']['total_amount']}")
    print(f"  • Sources: {', '.join(stats['transactions']['sources'])}")
    print()

def format_transactions(data) -> str:
    """Format transaction list as a readable table."""
    if not data:
        return "No transactions found."
    
    # Prepare table data
    table_data = []
    for tx in data:
        table_data.append([
            tx.get('date', 'N/A'),
            tx.get('time', 'N/A'),
            tx.get('jar', 'N/A'),
            f"${tx.get('amount', 0):.2f}",
            tx.get('description', 'N/A'),
            tx.get('source', 'N/A')
        ])
    
    return table_data

def test_predefined_scenarios():
    """Test with predefined scenarios covering different retrieval operations."""
    agent_interface = get_agent_interface()
    scenarios = [
        # Simple jar filtering
        ("show me necessities transactions", 
         "Should retrieve necessities jar transactions"),
        ("all my play spending", 
         "Should retrieve play jar transactions"),
        
        # Time period filtering
        ("transactions from last month", 
         "Should retrieve all from last month"),
        ("necessities this week", 
         "Should retrieve necessities from this week"),
         
        # Amount range
        ("purchases over $100", 
         "Should retrieve all over $100"),
        ("play under $20", 
         "Should retrieve play under $20"),
         
        # Hour range
        ("morning transactions 6 to 12", 
         "Should retrieve between 6am-12pm"),
        ("evening necessities 18 to 23", 
         "Should retrieve necessities 6pm-11pm"),
         
        # Source filtering
        ("manual input transactions", 
         "Should retrieve manual entries"),
        ("vpbank api necessities", 
         "Should retrieve bank API necessities"),
         
        # Complex multi-filter
        ("necessities last week under $50 from 9 to 17 manual input", 
         "Should use complex tool for multi-filters"),
        ("play this month over $20 after 18 from vpbank api", 
         "Should use complex for date + amount + hour + source"),
         
        # Vietnamese
        ("cho tôi xem thông tin ăn trưa dưới 20 đô từ tuần trước", 
         "Should handle Vietnamese: lunch under $20 from last week"),
        
        # Edge cases
        ("all transactions", 
         "Should retrieve all"),
        ("", 
         "Should handle empty input"),
    ]
    
    print("🧪 PREDEFINED TEST SCENARIOS")
    print("=" * 60)
    
    for i, (user_input, expected) in enumerate(scenarios, 1):
        print(f"\n{i:2d}. Input: '{user_input}'")
        print(f"    Expected: {expected}")
        
        try:
            history = get_conversation_history()
            result = agent_interface.process_task(user_input, history)
            print("\nRaw Agent Result:")
            print(json.dumps(result, indent=2))  # Print full raw result_dict
            
            response = result.get("response", "No response")
            # Handle response: dict (success) or str (error)
            if isinstance(response, dict):
                print(f"\nDescription: {response.get('description', 'N/A')}")
                data = response.get('data', [])
                print(f"Transactions Found: {len(data)}")
                if data:
                    print("\nTransactions:")
                    print(format_transactions(data))
                else:
                    print("No transactions.")
            else:
                print(f"\nResponse: {response}")
            display_context()
        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)
        input("Press Enter to continue...")

def run_interactive_session():
    """
    Starts an interactive command-line session to test the Transaction Fetcher agent.
    """
    agent_interface = get_agent_interface()
    print("========================================")
    print("     Transaction Fetcher Agent Test")
    print("========================================")
    print("Retrieve your transaction history with filters.")
    print("Examples:")
    print("  - Jar: 'necessities transactions'")
    print("  - Time: 'last month play spending'")
    print("  - Amount: 'purchases over $50'")
    print("  - Hour: 'morning transactions 6 to 12'")
    print("  - Source: 'manual input necessities'")
    print("  - Complex: 'necessities last week under $50 from 9 to 17'")
    print("  - Vietnamese: 'cho tôi xem ăn trưa dưới 20 đô từ tuần trước'")
    print("Options:")
    print("  - 'test'  : Run predefined test scenarios")
    print("  - 'show'  : Display current context")
    print("  - 'exit'  : End session")
    print("========================================")
    
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

            # Display response: dict (success) or str (error)
            if isinstance(response, dict):
                print(f"\nDescription: {response.get('description', 'No description')}")
                data = response.get('data', [])
                print(f"Transactions Found: {len(data)}")
                if data:
                    print("\nTransactions:")
                    print(format_transactions(data))
                else:
                    print("No transactions.")
            else:
                print(f"\nResponse: {response}")
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