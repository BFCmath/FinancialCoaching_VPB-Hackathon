#!/usr/bin/env python3
"""
VPBank Financial Coach Backend API - Comprehensive Test Suite
============================================================

This script provides an exhaustive test of all API endpoints with detailed verification
and an interactive chat mode for testing the conversational AI agents.

Features:
- Complete API endpoint testing
- Default jar system verification  
- Interactive chat mode for agent testing
- Detailed validation and error checking
- Progress tracking and comprehensive reporting

Usage:
    python fully_test.py

Requirements:
    - Backend server running on http://127.0.0.1:8000
    - 'requests' library: pip install requests
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

class VPBankComprehensiveTester:
    """Comprehensive API tester for the VPBank Financial Coach Backend."""
    
    # Default jar configuration based on user_setting_utils.py
    DEFAULT_JARS_DATA = [
        {
            "name": "necessities", 
            "description": "This is the foundation of your budget, covering essential living costs. Use it for non-negotiable expenses like rent/mortgage, utilities (electricity, water, internet), groceries, essential transportation, and insurance.", 
            "percent": 0.55
        },
        {
            "name": "long_term_savings", 
            "description": "Your safety net and goal-achiever. This jar is for saving for big-ticket items and preparing for the unexpected. Use it for your emergency fund, a down payment on a car or home, or a dream vacation.", 
            "percent": 0.10
        },
        {
            "name": "play", 
            "description": "This is your mandatory guilt-free fun money! You MUST spend this every month to pamper yourself and enjoy life. Use it for movies, dining out, hobbies, short trips, or buying something special just for you.", 
            "percent": 0.10
        },
        {
            "name": "education", 
            "description": "Invest in your greatest asset: you. This jar is for personal growth and learning new skills that can increase your knowledge and earning potential. Use it for books, online courses, seminars, workshops, or coaching.", 
            "percent": 0.10
        },
        {
            "name": "financial_freedom", 
            "description": "Your golden goose. This money is for building wealth and generating passive income so you eventually don't have to work for money. Use it for stocks, bonds, mutual funds, or other income-generating assets. You never spend this money, you only invest it.", 
            "percent": 0.10
        },
        {
            "name": "give", 
            "description": "Practice generosity and cultivate a mindset of abundance. Use this money to make a positive impact, whether through charity, donations, helping a friend in need, or buying an unexpected gift for a loved one.", 
            "percent": 0.05
        }
    ]
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_url = f"{self.base_url}/api"
        self.token: Optional[str] = None
        self.user_data: Dict[str, str] = {}
        self.test_results: List[Dict] = []
        self.created_items: Dict[str, List[str]] = {
            "transactions": [],
            "fees": [],
            "plans": [],
            "jars": []
        }
        self.interactive_mode = False

    def log_test(self, test_name: str, success: bool, details: str = "", level: str = "INFO"):
        """Log test results with detailed information."""
        status = "✅ PASS" if success else "❌ FAIL"
        if level == "ERROR":
            status = "🔥 ERROR"
        elif level == "WARN":
            status = "⚠️  WARN"
        
        print(f"\n{status} | {test_name}")
        if details: 
            print(f"      └── {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "level": level,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    params: Optional[Dict] = None, use_auth: bool = True, 
                    expected_status: Optional[int] = None) -> Optional[requests.Response]:
        """Make HTTP request with comprehensive error handling."""
        url = f"{self.api_url}{endpoint}"
        content_type = "application/x-www-form-urlencoded" if "token" in endpoint else "application/json"
        headers = {"Content-Type": content_type}
        
        if use_auth and self.token: 
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
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
                raise ValueError(f"Unsupported method: {method}")
            
            # Check expected status if provided
            if expected_status and response.status_code != expected_status:
                self.log_test(f"Status Check for {method} {endpoint}", False, 
                            f"Expected {expected_status}, got {response.status_code}", "ERROR")
            
            return response
            
        except requests.exceptions.ConnectionError:
            self.log_test(f"Connection Error for {method} {endpoint}", False, 
                         "Could not connect to server. Is it running?", "ERROR")
            return None
        except requests.exceptions.RequestException as e:
            self.log_test(f"Request Error for {method} {endpoint}", False, str(e), "ERROR")
            return None

    def validate_json_response(self, response: requests.Response, expected_fields: List[str] = None) -> bool:
        """Validate JSON response structure."""
        try:
            data = response.json()
            if expected_fields:
                missing_fields = [field for field in expected_fields if field not in data]
                if missing_fields:
                    self.log_test("JSON Validation", False, f"Missing fields: {missing_fields}", "WARN")
                    return False
            return True
        except json.JSONDecodeError:
            self.log_test("JSON Validation", False, "Response is not valid JSON", "ERROR")
            return False

    def setup_authentication(self) -> bool:
        """Set up user authentication."""
        print("\n" + "="*60)
        print("🔐 AUTHENTICATION SETUP")
        print("="*60)
        
        # Create unique test user
        timestamp = int(time.time())
        self.user_data = {
            "username": f"comprehensive_tester_{timestamp}",
            "email": f"test_{timestamp}@vpbank.test.com",
            "password": "SecurePassword123!"
        }
        
        # Register user
        print(f"Registering user: {self.user_data['username']}")
        response = self.make_request("POST", "/auth/register", self.user_data, use_auth=False, expected_status=201)
        
        if not response or response.status_code != 201:
            self.log_test("User Registration", False, f"Status: {response.status_code if response else 'No response'}", "ERROR")
            return False
        
        if not self.validate_json_response(response, ["_id", "username", "email"]):
            return False
        
        self.log_test("User Registration", True, f"User '{self.user_data['username']}' created successfully")
        
        # Login to get token
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        
        response = self.make_request("POST", "/auth/token", login_data, use_auth=False, expected_status=200)
        
        if not response or response.status_code != 200:
            self.log_test("User Login", False, "Failed to authenticate", "ERROR")
            return False
        
        if not self.validate_json_response(response, ["access_token", "token_type"]):
            return False
        
        self.token = response.json().get("access_token")
        self.log_test("User Login", True, "Authentication token acquired")
        
        # Test protected endpoint
        response = self.make_request("GET", "/auth/me", expected_status=200)
        if not response or response.status_code != 200:
            self.log_test("Token Validation", False, "Token validation failed", "ERROR")
            return False
        
        self.log_test("Token Validation", True, "Token works correctly")
        return True

    def test_user_settings(self) -> bool:
        """Test user settings endpoints."""
        print("\n" + "="*60)
        print("⚙️  USER SETTINGS TESTING")
        print("="*60)
        
        # Get initial settings
        response = self.make_request("GET", "/user/settings", expected_status=200)
        if not response:
            return False
        
        initial_settings = response.json()
        self.log_test("Get Initial Settings", True, f"Default income: ${initial_settings.get('total_income', 'N/A')}")
        
        # Update settings
        new_income = 10000.0
        update_data = {"total_income": new_income}
        
        response = self.make_request("PUT", "/user/settings", update_data, expected_status=200)
        if not response:
            return False
        
        updated_settings = response.json()
        if updated_settings.get("total_income") != new_income:
            self.log_test("Update Settings", False, "Income not updated correctly", "ERROR")
            return False
        
        self.log_test("Update Settings", True, f"Income updated to ${new_income}")
        
        # Test invalid income (FastAPI uses 422 for validation errors)
        response = self.make_request("PUT", "/user/settings", {"total_income": -1000}, expected_status=422)
        if response and response.status_code == 422:
            self.log_test("Invalid Income Validation", True, "Negative income properly rejected")
        else:
            self.log_test("Invalid Income Validation", False, "Should reject negative income", "WARN")
        
        return True

    def test_default_jars_system(self) -> bool:
        """Test the automatic default jar creation system."""
        print("\n" + "="*60)
        print("🏺 DEFAULT JARS SYSTEM TESTING")
        print("="*60)
        
        # Get all jars
        response = self.make_request("GET", "/jars/", expected_status=200)
        if not response:
            return False
        
        jars = response.json()
        
        # Verify we have exactly 6 jars
        if len(jars) != 6:
            self.log_test("Default Jar Count", False, f"Expected 6 jars, found {len(jars)}", "ERROR")
            return False
        
        self.log_test("Default Jar Count", True, "Found 6 default jars")
        
        # Verify each default jar exists with correct properties
        jar_names = [jar["name"] for jar in jars]
        expected_jars = [jar["name"] for jar in self.DEFAULT_JARS_DATA]
        
        missing_jars = set(expected_jars) - set(jar_names)
        if missing_jars:
            self.log_test("Default Jar Names", False, f"Missing jars: {missing_jars}", "ERROR")
            return False
        
        self.log_test("Default Jar Names", True, "All expected jar names present")
        
        # Verify jar percentages sum to 100%
        total_percent = sum(jar["percent"] for jar in jars)
        if abs(total_percent - 1.0) > 0.001:  # Allow for floating point errors
            self.log_test("Jar Percentages", False, f"Total percentage is {total_percent*100:.1f}%, not 100%", "ERROR")
            return False
        
        self.log_test("Jar Percentages", True, "Jar percentages sum to 100%")
        
        # Verify specific jar properties
        for expected_jar in self.DEFAULT_JARS_DATA:
            actual_jar = next((j for j in jars if j["name"] == expected_jar["name"]), None)
            if not actual_jar:
                continue
            
            # Check percentage
            if abs(actual_jar["percent"] - expected_jar["percent"]) > 0.001:
                self.log_test(f"Jar {expected_jar['name']} Percentage", False, 
                            f"Expected {expected_jar['percent']}, got {actual_jar['percent']}", "WARN")
            else:
                self.log_test(f"Jar {expected_jar['name']} Percentage", True, 
                            f"Correct percentage: {expected_jar['percent']*100}%")
        
        return True

    def test_jar_management(self) -> bool:
        """Test jar CRUD operations."""
        print("\n" + "="*60)
        print("🏺 JAR MANAGEMENT TESTING")
        print("="*60)
        
        # Test creating a new jar
        new_jar_data = {
            "name": "emergency_fund",
            "description": "Emergency fund for unexpected expenses",
            "percent": 0.05
        }
        
        response = self.make_request("POST", "/jars/", new_jar_data, expected_status=201)
        if not response:
            return False
        
        created_jar = response.json()
        self.created_items["jars"].append(created_jar["name"])
        self.log_test("Create New Jar", True, f"Created jar: {created_jar['name']}")
        
        # Test getting specific jar
        response = self.make_request("GET", f"/jars/{created_jar['name']}", expected_status=200)
        if not response:
            return False
        
        jar_details = response.json()
        self.log_test("Get Specific Jar", True, f"Retrieved jar: {jar_details['name']}")
        
        # Test updating jar
        update_data = {
            "description": "Updated emergency fund description",
            "percent": 0.08
        }
        
        response = self.make_request("PUT", f"/jars/{created_jar['name']}", update_data, expected_status=200)
        if not response:
            return False
        
        updated_jar = response.json()
        if updated_jar["description"] != update_data["description"]:
            self.log_test("Update Jar", False, "Description not updated", "ERROR")
            return False
        
        self.log_test("Update Jar", True, "Jar updated successfully")
        
        # Test jar rebalancing after creation
        response = self.make_request("GET", "/jars/", expected_status=200)
        if response:
            all_jars = response.json()
            total_percent = sum(jar["percent"] for jar in all_jars)
            if abs(total_percent - 1.0) > 0.001:
                self.log_test("Auto Rebalancing", False, f"Total percentage: {total_percent*100:.1f}%", "WARN")
            else:
                self.log_test("Auto Rebalancing", True, "Jars rebalanced to 100%")
        
        return True

    def test_transaction_system(self) -> bool:
        """Test transaction CRUD operations and jar integration."""
        print("\n" + "="*60)
        print("💰 TRANSACTION SYSTEM TESTING")
        print("="*60)
        
        # Test creating transaction
        transaction_data = {
            "amount": 150.75,
            "jar": "play",
            "description": "Dinner at fancy restaurant",
            "source": "manual_input",
            "transaction_datetime": datetime.now(timezone.utc).isoformat()
        }
        
        response = self.make_request("POST", "/transactions/", transaction_data, expected_status=201)
        if not response:
            return False
        
        created_transaction = response.json()
        transaction_id = created_transaction["_id"]
        self.created_items["transactions"].append(transaction_id)
        
        self.log_test("Create Transaction", True, f"Created transaction: ${transaction_data['amount']}")
        
        # Verify jar balance updated
        response = self.make_request("GET", f"/jars/{transaction_data['jar']}", expected_status=200)
        if response:
            jar = response.json()
            if jar["current_amount"] != transaction_data["amount"]:
                self.log_test("Jar Balance Update", False, 
                            f"Expected {transaction_data['amount']}, got {jar['current_amount']}", "ERROR")
            else:
                self.log_test("Jar Balance Update", True, f"Jar balance: ${jar['current_amount']}")
        
        # Test transaction filters
        response = self.make_request("GET", "/transactions/", params={"jar": "play"}, expected_status=200)
        if response:
            filtered_transactions = response.json()
            if len(filtered_transactions) >= 1:
                self.log_test("Filter by Jar", True, f"Found {len(filtered_transactions)} transactions")
            else:
                self.log_test("Filter by Jar", False, "No transactions found", "WARN")
        
        # Test date range filter
        start_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        end_date = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        response = self.make_request("GET", "/transactions/by-date-range", 
                                   params={"start_date": start_date, "end_date": end_date}, 
                                   expected_status=200)
        if response:
            date_filtered = response.json()
            self.log_test("Filter by Date Range", True, f"Found {len(date_filtered)} transactions in range")
        
        # Test amount range filter
        response = self.make_request("GET", "/transactions/by-amount-range",
                                   params={"min_amount": 100, "max_amount": 200},
                                   expected_status=200)
        if response:
            amount_filtered = response.json()
            self.log_test("Filter by Amount Range", True, f"Found {len(amount_filtered)} transactions in range")
        
        # Test source filter
        response = self.make_request("GET", f"/transactions/by-source/{transaction_data['source']}", 
                                   expected_status=200)
        if response:
            source_filtered = response.json()
            self.log_test("Filter by Source", True, f"Found {len(source_filtered)} transactions from source")
        
        # Test transaction deletion and jar refund
        original_balance = jar["current_amount"]
        response = self.make_request("DELETE", f"/transactions/{transaction_id}", expected_status=204)
        if response and response.status_code == 204:
            self.log_test("Delete Transaction", True, "Transaction deleted successfully")
            
            # Verify jar balance refunded
            response = self.make_request("GET", f"/jars/{transaction_data['jar']}", expected_status=200)
            if response:
                updated_jar = response.json()
                expected_balance = original_balance - transaction_data["amount"]
                if abs(updated_jar["current_amount"] - expected_balance) < 0.01:
                    self.log_test("Jar Refund", True, f"Jar balance refunded to ${updated_jar['current_amount']}")
                else:
                    self.log_test("Jar Refund", False, 
                                f"Expected {expected_balance}, got {updated_jar['current_amount']}", "ERROR")
        
        return True

    def test_recurring_fees(self) -> bool:
        """Test recurring fee management."""
        print("\n" + "="*60)
        print("🔄 RECURRING FEES TESTING")
        print("="*60)
        
        # Test creating recurring fees
        fees_data = [
            {
                "name": "Netflix",
                "amount": 15.99,
                "target_jar": "play",
                "description": "Monthly Netflix subscription",
                "pattern_type": "monthly",
                "pattern_details": [15]
            },
            {
                "name": "Rent",
                "amount": 2000.0,
                "target_jar": "necessities", 
                "description": "Monthly rent payment",
                "pattern_type": "monthly",
                "pattern_details": [1]
            },
            {
                "name": "Coffee",
                "amount": 5.0,
                "target_jar": "necessities",
                "description": "Daily coffee",
                "pattern_type": "daily",
                "pattern_details": []
            }
        ]
        
        created_fees = []
        for fee_data in fees_data:
            response = self.make_request("POST", "/fees/", fee_data, expected_status=201)
            if not response:
                return False
            
            created_fee = response.json()
            created_fees.append(created_fee["name"])
            self.created_items["fees"].append(created_fee["name"])
            self.log_test(f"Create Fee: {fee_data['name']}", True, 
                         f"${fee_data['amount']} {fee_data['pattern_type']} fee")
        
        # Test listing all fees
        response = self.make_request("GET", "/fees/", expected_status=200)
        if response:
            all_fees = response.json()
            self.log_test("List All Fees", True, f"Found {len(all_fees)} fees")
        
        # Test filtering by active status
        response = self.make_request("GET", "/fees/", params={"active_only": "true"}, expected_status=200)
        if response:
            active_fees = response.json()
            if len(active_fees) == len(created_fees):
                self.log_test("Filter Active Fees", True, f"Found {len(active_fees)} active fees")
            else:
                self.log_test("Filter Active Fees", False, 
                            f"Expected {len(created_fees)}, got {len(active_fees)}", "WARN")
        
        # Test filtering by target jar
        response = self.make_request("GET", "/fees/", params={"target_jar": "necessities"}, expected_status=200)
        if response:
            necessities_fees = response.json()
            expected_count = sum(1 for fee in fees_data if fee["target_jar"] == "necessities")
            if len(necessities_fees) == expected_count:
                self.log_test("Filter by Target Jar", True, f"Found {len(necessities_fees)} fees for necessities jar")
            else:
                self.log_test("Filter by Target Jar", False, 
                            f"Expected {expected_count}, got {len(necessities_fees)}", "WARN")
        
        # Test fees due today (should include daily fee)
        response = self.make_request("GET", "/fees/due/today", expected_status=200)
        if response:
            due_today = response.json()
            daily_fees_count = sum(1 for fee in fees_data if fee["pattern_type"] == "daily")
            if len(due_today) >= daily_fees_count:
                self.log_test("Fees Due Today", True, f"Found {len(due_today)} fees due today")
            else:
                self.log_test("Fees Due Today", False, 
                            f"Expected at least {daily_fees_count}, got {len(due_today)}", "WARN")
        
        # Test updating a fee
        update_data = {
            "amount": 17.99,
            "description": "Updated Netflix price"
        }
        
        response = self.make_request("PUT", f"/fees/Netflix", update_data, expected_status=200)
        if response:
            updated_fee = response.json()
            if updated_fee["amount"] == update_data["amount"]:
                self.log_test("Update Fee", True, f"Updated Netflix fee to ${update_data['amount']}")
            else:
                self.log_test("Update Fee", False, "Amount not updated correctly", "ERROR")
        
        # Test getting specific fee
        response = self.make_request("GET", "/fees/Netflix", expected_status=200)
        if response:
            netflix_fee = response.json()
            self.log_test("Get Specific Fee", True, f"Retrieved Netflix fee: ${netflix_fee['amount']}")
        
        return True

    def test_budget_plans(self) -> bool:
        """Test budget plan management."""
        print("\n" + "="*60)
        print("📋 BUDGET PLANS TESTING")
        print("="*60)
        
        # Test creating budget plans
        plans_data = [
            {
                "name": "Emergency Fund",
                "detail_description": "Build a 6-month emergency fund for financial security",
                "status": "active",
                "jar_recommendations": "Increase long_term_savings to 15%"
            },
            {
                "name": "Vacation Savings",
                "detail_description": "Save for a trip to Japan next year",
                "status": "active"
            },
            {
                "name": "Car Purchase",
                "detail_description": "Save for a new car down payment",
                "status": "paused"
            }
        ]
        
        created_plans = []
        for plan_data in plans_data:
            response = self.make_request("POST", "/plans/", plan_data, expected_status=201)
            if not response:
                return False
            
            created_plan = response.json()
            created_plans.append(created_plan["name"])
            self.created_items["plans"].append(created_plan["name"])
            self.log_test(f"Create Plan: {plan_data['name']}", True, 
                         f"Status: {plan_data['status']}")
        
        # Test listing all plans
        response = self.make_request("GET", "/plans/", expected_status=200)
        if response:
            all_plans = response.json()
            self.log_test("List All Plans", True, f"Found {len(all_plans)} plans")
        
        # Test filtering by status
        response = self.make_request("GET", "/plans/", params={"status": "active"}, expected_status=200)
        if response:
            active_plans = response.json()
            expected_active = sum(1 for plan in plans_data if plan["status"] == "active")
            if len(active_plans) == expected_active:
                self.log_test("Filter Active Plans", True, f"Found {len(active_plans)} active plans")
            else:
                self.log_test("Filter Active Plans", False, 
                            f"Expected {expected_active}, got {len(active_plans)}", "WARN")
        
        response = self.make_request("GET", "/plans/", params={"status": "paused"}, expected_status=200)
        if response:
            paused_plans = response.json()
            expected_paused = sum(1 for plan in plans_data if plan["status"] == "paused")
            if len(paused_plans) == expected_paused:
                self.log_test("Filter Paused Plans", True, f"Found {len(paused_plans)} paused plans")
            else:
                self.log_test("Filter Paused Plans", False, 
                            f"Expected {expected_paused}, got {len(paused_plans)}", "WARN")
        
        # Test updating a plan
        update_data = {
            "status": "completed",
            "detail_description": "Emergency fund goal achieved!"
        }
        
        response = self.make_request("PUT", "/plans/Emergency Fund", update_data, expected_status=200)
        if response:
            updated_plan = response.json()
            if updated_plan["status"] == update_data["status"]:
                self.log_test("Update Plan", True, f"Plan status updated to {update_data['status']}")
            else:
                self.log_test("Update Plan", False, "Status not updated correctly", "ERROR")
        
        # Test getting specific plan
        response = self.make_request("GET", "/plans/Emergency Fund", expected_status=200)
        if response:
            emergency_plan = response.json()
            self.log_test("Get Specific Plan", True, f"Retrieved plan: {emergency_plan['name']}")
        
        return True

    def test_chat_system(self) -> bool:
        """Test the chat system and orchestrator."""
        print("\n" + "="*60)
        print("💬 CHAT SYSTEM TESTING")
        print("="*60)
        
        # Test various chat messages
        test_messages = [
            "What is my current balance in the play jar?",
            "Add a $50 transaction to my education jar for an online course",
            "Show me all my active recurring fees",
            "What are my current budget plans?",
            "How much money do I have in total across all jars?",
            "Create a new budget plan for buying a laptop"
        ]
        
        chat_responses = []
        for i, message in enumerate(test_messages):
            print(f"\nSending message {i+1}/{len(test_messages)}: {message}")
            
            response = self.make_request("POST", "/chat/", {"message": message}, expected_status=200)
            if not response:
                self.log_test(f"Chat Message {i+1}", False, "Failed to send message", "ERROR")
                continue
            
            chat_response = response.json()
            chat_responses.append(chat_response)
            
            # Validate response structure
            required_fields = ["user_input", "agent_output", "agent_list", "tool_call_list"]
            if not self.validate_json_response(response, required_fields):
                self.log_test(f"Chat Message {i+1}", False, "Invalid response structure", "ERROR")
                continue
            
            # Check if agents were involved
            if not chat_response.get("agent_list"):
                self.log_test(f"Chat Message {i+1}", False, "No agents involved in response", "WARN")
            else:
                agents_involved = ", ".join(chat_response["agent_list"])
                self.log_test(f"Chat Message {i+1}", True, f"Agents: {agents_involved}")
            
            print(f"Response: {chat_response['agent_output'][:100]}...")
        
        # Test chat history
        response = self.make_request("GET", "/chat/history", params={"limit": len(test_messages)}, expected_status=200)
        if response:
            history = response.json()
            if len(history) >= len(test_messages):
                self.log_test("Chat History", True, f"Retrieved {len(history)} conversation turns")
            else:
                self.log_test("Chat History", False, 
                            f"Expected at least {len(test_messages)}, got {len(history)}", "WARN")
        
        return True

    def cleanup_created_items(self) -> bool:
        """Clean up items created during testing."""
        print("\n" + "="*60)
        print("🧹 CLEANUP")
        print("="*60)
        
        success_count = 0
        total_count = 0
        
        # Delete created plans
        for plan_name in self.created_items["plans"]:
            total_count += 1
            response = self.make_request("DELETE", f"/plans/{plan_name}", expected_status=204)
            if response and response.status_code == 204:
                success_count += 1
                print(f"✅ Deleted plan: {plan_name}")
            else:
                print(f"❌ Failed to delete plan: {plan_name}")
        
        # Delete created fees
        for fee_name in self.created_items["fees"]:
            total_count += 1
            response = self.make_request("DELETE", f"/fees/{fee_name}", expected_status=204)
            if response and response.status_code == 204:
                success_count += 1
                print(f"✅ Deleted fee: {fee_name}")
            else:
                print(f"❌ Failed to delete fee: {fee_name}")
        
        # Delete created jars
        for jar_name in self.created_items["jars"]:
            total_count += 1
            response = self.make_request("DELETE", f"/jars/{jar_name}", expected_status=204)
            if response and response.status_code == 204:
                success_count += 1
                print(f"✅ Deleted jar: {jar_name}")
            else:
                print(f"❌ Failed to delete jar: {jar_name}")
        
        # Note: Transactions are typically not deleted in cleanup as they represent historical data
        
        self.log_test("Cleanup", True, f"Cleaned up {success_count}/{total_count} items")
        return success_count == total_count

    def run_comprehensive_tests(self) -> bool:
        """Run all test suites."""
        print("\n🚀 Starting VPBank Financial Coach Backend Comprehensive Testing")
        print("=" * 80)
        
        test_suites = [
            ("Authentication Setup", self.setup_authentication),
            ("User Settings", self.test_user_settings),
            ("Default Jars System", self.test_default_jars_system),
            ("Jar Management", self.test_jar_management),
            ("Transaction System", self.test_transaction_system),
            ("Recurring Fees", self.test_recurring_fees),
            ("Budget Plans", self.test_budget_plans),
            ("Chat System", self.test_chat_system),
            ("Cleanup", self.cleanup_created_items)
        ]
        
        passed_suites = 0
        for suite_name, test_function in test_suites:
            try:
                print(f"\n🔄 Running: {suite_name}")
                if test_function():
                    print(f"✅ {suite_name} - PASSED")
                    passed_suites += 1
                else:
                    print(f"❌ {suite_name} - FAILED")
                    if not self.interactive_mode:
                        print("Stopping tests due to failure")
                        break
            except Exception as e:
                print(f"💥 {suite_name} - CRITICAL ERROR: {e}")
                self.log_test(suite_name, False, str(e), "ERROR")
                if not self.interactive_mode:
                    break
        
        return passed_suites == len(test_suites)

    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        if total_tests > 0:
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Show errors and warnings
        errors = [r for r in self.test_results if r["level"] == "ERROR"]
        warnings = [r for r in self.test_results if r["level"] == "WARN"]
        
        if errors:
            print(f"\n🔥 Errors ({len(errors)}):")
            for error in errors:
                print(f"  • {error['test']}: {error['details']}")
        
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning['test']}: {warning['details']}")

    def interactive_chat_mode(self):
        """Interactive mode for testing the chat API directly."""
        print("\n" + "="*80)
        print("💬 INTERACTIVE CHAT MODE")
        print("="*80)
        print("Type messages to test the chat API. Type 'EXIT' to quit.")
        print("Examples:")
        print("  - What's my balance in the play jar?")
        print("  - Add a $25 transaction to my education jar for books")
        print("  - Show me my recurring fees")
        print("  - Create a new budget plan for vacation")
        print("  - Help me analyze my spending patterns")
        print("-" * 80)
        
        if not self.token:
            print("❌ No authentication token available. Please run the full test suite first.")
            return
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.upper() == 'EXIT':
                    print("👋 Exiting interactive mode...")
                    break
                
                if not user_input:
                    print("Please enter a message or 'EXIT' to quit.")
                    continue
                
                print("🤖 Sending to agent...")
                
                # Send message to chat API
                response = self.make_request("POST", "/chat/", {"message": user_input})
                
                if not response:
                    print("❌ Failed to get response from server")
                    continue
                
                if response.status_code != 200:
                    print(f"❌ Error {response.status_code}: {response.text}")
                    continue
                
                try:
                    chat_response = response.json()
                    conversation_count += 1
                    
                    print(f"\n🤖 Agent Response:")
                    print(f"   {chat_response.get('agent_output', 'No response')}")
                    
                    # Show which agents were involved
                    agents = chat_response.get('agent_list', [])
                    if agents:
                        print(f"\n🔧 Agents involved: {', '.join(agents)}")
                    
                    # Show tool calls if any
                    tools = chat_response.get('tool_call_list', [])
                    if tools:
                        print(f"🛠️  Tools used: {', '.join(tools)}")
                    
                except json.JSONDecodeError:
                    print("❌ Invalid JSON response from server")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Exiting...")
                break
            except EOFError:
                print("\n\n👋 EOF detected. Exiting...")
                break
        
        print(f"\n📊 Interactive session summary: {conversation_count} messages exchanged")
        
        # Ask if user wants to see conversation history
        try:
            show_history = input("\nWould you like to see your conversation history? (y/n): ").strip().lower()
            if show_history in ['y', 'yes']:
                response = self.make_request("GET", "/chat/history", params={"limit": conversation_count + 10})
                if response and response.status_code == 200:
                    history = response.json()
                    print(f"\n📚 Conversation History ({len(history)} turns):")
                    for i, turn in enumerate(history[-conversation_count:], 1):
                        print(f"\n{i}. User: {turn['user_input']}")
                        print(f"   Agent: {turn['agent_output'][:200]}{'...' if len(turn['agent_output']) > 200 else ''}")
        except (KeyboardInterrupt, EOFError):
            pass


def main():
    """Main function to run tests or interactive mode."""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive-only":
        # Skip comprehensive tests, go straight to interactive mode
        tester = VPBankComprehensiveTester()
        tester.interactive_mode = True
        
        # Still need authentication
        if not tester.setup_authentication():
            print("❌ Authentication failed. Cannot start interactive mode.")
            return
        
        tester.interactive_chat_mode()
        return
    
    # Run comprehensive tests
    tester = VPBankComprehensiveTester()
    success = tester.run_comprehensive_tests()
    
    tester.print_test_summary()
    
    if success:
        print("\n🎉 All tests passed! The API is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
    
    # Ask if user wants to enter interactive mode
    try:
        if success and tester.token:
            interactive = input("\nWould you like to enter interactive chat mode? (y/n): ").strip().lower()
            if interactive in ['y', 'yes']:
                tester.interactive_chat_mode()
    except (KeyboardInterrupt, EOFError):
        pass
    
    print("\n👋 Testing completed!")


if __name__ == "__main__":
    main()
