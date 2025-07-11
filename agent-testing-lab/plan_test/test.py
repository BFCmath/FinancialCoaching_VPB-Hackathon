"""
Budget Advisor Agent Testing Framework
=====================================

Comprehensive testing for the Budget Advisor agent including:
- Interactive testing
- Predefined test scenarios
- Tool validation
- ReAct framework testing
"""

import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import Budget Advisor components
from tools import (
    transaction_fetcher,
    get_plan,
    adjust_plan,
    create_plan,
    get_jar,
    respond,
    BUDGET_PLANS_STORAGE,
    BudgetPlan
)
from config import config
from main import setup_llm, provide_budget_advice


def get_example_queries(category: str = "all") -> List[str]:
    """
    Get example queries for different categories.
    
    Args:
        category: Query category (plan_management, advisory, integration, or all)
        
    Returns:
        List of example queries
    """
    
    examples = {
        "plan_management": [
            "Create vacation savings plan for Japan trip",
            "Update my emergency fund plan to completed status",
            "Show me all my active financial goals",
            "Create car purchase plan with $15,000 target"
        ],
        "advisory": [
            "Analyze my spending patterns this month",
            "Give me advice on optimizing my budget",
            "Help me plan for a major expense",
            "Review my financial progress"
        ],
        "integration": [
            "Check my jar allocations and spending",
            "Find my dining out expenses last week",
            "ăn trưa dưới 20 đô",  # Vietnamese query
            "coffee purchases last month"
        ],
        "proposals": [
            "Create new jar for vacation savings",
            "Optimize my current budget allocation",
            "Set up recurring fee tracking",
            "Rebalance spending categories"
        ]
    }
    
    if category == "all":
        all_queries = []
        for queries in examples.values():
            all_queries.extend(queries)
        return all_queries
    
    return examples.get(category, [])


class BudgetAdvisorTester:
    """Comprehensive testing framework for the Budget Advisor agent"""
    
    def __init__(self):
        """Initialize the tester"""
        self.test_results = []
        self.session_active = True
        self.llm_with_tools = None
        self.conversation_history = []  # [(user_input, agent_response), ...]
        
    def setup_testing(self) -> bool:
        """
        Setup the testing environment.
        
        Returns:
            True if setup successful
        """
        # Validate configuration
        issues = config.validate()
        if issues:
            print("⚠️  Configuration Issues:")
            for issue in issues:
                print(f"   • {issue}")
            print("Please fix configuration before testing.\n")
            return False
        
        # Setup the actual LLM agent
        self.llm_with_tools = setup_llm()
        if not self.llm_with_tools:
            print("❌ Failed to setup LLM agent")
            return False
        
        print("✅ Budget Advisor testing environment ready")
        print(f"🔧 Debug mode: {'ON' if config.debug_mode else 'OFF'}")
        print(f"📊 Storage status: {len(BUDGET_PLANS_STORAGE)} plans in storage")
        print(f"🤖 LLM Agent: {config.model_name} ready")
        return True
    
    def show_help(self):
        """Display available commands and examples"""
        print("""
📖 Budget Advisor Commands & Examples:

📋 PLAN MANAGEMENT:
• "Create vacation savings plan for Japan trip"
• "Show me all my active financial goals"
• "Update my emergency fund plan to completed"
• "Create car purchase plan with $15,000 target"

💡 ADVISORY REQUESTS:
• "Analyze my spending patterns this month"
• "Give me advice on optimizing my budget"
• "Help me plan for a major expense"
• "Review my financial progress"

📊 DATA INTEGRATION:
• "Check my jar allocations and spending"
• "Find my dining out expenses last week"
• "coffee purchases last month"
• "groceries spending this week"

🌍 VIETNAMESE SUPPORT:
• "ăn trưa dưới 20 đô"
• "chi tiêu cà phê"
• "tiết kiệm cho kỳ nghỉ"
• "tôi muốn đi nhật, giúp tôi"

🎯 BUDGET PROPOSALS:
• "Create new jar for vacation savings"
• "Optimize my current budget allocation"
• "Set up recurring fee tracking"
• "Rebalance spending categories"

💰 SYSTEM COMMANDS:
• help - Show this help
• status - Show current advisor state
• examples [category] - Show examples for category
• debug - Toggle debug mode
• reset - Clear all test plans
• history - Show conversation history
• clear - Clear conversation memory
• quit/exit - Exit program

📝 CATEGORIES: plan_management, advisory, integration, proposals
        """)
    
    def show_status(self):
        """Display current Budget Advisor state"""
        print("\n📊 Current Budget Advisor State:")
        print("-" * 40)
        
        # Show plan storage
        plan_count = len(BUDGET_PLANS_STORAGE)
        active_plans = len([p for p in BUDGET_PLANS_STORAGE.values() if p.get("status") == "active"])
        print(f"📋 Plans: {plan_count} total ({active_plans} active)")
        
        if BUDGET_PLANS_STORAGE:
            print("   Active plans:")
            for name, plan in BUDGET_PLANS_STORAGE.items():
                if plan.get("status") == "active":
                    print(f"   • {name}: {plan.get('detail_description', '')[:50]}...")
        
        # Try to show jar status
        try:
            jar_result = get_jar.invoke({"description": "status check"})
            if jar_result.get("data"):
                print(f"🏺 Jars: {len(jar_result['data'])} available")
            else:
                print("🏺 Jars: No data available")
        except:
            print("🏺 Jars: Integration not available")
        
        print(f"🧪 Test results: {len(self.test_results)} recorded")
        print(f"🤖 LLM Agent: {'Ready' if self.llm_with_tools else 'Not initialized'}")
        
        # Show memory status
        if config.enable_memory:
            print(f"💭 Memory: {len(self.conversation_history)} conversations stored (max: {config.max_memory_turns})")
        else:
            print("💭 Memory: Disabled")
    
    def show_examples(self, category: str = "all"):
        """Show examples for specific category"""
        examples = get_example_queries(category)
        
        if examples:
            print(f"\n💡 Examples for {category}:")
            for i, example in enumerate(examples, 1):
                print(f"   {i}. {example}")
        else:
            print(f"\n💡 No examples available for category: {category}")
            print("Available categories: plan_management, advisory, integration, proposals")
    
    def reset_data(self):
        """Reset test data"""
        BUDGET_PLANS_STORAGE.clear()
        self.test_results.clear()
        print("🔄 Test data reset - all plans and results cleared")
    
    def toggle_debug(self):
        """Toggle debug mode"""
        config.debug_mode = not config.debug_mode
        print(f"🔧 Debug mode: {'ON' if config.debug_mode else 'OFF'}")
    
    def show_conversation_history(self):
        """Show conversation history"""
        if not config.enable_memory:
            print("💭 Memory is disabled in configuration")
            return
        
        if not self.conversation_history:
            print("💭 No conversation history yet")
            return
        
        print(f"\n💭 Conversation History ({len(self.conversation_history)} interactions):")
        print("=" * 60)
        
        for i, (user_msg, agent_response) in enumerate(self.conversation_history, 1):
            print(f"\n{i}. User: {user_msg}")
            # Truncate long responses for readability
            response_preview = agent_response[:150] + "..." if len(agent_response) > 150 else agent_response
            print(f"   Assistant: {response_preview}")
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        if not config.enable_memory:
            print("💭 Memory is disabled in configuration")
            return
        
        self.conversation_history.clear()
        print("🧹 Conversation history cleared")
    
    def process_with_agent(self, user_input: str) -> str:
        """
        Process user input using the actual LLM-powered Budget Advisor agent.
        
        Args:
            user_input: User's financial question or request
            
        Returns:
            Agent's response
        """
        
        if not self.llm_with_tools:
            return "❌ Error: LLM agent not initialized. Please restart the testing session."
        
        # Use conversation history if memory is enabled
        history_to_pass = None
        if config.enable_memory and self.conversation_history:
            # Limit to max_memory_turns to prevent context overflow
            history_to_pass = self.conversation_history[-config.max_memory_turns:]
        
        # Use the real Budget Advisor agent with conversation history
        response = provide_budget_advice(user_input, self.llm_with_tools, history_to_pass)
        
        # Store interaction in conversation history for memory
        if config.enable_memory:
            self.conversation_history.append((user_input, response))
            # Keep history within limits
            if len(self.conversation_history) > config.max_memory_turns:
                self.conversation_history = self.conversation_history[-config.max_memory_turns:]
        
        return response
    
    def run_interactive_test(self):
        """Run interactive testing mode"""
        
        print("\n💰 Budget Advisor Agent - Interactive Testing")
        print("=" * 50)
        print("Real LLM-powered agent with ReAct framework")
        memory_status = f" with memory ({config.max_memory_turns} turns)" if config.enable_memory else ""
        print(f"💭 Chat mode enabled{memory_status}")
        print("Ask me about:")
        print("📋 Plan management (create, update, view plans)")
        print("💡 Financial advice (spending analysis, optimization)")
        print("📊 Data integration (transactions, jars, spending)")
        print("🎯 Budget proposals (new jars, rebalancing)")
        print("Type 'quit' to exit, 'help' for examples\n")
        
        while self.session_active:
            try:
                user_input = input("💬 Your request: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Testing session ended!")
                    break
                
                if user_input.lower() in ['help', 'h', '?']:
                    self.show_help()
                    continue
                
                if user_input.lower() == 'status':
                    self.show_status()
                    continue
                
                if user_input.lower().startswith('examples'):
                    parts = user_input.split()
                    category = parts[1] if len(parts) > 1 else "all"
                    self.show_examples(category)
                    continue
                
                if user_input.lower() == 'debug':
                    self.toggle_debug()
                    continue
                
                if user_input.lower() == 'reset':
                    self.reset_data()
                    continue
                
                if user_input.lower() in ['history', 'hist']:
                    self.show_conversation_history()
                    continue
                
                if user_input.lower() in ['clear', 'clear_memory']:
                    self.clear_conversation_history()
                    continue
                
                if not user_input:
                    continue
                
                print(f"\n🤔 Processing with Budget Advisor Agent: '{user_input}'")
                start_time = time.time()
                
                # Use the REAL agent instead of mock
                response = self.process_with_agent(user_input)
                elapsed_time = time.time() - start_time
                
                print(f"\n💡 Budget Advisor Response ({elapsed_time:.2f}s):")
                print("-" * 50)
                print(response)
                print("-" * 50)
                
                # Store result for analysis
                self.test_results.append({
                    "query": user_input,
                    "response": response,
                    "time": elapsed_time,
                    "status": "success"
                })
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Testing session ended!")
                break
    
    def run_predefined_tests(self) -> Dict[str, Any]:
        """
        Run predefined test scenarios using the real agent.
        
        Returns:
            Test results summary
        """
        
        print("\n🧪 Running Predefined Test Scenarios")
        print("=" * 50)
        print("Using real LLM-powered Budget Advisor agent")
        
        test_categories = {
            "plan_management": [
                "Create vacation savings plan for Japan trip",
                "Show me all my active financial goals",
                "Create emergency fund plan", 
                "Update vacation plan to completed"
            ],
            "advisory_analysis": [
                "Analyze my spending patterns",
                "Give me budget optimization advice",
                "Help me plan for major expenses",
                "Review my financial progress"
            ],
            "data_integration": [
                "Check my jar allocations",
                "Find dining expenses last week",
                "ăn trưa dưới 20 đô",
                "coffee purchases this month"
            ],
            "budget_proposals": [
                "Create new vacation jar",
                "Optimize budget allocation", 
                "Set up fee tracking",
                "Rebalance spending categories"
            ]
        }
        
        results = {}
        total_tests = 0
        passed_tests = 0
        
        for category, queries in test_categories.items():
            print(f"\n📋 Testing {category.replace('_', ' ').title()}")
            print("-" * 40)
            
            category_results = []
            
            for query in queries:
                total_tests += 1
                print(f"\n🔍 Query: {query}")
                
                start_time = time.time()
                response = self.process_with_agent(query)
                elapsed_time = time.time() - start_time
                
                # Basic validation - check if agent provided substantive response
                is_valid = (len(response) > 50 and 
                           "❌ Error" not in response and 
                           "Could not provide" not in response)
                
                if is_valid:
                    passed_tests += 1
                    print(f"   ✅ PASS ({elapsed_time:.2f}s)")
                else:
                    print(f"   ❌ FAIL ({elapsed_time:.2f}s)")
                
                category_results.append({
                    "query": query,
                    "response": response,
                    "time": elapsed_time,
                    "passed": is_valid
                })
                
                if config.debug_mode:
                    print(f"   Response: {response[:100]}...")
            
            results[category] = category_results
        
        # Summary
        print(f"\n📊 Test Results Summary:")
        print(f"   Total tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return results
    
    def run_tool_validation(self) -> Dict[str, Any]:
        """
        Test individual tool functionality.
        
        Returns:
            Tool validation results
        """
        
        print("\n🔧 Tool Validation Tests")
        print("=" * 50)
        
        tools_to_test = [
            ("create_plan", lambda: create_plan.invoke({
                "name": "test_plan",
                "description": "Tool validation test plan",
                "status": "active"
            })),
            ("get_plan", lambda: get_plan.invoke({
                "status": "active",
                "description": "Tool validation check"
            })),
            ("adjust_plan", lambda: adjust_plan.invoke({
                "name": "test_plan",
                "status": "completed"
            })),
            ("respond", lambda: respond.invoke({
                "summary": "Tool validation test summary",
                "advice": "This is a test advice message",
                "question_ask_user": "Do you need any additional clarification?"
            })),

            ("transaction_fetcher", lambda: transaction_fetcher.invoke({
                "user_query": "test spending",
                "description": "Tool validation transaction query"
            })),
            ("get_jar", lambda: get_jar.invoke({
                "description": "Tool validation jar check"
            }))
        ]
        
        results = {}
        
        for tool_name, tool_func in tools_to_test:
            print(f"\n🔍 Testing {tool_name}...")
            
            start_time = time.time()
            result = tool_func()
            elapsed_time = time.time() - start_time
            
            print(f"   ✅ {tool_name} - PASS ({elapsed_time:.2f}s)")
            results[tool_name] = {
                "status": "pass",
                "time": elapsed_time,
                "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            }
        
        # Summary
        passed_tools = len([r for r in results.values() if r["status"] == "pass"])
        total_tools = len(results)
        
        print(f"\n📊 Tool Validation Summary:")
        print(f"   Tools tested: {total_tools}")
        print(f"   Passed: {passed_tools}")
        print(f"   Failed: {total_tools - passed_tools}")
        print(f"   Success rate: {(passed_tools/total_tools)*100:.1f}%")
        
        return results
    
    def run_react_simulation(self) -> bool:
        """
        Simulate ReAct framework workflow.
        
        Returns:
            True if simulation successful
        """
        
        print("\n🔄 ReAct Framework Simulation")
        print("=" * 50)
        print("Simulating: 'I want to save for a vacation to Japan'")
        
        react_steps = [
            ("Thought", "I need to understand the user's current financial situation and goals"),
            ("Action", "Check existing plans"),
            ("Observation", lambda: get_plan.invoke({"status": "active", "description": "checking current goals"})),
            ("Thought", "I should analyze their spending capacity for vacation savings"),
            ("Action", "Analyze transaction patterns"),
            ("Observation", lambda: transaction_fetcher.invoke({"user_query": "discretionary spending", "description": "finding savings capacity"})),
            ("Thought", "I need to check their current budget allocation"),
            ("Action", "Check jar allocations"),
            ("Observation", lambda: get_jar.invoke({"description": "analyzing budget capacity"})),
            ("Thought", "Based on analysis, I can create a vacation plan"),
            ("Action", "Create vacation savings plan"),
            ("Observation", lambda: create_plan.invoke({"name": "japan_vacation", "description": "Save for Japan vacation", "status": "active"})),
            ("Thought", "I should create the plan with jar recommendations to support this goal"),
            ("Action", "Create vacation plan with jar proposals"),
            ("Observation", lambda: create_plan.invoke({"name": "japan_vacation_with_jars", "description": "Save for Japan vacation with jar setup", "status": "active", "jar_propose_adjust_details": "Create vacation jar with monthly allocation to support Japan vacation goal"})),
            ("Thought", "I can now provide comprehensive advice"),
            ("Action", "Provide final advisory response"),
            ("Observation", lambda: respond.invoke({"summary": "Japan vacation planning analysis completed", "advice": "Start systematic savings for your Japan trip goal", "question_ask_user": "What is your monthly income so I can calculate precise jar allocations?"}))
        ]
        
        for i, step in enumerate(react_steps, 1):
            step_type, content = step
            
            print(f"\n{i:2d}. {step_type}: ", end="")
            
            if step_type == "Observation" and callable(content):
                result = content()
                print("✅ Action completed")
                if config.debug_mode:
                    print(f"    Result: {str(result)[:100]}...")
            else:
                print(content)
            
            time.sleep(0.5)  # Simulate thinking time
        
        print(f"\n✅ ReAct simulation completed successfully!")
        return True


def main():
    """Main testing interface"""
    
    print("💰 BUDGET ADVISOR AGENT TEST LAB")
    print("=" * 50)
    
    tester = BudgetAdvisorTester()
    
    if not tester.setup_testing():
        return
    
    while True:
        print("\nChoose testing mode:")
        print("1. 🎮 Interactive Testing")
        print("2. 🧪 Predefined Test Scenarios") 
        print("3. 🔧 Tool Validation")
        print("4. 🔄 ReAct Framework Simulation")
        print("5. 📊 Show Current Status")
        print("6. 💡 Show Examples")
        print("7. 🚪 Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            tester.run_interactive_test()
        elif choice == '2':
            tester.run_predefined_tests()
        elif choice == '3':
            tester.run_tool_validation()
        elif choice == '4':
            tester.run_react_simulation()
        elif choice == '5':
            tester.show_status()
        elif choice == '6':
            category = input("Enter category (plan_management/advisory/integration/proposals) or 'all': ").strip()
            tester.show_examples(category if category else "all")
        elif choice == '7':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-7.")
        
        print("\n" + "=" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Direct interactive mode
        tester = BudgetAdvisorTester()
        if tester.setup_testing():
            tester.run_interactive_test()
    else:
        main()
