"""
Budget Advisor Agent Tools
==========================

Tools for the ReAct-based financial planning and advisory agent.
These tools integrate with the unified service layer to manage budget plans,
communicate with other agents, and access data directly.
"""

import sys
import os
import json

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_core.tools import tool
from typing import Optional, Dict, Any, List

# Import from our unified service layer and utils
from service import get_plan_service, get_communication_service, get_jar_service
from utils import get_jar as get_jar_from_db, get_all_jars
from database import TOTAL_INCOME

# Get service instances
plan_service = get_plan_service()
communication_service = get_communication_service()
jar_service = get_jar_service()

@tool
def transaction_fetcher(user_query: str, description: str) -> Dict[str, Any]:
    """
    Calls the Transaction Fetcher agent to retrieve user spending data for analysis.
    This is the primary tool for understanding a user's financial habits and history.
    It is essential to use this tool before providing any spending-related advice.

    Args:
        user_query: A natural language query describing the transactions to fetch.
                    Examples: "spending on groceries last month", "how much did I spend on coffee",
                    "tôi đã chi bao nhiêu cho việc đi lại trong tuần này"
        description: A brief explanation of why you are fetching this data.
                     Example: "To analyze the user's monthly spending on non-essential items."

    Returns:
        A dictionary containing the fetched transaction data and a summary.
    """
    return communication_service.call_transaction_fetcher(
        user_query=user_query,
        description=description
    )

@tool
def get_jar(jar_name: Optional[str] = None, description: str = "") -> Dict[str, Any]:
    """
    Retrieves the user's current budget jar allocations and balances directly from the database.
    Returns all jars if no name is provided. You MUST use this tool to see the user's budget structure before creating or adjusting plans.
    Also includes the total income for reference in calculations.

    Args:
        jar_name: The specific name of a jar to query. Example: "Savings", "Necessities".
                  If not provided, all jars are returned.
        description: A brief explanation of why you need this jar information.
                     Example: "To check the current balance of the 'Play' jar before making a recommendation."

    Returns:
        A dictionary containing a list of jar data, the total income, and a summary.
    """
    if jar_name:
        jar = get_jar_from_db(jar_name.lower().replace(' ', '_'))
        if not jar:
            return {"data": [], "total_income": TOTAL_INCOME, "description": f"jar '{jar_name}' not found"}
        
        jar_data = [jar.to_dict()]
        description_text = f"Retrieved information for the '{jar_name}' jar."
    else:
        jars = get_all_jars()
        jar_data = [j.to_dict() for j in jars]
        description_text = "Retrieved information for all budget jars."

    return {
        "data": jar_data,
        "total_income": TOTAL_INCOME,
        "description": description or description_text
    }

@tool
def get_plan(status: str = "active", description: str = "") -> Dict[str, Any]:
    """
    Retrieves existing budget plans from the Plan Service, filtered by their status.
    Use this to understand the user's existing financial goals.

    Args:
        status: The status of plans to retrieve.
                - "active": (Default) Plans the user is currently working on.
                - "completed": Plans the user has finished.
                - "paused": Plans that are temporarily on hold.
                - "all": All plans regardless of status.
        description: A brief explanation for the query. Example: "Checking for existing saving plans."

    Returns:
        A dictionary containing a list of plans and a summary.
    """
    return plan_service.get_plan(status=status, description=description)

@tool
def create_plan(name: str, description: str, jar_changes: str, status: str = "active") -> Dict[str, Any]:
    """
    Creates a new budget plan, this should be used after the user have accepted the proposed plan and jar changes.
    Use this to establish a new financial goal, such as saving for a vacation or paying off debt.

    Args:
        name: A unique, descriptive name for the plan. Example: "Japan Vacation Fund".
        description: A detailed description of the plan's purpose and goals.
        status: The initial status of the plan, usually "active".
        jar_changes: A DETAILED, ACTIONABLE command for how the user's budget jars
                     should be changed to support this plan. This must be in a format that can be directly sent to the Jar Manager (e.g., JSON with jar names, percentages, amounts, and rebalancing instructions).

    Returns:
        A dictionary containing the newly created plan data.
    """
    return plan_service.create_plan(
        name=name,
        description=description,
        status=status,
        jar_propose_adjust_details=jar_changes  # Renamed internally to match service, but detailed as command
    )

@tool
def adjust_plan(name: str,  description: str, jar_changes: str, status: Optional[str] = None) -> Dict[str, Any]:
    """
    Modifies an existing budget plan, this should be used when the user wants to update an existing plan or change jar allocations.
    This is useful for adjusting goals based on new financial data or user feedback.
    Use this to update a plan's details, mark it as complete, or change jar allocations.

    Args:
        name: The name of the existing plan to modify.
        description: A new, updated description for the plan.
        status: A new status for the plan (e.g., "completed", "paused").
        jar_changes: A DETAILED, ACTIONABLE command for jar adjustments. This must be in a format that can be directly sent to the Jar Manager (e.g., JSON with jar names, percentages, amounts, and rebalancing instructions).

    Returns:
        A dictionary containing the updated plan data.
    """
    return plan_service.adjust_plan(
        name=name,
        description=description,
        status=status,
        jar_propose_adjust_details=jar_changes  # Renamed internally, detailed as command
    )

@tool
def request_clarification(question: str, suggestion: Optional[str] = None) -> Dict[str, Any]:
    """
    Requests clarification from the user about their financial goals or plan details.
    This tool is used when the agent needs more information to proceed with plan creation or adjustment.
    Information you should ask:
    + The purpose of the plan
    + How much they want to save per month
    
    Avoid asking irrelevant questions like who user gonna travel with, or what they want to do on vacation, or how long they spend on vacation, ...
    
    Args:
        question: The specific question to ask the user to clarify their needs.
        suggestion: Optional suggestions to help the user respond, such as examples or formats.
    """
    from database import set_active_agent_context
    set_active_agent_context("budget_advisor")
    response = f"❓ {question}"
    if suggestion:
        response += f"\n💡 {suggestion}"
    return {"response": response, "requires_follow_up": True, "stage": "1"}  # Stay current

@tool
def propose_plan(financial_plan: str, jar_changes: str) -> Dict[str, Any]:
    """
    Proposes a new financial plan and jar changes plan based on the user's goals and current budget jars.
    This tool MUST BE USED after gathering all necessary information and clarifying the user's needs.
    
    Args:
        financial_plan: A detailed proposal for the plan, including financial goals and strategies.
        jar_changes: A detailed proposal for changes to jars aligned with financial_plan, such as new allocations or adjustments to existing jars.
    """
    from database import set_active_agent_context
    set_active_agent_context("budget_advisor")
    return {"financial_plan": financial_plan, "jar_changes": jar_changes, "requires_follow_up": True, "stage": "2"}

def get_stage1_tools() -> List[tool]:
    return [transaction_fetcher, get_jar, get_plan, request_clarification, propose_plan]

def get_stage2_tools() -> List[tool]:
    return [transaction_fetcher, get_jar, get_plan, propose_plan]

def get_stage3_tools() -> List[tool]:
    return [create_plan, adjust_plan]  # Removed apply_changes