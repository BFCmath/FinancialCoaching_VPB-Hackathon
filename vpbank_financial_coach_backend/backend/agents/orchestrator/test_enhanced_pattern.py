"""
Test Enhanced Pattern 2 Orchestrator Implementation
==================================================

Tests that the orchestrator properly routes to Enhanced Pattern 2 agents.
"""

import asyncio
import sys
import os

# Add the parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from backend.agents.orchestrator.main import process_task_async
from backend.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient


async def test_orchestrator():
    """Test basic orchestrator routing functionality."""
    
    # Mock database connection (for testing)
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_db
    user_id = "test_user_123"
    
    print("🧪 Testing Enhanced Pattern 2 Orchestrator")
    print("=" * 50)
    
    test_cases = [
        "Hello, how are you?",  # Should use provide_direct_response
        "I spent $25 on lunch",  # Should route to classifier
        "Create a vacation jar",  # Should route to jar manager
        "What is compound interest?",  # Should route to knowledge
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_input}'")
        print("-" * 40)
        
        try:
            result = await process_task_async(test_input, user_id, db)
            print(f"✅ Response: {result['response']}")
            print(f"📝 Follow-up needed: {result.get('requires_follow_up', False)}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Testing complete!")
    
    # Clean up
    client.close()


if __name__ == "__main__":
    # Check if we have the required API key
    if not settings.GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY not found in environment!")
        print("Please set GOOGLE_API_KEY environment variable to test.")
        exit(1)
    
    # Run the test
    asyncio.run(test_orchestrator())
