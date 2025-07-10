"""
Transaction History Fetcher Testing Interface
=============================================

Interactive testing lab for LangChain tool binding with multi-tool intelligence.
"""

import json
from typing import Dict, List
from main import TransactionHistoryFetcher, fetch_transaction_history
from config import config

def test_tool_binding():
    """Test the LangChain tool binding with various scenarios."""
    
    print("🧪 LangChain Tool Binding Testing")
    print("=" * 50)
    
    # Initialize history fetcher
    try:
        fetcher = TransactionHistoryFetcher()
        print("✅ Transaction history fetcher initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize fetcher: {e}")
        return
    
    # Test scenarios for tool binding
    test_scenarios = [
        {
            "name": "Simple Jar Query",
            "query": "Show me all my groceries transactions",
            "expected": "Should use get_jar_transactions with groceries"
        },
        {
            "name": "Time Period Query", 
            "query": "What did I spend last month?",
            "expected": "Should use get_time_period_transactions"
        },
        {
            "name": "Amount Range Query",
            "query": "Show me all transactions over $50",
            "expected": "Should use get_amount_range_transactions"
        },
        {
            "name": "Comparison Query",
            "query": "Compare groceries vs meals spending",
            "expected": "Should use multiple get_jar_transactions calls"
        },
        {
            "name": "Multi-Filter Query",
            "query": "Large entertainment purchases from last month",
            "expected": "Should combine time and amount filtering"
        },
        {
            "name": "Behavioral Analysis",
            "query": "What do I buy in the morning?",
            "expected": "Should use get_hour_range_transactions"
        },
        {
            "name": "Source Analysis",
            "query": "Show me manually entered transactions",
            "expected": "Should use get_source_transactions"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔬 Test {i}: {scenario['name']}")
        print(f"Query: '{scenario['query']}'")
        print(f"Expected: {scenario['expected']}")
        print("-" * 40)
        
        try:
            result = fetcher.fetch_transaction_history(scenario['query'])
            print("📋 Result:")
            if isinstance(result, list) and result:
                # New format: list of tool results with descriptions
                total_transactions = 0
                for tool_result in result:
                    if "data" in tool_result and "description" in tool_result:
                        print(f"✅ {tool_result['description']}: {len(tool_result['data'])} transactions")
                        total_transactions += len(tool_result['data'])
                        if tool_result['data']:
                            sample_tx = tool_result['data'][0]
                            print(f"   Sample: {sample_tx.get('date', 'N/A')}: ${sample_tx.get('amount', 0):.2f} - {sample_tx.get('description', 'No description')}")
                print(f"✅ Total: {total_transactions} transactions across {len(result)} tool(s)")
            elif isinstance(result, list):
                print("No data returned")
            else:
                print("❌ Expected list, got:", type(result))
            print("✅ Test completed")
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        print()

def interactive_fetcher_chat():
    """Interactive chat mode using transaction history fetcher."""
    
    print("💬 Interactive Transaction History Chat")
    print("=" * 50)
    print("Ask questions about your transactions and spending.")
    print("The AI will use intelligent tool selection to get your data.")
    print("Type 'quit' to exit.\n")
    
    try:
        fetcher = TransactionHistoryFetcher()
    except Exception as e:
        print(f"❌ Failed to initialize fetcher: {e}")
        return
    
    while True:
        try:
            user_input = input("💭 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n🔄 Processing with tool binding...")
            print("-" * 40)
            
            # Enable debug mode for interactive sessions
            original_debug = config.debug_mode
            config.debug_mode = True
            
            try:
                result = fetcher.fetch_transaction_history(user_input)
                print("\n📋 Response:")
                if isinstance(result, list) and result:
                    total_transactions = 0
                    total_amount = 0
                    
                    for tool_result in result:
                        if "data" in tool_result and "description" in tool_result:
                            data = tool_result['data']
                            description = tool_result['description']
                            
                            print(f"✅ {description}: {len(data)} transactions")
                            
                            if data:
                                tool_amount = sum(tx.get('amount', 0) for tx in data)
                                total_amount += tool_amount
                                total_transactions += len(data)
                                
                                print(f"   💰 Total: ${tool_amount:.2f}")
                                print("   📋 Recent transactions:")
                                for i, tx in enumerate(data[:2]):  # Show first 2
                                    print(f"     • {tx.get('date', 'N/A')}: ${tx.get('amount', 0):.2f} - {tx.get('description', 'No description')}")
                                if len(data) > 2:
                                    print(f"     ... and {len(data) - 2} more")
                            print()
                    
                    if len(result) > 1:
                        print(f"🎯 Summary: {total_transactions} total transactions, ${total_amount:.2f} total amount")
                        
                elif isinstance(result, list):
                    print("No transactions found for your query")
                else:
                    print("❌ Unexpected result format:", type(result))
            finally:
                config.debug_mode = original_debug
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def test_multi_tool_scenarios():
    """Test complex multi-tool scenarios."""
    
    print("🎯 Multi-Tool Scenario Testing")
    print("=" * 50)
    
    fetcher = TransactionHistoryFetcher()
    
    scenarios = [
        {
            "name": "Food Spending Comparison",
            "query": "Compare my groceries vs meals spending",
            "description": "Should use multiple jar-specific calls and format comparison"
        },
        {
            "name": "Time-based Behavioral Analysis",
            "query": "Compare morning vs evening spending patterns",
            "description": "Should use hour range tools for different time periods"
        },
        {
            "name": "Amount and Category Filter",
            "query": "Show me large entertainment purchases over $30",
            "description": "Should combine amount filtering with jar filtering"
        },
        {
            "name": "Source Quality Analysis",
            "query": "Compare manual entries vs bank imported data",
            "description": "Should use source filtering tools for comparison"
        },
        {
            "name": "Complex Time and Amount Query",
            "query": "Small transactions under $15 from last week",
            "description": "Should combine time period and amount range filtering"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔧 Scenario {i}: {scenario['name']}")
        print(f"Query: '{scenario['query']}'")
        print(f"Description: {scenario['description']}")
        print("-" * 40)
        
        try:
            # Enable debug to see tool calls
            original_debug = config.debug_mode
            config.debug_mode = True
            
            result = fetcher.fetch_transaction_history(scenario['query'])
            
            config.debug_mode = original_debug
            
            print("📊 Result:")
            if isinstance(result, list) and result:
                total_transactions = 0
                total_amount = 0
                
                for tool_result in result:
                    if "data" in tool_result and "description" in tool_result:
                        data = tool_result['data']
                        description = tool_result['description']
                        
                        print(f"✅ {description}: {len(data)} transactions")
                        
                        if data:
                            tool_amount = sum(tx.get('amount', 0) for tx in data)
                            total_amount += tool_amount
                            total_transactions += len(data)
                            avg_amount = tool_amount / len(data)
                            
                            print(f"   💰 Total: ${tool_amount:.2f}, Average: ${avg_amount:.2f}")
                            
                            # Show sample transactions
                            print("   📋 Sample transactions:")
                            for i, tx in enumerate(data[:2]):
                                print(f"     • {tx.get('date', 'N/A')}: ${tx.get('amount', 0):.2f} - {tx.get('description', 'No description')}")
                        print()
                
                if len(result) > 1:
                    print(f"🎯 Overall Summary: {total_transactions} transactions, ${total_amount:.2f} total")
                    
            elif isinstance(result, list):
                print("No transactions found")
            else:
                print("❌ Expected list, got:", type(result))
            print("✅ Scenario completed")
        except Exception as e:
            print(f"❌ Scenario failed: {e}")
        
        print()

def test_tool_combinations():
    """Test specific tool combination patterns."""
    
    print("🔧 Tool Combination Testing")
    print("=" * 50)
    
    fetcher = TransactionHistoryFetcher()
    
    combinations = [
        {
            "name": "Single Tool - Jar Filter",
            "query": "Show me transportation expenses",
            "expected_tools": 1
        },
        {
            "name": "Dual Tool - Comparison",
            "query": "Compare health vs utilities spending",
            "expected_tools": 2
        },
        {
            "name": "Multi-Filter - Time + Amount",
            "query": "Large purchases over $100 from February",
            "expected_tools": "2-3"
        },
        {
            "name": "Complex Query - Multiple Dimensions",
            "query": "Compare morning vs evening meal spending patterns",
            "expected_tools": "2-4"
        }
    ]
    
    for i, combo in enumerate(combinations, 1):
        print(f"\n⚙️ Combination {i}: {combo['name']}")
        print(f"Query: '{combo['query']}'")
        print(f"Expected tools: {combo['expected_tools']}")
        print("-" * 30)
        
        try:
            # Count tool calls with debug mode
            original_debug = config.debug_mode
            config.debug_mode = True
            
            result = fetcher.fetch_transaction_history(combo['query'])
            
            config.debug_mode = original_debug
            
            print(f"✅ Combination test completed")
        except Exception as e:
            print(f"❌ Combination test failed: {e}")

def quick_validation():
    """Quick validation of fetcher setup."""
    
    print("⚡ Quick Fetcher Validation")
    print("=" * 30)
    
    # Test 1: Configuration
    try:
        print(f"📋 Model: {config.model_name}")
        print(f"📋 Debug: {config.debug_mode}")
        print(f"📋 Mock Data: {config.mock_data_mode}")
        print(f"📋 Multi-tool: {config.enable_multi_tool_queries}")
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Test 2: Fetcher initialization
    try:
        fetcher = TransactionHistoryFetcher()
        print("✅ Transaction history fetcher initialized")
    except Exception as e:
        print(f"❌ Fetcher initialization failed: {e}")
        return
    
    # Test 3: Simple query
    try:
        result = fetcher.fetch_transaction_history("How many transactions do I have?")
        print("✅ Simple query processed")
        print(f"📊 Result preview: {result[:100]}...")
    except Exception as e:
        print(f"❌ Query processing failed: {e}")

def run_comprehensive_test_suite():
    """Run comprehensive test suite covering all functionality."""
    
    test_suites = [
        {
            "name": "Basic Queries",
            "queries": [
                "Show me my meals transactions",
                "All transactions from last week",
                "Entertainment spending"
            ]
        },
        {
            "name": "Amount-Based Queries", 
            "queries": [
                "Transactions over $50",
                "Small purchases under $20",
                "Medium expenses between $20 and $80"
            ]
        },
        {
            "name": "Time-Based Queries",
            "queries": [
                "What did I spend yesterday?",
                "This month's transactions",
                "Morning spending habits"
            ]
        },
        {
            "name": "Comparison Queries",
            "queries": [
                "Compare groceries vs entertainment",
                "Morning vs evening spending",
                "Manual vs bank transactions"
            ]
        },
        {
            "name": "Complex Multi-Filter",
            "queries": [
                "Large grocery purchases from last month",
                "Small entertainment expenses under $25",
                "Evening dining out patterns"
            ]
        }
    ]
    
    print("📋 Comprehensive Test Suite")
    print("=" * 50)
    
    fetcher = TransactionHistoryFetcher()
    
    for suite in test_suites:
        print(f"\n📂 {suite['name']} Test Suite")
        print("-" * 30)
        
        for i, query in enumerate(suite['queries'], 1):
            print(f"\n🔍 Query {i}: {query}")
            try:
                result = fetcher.fetch_transaction_history(query)
                # Show first line of result as preview
                first_line = result.split('\n')[0] if result else "No result"
                print(f"✅ Success: {first_line}")
            except Exception as e:
                print(f"❌ Failed: {e}")

def test_vietnamese_complex_query():
    """Test Vietnamese complex query handling."""
    
    print("🇻🇳 Vietnamese Complex Query Testing")
    print("=" * 50)
    
    vietnamese_queries = [
        {
            "query": "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô",
            "translation": "show me lunch information (11am -> 2pm) under $20",
            "expected_filters": "jar=meals, start_hour=11, end_hour=14, max_amount=20",
            "description": "Vietnamese lunch query with time and amount filters"
        },
        {
            "query": "ăn sáng từ 6 giờ đến 10 giờ sáng dưới 15 đô",
            "translation": "breakfast from 6am to 10am under $15",
            "expected_filters": "jar=meals, start_hour=6, end_hour=10, max_amount=15",
            "description": "Breakfast time filtering with amount"
        },
        {
            "query": "cho tôi xem chi tiêu giải trí tối (sau 6h chiều) trên 30 đô",
            "translation": "show me evening entertainment spending (after 6pm) over $30",
            "expected_filters": "jar=entertainment, start_hour=18, min_amount=30",
            "description": "Evening entertainment with amount threshold"
        },
        {
            "query": "mua sắm grocery buổi sáng dưới 100 đô từ bank data",
            "translation": "morning grocery shopping under $100 from bank data",
            "expected_filters": "jar=groceries, start_hour=6, end_hour=12, max_amount=100, source=vpbank_api",
            "description": "Complex 4-filter query: jar + time + amount + source"
        }
    ]
    
    fetcher = TransactionHistoryFetcher()
    
    for i, query_test in enumerate(vietnamese_queries, 1):
        print(f"\n🔍 Vietnamese Query {i}")
        print(f"Vietnamese: {query_test['query']}")
        print(f"Translation: {query_test['translation']}")
        print(f"Expected: {query_test['expected_filters']}")
        print(f"Type: {query_test['description']}")
        print("-" * 40)
        
        try:
            # Enable debug to see tool selection
            original_debug = config.debug_mode
            config.debug_mode = True
            
            result = fetcher.fetch_transaction_history(query_test['query'])
            
            config.debug_mode = original_debug
            
            if result:
                total_transactions = sum(len(r["data"]) for r in result)
                print(f"✅ Success: {len(result)} tool(s) called, {total_transactions} transactions found")
                
                # Show details of each tool call
                for j, tool_result in enumerate(result, 1):
                    print(f"   Tool {j}: {tool_result['tool_name']}")
                    print(f"   Args: {tool_result['args']}")
                    print(f"   Description: {tool_result['description']}")
                    print(f"   Results: {len(tool_result['data'])} transactions")
                    
                    # Show first few transactions as sample
                    if tool_result['data']:
                        print(f"   Sample: {tool_result['data'][0]['amount']} - {tool_result['data'][0]['description']} ({tool_result['data'][0]['time']})")
            else:
                print("⚠️ No results returned")
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    print(f"\n✅ Vietnamese complex query testing completed")

def main():
    """Main testing interface."""
    
    print("🔍 Transaction History Fetcher - Interactive Testing Lab")
    print("=" * 70)
    print(f"Configuration: {config.model_name} | Debug: {config.debug_mode} | Mock Data: {config.mock_data_mode}")
    print("=" * 70)
    
    options = {
        "1": ("💬 Interactive Transaction Chat", interactive_fetcher_chat),
        "2": ("🧪 Test Tool Binding", test_tool_binding),
        "3": ("🎯 Multi-Tool Scenarios", test_multi_tool_scenarios),
        "4": ("🔧 Tool Combination Tests", test_tool_combinations),
        "5": ("📋 Comprehensive Test Suite", run_comprehensive_test_suite),
        "6": ("🇻🇳 Vietnamese Complex Queries", test_vietnamese_complex_query),
        "7": ("⚡ Quick Validation", quick_validation),
        "8": ("❌ Exit", lambda: print("👋 Goodbye!"))
    }
    
    while True:
        print("\n📋 Testing Options:")
        for key, (description, _) in options.items():
            print(f"{key}. {description}")
        
        choice = input(f"\nSelect option (1-{len(options)}): ").strip()
        
        if choice in options:
            description, func = options[choice]
            print(f"\n🚀 {description}")
            print("-" * 50)
            
            if choice == "8":  # Exit
                func()
                break
            else:
                try:
                    func()
                except KeyboardInterrupt:
                    print("\n⏹️  Operation cancelled")
                except Exception as e:
                    print(f"\n❌ Error: {e}")
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    main()
