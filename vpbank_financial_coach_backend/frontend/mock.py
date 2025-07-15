#!/usr/bin/env python3
"""
VPBank Financial Coach Backend API Testing Script
=================================================

This script provides comprehensive testing of all API endpoints
using the running backend server at http://127.0.0.1:8000

Usage:
    python frontend/mock.py

Requirements:
    - Backend server running on http://127.0.0.1:8000
    - requests library: pip install requests
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class VPBankAPITester:
    """
    Comprehensive API tester for VPBank Financial Coach Backend
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = {}
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    use_auth: bool = True, content_type: str = "application/json") -> requests.Response:
        """Make HTTP request with optional authentication"""
        url = f"{self.api_url}{endpoint}"
        headers = {"Content-Type": content_type}
        
        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                if content_type == "application/x-www-form-urlencoded":
                    response = requests.post(url, data=data, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Cannot connect to {url}")
            print("   Make sure the backend server is running on http://127.0.0.1:8000")
            return None
    
    def test_health_check(self):
        """Test server health check"""
        print("\n🏥 Testing Server Health...")
        
        try:
            response = requests.get(self.base_url)
            if response and response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status', 'unknown')}")
                return True
            else:
                self.log_test("Health Check", False, f"Status Code: {response.status_code if response else 'No response'}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        print("\n👤 Testing User Registration...")
        
        # Generate unique username
        timestamp = int(time.time())
        self.user_data = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        response = self.make_request("POST", "/auth/register", self.user_data, use_auth=False)
        
        if response and response.status_code == 201:
            user = response.json()
            self.log_test("User Registration", True, f"Created user: {user.get('username')}")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("User Registration", False, f"Error: {error_msg}")
            return False
    
    def test_user_login(self):
        """Test user login and token retrieval"""
        print("\n🔐 Testing User Login...")
        
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        
        response = self.make_request("POST", "/auth/token", login_data, 
                                   use_auth=False, content_type="application/x-www-form-urlencoded")
        
        if response and response.status_code == 200:
            token_data = response.json()
            self.token = token_data.get("access_token")
            self.log_test("User Login", True, f"Token received (length: {len(self.token) if self.token else 0})")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("User Login", False, f"Error: {error_msg}")
            return False
    
    def test_user_profile(self):
        """Test getting current user profile"""
        print("\n👨‍💼 Testing User Profile...")
        
        response = self.make_request("GET", "/auth/me")
        
        if response and response.status_code == 200:
            user = response.json()
            self.log_test("Get User Profile", True, f"User: {user.get('username')} ({user.get('email')})")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Get User Profile", False, f"Error: {error_msg}")
            return False
    
    def test_user_settings(self):
        """Test user settings management"""
        print("\n⚙️ Testing User Settings...")
        
        # Test getting default settings
        response = self.make_request("GET", "/user/settings")
        if response and response.status_code == 200:
            settings = response.json()
            self.log_test("Get User Settings", True, f"Total income: ${settings.get('total_income', 0)}")
        else:
            self.log_test("Get User Settings", False, "Failed to get settings")
            return False
        
        # Test updating settings
        new_settings = {"total_income": 6000.0}
        response = self.make_request("PUT", "/user/settings", new_settings)
        
        if response and response.status_code == 200:
            updated_settings = response.json()
            self.log_test("Update User Settings", True, f"New income: ${updated_settings.get('total_income')}")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
            self.log_test("Update User Settings", False, f"Error: {error_msg}")
            return False
    
    def test_jar_management(self):
        """Test jar management functionality"""
        print("\n🏺 Testing Jar Management...")
        
        # Test creating jars
        jars_to_create = [
            {
                "name": "asdfasdf",
                "description": "Essential expenses like rent and groceries",
                "percent": 0.55
            },
            # {
            #     "name": "Play",
            #     "description": "Entertainment and leisure activities",
            #     "percent": 0.10
            # },
            # {
            #     "name": "Emergency",
            #     "description": "Emergency fund for unexpected expenses",
            #     "amount": 1000.0
            # }
        ]
        
        created_jars = []
        for jar_data in jars_to_create:
            response = self.make_request("POST", "/jars/", jar_data)
            
            if response and response.status_code == 201:
                jar = response.json()
                created_jars.append(jar)
                allocation = f"{jar.get('percent', 0)*100:.1f}%" if 'percent' in jar_data else f"${jar.get('amount', 0)}"
                self.log_test(f"Create Jar: {jar_data['name']}", True, f"Allocation: {allocation}")
            else:
                error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                self.log_test(f"Create Jar: {jar_data['name']}", False, f"Error: {error_msg}")
                return False
        # Test listing jars
        response = self.make_request("GET", "/jars/")
        if response and response.status_code == 200:
            jars = response.json()
            self.log_test("List Jars", True, f"Found {len(jars)} jars")
            return len(jars) > 0
        else:
            self.log_test("List Jars", False, "Failed to list jars")
            return False
    
    def test_transaction_management(self):
        """Test transaction management functionality"""
        print("\n💸 Testing Transaction Management...")
        
        # Test creating transactions
        transactions_to_create = [
            {
                "amount": 85.50,
                "jar": "necessities",
                "description": "Weekly grocery shopping",
                "date": "2025-07-15",
                "time": "09:30",
                "source": "manual_input"
            },
            {
                "amount": 45.00,
                "jar": "play",
                "description": "Movie tickets",
                "date": "2025-07-14",
                "time": "19:00",
                "source": "manual_input"
            },
            {
                "amount": 12.99,
                "jar": "play",
                "description": "Netflix subscription",
                "date": "2025-07-13",
                "time": "10:00",
                "source": "manual_input"
            }
        ]
        
        created_transactions = []
        for transaction_data in transactions_to_create:
            response = self.make_request("POST", "/transactions/", transaction_data)
            
            if response and response.status_code == 201:
                transaction = response.json()
                created_transactions.append(transaction)
                self.log_test(f"Create Transaction: ${transaction_data['amount']}", True, 
                            f"Jar: {transaction_data['jar']}")
            else:
                error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                self.log_test(f"Create Transaction: ${transaction_data['amount']}", False, f"Error: {error_msg}")
                return False
        # Test listing transactions
        response = self.make_request("GET", "/transactions/")
        if response and response.status_code == 200:
            transactions = response.json()
            self.log_test("List Transactions", True, f"Found {len(transactions)} transactions")
        else:
            self.log_test("List Transactions", False, "Failed to list transactions")
            return False
        # Test filtering transactions
        response = self.make_request("GET", "/transactions/?jar=play&limit=10")
        if response and response.status_code == 200:
            play_transactions = response.json()
            self.log_test("Filter Transactions", True, f"Found {len(play_transactions)} play transactions")
            return True
        else:
            self.log_test("Filter Transactions", False, "Failed to filter transactions")
            return False
    
    def test_fee_management(self):
        """Test recurring fee management"""
        print("\n💳 Testing Fee Management...")
        
        # Test creating recurring fees
        fees_to_create = [
            {
                "name": "Netflix Subscription",
                "amount": 15.99,
                "description": "Weekly Netflix streaming",
                "target_jar": "play",
                "pattern_type": "weekly",
                "pattern_details": [1]
            },
            # {
            #     "name": "Gym Membership",
            #     "amount": 29.99,
            #     "description": "Monthly gym membership",
            #     "target_jar": "necessities",
            #     "pattern_type": "monthly",
            #     "pattern_details": [15]
            # }
        ]
        
        created_fees = []
        for fee_data in fees_to_create:
            response = self.make_request("POST", "/fees/", fee_data)
            
            if response and response.status_code == 201:
                fee = response.json()
                created_fees.append(fee)
                self.log_test(f"Create Fee: {fee_data['name']}", True, f"${fee_data['amount']}/month")
            else:
                error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                self.log_test(f"Create Fee: {fee_data['name']}", False, f"Error: {error_msg}")
                return False
        # Test listing fees
        response = self.make_request("GET", "/fees/")
        if response and response.status_code == 200:
            fees = response.json()
            self.log_test("List Fees", True, f"Found {len(fees)} recurring fees")
        else:
            self.log_test("List Fees", False, "Failed to list fees")
            return False
        # Test deleting a fee
        if created_fees:
            fee_name = created_fees[0]["name"]
            response = self.make_request("DELETE", f"/fees/{fee_name}")
            if response and response.status_code == 204:
                self.log_test(f"Delete Fee: {fee_name}", True, "Successfully deleted")
                return True
            else:
                self.log_test(f"Delete Fee: {fee_name}", False, "Failed to delete")
                return False
        
        return len(created_fees) > 0
    
    def test_plan_management(self):
        """Test budget plan management"""
        print("\n📋 Testing Plan Management...")
        
        # Test creating budget plans
        plans_to_create = [
            {
                "name": "Vacation Savings",
                "detail_description": "Save $2000 for a trip to Japan next year",
                "day_created": "2025-07-15",
                "status": "active",
                "jar_recommendations": "Increase savings jar allocation by 5%"
            },
            {
                "name": "Emergency Fund",
                "detail_description": "Build a 6-month emergency fund",
                "day_created": "2025-07-15",
                "status": "active",
                "jar_recommendations": "Set aside $500/month to emergency jar"
            }
        ]
        
        created_plans = []
        for plan_data in plans_to_create:
            response = self.make_request("POST", "/plans/", plan_data)
            
            if response and response.status_code == 201:
                plan = response.json()
                created_plans.append(plan)
                self.log_test(f"Create Plan: {plan_data['name']}", True, f"Status: {plan_data['status']}")
            else:
                error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                self.log_test(f"Create Plan: {plan_data['name']}", False, f"Error: {error_msg}")
                return False
        # Test listing plans
        response = self.make_request("GET", "/plans/")
        if response and response.status_code == 200:
            plans = response.json()
            self.log_test("List Plans", True, f"Found {len(plans)} budget plans")
        else:
            self.log_test("List Plans", False, "Failed to list plans")
            return False
        # Test updating a plan
        if created_plans:
            plan_name = created_plans[0]["name"]
            update_data = {
                "status": "completed",
                "jar_recommendations": "Updated recommendations"
            }
            response = self.make_request("PUT", f"/plans/{plan_name}", update_data)
            if response and response.status_code == 200:
                updated_plan = response.json()
                self.log_test(f"Update Plan: {plan_name}", True, f"New status: {updated_plan.get('status')}")
            else:
                self.log_test(f"Update Plan: {plan_name}", False, "Failed to update")
                return False
        # Test deleting a plan
        if len(created_plans) > 1:
            plan_name = created_plans[1]["name"]
            response = self.make_request("DELETE", f"/plans/{plan_name}")
            if response and response.status_code == 204:
                self.log_test(f"Delete Plan: {plan_name}", True, "Successfully deleted")
                return True
            else:
                self.log_test(f"Delete Plan: {plan_name}", False, "Failed to delete")
                return False
        # If no plans were created, return False
        return len(created_plans) > 0
    
    def test_ai_chat(self):
        """Test AI chat functionality, including history retrieval."""
        print("\n💬 Testing AI Chat (POST and GET)...")
        
        # 1. --- Send a series of messages via POST ---
        chat_messages = [
            "Dining with my wife 5 dollar",
            # "show jars",
            # "show fees",
            # "daily commute expenses (from monday to friday) 5 dollar"
        ]
        
        print("\n--- Sending POST requests to /api/chat/ ---")
        for message in chat_messages:
            chat_data = {
                "message": message,
                "context": {"test_run": True}
            }
            
            response = self.make_request("POST", "/chat/", chat_data)
            
            # Check if the request was successful
            if not response or response.status_code != 200:
                error_msg = response.json().get('detail', 'Unknown error') if response else 'No response'
                self.log_test(f"Chat: '{message[:30]}...'", False, f"HTTP Error: {error_msg}")
                return False # Fail fast if any chat request fails
            
            # Check the content of the response
            try:
                chat_response = response.json()
                if chat_response.get("success", False):
                    self.log_test(f"Chat: '{message[:30]}...'", True, "Received successful AI response.")
                    # Print the AI's actual response for review
                    print(f"   🤖 AI Response: {chat_response.get('response')}\n")
                else:
                    self.log_test(f"Chat: '{message[:30]}...'", False, f"Response marked as unsuccessful: {chat_response.get('response')}")
                    return False
            except Exception as e:
                self.log_test(f"Chat: '{message[:30]}...'", False, f"Failed to parse JSON response: {e}")
                return False

        # 2. --- Verify the conversation history via GET ---
        print("\n--- Sending GET request to /api/chat/history ---")
        
        # Add a limit to the request to match the number of messages sent
        history_response = self.make_request("GET", f"/chat/history?limit={len(chat_messages)}")

        if not history_response or history_response.status_code != 200:
            error_msg = history_response.json().get('detail', 'Unknown error') if history_response else 'No response'
            self.log_test("Get Chat History", False, f"HTTP Error: {error_msg}")
            return False

        try:
            history = history_response.json()
            
            # Validate the history
            if not isinstance(history, list):
                self.log_test("Get Chat History", False, "Response is not a list as expected.")
                return False
            
            if len(history) != len(chat_messages):
                self.log_test("Get Chat History", False, 
                            f"Expected {len(chat_messages)} turns, but got {len(history)}.")
                return False
                
            # Check if the last message in history matches the last one sent
            last_turn_in_history = history[-1]
            last_message_sent = chat_messages[-1]
            if last_turn_in_history.get("user_input") != last_message_sent:
                self.log_test("Get Chat History", False, "The last message in the history does not match.")
                return False

            self.log_test("Get Chat History", True, f"Successfully retrieved {len(history)} conversation turns.")

        except Exception as e:
            self.log_test("Get Chat History", False, f"Failed to parse history response: {e}")
            return False
            
        return True # Return True only if all steps passed
    
    def test_comprehensive_workflow(self):
        """Test a comprehensive user workflow"""
        print("\n🔄 Testing Comprehensive Workflow...")
        
        # This tests the complete user journey
        workflow_steps = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("User Profile", self.test_user_profile),
            ("User Settings", self.test_user_settings),
            ("Jar Management", self.test_jar_management),
            ("Transaction Management", self.test_transaction_management),
            ("Fee Management", self.test_fee_management),
            ("Plan Management", self.test_plan_management),
            ("AI Chat", self.test_ai_chat)
        ]
        
        successful_steps = 0
        total_steps = len(workflow_steps)
        
        for step_name, test_function in workflow_steps:
            try:
                while True:
                    if test_function():
                        successful_steps += 1
                        break
                    isnext = input(f"Input 1 to continue to next step, or any other key to skip: ")
                    if isnext != "1":
                        break
            except Exception as e:
                self.log_test(f"Workflow Step: {step_name}", False, f"Exception: {str(e)}")
        
        success_rate = (successful_steps / total_steps) * 100
        self.log_test("Complete Workflow", successful_steps == total_steps, 
                     f"Success rate: {success_rate:.1f}% ({successful_steps}/{total_steps})")
        
        return successful_steps == total_steps
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 TEST REPORT SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}")
            if result["details"]:
                print(f"      {result['details']}")
        
        print("\n" + "="*60)
        
        # Save report to file
        report_file = "api_test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": f"{(passed_tests/total_tests)*100:.1f}%",
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")

def main():
    """Main testing function"""
    print("🚀 VPBank Financial Coach Backend API Testing")
    print("=" * 50)
    print("Testing against: http://127.0.0.1:8000")
    print("Make sure the backend server is running!")
    print("=" * 50)
    
    # Initialize tester
    tester = VPBankAPITester()
    
    # Run comprehensive test workflow
    tester.test_comprehensive_workflow()
    
    # Generate test report
    tester.generate_test_report()
    
    print("\n🎉 Testing completed!")
    print("Check the detailed API documentation at: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    # Check if requests library is available
    try:
        import requests
    except ImportError:
        print("❌ Error: 'requests' library not found")
        print("Install it with: pip install requests")
        exit(1)
    
    main()
