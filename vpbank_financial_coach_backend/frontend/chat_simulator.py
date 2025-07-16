#!/usr/bin/env python3
"""
VPBank Financial Coach - Interactive Chat Simulator
===================================================

A simple interactive chat simulator for testing the financial coach backend.
This script allows you to have a real-time conversation with the agent system.

Usage:
    python chat_simulator.py

Requirements:
    - Backend server running on http://127.0.0.1:8000
    - 'requests' library: pip install requests
"""

import sys
import os

# Add the frontend directory to the path to import mock module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the interactive chat function
try:
    from frontend.mock import run_interactive_chat
except ImportError:
    print("❌ Error: Could not import mock.py. Make sure this script is in the same directory as mock.py")
    sys.exit(1)

if __name__ == "__main__":
    print("🤖 VPBank Financial Coach - Interactive Chat Simulator")
    print("="*60)
    print("This tool allows you to chat directly with the financial coach agent.")
    print("Perfect for testing agent responses and workflows in real-time.")
    print("="*60)
    
    # Check if user wants to proceed
    try:
        proceed = input("\nReady to start? (y/n): ").strip().lower()
        if proceed in ['y', 'yes', '']:
            run_interactive_chat()
        else:
            print("👋 Maybe next time!")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
