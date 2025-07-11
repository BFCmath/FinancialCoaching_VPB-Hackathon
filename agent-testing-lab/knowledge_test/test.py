"""
Knowledge Base Agent Testing Framework
=====================================

Comprehensive testing for the knowledge base agent including:
- Interactive testing
- Predefined test scenarios
- Tool validation
- ReAct framework testing
"""

import sys
import time
from typing import List, Dict, Any, Optional
from main import KnowledgeBaseAgent, get_knowledge_response
from config import config, validate_environment
from tools import get_all_knowledge_tools


def get_example_queries(category: str = "all") -> List[str]:
    """
    Get example queries for different categories.
    
    Args:
        category: Query category (financial_knowledge, app_features, mixed_questions, or all)
        
    Returns:
        List of example queries
    """
    
    examples = {
        "financial_knowledge": [
            "What is compound interest?",
            "How does budgeting work?", 
            "What are investment strategies?",
            "Explain emergency funds",
            "What is the difference between savings and checking accounts?",
            "How do credit scores work?"
        ],
        "app_features": [
            "How does this app work?",
            "What is the jar system?",
            "Tell me about budget suggestions",
            "How does automatic categorization work?",
            "How do I track subscriptions?",
            "What are the main features of this app?"
        ],
        "mixed_questions": [
            "What is budgeting and how does this app help?",
            "Explain savings and how to track them in the app",
            "How can this app help me manage my finances better?",
            "What financial concepts should I know and how does the app support them?"
        ]
    }
    
    if category == "all":
        all_queries = []
        for queries in examples.values():
            all_queries.extend(queries)
        return all_queries
    
    return examples.get(category, [])


class KnowledgeBaseAgentTester:
    """Comprehensive testing framework for the knowledge base agent"""
    
    def __init__(self):
        """Initialize the tester"""
        self.agent = None
        self.test_results = []
        
    def setup_agent(self) -> bool:
        """
        Setup the agent for testing.
        
        Returns:
            True if setup successful
        """
        try:
            self.agent = KnowledgeBaseAgent()
            print("✅ Agent initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Agent initialization failed: {str(e)}")
            return False
    
    def run_interactive_test(self):
        """Run interactive testing mode"""
        
        print("\n🧠 Knowledge Base Agent - Interactive Testing")
        print("=" * 50)
        print("Ask questions about:")
        print("📚 Financial concepts (compound interest, budgeting, etc.)")
        print("📱 App features (jar system, budget advisor, etc.)")
        print("Type 'quit' to exit, 'help' for examples\n")
        
        while True:
            try:
                user_input = input("❓ Your question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Testing session ended!")
                    break
                
                if user_input.lower() in ['help', 'examples']:
                    self.show_example_queries()
                    continue
                
                if not user_input:
                    continue
                
                print(f"\n🤔 Processing: '{user_input}'")
                start_time = time.time()
                
                try:
                    response = self.agent.get_knowledge(user_input)
                    elapsed_time = time.time() - start_time
                    
                    print(f"\n💡 Response ({elapsed_time:.2f}s):")
                    print("-" * 30)
                    print(response)
                    print("-" * 50)
                    
                    # Store result for analysis
                    self.test_results.append({
                        "query": user_input,
                        "response": response,
                        "time": elapsed_time,
                        "status": "success"
                    })
                    
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
                    self.test_results.append({
                        "query": user_input,
                        "response": f"Error: {str(e)}",
                        "time": 0,
                        "status": "error"
                    })
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Testing session ended!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
    
    def run_predefined_tests(self) -> Dict[str, Any]:
        """
        Run predefined test scenarios.
        
        Returns:
            Test results summary
        """
        
        print("\n🧪 Running Predefined Test Scenarios")
        print("=" * 50)
        
        test_categories = {
            "financial_knowledge": [
                "What is compound interest?",
                "How does budgeting work?",
                "What are investment strategies?",
                "Explain emergency funds"
            ],
            "app_features": [
                "How does this app work?",
                "What is the jar system?",
                "Tell me about budget suggestions",
                "How does automatic categorization work?"
            ],
            "mixed_questions": [
                "What is budgeting and how does this app help?",
                "Explain savings and how to track them in the app"
            ]
        }
        
        results = {}
        total_tests = 0
        passed_tests = 0
        
        for category, queries in test_categories.items():
            print(f"\n📋 Testing {category.replace('_', ' ').title()}")
            print("-" * 30)
            
            category_results = []
            
            for query in queries:
                total_tests += 1
                print(f"\n🔍 Query: {query}")
                
                try:
                    start_time = time.time()
                    response = self.agent.get_knowledge(query)
                    elapsed_time = time.time() - start_time
                    
                    # Basic validation
                    is_valid = self.validate_response(response, query)
                    
                    if is_valid:
                        passed_tests += 1
                        status = "✅ PASS"
                    else:
                        status = "❌ FAIL"
                    
                    print(f"⏱️  Time: {elapsed_time:.2f}s")
                    print(f"📄 Response: {response[:100]}..." if len(response) > 100 else f"📄 Response: {response}")
                    print(f"🔍 Status: {status}")
                    
                    category_results.append({
                        "query": query,
                        "response": response,
                        "time": elapsed_time,
                        "valid": is_valid,
                        "status": "success"
                    })
                    
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
                    category_results.append({
                        "query": query,
                        "response": f"Error: {str(e)}",
                        "time": 0,
                        "valid": False,
                        "status": "error"
                    })
            
            results[category] = category_results
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 30)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        return {
            "results": results,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": passed_tests/total_tests*100
            }
        }
    
    def validate_response(self, response: str, query: str) -> bool:
        """
        Basic validation of response quality.
        
        Args:
            response: The agent's response
            query: The original query
            
        Returns:
            True if response appears valid
        """
        
        if not response or len(response.strip()) < 10:
            return False
        
        # Check for error indicators
        error_indicators = ["error", "failed", "couldn't", "unable", "sorry"]
        if any(indicator in response.lower() for indicator in error_indicators):
            return False
        
        # Check if response is relevant to query
        query_words = query.lower().split()
        response_lower = response.lower()
        
        # At least some query words should appear in response
        matching_words = sum(1 for word in query_words if word in response_lower)
        relevance_ratio = matching_words / len(query_words)
        
        return relevance_ratio > 0.2  # At least 20% of query words should appear
    
    def test_tool_functionality(self) -> Dict[str, Any]:
        """
        Test individual tool functionality.
        
        Returns:
            Tool test results
        """
        
        print("\n🔧 Testing Individual Tools")
        print("=" * 40)
        
        tools = get_all_knowledge_tools()
        results = {}
        
        for tool in tools:
            tool_name = tool.name
            print(f"\n🛠️  Testing {tool_name}")
            
            try:
                if tool_name == "search_online":
                    result = tool.invoke({"query": "compound interest", "description": "test search"})
                elif tool_name == "get_application_information":
                    result = tool.invoke({"description": "test app info"})
                elif tool_name == "respond":
                    result = tool.invoke({"answer": "test response", "description": "test respond"})
                
                print(f"✅ {tool_name}: Working")
                results[tool_name] = {"status": "success", "result": result}
                
            except Exception as e:
                print(f"❌ {tool_name}: Error - {str(e)}")
                results[tool_name] = {"status": "error", "error": str(e)}
        
        return results
    
    def test_react_framework(self) -> bool:
        """
        Test the ReAct framework with a simple query.
        
        Returns:
            True if ReAct framework works correctly
        """
        
        print("\n🔄 Testing ReAct Framework")
        print("=" * 30)
        
        test_query = "What is compound interest?"
        
        try:
            print(f"🔍 Test Query: {test_query}")
            
            # Enable debug mode for this test
            original_debug = config.debug_mode
            config.debug_mode = True
            
            response = self.agent.get_knowledge(test_query)
            
            # Restore debug mode
            config.debug_mode = original_debug
            
            print(f"✅ ReAct Response: {response[:100]}...")
            
            # Basic validation
            if response and len(response) > 20 and "compound interest" in response.lower():
                print("✅ ReAct framework is working correctly")
                return True
            else:
                print("❌ ReAct framework response seems invalid")
                return False
                
        except Exception as e:
            print(f"❌ ReAct framework test failed: {str(e)}")
            return False
    
    def show_example_queries(self):
        """Show example queries for different categories"""
        
        print("\n💡 Example Queries")
        print("=" * 20)
        
        print("\n📚 Financial Knowledge:")
        for query in get_example_queries("financial_knowledge"):
            print(f"  • {query}")
        
        print("\n📱 App Features:")
        for query in get_example_queries("app_features"):
            print(f"  • {query}")
        
        print("\n🔄 Mixed Questions:")
        for query in get_example_queries("mixed_questions"):
            print(f"  • {query}")
        
        print()
    
    def run_performance_test(self, num_queries: int = 5) -> Dict[str, Any]:
        """
        Run performance testing.
        
        Args:
            num_queries: Number of queries to test
            
        Returns:
            Performance test results
        """
        
        print(f"\n⚡ Performance Testing ({num_queries} queries)")
        print("=" * 40)
        
        test_queries = [
            "What is compound interest?",
            "How does the jar system work?",
            "What is budgeting?",
            "Tell me about app features",
            "What are investment strategies?"
        ][:num_queries]
        
        response_times = []
        successful_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Query {i}/{num_queries}: {query}")
            
            try:
                start_time = time.time()
                response = self.agent.get_knowledge(query)
                elapsed_time = time.time() - start_time
                
                response_times.append(elapsed_time)
                
                if response and len(response) > 10:
                    successful_queries += 1
                    print(f"✅ Success in {elapsed_time:.2f}s")
                else:
                    print(f"❌ Invalid response in {elapsed_time:.2f}s")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"\n📊 Performance Results:")
            print(f"  • Average response time: {avg_time:.2f}s")
            print(f"  • Fastest response: {min_time:.2f}s")
            print(f"  • Slowest response: {max_time:.2f}s")
            print(f"  • Success rate: {successful_queries}/{num_queries} ({successful_queries/num_queries*100:.1f}%)")
            
            return {
                "average_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "success_rate": successful_queries/num_queries*100,
                "total_queries": num_queries
            }
        
        return {"error": "No successful queries"}


def main():
    """Main testing interface"""
    
    print("🧠 Knowledge Base Agent - Testing Framework")
    print("=" * 50)
    
    # Validate environment first
    if not validate_environment():
        print("\n❌ Environment validation failed. Please check your configuration.")
        return
    
    # Initialize tester
    tester = KnowledgeBaseAgentTester()
    
    if not tester.setup_agent():
        print("\n❌ Agent setup failed. Cannot proceed with testing.")
        return
    
    # Show menu
    while True:
        print("\n🔍 Testing Options:")
        print("1. 💬 Interactive Testing")
        print("2. 🧪 Predefined Test Scenarios")
        print("3. 🔧 Tool Functionality Tests")
        print("4. 🔄 ReAct Framework Test")
        print("5. ⚡ Performance Test")
        print("6. 💡 Show Example Queries")
        print("7. ⚙️ Show Configuration")
        print("8. 🚪 Exit")
        
        try:
            choice = input("\n❓ Select option (1-8): ").strip()
            
            if choice == "1":
                tester.run_interactive_test()
            elif choice == "2":
                tester.run_predefined_tests()
            elif choice == "3":
                tester.test_tool_functionality()
            elif choice == "4":
                tester.test_react_framework()
            elif choice == "5":
                num_queries = input("Number of queries for performance test (default 5): ").strip()
                num_queries = int(num_queries) if num_queries.isdigit() else 5
                tester.run_performance_test(num_queries)
            elif choice == "6":
                tester.show_example_queries()
            elif choice == "7":
                print(config.display_config())
            elif choice == "8":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
