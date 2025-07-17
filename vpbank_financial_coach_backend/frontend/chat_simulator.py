#!/usr/bin/env python3
"""
VPBank Financial Coach - Interactive Chat Simulator
==================================================

A simple interactive chat simulator to test the VPBank Financial Coach API.
This script handles authentication and provides a clean chat interface.

Usage:
    python chat_simulator.py

Requirements:
    - Backend server running on http://127.0.0.1:8000
    - 'requests' library: pip install requests
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone

class VPBankChatSimulator:
    """Simple chat simulator for VPBank Financial Coach API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.user_data = {}
        self.conversation_count = 0

    def make_request(self, method: str, endpoint: str, data=None, params=None, use_auth=True):
        """Make HTTP request to the API."""
        url = f"{self.api_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if "token" in endpoint:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                if "token" in endpoint:
                    response = requests.post(url, data=data, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
            
        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to server. Is it running on http://127.0.0.1:8000?")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return None

    def authenticate(self):
        """Handle user authentication - login or register."""
        print("🔐 VPBank Financial Coach - Authentication")
        print("=" * 50)
        
        while True:
            choice = input("\nChoose an option:\n1. Login with existing account\n2. Create new account\n3. Exit\nEnter choice (1-3): ").strip()
            
            if choice == "3":
                print("👋 Goodbye!")
                sys.exit(0)
            elif choice == "1":
                if self.login():
                    return True
            elif choice == "2":
                if self.register():
                    return True
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")

    def register(self):
        """Register a new user."""
        print("\n📝 Create New Account")
        print("-" * 30)
        
        try:
            username = input("Username: ").strip()
            if len(username) < 3:
                print("❌ Username must be at least 3 characters long.")
                return False
            
            email = input("Email: ").strip()
            if "@" not in email:
                print("❌ Please enter a valid email address.")
                return False
            
            password = input("Password (min 8 characters): ").strip()
            if len(password) < 8:
                print("❌ Password must be at least 8 characters long.")
                return False
            
            user_data = {
                "username": username,
                "email": email,
                "password": password
            }
            
            print("\n🔄 Creating account...")
            response = self.make_request("POST", "/auth/register", user_data, use_auth=False)
            
            if not response:
                return False
            
            if response.status_code == 201:
                print("✅ Account created successfully!")
                self.user_data = user_data
                return self.login()
            else:
                try:
                    error_data = response.json()
                    print(error_data)
                    print(f"❌ Registration failed: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"❌ Registration failed with status {response.status_code}")
                return False
                
        except KeyboardInterrupt:
            print("\n👋 Registration cancelled.")
            return False

    def login(self):
        """Login with user credentials."""
        print("\n🔑 Login")
        print("-" * 15)
        
        try:
            if not hasattr(self, 'user_data') or not self.user_data:
                username = input("Username: ").strip()
                password = input("Password: ").strip()
            else:
                username = self.user_data.get("username")
                password = self.user_data.get("password")
                print(f"Logging in as: {username}")
            
            login_data = {
                "username": username,
                "password": password
            }
            
            print("🔄 Logging in...")
            response = self.make_request("POST", "/auth/token", login_data, use_auth=False)
            
            if not response:
                return False
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                print("✅ Login successful!")
                
                # Test the token by getting user info
                response = self.make_request("GET", "/auth/me")
                if response and response.status_code == 200:
                    user_info = response.json()
                    print(f"👋 Welcome back, {user_info.get('username')}!")
                    return True
                else:
                    print("❌ Token validation failed.")
                    return False
            else:
                print("❌ Invalid username or password.")
                return False
                
        except KeyboardInterrupt:
            print("\n👋 Login cancelled.")
            return False

    def show_help(self):
        """Show available commands and examples."""
        print("\n💡 Available Commands and Examples:")
        print("=" * 50)
        print("🏺 Jar Operations:")
        print("  • What's my balance in the play jar?")
        print("  • Show me all my jars")
        print("  • How much have I spent from my necessities jar?")
        print()
        print("💰 Transaction Operations:")
        print("  • Add a $25 transaction to my education jar for books")
        print("  • Add $150 to my necessities jar for groceries")
        print("  • Show my recent transactions")
        print()
        print("🔄 Fee Management:")
        print("  • Show me my recurring fees")
        print("  • What fees are due today?")
        print("  • Create a monthly Netflix fee for $15.99 in my play jar")
        print()
        print("📋 Budget Planning:")
        print("  • Show my budget plans")
        print("  • Create a plan to save for vacation")
        print("  • What's my emergency fund plan status?")
        print()
        print("📊 Analysis:")
        print("  • Analyze my spending patterns")
        print("  • How much money do I have in total?")
        print("  • Give me financial advice")
        print()
        print("🎮 Special Commands:")
        print("  • help - Show this help")
        print("  • history - Show conversation history")
        print("  • clear - Clear screen")
        print("  • exit - Quit the simulator")

    def show_history(self):
        """Show conversation history."""
        print("\n📚 Conversation History")
        print("=" * 30)
        
        response = self.make_request("GET", "/chat/history", params={"limit": 10})
        
        if not response or response.status_code != 200:
            print("❌ Failed to retrieve conversation history.")
            return
        
        try:
            history = response.json()
            if not history:
                print("No conversation history found.")
                return
            
            for i, turn in enumerate(history[-5:], 1):  # Show last 5 conversations
                print(f"\n{i}. 💬 You: {turn['user_input']}")
                print(f"   🤖 Bot: {turn['agent_output'][:150]}{'...' if len(turn['agent_output']) > 150 else ''}")
                
                if turn.get('agent_list'):
                    print(f"   🔧 Agents: {', '.join(turn['agent_list'])}")
                    
        except json.JSONDecodeError:
            print("❌ Failed to parse conversation history.")

    def clear_screen(self):
        """Clear the terminal screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def chat_loop(self):
        """Main interactive chat loop."""
        print("\n" + "=" * 60)
        print("💬 VPBank Financial Coach - Interactive Chat")
        print("=" * 60)
        print("Type your questions about your finances. Type 'help' for examples.")
        print("Type 'exit' to quit, 'history' to see past conversations.")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() == 'exit':
                    print("👋 Thanks for using VPBank Financial Coach!")
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'history':
                    self.show_history()
                    continue
                elif user_input.lower() == 'clear':
                    self.clear_screen()
                    continue
                
                # Send message to chat API
                print("🤖 Thinking...")
                
                response = self.make_request("POST", "/chat/", {"message": user_input})
                
                if not response:
                    print("❌ Failed to get response from server")
                    continue
                
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        print(f"❌ Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        print(f"❌ Error {response.status_code}: {response.text}")
                    continue
                
                try:
                    chat_response = response.json()
                    self.conversation_count += 1
                    
                    print(f"\n🤖 Assistant:")
                    print(f"   {chat_response.get('agent_output', 'No response available')}")
                    
                    # Show agent info if available
                    agents = chat_response.get('agent_list', [])
                    if agents:
                        print(f"\n🔧 Handled by: {', '.join(agents)}")
                    
                    # Show tools used if available
                    tools = chat_response.get('tool_call_list', [])
                    if tools:
                        print(f"🛠️  Tools used: {', '.join(tools[:3])}{'...' if len(tools) > 3 else ''}")
                    
                except json.JSONDecodeError:
                    print("❌ Invalid response from server")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Thanks for using VPBank Financial Coach!")
                break
            except EOFError:
                print("\n\n👋 Chat ended. Thanks for using VPBank Financial Coach!")
                break
        
        if self.conversation_count > 0:
            print(f"\n📊 Session Summary: {self.conversation_count} messages exchanged")

    def run(self):
        """Main entry point."""
        print("🏦 VPBank Financial Coach - Chat Simulator")
        print("=" * 50)
        print("Welcome to your personal financial assistant!")
        print("First, let's get you authenticated...")
        
        # Check server connectivity
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code != 200:
                print("⚠️  Warning: Server might not be fully ready")
        except:
            print("❌ Cannot connect to server. Make sure it's running on http://127.0.0.1:8000")
            return
        
        # Authenticate user
        if not self.authenticate():
            print("❌ Authentication failed. Cannot start chat.")
            return
        
        # Start chat loop
        self.chat_loop()


def main():
    """Main function."""
    try:
        simulator = VPBankChatSimulator()
        simulator.run()
    except KeyboardInterrupt:
        print("\n\n👋 Simulator interrupted. Goodbye!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("Please check that the backend server is running and try again.")


if __name__ == "__main__":
    main()