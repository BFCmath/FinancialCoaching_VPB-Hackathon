"""
Fee Manager Interactive Test Interface
=====================================

Interactive testing for fee pattern recognition and management.
"""

import sys
from typing import Optional

# Local imports
from main import setup_llm, handle_confidence_flow, get_fee_summary
from tools import FEES_STORAGE, fetch_existing_fees, initialize_mock_data
from config import config

class FeeManagerTester:
    """Interactive tester for fee manager agent"""
    
    def __init__(self):
        self.llm_with_tools = None
        self.session_active = True
        
    def setup(self):
        """Initialize the fee manager system"""
        print("🚀 Fee Manager Test Lab")
        print("=" * 40)
        
        try:
            self.llm_with_tools = setup_llm()
            print(f"✅ LLM ready: {config.model_name}")
            print(f"🔧 Debug mode: {'ON' if config.debug_mode else 'OFF'}")
            print(f"🎯 Confidence thresholds: High {config.high_confidence_threshold}%, Low {config.low_confidence_threshold}%")
            
            # Show initial fee summary
            print(f"\n{get_fee_summary()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def show_menu(self):
        """Show the interactive menu"""
        print("\n" + "=" * 50)
        print("🎯 Fee Manager Commands:")
        print("")
        print("📝 CREATE FEES:")
        print("  • '5 dollar daily for coffee'")
        print("  • '10 dollar every Monday and Friday for commute'") 
        print("  • '50 dollar every 15th for insurance'")
        print("  • '30k mỗi thứ hai cho xe buýt' (Vietnamese)")
        print("")
        print("🔧 MANAGE FEES:")
        print("  • 'list my fees'")
        print("  • 'stop my coffee fee'") 
        print("  • 'change bus fare to 12 dollars'")
        print("  • 'disable YouTube subscription'")
        print("")
        print("❓ TEST EDGE CASES:")
        print("  • 'subscription for stuff' (ambiguous)")
        print("  • 'pay for things regularly' (unclear)")
        print("  • 'Netflix 15.99 monthly' (conflict detection)")
        print("")
        print("💡 SYSTEM COMMANDS:")
        print("  • 'help' - Show this menu")
        print("  • 'summary' - Show fee summary")
        print("  • 'reset' - Reset all fees to default")
        print("  • 'debug' - Toggle debug mode")
        print("  • 'quit' - Exit")
        print("")
    
    def handle_system_command(self, user_input: str) -> bool:
        """Handle system commands, return True if handled"""
        
        cmd = user_input.lower().strip()
        
        if cmd in ['help', 'h', '?']:
            self.show_menu()
            return True
            
        elif cmd in ['summary', 'sum', 's']:
            print(f"\n{get_fee_summary()}")
            return True
            
        elif cmd in ['reset', 'r']:
            # Clear and reinitialize
            FEES_STORAGE.clear()
            initialize_mock_data()
            print("✅ Fees reset to initial state")
            print(f"\n{get_fee_summary()}")
            return True
            
        elif cmd in ['debug', 'd']:
            config.debug_mode = not config.debug_mode
            print(f"🔧 Debug mode: {'ON' if config.debug_mode else 'OFF'}")
            return True
            
        elif cmd in ['quit', 'exit', 'q']:
            self.session_active = False
            print("👋 Goodbye!")
            return True
            
        return False
    
    def process_fee_input(self, user_input: str):
        """Process fee-related user input"""
        
        print(f"\n🔍 Processing: '{user_input}'")
        
        try:
            result = handle_confidence_flow(user_input, self.llm_with_tools)
            
            # Check result type and format output
            if result.startswith("❓") and "Confidence:" in result:
                # Confirmation request
                print(f"\n{result}")
                
                # In real system, would wait for y/n response
                # For demo, show what would happen
                print("\n💡 In real usage, you would respond with 'y' or 'n'")
                
            elif result.startswith("❓"):
                # Clarification request  
                print(f"\n{result}")
                print("\n💡 Please provide more specific information")
                
            else:
                # Direct action taken
                print(f"\n{result}")
                
                # Show updated summary if fee was created/modified
                if any(keyword in result for keyword in ["✅ Created", "✅ Adjusted", "✅ Deleted"]):
                    print(f"\n{get_fee_summary()}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def run_interactive_session(self):
        """Main interactive loop"""
        
        if not self.setup():
            return
        
        self.show_menu()
        
        print("\n💬 Enter fee commands (type 'help' for examples):")
        
        while self.session_active:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Handle system commands first
                if self.handle_system_command(user_input):
                    continue
                
                # Process as fee input
                self.process_fee_input(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Session ended. Goodbye!")
                break

def run_quick_test():
    """Run a quick automated test of key scenarios"""
    
    print("⚡ Quick Test Mode")
    print("=" * 30)
    
    tester = FeeManagerTester()
    if not tester.setup():
        return
    
    test_cases = [
        ("High Confidence", "5 dollar daily for coffee"),
        ("Weekly Pattern", "10 dollar every Monday and Friday for commute"),
        ("Monthly Pattern", "YouTube Premium 15.99 monthly"),
        ("Vietnamese", "30k mỗi thứ hai cho xe buýt"),
        ("Fee Listing", "list my fees"),
        ("Fee Management", "change coffee to 6 dollars"),
        ("Ambiguous Input", "subscription for stuff"),
        ("Low Confidence", "pay for things regularly"),
    ]
    
    for category, test_input in test_cases:
        print(f"\n--- {category}: '{test_input}' ---")
        
        try:
            result = handle_confidence_flow(test_input, tester.llm_with_tools)
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n{get_fee_summary()}")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        run_quick_test()
    else:
        tester = FeeManagerTester()
        tester.run_interactive_session()

if __name__ == "__main__":
    main()
