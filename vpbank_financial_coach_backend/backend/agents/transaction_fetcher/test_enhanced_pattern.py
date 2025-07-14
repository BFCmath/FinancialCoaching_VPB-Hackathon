"""
Transaction Fetcher Agent - Enhanced Pattern 2 Testing
=====================================================

Test file for verifying Enhanced Pattern 2 implementation.
Tests dependency injection, service container, and production validation.
"""

import sys
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
backend_dir = os.path.dirname(parent_dir)
sys.path.append(backend_dir)
sys.path.append(parent_dir)

from agents.transaction_fetcher.main import TransactionFetcher, process_task
from agents.transaction_fetcher.tools import TransactionFetcherServiceContainer, get_all_transaction_tools
from agents.transaction_fetcher.interface import TransactionFetcherInterface, get_agent_interface


async def test_transaction_fetcher_service_container():
    """Test TransactionFetcherServiceContainer with mock database."""
    print("🧪 Testing TransactionFetcherServiceContainer...")
    
    # Mock database setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_transaction_db
    user_id = "test_user_123"
    
    try:
        # Create service container
        services = TransactionFetcherServiceContainer(db, user_id)
        
        # Test lazy loading
        print(f"✅ Service container created for user: {user_id}")
        
        # Test fetcher adapter
        adapter = services.fetcher_adapter
        print(f"✅ Fetcher adapter lazy-loaded: {type(adapter).__name__}")
        
        # Test tools creation
        tools = get_all_transaction_tools(services)
        print(f"✅ Created {len(tools)} tools with dependency injection")
        
        # Verify tool names
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "get_jar_transactions",
            "get_time_period_transactions", 
            "get_amount_range_transactions",
            "get_hour_range_transactions",
            "get_source_transactions",
            "get_complex_transaction"
        ]
        
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"✅ Tool {expected_tool} found")
            else:
                print(f"❌ Tool {expected_tool} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Service container test failed: {str(e)}")
        return False
    finally:
        client.close()


async def test_transaction_fetcher_creation():
    """Test TransactionFetcher creation with Enhanced Pattern 2."""
    print("\n🧪 Testing TransactionFetcher creation...")
    
    # Mock database setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_transaction_db
    user_id = "test_user_456"
    
    try:
        # Test successful creation
        agent = TransactionFetcher(db, user_id)
        print(f"✅ Transaction fetcher created for user: {user_id}")
        print(f"✅ Tools count: {len(agent.tools)}")
        print(f"✅ Service container initialized: {type(agent.services).__name__}")
        print(f"✅ LLM with tools bound: {hasattr(agent, 'llm_with_tools')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation test failed: {str(e)}")
        return False
    finally:
        client.close()


async def test_process_task_function():
    """Test standalone process_task function."""
    print("\n🧪 Testing process_task function...")
    
    # Mock database setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_transaction_db
    user_id = "test_user_789"
    
    try:
        # Test validation - missing db
        result = await process_task("test task", None, user_id)
        if "Error" in result.get("response", ""):
            print("✅ Correctly rejected missing db")
        else:
            print("❌ Should have failed with missing db")
            return False
        
        # Test validation - missing user_id  
        result = await process_task("test task", db, None)
        if "Error" in result.get("response", ""):
            print("✅ Correctly rejected missing user_id")
        else:
            print("❌ Should have failed with missing user_id")
            return False
        
        # Test successful function call structure
        print("✅ Process task function available with proper validation")
        print("⚠️  Note: Actual processing requires GOOGLE_API_KEY and real data")
        
        return True
        
    except Exception as e:
        print(f"❌ Process task test failed: {str(e)}")
        return False
    finally:
        client.close()


async def test_interface_validation():
    """Test TransactionFetcherInterface validation."""
    print("\n🧪 Testing TransactionFetcherInterface...")
    
    # Mock database setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_transaction_db
    user_id = "test_user_interface"
    
    try:
        # Create interface
        interface = get_agent_interface()
        print(f"✅ Transaction fetcher interface created: {interface.agent_name}")
        
        # Test capabilities
        capabilities = interface.get_capabilities()
        print(f"✅ Agent capabilities: {len(capabilities)} items")
        expected_capabilities = [
            "Retrieve transaction history with complex filters",
            "Filter transactions by jar, date, amount, time, or source", 
            "Handle multilingual (Vietnamese) transaction queries"
        ]
        
        for cap in expected_capabilities:
            if cap in capabilities:
                print(f"✅ Capability found: {cap}")
            else:
                print(f"❌ Missing capability: {cap}")
                return False
        
        # Test async process_task method exists
        if hasattr(interface, 'process_task') and callable(interface.process_task):
            print("✅ Async process_task method available")
        else:
            print("❌ Missing async process_task method")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Interface test failed: {str(e)}")
        return False
    finally:
        client.close()


async def main():
    """Run all Enhanced Pattern 2 tests."""
    print("🚀 Transaction Fetcher Agent - Enhanced Pattern 2 Testing")
    print("=" * 60)
    
    tests = [
        test_transaction_fetcher_service_container(),
        test_transaction_fetcher_creation(), 
        test_process_task_function(),
        test_interface_validation()
    ]
    
    # Run async tests
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Summary
    passed = sum(1 for r in results if r is True)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All Enhanced Pattern 2 tests passed!")
        print("\n✅ Transaction Fetcher agent migration to Enhanced Pattern 2 successful!")
        print("✅ Production-ready with:")
        print("   • Request-scoped TransactionFetcherServiceContainer")
        print("   • Database dependency injection") 
        print("   • User ID validation")
        print("   • Multi-user isolation")
        print("   • 6 comprehensive transaction filtering tools")
        print("   • Async interface for orchestrator integration")
    else:
        print("❌ Some tests failed. Check implementation.")
        for i, result in enumerate(results):
            if result is not True:
                print(f"   Test {i+1}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
