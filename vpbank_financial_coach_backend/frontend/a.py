#!/usr/bin/env python3
"""
VPBank Financial Coach - Transaction API Testing Script
=========================================================

This script provides a comprehensive, interactive, end-to-end test of all
Transaction API endpoints. It is specifically designed to verify the full 
lifecycle and all filtering capabilities of transactions.

It replicates the structure of `final_mock.py` for consistency and includes
the necessary logic to handle the `x-www-form-urlencoded` token endpoint.

Usage:
    python mock_transaction.py

Requirements:
    - Backend server running on http://127.0.0.1:8000
    - 'requests' library: pip install requests
"""

import requests
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

class TransactionAPITester:
    """A structured and comprehensive API tester for the Transaction endpoints."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_url = f"{self.base_url}/api"
        self.token: Optional[str] = None
        self.user_data: Dict[str, str] = {}
        self.test_results: list = []
        self.created_item_ids: Dict[str, List[str]] = {"transactions": []}

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
            if response.request.body:
                 # Avoid printing sensitive data like passwords in logs
                if "password" not in str(response.request.body):
                    print(f"Request Body: {response.request.body}")
            print(f"Status Code: {response.status_code}")
            try: print("Response Body:\n" + json.dumps(response.json(), indent=2))
            except json.JSONDecodeError: print(f"Response Body: (No JSON content, Status {response.status_code})")
        else: print("❌ No response received from server.")
        input("-" * 15 + " Press Enter to continue... " + "-"*15)

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None,
                     use_auth: bool = True) -> Optional[requests.Response]:
        url = f"{self.api_url}{endpoint}"
        # This logic is critical for the login to work correctly
        content_type = "application/x-www-form-urlencoded" if "token" in endpoint else "application/json"
        headers = {"Accept": "application/json"}
        if content_type != "application/x-www-form-urlencoded":
            headers["Content-Type"] = content_type

        if use_auth and self.token: headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET": return requests.get(url, headers=headers, params=params)
            if method.upper() == "POST":
                # Send as form data for token, otherwise JSON
                return requests.post(url, data=data if content_type == "application/x-www-form-urlencoded" else None, 
                                     json=data if content_type == "application/json" else None, headers=headers)
            if method.upper() == "PUT": return requests.put(url, json=data, headers=headers)
            if method.upper() == "DELETE": return requests.delete(url, headers=headers)
            raise ValueError(f"Unsupported method: {method}")
        except requests.exceptions.RequestException as e: print(f"❌ Connection Error: {e}"); return None

    def run_stage(self, stage_name: str, test_function) -> bool:
        print("\n" + "="*60 + f"\n🚀 STAGE: {stage_name}\n" + "="*60)
        try:
            if test_function(): 
                print(f"\n✅ STAGE SUCCEEDED: {stage_name}")
                return True
            else: 
                print(f"\n❌ STAGE FAILED: {stage_name}.")
                return False
        except Exception as e: 
            print(f"\n💥 CRITICAL ERROR in {stage_name}: {e}")
            return False

    def setup_test_user(self) -> bool:
        """Sets up a new user, logs in, and verifies default jar creation."""
        print("--- Setting up a new user for a clean test environment ---")
        timestamp = int(time.time())
        self.user_data = {"username": f"tx_tester_{timestamp}", "email": f"tx_{timestamp}@test.com", "password": "Password123"}
        
        res = self.make_request("POST", "/auth/register", self.user_data, use_auth=False)
        if not (res and res.status_code == 201):
            self.log_test("Setup: Registration", False, "Failed to create a new user.")
            self.pause_and_check(res, "User registration failed.")
            return False
        
        login_data = {"username": self.user_data["username"], "password": self.user_data["password"]}
        res = self.make_request("POST", "/auth/token", login_data, use_auth=False)
        if not (res and res.status_code == 200 and res.json().get("access_token")):
            self.log_test("Setup: Login", False, "Failed to log in and get token.")
            self.pause_and_check(res, "User login failed. Check server and request format.")
            return False
        self.token = res.json()["access_token"]
        self.log_test("Setup: Auth", True, f"User '{self.user_data['username']}' created and logged in.")
        
        res = self.make_request("GET", "/jars/")
        if not (res and res.status_code == 200 and len(res.json()) > 0 and any(j['name'] == 'play' for j in res.json())):
            self.log_test("Setup: Verify Jars", False, "Could not find default 'play' jar.")
            self.pause_and_check(res, "Default jar verification failed.")
            return False
        self.log_test("Setup: Verify Jars", True, "Default jars are present.")
        self.pause_and_check(res, "User setup complete. Default jars verified.")
        return True

    def test_transaction_lifecycle(self) -> bool:
        """Tests transaction creation/deletion and its effect on jar balance."""
        print("--- Testing core Create, Read, Delete (CRUD) operations and side-effects ---")
        
        tx_data = {"amount": 50.25, "jar": "Play", "description": "Cinema tickets", "source": "manual_input"}
        
        # 1. Create transaction
        res = self.make_request("POST", "/transactions/", tx_data)
        if not (res and res.status_code == 201):
            self.log_test("Lifecycle: Create TX", False, "Status code was not 201.")
            return False
        tx_id = res.json().get("_id")
        self.created_item_ids["transactions"].append(tx_id)
        self.log_test("Lifecycle: Create TX", True, f"Transaction {tx_id} created.")
        self.pause_and_check(res, "Check that transaction was created successfully.")
        
        # 2. Verify Jar balance is UPDATED correctly (should be 50.25)
        # NOTE: This test is designed to FAIL with the provided buggy `transactions.py`
        res_jar = self.make_request("GET", "/jars/play")
        actual_balance = res_jar.json().get('current_amount') if res_jar else None
        is_debit_correct = res_jar and res_jar.status_code == 200 and actual_balance == tx_data["amount"]
        self.log_test("Lifecycle: Verify Jar Balance After Creation", is_debit_correct, f"Expected {tx_data['amount']}, got {actual_balance}.")
        if not is_debit_correct:
            print("🔴 ATTENTION: The test failed as expected. Creating a transaction should correctly update the jar's balance.")
        self.pause_and_check(res_jar, f"Check 'play' jar balance. It should now be {tx_data['amount']}.")

        # 3. Get the specific transaction by ID
        res = self.make_request("GET", f"/transactions/{tx_id}")
        self.log_test("Lifecycle: Get TX by ID", res and res.status_code == 200 and res.json()['_id'] == tx_id)
        self.pause_and_check(res)

        # 4. Delete the transaction
        res = self.make_request("DELETE", f"/transactions/{tx_id}")
        if not (res and res.status_code == 204):
            self.log_test("Lifecycle: Delete TX", False, "Status code was not 204.")
            return False
        self.log_test("Lifecycle: Delete TX", True, "DELETE request successful.")
        self.pause_and_check(res, "Check that the delete request returned a 204 No Content.")

        # 5. Verify Jar balance is RESTORED (should be 0.0)
        res_jar = self.make_request("GET", "/jars/play")
        actual_balance = res_jar.json().get('current_amount') if res_jar else None
        is_refund_correct = res_jar and res_jar.status_code == 200 and actual_balance == 0.0
        self.log_test("Lifecycle: Verify Jar Refund", is_refund_correct, f"Expected 0.0, got {actual_balance}.")
        if not is_refund_correct:
            print("🔴 ATTENTION: The test failed as expected. Deleting a transaction should correctly refund the jar's balance.")
        self.pause_and_check(res_jar, "Check 'play' jar balance. It should be restored to 0.0.")
        
        return True

    def test_all_filters(self) -> bool:
        """Tests filtering by date, amount, source, and jar."""
        print("--- Populating data for filter tests ---")
        
        tx_data = [
            {"amount": 15.00, "jar": "necessities", "description": "Lunch", "source": "manual_input", "transaction_datetime": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()},
            {"amount": 75.50, "jar": "play", "description": "Concert", "source": "vpbank_api", "transaction_datetime": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()},
            {"amount": 1200.00, "jar": "financial_freedom", "description": "Invest", "source": "manual_input", "transaction_datetime": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}
        ]
        for tx in tx_data:
            res = self.make_request("POST", "/transactions/", tx)
            if not (res and res.status_code == 201): return False
            self.created_item_ids["transactions"].append(res.json()['_id'])
        
        self.log_test("Filter Setup", True, "Created 3 diverse transactions for testing.")
        self.pause_and_check(self.make_request("GET", "/transactions/"), "Verify all new transactions are listed.")

        res = self.make_request("GET", "/transactions/", params={"jar": "play"})
        self.log_test("Filter by Jar ('play')", res and res.status_code == 200 and len(res.json()) == 1 and res.json()[0]['jar'] == 'play')
        self.pause_and_check(res, "Should list only the 'Concert' transaction.")

        res = self.make_request("GET", "/transactions/by-source/vpbank_api")
        self.log_test("Filter by Source ('vpbank_api')", res and res.status_code == 200 and len(res.json()) == 1 and res.json()[0]['source'] == 'vpbank_api')
        self.pause_and_check(res, "Should list only the 'Concert' transaction.")

        res = self.make_request("GET", "/transactions/by-amount-range", params={"min_amount": 50, "max_amount": 100})
        self.log_test("Filter by Amount (50-100)", res and res.status_code == 200 and len(res.json()) == 1 and res.json()[0]['amount'] == 75.50)
        self.pause_and_check(res, "Should list only the 'Concert' transaction (75.50).")

        start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        res = self.make_request("GET", "/transactions/by-date-range", params={"start_date": start})
        self.log_test("Filter by Date Range (start only)", res and res.status_code == 200 and len(res.json()) == 2)
        self.pause_and_check(res, "Should list 'Concert' and 'Invest' transactions (from 5 days ago and 1 day ago).")
        
        res = self.make_request("GET", "/transactions/by-date-range", params={"start_date": "not-a-date"})
        self.log_test("Filter by Date (Invalid)", res and res.status_code == 400)
        self.pause_and_check(res, "Should return a 400 Bad Request for invalid date format.")

        return True

    def cleanup(self):
        """Removes all items created during the test run."""
        print("\n" + "="*60 + "\n🧹 STAGE: CLEANUP\n" + "="*60)
        if not self.token:
            print("No token, skipping cleanup.")
            return

        tx_ids_to_delete = self.created_item_ids.get("transactions", [])
        if not tx_ids_to_delete:
            print("No transactions to clean up.")
            return

        print(f"Attempting to delete {len(tx_ids_to_delete)} created transactions...")
        deleted_count = 0
        for tx_id in tx_ids_to_delete:
            # We don't check the response of GET /transactions/{tx_id} as it might have been deleted by the test itself
            res = self.make_request("DELETE", f"/transactions/{tx_id}")
            if res and res.status_code in [204, 404]: # 404 is ok if already deleted
                deleted_count += 1
        print(f"Successfully cleaned up {deleted_count}/{len(tx_ids_to_delete)} transactions.")


    def run_all_tests(self):
        """Executes all testing stages in a sequential workflow."""
        if not self.run_stage("Setup Test User", self.setup_test_user):
            self.cleanup()
            return
        
        workflow = [
            ("Transaction Lifecycle & Side-Effects", self.test_transaction_lifecycle),
            ("Transaction Filters (Date, Amount, Source, Jar)", self.test_all_filters),
        ]
        
        for name, func in workflow:
            if not self.run_stage(name, func): 
                print(f"Stopping tests due to failure in stage: {name}")
                break
        
        self.cleanup()
        
        print("\n" + "="*60 + "\n📊 FINAL TEST REPORT\n" + "="*60)
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        if total > 0:
            print(f"Total Steps: {total}, Passed: {passed}, Failed: {total - passed}")
            print(f"Success Rate: {(passed/total)*100:.2f}%")
        else:
            print("No tests were run.")


if __name__ == "__main__":
    print("🚀 Starting VPBank Transaction API Comprehensive Test")
    print("   Server should be running at http://127.0.0.1:8000")
    tester = TransactionAPITester()
    tester.run_all_tests()
    print("\n🎉 Testing workflow completed!")