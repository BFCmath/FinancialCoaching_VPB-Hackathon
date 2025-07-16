#!/usr/bin/env python3
"""
VPBank Financial Coach Backend API - Final Comprehensive Testing Script
========================================================================

This script provides a definitive, interactive, end-to-end test of all API
endpoints. It is specifically designed for a backend that AUTOMATICALLY
initializes a new user with a default 6-jar system upon registration.

Usage:
    python final_mock.py

Requirements:
    - Backend server running on http://127.0.0.1:8000
    - 'requests' library: pip install requests
"""

import requests
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class VPBankAPITester:
    """Definitive interactive API tester for the Financial Coach Backend."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_url = f"{self.base_url}/api"
        self.token: Optional[str] = None
        self.user_data: Dict[str, str] = {}
        self.test_results: list = []
        self.created_item_ids: Dict[str, str] = {}

    def log_test(self, test_name: str, success: bool, details: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} | {test_name}")
        if details: print(f"      └── {details}")
        self.test_results.append({"test": test_name, "success": success, "details": details})

    def pause_and_check(self, response: Optional[requests.Response], prompt: str = ""):
        print("\n" + "-"*20 + " CHECKPOINT " + "-"*20)
        if prompt: print(f"ACTION: {prompt}")
        if response:
            print(f"Request: {response.request.method} {response.request.url.replace(self.api_url, '/api')}")
            print(f"Status Code: {response.status_code}")
            try: print("Response Body:\n" + json.dumps(response.json(), indent=2))
            except json.JSONDecodeError: print("Response Body: (No JSON content)")
        else: print("❌ No response received from server.")
        input("-" * 15 + " Press Enter to continue... " + "-"*15)

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None,
                     use_auth: bool = True) -> Optional[requests.Response]:
        url = f"{self.api_url}{endpoint}"
        content_type = "application/x-www-form-urlencoded" if "token" in endpoint else "application/json"
        headers = {"Content-Type": content_type}
        if use_auth and self.token: headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET": return requests.get(url, headers=headers, params=params)
            if method.upper() == "POST":
                return requests.post(url, data=data if content_type != "application/json" else None, json=data if content_type == "application/json" else None, headers=headers)
            if method.upper() == "PUT": return requests.put(url, json=data, headers=headers)
            if method.upper() == "DELETE": return requests.delete(url, headers=headers)
            raise ValueError(f"Unsupported method: {method}")
        except requests.exceptions.RequestException as e: print(f"❌ Connection Error: {e}"); return None

    def run_stage(self, stage_name: str, test_function) -> bool:
        print("\n" + "="*60 + f"\n🚀 STAGE: {stage_name}\n" + "="*60)
        try:
            if test_function(): print(f"\n✅ STAGE SUCCEEDED: {stage_name}"); return True
            else: print(f"\n❌ STAGE FAILED: {stage_name}."); return False
        except Exception as e: print(f"\n💥 CRITICAL ERROR in {stage_name}: {e}"); return False

    def setup_initial_state(self) -> bool:
        """One-time setup: auth, settings, and VERIFYING default items."""
        print("--- Setting up initial user and verifying default data creation ---")
        # 1. Auth
        timestamp = int(time.time())
        self.user_data = {"username": f"final_tester_{timestamp}", "email": f"final_{timestamp}@test.com", "password": "Password123"}
        if not (res := self.make_request("POST", "/auth/register", self.user_data, use_auth=False)) or res.status_code != 201: return False
        
        login_data = {"username": self.user_data["username"], "password": self.user_data["password"]}
        if not (res := self.make_request("POST", "/auth/token", login_data, use_auth=False)) or res.status_code != 200: return False
        self.token = res.json().get("access_token")
        self.log_test("Setup: Auth", True, f"User '{self.user_data['username']}' logged in.")
        self.pause_and_check(res, "User registered and logged in.")

        # 2. Settings
        if not (res := self.make_request("PUT", "/user/settings", {"total_income": 8000.0})) or res.status_code != 200: return False
        self.log_test("Setup: Settings", True, "Total income set to $8000.0")
        self.pause_and_check(res, "User income set.")

        # 3. VERIFY Default Jars
        # The script no longer creates jars. It verifies the ones created automatically.
        res = self.make_request("GET", "/jars/")
        if not (res and res.status_code == 200 and len(res.json()) == 6): return False
        self.log_test("Setup: Verify Default Jars", True, "Found 6 jars created automatically.")
        self.pause_and_check(res, "Verify the 6 default jars are present.")

        # 4. Create Fees & Plans for testing
        fees = [
            {"name": "Rent", "amount": 2200, "target_jar": "necessities", "description": "monthly renting fee", "pattern_type": "monthly", "pattern_details": [1]},
            {"name": "Gym", "amount": 40, "target_jar": "play", "description": "monthly gym fee", "pattern_type": "monthly", "pattern_details": [15]},
            {"name": "Daily Lunch", "amount": 15, "target_jar": "necessities", "description": "daily lunch expense", "pattern_type": "daily", "pattern_details": []}
        ]
        for fee in fees:
            if not (res := self.make_request("POST", "/fees/", fee)) or res.status_code != 201: return False
        self.log_test("Setup: Fees", True, "Created 3 fees for testing.")
        
        plans = [{"name": "Emergency Fund", "status": "active"}, {"name": "Buy New Car", "status": "paused"}]
        for plan in plans:
            if not (res := self.make_request("POST", "/plans/", {"name": plan["name"], "detail_description": "Test Plan", "status": plan["status"]})) or res.status_code != 201: return False
        self.log_test("Setup: Plans", True, "Created 2 plans for testing.")
        self.pause_and_check(res, "Fees and Plans created.")
        
        return True

    def test_transaction_lifecycle_and_filters(self) -> bool:
        """Tests transaction creation, deletion, side-effects, and filtering."""
        # 1. Create a transaction in a default jar and verify debit
        tx_data = {"amount": 75.50, "jar": "play", "description": "Dinner with friends", "source": "manual_input", "transaction_datetime": datetime.now(timezone.utc).isoformat()}
        res = self.make_request("POST", "/transactions/", tx_data)
        if not (res and res.status_code == 201): self.log_test("TX Create", False); return False
        tx_id = res.json().get("_id")
        print(f"Created transaction ID: {tx_id}")
        self.log_test("TX Create", True, "Transaction for $75.50 in 'play' jar created.")
        self.pause_and_check(res)
        res = self.make_request("GET", "/transactions/")
        print(f"All transactions: {res.json()}")
        res = self.make_request("GET", "/jars/play")
        self.log_test("Verify Jar Debit", res and res.status_code == 200 and res.json()['current_amount'] == 75.50)
        self.pause_and_check(res, "Check that 'current_amount' in 'play' jar is 75.50.")
        
        # 2. Delete the transaction and verify jar refund
        res = self.make_request("DELETE", f"/transactions/{tx_id}")
        if not (res and res.status_code == 204): self.log_test("TX Delete", False); return False
        self.log_test("TX Delete", True, "Transaction deleted.")
        self.pause_and_check(res)

        res = self.make_request("GET", "/jars/play")
        self.log_test("Verify Jar Refund", res and res.status_code == 200 and res.json()['current_amount'] == 0)
        self.pause_and_check(res, "Check that 'current_amount' is now 0.0 after refund.")

        # 3. Test Filters (using pre-created setup data)
        # Create one more transaction for better filter testing
        self.make_request("POST", "/transactions/", {"amount": 500, "jar": "financial_freedom", "description": "Stock investment", "source": "vpbank_api", "transaction_datetime": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()})
        
        res = self.make_request("GET", "/transactions/", params={"jar": "financial_freedom"})
        self.log_test("Filter TX by Jar ('financial_freedom')", res and res.status_code == 200 and len(res.json()) == 1)
        self.pause_and_check(res, "Should list 1 transaction from the 'financial_freedom' jar.")

        return True

    def test_fee_filters_and_special_routes(self) -> bool:
        """Focuses on testing the filtering logic for fees."""
        # Note: Data was created in the setup stage.
        res = self.make_request("GET", "/fees/", params={"active_only": "true"})
        self.log_test("Filter Fees: Active Only", res and res.status_code == 200 and len(res.json()) == 2)
        self.pause_and_check(res)

        res = self.make_request("GET", "/fees/", params={"target_jar": "necessities"})
        self.log_test("Filter Fees: By Jar ('necessities')", res and res.status_code == 200 and len(res.json()) == 2)
        self.pause_and_check(res)
        
        res = self.make_request("GET", "/fees/due/today")
        self.log_test("Get Fees Due Today", res and res.status_code == 200 and len(res.json()) >= 1 and res.json()[0]['name'] == 'Daily Lunch')
        self.pause_and_check(res, "Should find 'Daily Lunch' as it has a daily recurrence.")
        
        return True

    def test_plan_filters(self) -> bool:
        """Focuses on testing the filtering logic for plans."""
        # Note: Data was created in the setup stage.
        res = self.make_request("GET", "/plans/", params={"status": "active"})
        self.log_test("Filter Plans: Active", res and res.status_code == 200 and len(res.json()) == 1)
        self.pause_and_check(res)

        res = self.make_request("GET", "/plans/", params={"status": "paused"})
        self.log_test("Filter Plans: Paused", res and res.status_code == 200 and len(res.json()) == 1)
        self.pause_and_check(res)
        
        return True

    def test_chat_and_history(self) -> bool:
        """Tests sending chat messages and retrieving the conversation history."""
        messages = [
            "Add a $25 transaction to my play jar for a movie.",
            "What's the balance of my play jar now?",
            "Show me my active budget plans."
        ]
        
        for msg in messages:
            res = self.make_request("POST", "/chat/", {"message": msg})
            # Check for ConversationTurnInDB response format
            is_valid_response = (res and res.status_code == 200 and 
                               'agent_output' in res.json() and 
                               'user_input' in res.json() and
                               'agent_list' in res.json())
            self.log_test(f"Chat: '{msg[:30]}...'", is_valid_response)
            
            if is_valid_response:
                response_data = res.json()
                print(f"Agent Output: {response_data.get('agent_output', 'No response')}")
                print(f"Agents Used: {response_data.get('agent_list', [])}")
                print(f"Tools Called: {response_data.get('tool_call_list', [])}")
                if response_data.get('agent_lock'):
                    print(f"Agent Lock: {response_data.get('agent_lock')}")
                if response_data.get('plan_stage'):
                    print(f"Plan Stage: {response_data.get('plan_stage')}")
            
            self.pause_and_check(res, f"Sent message: '{msg}' to chat orchestrator.")
            if not is_valid_response: return False

        res = self.make_request("GET", "/chat/history", params={"limit": len(messages)})
        is_valid_history = (res and res.status_code == 200 and 
                          len(res.json()) == len(messages) and
                          all('agent_output' in turn for turn in res.json()))
        self.log_test("Get Chat History", is_valid_history)
        self.pause_and_check(res, f"Retrieved the last {len(messages)} turns of conversation history.")
        return is_valid_history

    def run_all_tests(self):
        """Executes all testing stages in a sequential workflow."""
        workflow = [
            ("Initial State Setup & Verification", self.setup_initial_state),
            ("Transaction Lifecycle & Filters", self.test_transaction_lifecycle_and_filters),
            ("Fee Filters & Special Routes", self.test_fee_filters_and_special_routes),
            ("Plan Filters", self.test_plan_filters),
            ("Chat and History", self.test_chat_and_history),
        ]
        
        for name, func in workflow:
            if not self.run_stage(name, func): break
        
        print("\n" + "="*60 + "\n📊 FINAL TEST REPORT\n" + "="*60)
        total = len(self.test_results); passed = sum(1 for r in self.test_results if r["success"])
        print(f"Total Steps: {total}, Passed: {passed}, Failed: {total - passed}")
        if total > 0: print(f"Success Rate: {(passed/total)*100:.2f}%")

    def interactive_chat_simulator(self):
        """Interactive chat simulator for testing the chat API in real-time."""
        print("\n" + "="*60 + "\n🤖 INTERACTIVE CHAT SIMULATOR\n" + "="*60)
        print("This will create a test user and allow you to chat with the financial coach agent.")
        print("Type 'quit', 'exit', or 'bye' to end the session.")
        print("Type 'history' to see recent conversation history.")
        print("Type 'status' to see current agent lock and plan stage.")
        print("-" * 60)

        # Setup a test user for interactive chat
        timestamp = int(time.time())
        self.user_data = {
            "username": f"interactive_user_{timestamp}", 
            "email": f"interactive_{timestamp}@test.com", 
            "password": "Password123"
        }
        
        # Register and login
        print("Setting up test user for interactive chat...")
        res = self.make_request("POST", "/auth/register", self.user_data, use_auth=False)
        if not (res and res.status_code == 201):
            print("❌ Failed to register test user")
            return
        
        login_data = {"username": self.user_data["username"], "password": self.user_data["password"]}
        res = self.make_request("POST", "/auth/token", login_data, use_auth=False)
        if not (res and res.status_code == 200):
            print("❌ Failed to login test user")
            return
        
        self.token = res.json().get("access_token")
        print(f"✅ Logged in as: {self.user_data['username']}")

        # Set up basic user settings
        self.make_request("PUT", "/user/settings", {"total_income": 5000.0})
        print("✅ User settings configured (income: $5000)")

        print("\n" + "="*60)
        print("🚀 Chat session started! Start typing your messages...")
        print("="*60)

        last_response = None
        
        while True:
            try:
                # Get user input
                user_message = input("\n💬 You: ").strip()
                
                # Handle special commands
                if user_message.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye! Chat session ended.")
                    break
                
                if user_message.lower() == 'history':
                    self._show_chat_history()
                    continue
                    
                if user_message.lower() == 'status':
                    self._show_chat_status(last_response)
                    continue
                
                if not user_message:
                    print("Please enter a message or 'quit' to exit.")
                    continue
                
                # Send message to chat API
                print("🤔 Processing your message...")
                res = self.make_request("POST", "/chat/", {"message": user_message})
                
                if res and res.status_code == 200:
                    response_data = res.json()
                    last_response = response_data
                    
                    # Display the agent's response
                    agent_output = response_data.get('agent_output', 'No response generated.')
                    print(f"\n🤖 Agent: {agent_output}")
                    
                    # Show additional info if available
                    agents_used = response_data.get('agent_list', [])
                    if agents_used and len(agents_used) > 1:
                        print(f"   └── Agents involved: {', '.join(agents_used)}")
                    
                    tools_called = response_data.get('tool_call_list', [])
                    if tools_called:
                        print(f"   └── Tools used: {', '.join(tools_called[:3])}{'...' if len(tools_called) > 3 else ''}")
                    
                    agent_lock = response_data.get('agent_lock')
                    if agent_lock:
                        print(f"   └── 🔒 Locked to {agent_lock} agent")
                    
                    plan_stage = response_data.get('plan_stage')
                    if plan_stage:
                        print(f"   └── 📋 Plan stage: {plan_stage}")
                        
                else:
                    print(f"❌ Error: {res.status_code if res else 'No response'}")
                    if res and res.text:
                        try:
                            error_detail = res.json().get('detail', 'Unknown error')
                            print(f"   └── {error_detail}")
                        except:
                            print(f"   └── {res.text}")
                            
            except KeyboardInterrupt:
                print("\n\n👋 Chat session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

    def _show_chat_history(self):
        """Display recent chat history."""
        res = self.make_request("GET", "/chat/history", params={"limit": 5})
        if res and res.status_code == 200:
            history = res.json()
            print("\n📜 Recent Chat History (last 5 turns):")
            print("-" * 40)
            for i, turn in enumerate(reversed(history), 1):
                print(f"{i}. You: {turn.get('user_input', 'Unknown input')}")
                print(f"   Agent: {turn.get('agent_output', 'No response')}")
                if turn.get('agent_lock'):
                    print(f"   (🔒 {turn.get('agent_lock')} agent)")
                print()
        else:
            print("❌ Could not retrieve chat history")

    def _show_chat_status(self, last_response):
        """Display current chat session status."""
        print("\n📊 Current Chat Session Status:")
        print("-" * 40)
        
        if last_response:
            agent_lock = last_response.get('agent_lock')
            plan_stage = last_response.get('plan_stage')
            
            if agent_lock:
                print(f"🔒 Agent Lock: {agent_lock}")
                print("   └── Your next message will be routed directly to this agent")
            else:
                print("🔓 No Agent Lock")
                print("   └── Your next message will be routed by the orchestrator")
            
            if plan_stage:
                print(f"📋 Plan Stage: {plan_stage}")
                print("   └── You're in the middle of a planning workflow")
            else:
                print("📋 No Active Plan Stage")
            
            print(f"🕒 Last Response Time: {last_response.get('timestamp', 'Unknown')}")
        else:
            print("No previous conversation data available")
        
        # Show user info
        print(f"👤 User: {self.user_data.get('username', 'Unknown')}")
        print(f"🔑 Token: {'***' + (self.token[-10:] if self.token else 'None')}")

def run_interactive_chat():
    """Standalone function to run just the interactive chat simulator."""
    print("🚀 Starting VPBank Financial Coach Interactive Chat Simulator")
    print("   Server should be running at http://127.0.0.1:8000")
    tester = VPBankAPITester()
    tester.interactive_chat_simulator()

if __name__ == "__main__":
    import sys
    
    print("🚀 VPBank Financial Coach Backend API Tool")
    print("   Server should be running at http://127.0.0.1:8000")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] in ['chat', 'interactive']:
        # Run interactive chat simulator only
        run_interactive_chat()
    else:
        # Show menu for user to choose
        print("Choose an option:")
        print("1. Run comprehensive API tests")
        print("2. Start interactive chat simulator")
        print("3. Run tests then start interactive chat")
        print()
        
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == "1":
                print("\n🧪 Starting comprehensive API tests...")
                VPBankAPITester().run_all_tests()
                print("\n🎉 Testing workflow completed!")
                
            elif choice == "2":
                print("\n💬 Starting interactive chat simulator...")
                run_interactive_chat()
                
            elif choice == "3":
                print("\n🧪 Running comprehensive API tests first...")
                tester = VPBankAPITester()
                tester.run_all_tests()
                print("\n🎉 Testing completed! Starting interactive chat...")
                print("\nNote: This will create a new test user for the chat session.")
                input("Press Enter to continue to interactive chat...")
                run_interactive_chat()
                
            else:
                print("Invalid choice. Running comprehensive tests by default...")
                VPBankAPITester().run_all_tests()
                print("\n🎉 Testing workflow completed!")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Running comprehensive tests by default...")
            VPBankAPITester().run_all_tests()
            print("\n🎉 Testing workflow completed!")