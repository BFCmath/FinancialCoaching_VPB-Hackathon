"""
Interactive Testing for Transaction Classifier
===============================================

Test the LLM-powered classifier with various scenarios and user inputs.
"""

from main import classify_and_add_transaction, classify_simple
from config import config
from tools import fetch_jar_information, fetch_past_transactions


def display_context():
    """Display current jar and transaction context."""
    print("📊 CURRENT CONTEXT")
    print("=" * 50)
    
    # Show jars
    jars = fetch_jar_information()
    print("\n💰 Available Jars:")
    for jar in jars:
        print(f"  • {jar['name']}: ${jar['current']}/${jar['budget']} - {jar['description']}")
    
    # Show recent transactions
    transactions = fetch_past_transactions()
    print("\n📝 Recent Transactions:")
    for tx in transactions[:5]:
        print(f"  • ${tx['amount']} → {tx['jar']}: '{tx['description']}' ({tx['date']})")
    print()


def test_predefined_scenarios():
    """Test with predefined scenarios covering different use cases."""
    scenarios = [
        # High confidence transactions (90-100%)
        ("meal 20 dollar", "Should add to meals jar with high confidence"),
        ("groceries 45 dollars", "Should add to groceries jar with high confidence"),
        ("gas 50 dollar", "Should add to gas jar with high confidence"),
        ("rent 1200", "Should add to rent jar with high confidence"),
        
        # Vietnamese inputs (should be high confidence)
        ("tôi ăn cơm 25k", "Vietnamese meal input - high confidence"),
        ("mua xăng 100k", "Vietnamese gas purchase - high confidence"),
        ("đi taxi 15k", "Vietnamese transport - high confidence"),
        
        # Multiple high confidence transactions
        ("gas 50, groceries 30", "Two clear jars - both high confidence"),
        ("meal 20, utilities 65", "Two different clear transactions"),
        
        # Medium confidence transactions (70-89%)
        ("snack 10 dollar", "Could be meals or groceries - medium confidence"),
        ("coffee 5 dollar", "Could be meals - medium confidence"),
        ("internet bill 65", "Should be utilities but medium confidence"),
        
        # Multiple mixed confidence
        ("chicken rice 10, youtube subscription 100, medicine bill 100", "Mixed confidence levels"),
        ("coffee 5, gas 50", "One medium, one high confidence"),
        ("snack 10, groceries 30", "One uncertain, one confident"),
        
        # Low confidence or unclear transactions
        ("subscription 15", "Unclear which subscription - lower confidence"),
        ("bill 100", "Vague description - need more info or low confidence"),
        
        # Complex multi-transaction formats
        ("meal 20; gas 40; entertainment 25", "Semicolon separated - mixed confidence"),
        ("tôi ăn cơm 25k, mua xăng 100k", "Vietnamese multiple - both high confidence"),
        ("1. coffee 5 2. lunch 15 3. gas 40", "Numbered list - mixed confidence"),
        
        # No suitable jar (should use report_no_suitable_jar)
        ("gym membership 30 dollar", "No fitness jar exists"),
        ("medical checkup 100 dollar", "Should suggest health category"),
        
        # Need more info (should use request_more_info)
        ("50k", "Amount only, no description"),
        ("bought something", "Description only, no amount"),
        ("", "Empty input"),
        
        # Amount format variations
        ("meal 20k", "K format for thousands"),
        ("dinner 25 đô la", "Vietnamese dollar format"),
        ("lunch twenty dollars", "Written amount"),
    ]
    
    print("🧪 PREDEFINED TEST SCENARIOS (Confidence-Based)")
    print("=" * 60)
    
    for i, (user_input, expected) in enumerate(scenarios, 1):
        print(f"\n{i:2d}. Input: '{user_input}'")
        print(f"    Expected: {expected}")
        
        try:
            result = classify_and_add_transaction(user_input)
            print(f"    Result: {result}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        print("-" * 60)


def interactive_testing():
    """Interactive testing mode for manual input testing."""
    print("🎮 INTERACTIVE TESTING MODE")
    print("=" * 50)
    print("Enter transaction descriptions to test the classifier.")
    print("Type 'quit' to exit, 'context' to see jars/transactions, 'debug' to toggle debug mode.")
    print()
    
    while True:
        try:
            user_input = input("💬 Enter transaction: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'context':
                display_context()
                continue
            elif user_input.lower() == 'debug':
                config.debug_mode = not config.debug_mode
                print(f"🔧 Debug mode: {'ON' if config.debug_mode else 'OFF'}")
                continue
            elif not user_input:
                continue
            
            print(f"🤖 Processing: '{user_input}'")
            result = classify_and_add_transaction(user_input)
            print(f"🎯 Result: {result}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def test_simple_mode():
    """Test with simplified prompts."""
    print("🔧 SIMPLE MODE TESTING")
    print("=" * 50)
    
    simple_tests = [
        "meal 20 dollar",
        "groceries 30 dollar", 
        "unknown expense 15 dollar"
    ]
    
    for test_input in simple_tests:
        print(f"\n📝 Input: '{test_input}'")
        result = classify_simple(test_input)
        print(f"🎯 Result: {result}")


def main():
    """Main testing interface."""
    # Check configuration
    issues = config.validate()
    if issues:
        print("⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   • {issue}")
        print("Please fix configuration before testing.\n")
        return
    
    print("🧪 TRANSACTION CLASSIFIER TEST LAB")
    print("=" * 50)
    print(f"Model: {config.model_name}")
    print(f"Temperature: {config.temperature}")
    print(f"Debug mode: {'ON' if config.debug_mode else 'OFF'}")
    print()
    
    while True:
        print("Choose testing mode:")
        print("1. 📊 Display Context (jars & transactions)")
        print("2. 🎯 Predefined Scenarios")
        print("3. 🎮 Interactive Testing") 
        print("4. 🔧 Simple Mode Testing")
        print("5. 🚪 Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            display_context()
        elif choice == '2':
            test_predefined_scenarios()
        elif choice == '3':
            interactive_testing()
        elif choice == '4':
            test_simple_mode()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")
        
        print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
