"""
Multi-Jar Manager Interactive Test Interface
============================================

Interactive testing for multi-jar CRUD operations and T. Harv Eker's 6-jar budget management.
"""

import sys
from typing import Optional

# Local imports
from main import setup_llm, handle_confidence_flow, get_jar_summary
from tools import JARS_STORAGE, fetch_existing_jars, initialize_mock_data, TOTAL_INCOME
from config import config

class MultiJarManagerTester:
    """Interactive tester for multi-jar manager agent"""
    
    def __init__(self):
        self.llm_with_tools = None
        self.session_active = True
        
    def setup(self):
        """Initialize the multi-jar manager system"""
        print("🚀 Multi-Jar Manager Test Lab")
        print("=" * 40)
        
        try:
            self.llm_with_tools = setup_llm()
            if not self.llm_with_tools:
                print("❌ Failed to initialize LLM")
                return False
                
            print(f"✅ LLM ready: {config.model_name}")
            print(f"🔧 Debug mode: {'ON' if config.debug_mode else 'OFF'}")
            print(f"💰 Sample income: ${TOTAL_INCOME:,.2f}")
            
            # Show initial jar status
            print("\n" + get_jar_summary())
            
            return True
            
        except Exception as e:
            print(f"❌ Setup error: {e}")
            return False
    
    def show_help(self):
        """Display available commands and examples"""
        print("""
📖 Multi-Jar Manager Commands & Examples:

🎯 T. HARV EKER'S 6-JAR SYSTEM:
• "set up the 6-jar system"
• "list my jars"

📝 SINGLE JAR OPERATIONS:
• "create vacation jar with 15%"
• "create emergency fund with $1000 budget"
• "update vacation jar to 12%"
• "delete vacation jar because trip cancelled"

🔥 MULTI-JAR OPERATIONS:
• "create vacation and emergency jars with 10% each"
• "create car repair and home improvement jars with $500 each"
• "update vacation to 8% and emergency to 15%"
• "delete vacation and car repair jars because plans changed"

💡 PERCENTAGE & AMOUNT EXAMPLES:
• "create vacation jar with 15%" (percentage-based)
• "create emergency jar with $750" (amount-based, auto-converts to 15%)
• "update vacation to $600" (updates to 12% of $5000 income)

🌍 VIETNAMESE EXAMPLES:
• "tạo hũ du lịch với 15%"
• "tạo hũ du lịch và hũ khẩn cấp với 10% mỗi cái"

🔄 REBALANCING EXAMPLES:
• Creating new jars automatically scales down existing jars
• Deleting jars redistributes percentage to remaining jars
• All operations maintain 100% total allocation

💰 SYSTEM COMMANDS:
• help - Show this help
• summary - Show jar summary with percentages and amounts
• reset - Reset to T. Harv Eker's default 6-jar system
• debug - Toggle debug mode
• quit/exit - Exit program
        """)
    
    def show_summary(self):
        """Show current jar summary"""
        print("\n" + get_jar_summary())
    
    def reset_jars(self):
        """Reset to default jar configuration"""
        print("🔄 Resetting jars to T. Harv Eker's 6-jar system...")
        initialize_mock_data()
        print("✅ Jars reset to default configuration")
        self.show_summary()
    
    def toggle_debug(self):
        """Toggle debug mode"""
        config.debug_mode = not config.debug_mode
        print(f"🔧 Debug mode: {'ON' if config.debug_mode else 'OFF'}")
    
    def process_input(self, user_input: str) -> bool:
        """Process user input and return True to continue, False to exit"""
        
        # Handle special commands
        command = user_input.lower().strip()
        
        if command in ['quit', 'exit', 'q']:
            return False
        elif command in ['help', 'h', '?']:
            self.show_help()
            return True
        elif command in ['summary', 'sum', 's']:
            self.show_summary()
            return True
        elif command in ['reset', 'r']:
            self.reset_jars()
            return True
        elif command in ['debug', 'd']:
            self.toggle_debug()
            return True
        elif command == '':
            return True  # Empty input, continue
        
        # Process with LLM
        try:
            print(f"\n🔍 Processing: '{user_input}'")
            result = handle_confidence_flow(user_input, self.llm_with_tools)
            print(f"\n{result}")
            
            # Show updated summary if jar operations were performed
            if any(keyword in result for keyword in ["✅ Created", "✅ Updated", "✅ Deleted", "✅ Added"]):
                print(f"\n{get_jar_summary()}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if config.debug_mode:
                import traceback
                print(f"🐛 Debug traceback:\n{traceback.format_exc()}")
        
        return True
    
    def run_interactive(self):
        """Run interactive testing session"""
        
        if not self.setup():
            return
        
        print("""
🎯 Interactive Multi-Jar Manager Testing

Type your jar management requests in natural language.
Type 'help' for examples, 'quit' to exit.

💡 Quick starts:
• 'set up the 6-jar system' - Initialize T. Harv Eker's system
• 'create vacation jar with 15%' - Single jar creation
• 'create vacation and emergency jars with 10% each' - Multi-jar creation
        """)
        
        while self.session_active:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not self.process_input(user_input):
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Session ended by user.")
                break
            except EOFError:
                print("\n\n👋 Goodbye! Session ended.")
                break
        
        print("✅ Multi-Jar Manager Test Session Complete")
    
    def run_batch_tests(self):
        """Run predefined batch test scenarios"""
        
        if not self.setup():
            return
        
        print("\n🧪 Running Multi-Jar Batch Test Scenarios...")
        
        test_scenarios = [
            # Basic operations
            ("List initial state", "list my jars"),
            
            # Single jar operations
            ("Single jar creation (percentage)", "create vacation jar with 15%"),
            ("Single jar creation (amount)", "create emergency fund with $1000"),
            ("Single jar update", "update vacation jar to 12%"),
            
            # Multi-jar operations
            ("Multi-jar creation", "create car repair and home improvement jars with $500 each"),
            ("Multi-jar updates", "update car repair to 8% and home improvement to 6%"),
            ("Multi-jar deletion", "delete car repair and home improvement jars because priorities changed"),
            
            # T. Harv Eker system test
            ("Reset to 6-jar system", "reset"),
            ("6-jar system verification", "list all jars"),
            
            # Vietnamese language test
            ("Vietnamese single jar", "tạo hũ du lịch với 10%"),
            ("Vietnamese multi-jar", "tạo hũ xe hơi và hũ nhà cửa với 5% mỗi cái"),
            
            # Edge cases
            ("Percentage overflow test", "create big jar with 50%"),
            ("Amount conversion test", "create test jar with $250"),  # Should be 5%
            
            # Final state
            ("Final summary", "show jar summary")
        ]
        
        for i, (description, scenario) in enumerate(test_scenarios, 1):
            print(f"\n--- Test {i}/{len(test_scenarios)}: {description} ---")
            print(f"Input: '{scenario}'")
            
            try:
                if scenario == "reset":
                    self.reset_jars()
                    continue
                    
                result = handle_confidence_flow(scenario, self.llm_with_tools)
                print(f"Result: {result}")
                
                # Show summary for jar operations
                if any(keyword in result for keyword in ["✅ Created", "✅ Updated", "✅ Deleted", "✅ Added"]):
                    print(f"Updated State: {get_jar_summary()}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if config.debug_mode:
                    import traceback
                    print(f"🐛 Debug traceback:\n{traceback.format_exc()}")
            
            print("-" * 50)
        
        print("\n✅ Multi-jar batch testing completed!")
    
    def run_rebalancing_tests(self):
        """Run specific tests for automatic rebalancing functionality"""
        
        if not self.setup():
            return
        
        print("\n🔄 Running Rebalancing Test Scenarios...")
        
        rebalancing_scenarios = [
            ("Reset to clean state", "reset"),
            ("Show initial 6-jar allocation", "list jars"),
            ("Create 20% jar (should trigger rebalancing)", "create vacation jar with 20%"),
            ("Show rebalanced state", "list jars"),
            ("Create multi-jar 15% total", "create car and emergency jars with $375 each"),  # 7.5% each
            ("Show multi-jar rebalancing", "list jars"),
            ("Delete vacation jar (redistribute 20%)", "delete vacation jar because trip cancelled"),
            ("Show redistribution", "list jars"),
            ("Update existing jar percentages", "update car to 15% and emergency to 10%"),
            ("Show update rebalancing", "list jars"),
        ]
        
        for i, (description, scenario) in enumerate(rebalancing_scenarios, 1):
            print(f"\n--- Rebalancing Test {i}/{len(rebalancing_scenarios)}: {description} ---")
            print(f"Input: '{scenario}'")
            
            try:
                if scenario == "reset":
                    self.reset_jars()
                    continue
                elif scenario in ["list jars", "show rebalanced state", "show multi-jar rebalancing", "show redistribution", "show update rebalancing"]:
                    print(f"Current State:\n{get_jar_summary()}")
                    continue
                    
                result = handle_confidence_flow(scenario, self.llm_with_tools)
                print(f"Result: {result}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 50)
        
        print("\n✅ Rebalancing testing completed!")
    
    def run_confidence_tests(self):
        """Run tests focused on confidence scoring and edge cases"""
        
        if not self.setup():
            return
        
        print("\n🎯 Running Confidence & Edge Case Tests...")
        
        confidence_scenarios = [
            # High confidence (90%+)
            ("High confidence - clear percentage", "create vacation jar with 15%"),
            ("High confidence - clear amount", "create emergency fund with $1000"),
            ("High confidence - multi-jar clear", "create car and home jars with 10% each"),
            
            # Medium confidence (70-89%)
            ("Medium confidence - vague amount", "add entertainment jar"),
            ("Medium confidence - unclear purpose", "create saving jar for future"),
            
            # Low confidence / clarification needed
            ("Low confidence - very vague", "create jar for stuff"),
            ("Clarification needed - missing info", "create jar"),
            ("Clarification needed - no amount", "add vacation jar for travel"),
            
            # Vietnamese confidence tests
            ("Vietnamese high confidence", "tạo hũ du lịch với 15%"),
            ("Vietnamese medium confidence", "tạo hũ tiết kiệm"),
            
            # Edge cases
            ("Edge case - impossible percentage", "create jar with 200%"),
            ("Edge case - negative amount", "create jar with -$500"),
            ("Edge case - zero amount", "create jar with $0"),
        ]
        
        for i, (description, scenario) in enumerate(confidence_scenarios, 1):
            print(f"\n--- Confidence Test {i}/{len(confidence_scenarios)}: {description} ---")
            print(f"Input: '{scenario}'")
            
            try:
                result = handle_confidence_flow(scenario, self.llm_with_tools)
                print(f"Result: {result}")
                
                # Analyze confidence level from result
                if "confident)" in result:
                    if "✅" in result:
                        print("✅ High confidence operation completed")
                    elif "⚠️" in result:
                        print("⚠️ Medium confidence operation completed")
                    elif "❓" in result:
                        print("❓ Low confidence - verification requested")
                elif "❓" in result and "clarification" in result.lower():
                    print("🤔 Clarification requested - good edge case handling")
                elif "❌" in result:
                    print("❌ Operation rejected - good validation")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 50)
        
        print("\n✅ Confidence testing completed!")

def main():
    """Main entry point for multi-jar manager testing"""
    
    tester = MultiJarManagerTester()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--batch', '-b']:
            tester.run_batch_tests()
        elif arg in ['--rebalancing', '-r']:
            tester.run_rebalancing_tests()
        elif arg in ['--confidence', '-c']:
            tester.run_confidence_tests()
        elif arg in ['--help', '-h']:
            print("""
Multi-Jar Manager Test Interface

Usage:
  python test.py                 # Interactive mode
  python test.py --batch         # Run comprehensive batch tests
  python test.py --rebalancing   # Test automatic rebalancing functionality
  python test.py --confidence    # Test confidence scoring and edge cases
  python test.py --help          # Show this help

Interactive Commands:
  help     - Show command examples
  summary  - Show current jar state
  reset    - Reset to T. Harv Eker's 6-jar system
  debug    - Toggle debug mode
  quit     - Exit program

Example Operations:
  Single:    "create vacation jar with 15%"
  Multi:     "create vacation and emergency jars with 10% each"
  Update:    "update vacation to 12% and emergency to 8%"
  Delete:    "delete vacation and car repair jars"
  
Features:
  • T. Harv Eker's official 6-jar system
  • Automatic percentage rebalancing
  • Multi-jar operations with atomic transactions
  • Percentage (0.0-1.0) and amount ($) input modes
  • Vietnamese language support
  • Overflow detection and warnings
            """)
        else:
            print(f"❌ Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        # Default: interactive mode
        tester.run_interactive()

if __name__ == "__main__":
    main()
