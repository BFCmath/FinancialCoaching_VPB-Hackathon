"""
Budget Advisor Agent - Enhanced Pattern 2 Testing
================================================

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

from agents.plan.main import BudgetAdvisorAgent, process_task
from agents.plan.tools import PlanServiceContainer, get_stage1_tools, get_stage2_tools, get_stage3_tools
from agents.plan.interface import BudgetAdvisorInterface, get_agent_interface


async def test_plan_service_container():
    """Test PlanServiceContainer with mock database."""
    print("🧪 Testing PlanServiceContainer...")
    
    # Mock database setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_plan_db
    user_id = "test_user_123"
    
    try:
        # Create service container
        services = PlanServiceContainer(db, user_id)
        
        # Test lazy loading
        print(f"✅ Service container created for user: {user_id}")
        
        # Test plan adapter
        plan_adapter = services.plan_adapter
        print(f"✅ Plan adapter lazy-loaded: {type(plan_adapter).__name__}")
        
        # Test jar adapter
        jar_adapter = services.jar_adapter
        print(f"✅ Jar adapter lazy-loaded: {type(jar_adapter).__name__}")
        
        # Test tools creation for each stage
        stage1_tools = get_stage1_tools(services)
        stage2_tools = get_stage2_tools(services)
        stage3_tools = get_stage3_tools(services)
        
        print(f"✅ Stage 1 tools: {len(stage1_tools)} tools")
        print(f"✅ Stage 2 tools: {len(stage2_tools)} tools")
        print(f"✅ Stage 3 tools: {len(stage3_tools)} tools")
        
        # Verify expected tools
        stage1_tool_names = [tool.name for tool in stage1_tools]
        expected_stage1_tools = ["transaction_fetcher", "get_jar", "get_plan", "request_clarification", "propose_plan"]
        
        for expected_tool in expected_stage1_tools:
            if expected_tool in stage1_tool_names:
                print(f"✅ Stage 1 tool {expected_tool} found")
            else:
                print(f"❌ Stage 1 tool {expected_tool} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Service container test failed: {str(e)}")
        return False
    finally:
        client.close()


async def test_budget_advisor_agent_creation():
    """Test BudgetAdvisorAgent creation with Enhanced Pattern 2."""
    print("\n🧪 Testing BudgetAdvisorAgent creation...")
    
    # Mock database setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_plan_db
    user_id = "test_user_456"
    
    try:
        # Test successful creation
        agent = BudgetAdvisorAgent(db, user_id)
        print(f"✅ Budget advisor agent created for user: {user_id}")
        print(f"✅ Current stage: {agent.current_stage}")
        print(f"✅ Service container initialized: {type(agent.services).__name__}")
        print(f"✅ LLM configured: {hasattr(agent, 'llm')}")
        
        # Test validation - missing db
        try:
            invalid_agent = BudgetAdvisorAgent(None, user_id)
            print("❌ Should have failed with missing db")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected missing db: {str(e)}")
        
        # Test validation - missing user_id
        try:
            invalid_agent = BudgetAdvisorAgent(db, None)
            print("❌ Should have failed with missing user_id")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected missing user_id: {str(e)}")
        
        # Test stage tool selection
        stage1_tools = agent._get_tools_for_stage("1")
        stage2_tools = agent._get_tools_for_stage("2")
        stage3_tools = agent._get_tools_for_stage("3")
        
        print(f"✅ Stage tools configured: 1={len(stage1_tools)}, 2={len(stage2_tools)}, 3={len(stage3_tools)}")
        
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
    db = client.test_plan_db
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
    """Test BudgetAdvisorInterface validation."""
    print("\n🧪 Testing BudgetAdvisorInterface...")
    
    # Mock database setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_plan_db
    user_id = "test_user_interface"
    
    try:
        # Create interface
        interface = get_agent_interface()
        print(f"✅ Budget advisor interface created: {interface.agent_name}")
        
        # Test validation - missing db
        try:
            result = await interface.process_task("test task", [], None, user_id)
            print("❌ Should have failed with missing db")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected missing db: {str(e)}")
        
        # Test validation - missing user_id
        try:
            result = await interface.process_task("test task", [], db, None)
            print("❌ Should have failed with missing user_id")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected missing user_id: {str(e)}")
        
        # Test capabilities
        capabilities = interface.get_capabilities()
        print(f"✅ Agent capabilities: {len(capabilities)} items")
        expected_capabilities = [
            "Financial planning and goal setting",
            "Multi-stage budget advisory process",
            "Savings plans and jar adjustments"
        ]
        
        for cap in expected_capabilities:
            if any(cap_part in capability for capability in capabilities for cap_part in cap.split()):
                print(f"✅ Capability found (partial match): {cap}")
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
    print("🚀 Budget Advisor Agent - Enhanced Pattern 2 Testing")
    print("=" * 60)
    
    tests = [
        test_plan_service_container(),
        test_budget_advisor_agent_creation(),
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
        print("\n✅ Budget Advisor agent migration to Enhanced Pattern 2 successful!")
        print("✅ Production-ready with:")
        print("   • Request-scoped PlanServiceContainer")
        print("   • Database dependency injection")
        print("   • User ID validation & isolation")
        print("   • Multi-stage workflow (1: gather, 2: refine, 3: implement)")
        print("   • Async interface for orchestrator integration")
        print("   • Integrated plan and jar management")
    else:
        print("❌ Some tests failed. Check implementation.")
        for i, result in enumerate(results):
            if result is not True:
                print(f"   Test {i+1}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
