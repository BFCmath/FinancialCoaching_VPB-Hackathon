"""
Knowledge Base Agent Testing Framework
====================================

Test framework for the ReAct-based knowledge agent.
This agent is purely functional (no state/follow-up) and uses ReAct framework
for reasoning about financial knowledge and app features.

Key Features:
- Financial knowledge queries
- App feature explanations
- Vietnamese language support
- ReAct framework validation
- Tool usage verification

Usage:
    cd agent-testing-lab/full_multi_agent
    python -m agents.knowledge.test

Example Queries:
    'What is compound interest?'
    'How does the jar system work?'
    'tôi muốn tiết kiệm tiền'
    'What budgeting features are available?'
"""

import os
import sys
import time
from typing import Dict, Any, List

# Path setup for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(grandparent_dir)

from agents.knowledge.interface import KnowledgeAgent
from agents.knowledge.main import get_knowledge

class KnowledgeAgentTester:
    """Test framework for ReAct-based Knowledge Agent"""
    
    def __init__(self):
        """Initialize the test framework"""
        self.agent = KnowledgeAgent()
        self.test_results = []
    
    def run_interactive_test(self):
        """Interactive testing mode"""
        print("=" * 60)
        print("                Knowledge Agent Test")
        print("=" * 60)
        print("📚 Financial Knowledge & App Documentation Assistant")
        print("\nQuery Categories:")
        print("  Financial: 'What is compound interest?'")
        print("            'How does inflation work?'")
        print("            'Explain emergency funds'")
        print("\nApp Features: 'How does the jar system work?'")
        print("             'What budgeting features are available?'")
        print("             'How do I track my spending?'")
        print("\nMixed Queries: 'How can I save money using this app?'")
        print("              'What's the best way to budget?'")
        print("\nVietnamese: 'tôi muốn tiết kiệm tiền'")
        print("           'làm thế nào để theo dõi chi tiêu'")
        print("\nCommands: 'exit' to end session")
        print("=" * 60)
        
        while True:
            try:
                query = input("\nYou: ").strip()
                
                if query.lower() in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    break
                    
                if not query:
                    continue
                
                print("\n🤔 Processing with ReAct framework...")
                start_time = time.time()
                
                response = self.agent.process(query)
                elapsed = time.time() - start_time
                
                print(f"\n🤖 Response ({elapsed:.2f}s):")
                print("-" * 50)
                print(response)
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def run_predefined_tests(self) -> Dict[str, Any]:
        """Run predefined test scenarios"""
        print("\n🧪 Running Predefined Test Scenarios")
        print("=" * 50)
        
        scenarios = [
            # Financial Knowledge (Direct Explanations)
            ("What is compound interest?",
             "Basic financial concept explanation"),
            ("How does inflation work?",
             "Economic concept explanation"),
            ("Explain emergency funds",
             "Financial planning fundamentals"),
            ("What's the difference between saving and investing?",
             "Core financial education"),
             
            # App Features (Documentation Queries)
            ("How does the jar system work?",
             "Core feature explanation"),
            ("What budgeting features are available?",
             "Feature overview query"),
            ("How do I track my spending?",
             "Usage guidance"),
            ("Tell me about subscription tracking",
             "Specific feature inquiry"),
             
            # Combined Knowledge (Multi-tool Usage)
            ("What is budgeting and how does this app help?",
             "Combines concept and features"),
            ("How can I save money using the jar system?",
             "Financial advice with features"),
            ("Explain the best way to manage my budget",
             "Practical advice with tools"),
             
            # Vietnamese Language Support
            ("tôi muốn tiết kiệm tiền",  # I want to save money
             "Basic Vietnamese query"),
            ("làm thế nào để theo dõi chi tiêu",  # How to track expenses
             "Complex Vietnamese query"),
             
            # Edge Cases
            ("",
             "Empty input handling"),
            ("tell me everything",
             "Too broad query"),
            ("xyz123",
             "Invalid input handling")
        ]
        
        results = []
        total = len(scenarios)
        passed = 0
        
        for i, (query, expected) in enumerate(scenarios, 1):
            print(f"\n{i:2d}. Query: '{query}'")
            print(f"    Expected: {expected}")
            
            try:
                start_time = time.time()
                response = self.agent.process(query)
                elapsed = time.time() - start_time
                
                # Validate response
                is_valid = (
                    len(response) > 50 and 
                    "Error" not in response and
                    (query == "" or query.lower() in response.lower())
                )
                
                if is_valid:
                    passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                print(f"    ⏱️  Time: {elapsed:.2f}s")
                print(f"    Status: {status}")
                print(f"    Response: {response[:150]}..." if len(response) > 150 else f"    Response: {response}")
                
                results.append({
                    "query": query,
                    "expected": expected,
                    "response": response,
                    "time": elapsed,
                    "valid": is_valid
                })
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                results.append({
                    "query": query,
                    "expected": expected,
                    "error": str(e),
                    "valid": False
                })
            
            print("-" * 60)
        
        # Summary
        print(f"\n📊 Test Results Summary")
        print("=" * 30)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        return results

    def test_react_flow(self) -> bool:
        """Test the ReAct framework's reasoning and tool usage flow"""
        print("\n🔄 REACT FRAMEWORK VALIDATION")
        print("=" * 60)
        
        test_scenarios = [
            {
                "query": "What is compound interest and how can I save money using this app?",
                "description": "Complex query requiring financial knowledge and app features",
                "expected_tools": ["search_online", "get_application_information"],
                "required_elements": ["compound interest", "save", "app"]
            },
            {
                "query": "Compare different investment strategies and how to track them",
                "description": "Multi-aspect query needing external and internal info",
                "expected_tools": ["search_online", "get_application_information"],
                "required_elements": ["investment", "track", "strategy"]
            },
            {
                "query": "tôi muốn đầu tư và theo dõi trong ứng dụng",  # I want to invest and track in the app
                "description": "Vietnamese complex query with multiple aspects",
                "expected_tools": ["search_online", "get_application_information"],
                "required_elements": ["đầu tư", "theo dõi"]  # invest, track
            }
        ]
        
        passed = 0
        total = len(test_scenarios)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario['description']}")
            print(f"Query: '{scenario['query']}'")
            
            try:
                start_time = time.time()
                response = self.agent.process(scenario['query'])
                elapsed = time.time() - start_time
                
                # Validate response
                has_required = all(
                    element.lower() in response.lower() 
                    for element in scenario['required_elements']
                )
                
                is_valid = (
                    len(response) > 100 and
                    has_required and
                    "Error" not in response
                )
                
                if is_valid:
                    passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                print(f"\n⏱️  Response time: {elapsed:.2f}s")
                print(f"Status: {status}")
                print(f"Response Preview: {response[:150]}...")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            print("-" * 60)
        
        # Summary
        print(f"\n📊 ReAct Framework Test Results")
        print(f"Total Scenarios: {total}")
        print(f"Passed: {passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        return passed == total

def main():
    """Main testing interface"""
    print("🧠 Knowledge Agent Test Lab (ReAct Framework)")
    print("=" * 50)
    
    tester = KnowledgeAgentTester()
    
    while True:
        print("\nTest Options:")
        print("1. 💬 Interactive Testing")
        print("2. 🧪 Run Predefined Scenarios")
        print("3. 🔄 Test ReAct Framework Flow")
        print("4. 🚪 Exit")
        
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                tester.run_interactive_test()
            elif choice == '2':
                tester.run_predefined_tests()
            elif choice == '3':
                tester.test_react_flow()
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Direct interactive mode
        tester = KnowledgeAgentTester()
        tester.run_interactive_test()
    else:
        main() 