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
            self.log_test(f"Chat: '{msg[:30]}...'", res and res.status_code == 200 and res.json().get('success'))
            self.pause_and_check(res, "Sent a message to the chat orchestrator.")
            if not (res and res.status_code == 200): return False

        res = self.make_request("GET", "/chat/history", params={"limit": len(messages)})
        self.log_test("Get Chat History", res and res.status_code == 200 and len(res.json()) == len(messages))
        self.pause_and_check(res, f"Retrieved the last {len(messages)} turns of conversation history.")
        return res and res.status_code == 200

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

if __name__ == "__main__":
    print("🚀 Starting VPBank Financial Coach Backend API Final Comprehensive Test")
    print("   (Verifying default jar initialization)")
    print("   Server should be running at http://127.0.0.1:8000")
    VPBankAPITester().run_all_tests()
    print("\n🎉 Testing workflow completed!")