"""
Budget Advisor Tools - Transaction Fetcher Interface
==================================================

Single tool interface to the transaction fetcher agent.
"""

import json
import sys
import os
from langchain_core.tools import tool
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

# Budget Plan Storage
BUDGET_PLANS_STORAGE: Dict[str, Dict] = {}

@dataclass
class BudgetPlan:
    """Simple budget plan structure"""
    name: str
    detail_description: str
    day_created: str
    status: str = "active"
    
    def to_dict(self):
        return asdict(self)

@tool
def transaction_fetcher(user_query: str, description: str = "") -> Dict[str, Any]:
    """
    Call transaction fetcher agent to retrieve spending data.
    
    Args:
        user_query: Natural language transaction query
            Examples: "groceries spending", "lunch transactions 11am-2pm under $20", "ăn trưa dưới 20 đô"
        description: Context for what data is needed (optional)
    
    Returns:
        Dictionary with:
        - data: List of transaction dictionaries
        - description: Summary of retrieved data
    """
    
    # Direct import from the data agent's tools to avoid main.py import conflicts
    from tool_agent.data.tools import get_jar_transactions
    
    # For now, use a simple approach - call get_jar_transactions for all transactions
    # The LLM agent will call this tool and interpret the user_query contextually
    result = get_jar_transactions.invoke({
        "description": description or f"transaction query: {user_query}"
    })
    
    return result


@tool
def get_plan(status: str = "active", description: str = "") -> Dict[str, Any]:
    """
    Retrieve budget plans by status.
    
    Args:
        status: Plan status - "active" (default), "completed", "paused", "all"
        description: Context for what plan info is needed
    
    Returns:
        Dictionary with:
        - data: List of budget plans matching status
        - description: Summary of retrieved plans
    """
    if status == "all":
        plans = list(BUDGET_PLANS_STORAGE.values())
    else:
        plans = [p for p in BUDGET_PLANS_STORAGE.values() if p.get("status") == status]
    
    return {
        "data": plans,
        "description": description or f"retrieved {len(plans)} {status} plans"
    }

@tool
def adjust_plan(name: str, description: str = None, status: str = None, jar_propose_adjust_details: str = None) -> Dict[str, Any]:
    """
    Modify existing budget plan with comprehensive jar adjustment proposals.
    
    Args:
        name: Plan name to modify
        description: New description (optional)
        status: New status - "active", "completed", "paused" (optional)
        jar_propose_adjust_details: DETAILED and COMPREHENSIVE jar adjustments needed for this plan update. (should have a reason to change)
            
    Returns:
        Dictionary with:
        - data: Updated plan with jar proposals
        - description: Summary of changes made and jar recommendations
    """
    if name not in BUDGET_PLANS_STORAGE:
        return {"data": {}, "description": f"plan {name} not found"}
    
    plan = BUDGET_PLANS_STORAGE[name].copy()
    changes = []
    
    # Update description if provided
    if description is not None:
        old_desc = plan["detail_description"]
        plan["detail_description"] = description
        changes.append(f"description: {old_desc} → {description}")
    
    # Update status if provided
    if status is not None:
        old_status = plan["status"]
        plan["status"] = status
        changes.append(f"status: {old_status} → {status}")
    
    # Save updated plan
    BUDGET_PLANS_STORAGE[name] = plan
    
    # Build response with jar recommendations
    response_data = plan.copy()
    description_parts = [f"updated plan {name}: {', '.join(changes) if changes else 'no changes made'}"]
    
    if jar_propose_adjust_details:
        response_data["jar_recommendations"] = jar_propose_adjust_details
        description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
    
    return {
        "data": response_data,
        "description": " | ".join(description_parts)
    }

@tool
def create_plan(name: str, description: str, status: str = "active", jar_propose_adjust_details: str = None) -> Dict[str, Any]:
    """
    Create a new budget plan with comprehensive jar adjustment proposals.
    
    Args:
        name: Plan name (must be unique)
        description: Plan description 
        status: Plan status - "active" (default), "completed", "paused"
        jar_propose_adjust_details: DETAILED jar adjustments needed for this plan. (should have a reason to change)
        
    Returns:
        Dictionary with:
        - data: Created plan with jar proposals
        - description: Summary of plan creation and jar recommendations
    """
    if name in BUDGET_PLANS_STORAGE:
        return {"data": {}, "description": f"plan {name} already exists"}
    
    plan = BudgetPlan(
        name=name,
        detail_description=description,
        day_created=datetime.now().isoformat(),
        status=status
    )
    
    BUDGET_PLANS_STORAGE[name] = plan.to_dict()
    
    # Build response with jar recommendations
    response_data = plan.to_dict()
    description_parts = [f"created plan {name} with status {status}"]
    
    if jar_propose_adjust_details:
        response_data["jar_recommendations"] = jar_propose_adjust_details
        description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
    
    return {
        "data": response_data,
        "description": " | ".join(description_parts)
    }

@tool  
def get_jar(jar_name: str = None, description: str = "") -> Dict[str, Any]:
    """
    Get jar allocations and status.
    
    Args:
        jar_name: Specific jar name (optional) - "groceries", "meals", etc.
        description: Context for jar analysis needed
    
    Returns:
        Dictionary with:
        - data: List of jar information
        - description: Summary of jar status
    """
    # Direct import to avoid conflicts - use importlib to load specific module
    import importlib.util
    import os
    
    jar_tools_path = os.path.join(os.path.dirname(__file__), 'tool_agent', 'jar', 'tools.py')
    spec = importlib.util.spec_from_file_location("jar_tools", jar_tools_path)
    jar_tools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jar_tools)
    
    fetch_existing_jars = jar_tools.fetch_existing_jars
    
    # Get jar data
    if jar_name:
        # For specific jar, filter the results
        all_jars = fetch_existing_jars()
        jars = [jar for jar in all_jars if jar.get("name", "").lower() == jar_name.lower()]
    else:
        jars = fetch_existing_jars()
    
    if not jars:
        return {"data": [], "description": f"no jars found" + (f" for {jar_name}" if jar_name else "")}
    
    return {
        "data": jars,
        "description": description or f"retrieved {len(jars)} jars" + (f" for {jar_name}" if jar_name else "")
    }

@tool
def respond(summary: str, advice: str = None, question_ask_user: str = None) -> Dict[str, Any]:
    """
    Provide final advisory response to user with optional follow-up question.
    
    Args:
        summary: Analysis summary of financial situation
        advice: Personalized recommendations (optional)
        question_ask_user: Follow-up question to ask the user for more information when the user's plan is not clear (optional)
    
    Returns:
        Dictionary with:
        - data: Advisory response with summary, advice, and optional question
        - description: Summary of response provided
    """
    if not summary.strip():
        return {"data": {}, "description": "missing summary"}
    
    response_data = {"summary": summary}
    if advice is not None:
        response_data["advice"] = advice
    if question_ask_user is not None:
        response_data["question_ask_user"] = question_ask_user
    
    description_parts = ["advisory response with summary"]
    if advice:
        description_parts.append("advice")
    if question_ask_user:
        description_parts.append("follow-up question")
    
    return {
        "data": response_data,
        "description": " and ".join(description_parts)
    }



