"""
Budget Advisor (Plan Test) Agent Tools
=========================================

Tools for the ReAct-based financial planning and advisory agent.
These tools integrate with the unified service layer to manage budget plans,
communicate with other agents, and access data directly.
"""

import sys
import os

# Add parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(parent_dir)

from langchain_core.tools import tool
from typing import Optional, Dict, Any, List

# Import from our unified service layer and utils
from service import get_plan_service, get_communication_service
from utils import get_jar as get_jar_from_db, get_all_jars

# Get service instances
plan_service = get_plan_service()
communication_service = get_communication_service()


# =============================================================================
# AGENT COMMUNICATION TOOLS
# =============================================================================

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

# =============================================================================
# DIRECT DATA ACCESS TOOLS
# =============================================================================

@tool
def get_jar(jar_name: Optional[str] = None, description: str = "") -> Dict[str, Any]:
    """
    Retrieves the user's current budget jar allocations and balances directly from the database.
    You MUST use this tool to see the user's budget structure before creating or adjusting plans.
    If 'jar_name' is omitted, it will return all jars.

    Args:
        jar_name: The specific name of a jar to query. Example: "Savings", "Necessities".
                  If not provided, all jars are returned.
        description: A brief explanation of why you need this jar information.
                     Example: "To check the current balance of the 'Play' jar before making a recommendation."

    Returns:
        A dictionary containing a list of jar data and a summary.
    """
    if jar_name:
        jar = get_jar_from_db(jar_name.lower().replace(' ', '_'))
        if not jar:
            return {"data": [], "description": f"jar '{jar_name}' not found"}
        
        jar_data = [jar.to_dict()]
        description_text = f"Retrieved information for the '{jar_name}' jar."
    else:
        jars = get_all_jars()
        jar_data = [j.to_dict() for j in jars]
        description_text = "Retrieved information for all budget jars."

    return {
        "data": jar_data,
        "description": description or description_text
    }

# =============================================================================
# PLAN MANAGEMENT TOOLS (via Plan Service)
# =============================================================================

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
def create_plan(name: str, description: str, status: str = "active", jar_propose_adjust_details: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a new budget plan for the user via the Plan Service.
    Use this to establish a new financial goal, such as saving for a vacation or paying off debt.

    Args:
        name: A unique, descriptive name for the plan. Example: "Japan Vacation Fund".
        description: A detailed description of the plan's purpose and goals.
        status: The initial status of the plan, usually "active".
        jar_propose_adjust_details: A DETAILED, ACTIONABLE proposal for how the user's budget jars
                                    should be changed to support this plan. This is critical.

    Returns:
        A dictionary containing the newly created plan data.
    """
    return plan_service.create_plan(
        name=name,
        description=description,
        status=status,
        jar_propose_adjust_details=jar_propose_adjust_details
    )


@tool
def adjust_plan(name: str, description: Optional[str] = None, status: Optional[str] = None, jar_propose_adjust_details: Optional[str] = None) -> Dict[str, Any]:
    """
    Modifies an existing budget plan via the Plan Service.
    Use this to update a plan's details, mark it as complete, or change jar allocations.

    Args:
        name: The name of the existing plan to modify.
        description: A new, updated description for the plan.
        status: A new status for the plan (e.g., "completed", "paused").
        jar_propose_adjust_details: An updated proposal for jar adjustments. If the user is increasing
                                    their goal, this field is critical and must be detailed.

    Returns:
        A dictionary containing the updated plan data.
    """
    return plan_service.adjust_plan(
        name=name,
        description=description,
        status=status,
        jar_propose_adjust_details=jar_propose_adjust_details
    )


# =============================================================================
# ReAct RESPONSE TOOL WITH CONVERSATION LOCK
# =============================================================================

@tool
def respond(summary: str, advice: str, question_ask_user: Optional[str] = None) -> Dict[str, Any]:
    """
    Provides the final response to the user and terminates the ReAct loop. THIS IS YOUR FINAL ACTION.
    You MUST call this tool to end the conversation turn.

    If you need more information from the user, use the 'question_ask_user' argument. This will
    pause the ReAct loop and put the agent in a waiting state for the user's next input,
    ensuring the conversation continues with the necessary context.

    Args:
        summary: A brief, one-sentence summary of the action taken or conclusion reached.
                 Example: "I have created a new savings plan for your trip to Japan."
        advice: The detailed, final financial advice or result for the user.
                Example: "Based on your spending, I've set up a plan that contributes $200/month..."
        question_ask_user: A specific, clear question to ask the user if more information is needed
                           to proceed. Using this argument will LOCK the conversation to this agent.
                           Example: "You mentioned saving for a car. What is your target amount?"

    Returns:
        A dictionary containing the final response details, which signals the end of the agent's turn.
    """
    from database import set_active_agent_context

    if question_ask_user:
        set_active_agent_context("budget_advisor")
        requires_follow_up = True
    else:
        set_active_agent_context(None) # Release the lock
        requires_follow_up = False

    # This structure is designed to be interpreted by the agent's main loop.
    return {
        "summary": summary,
        "advice": advice,
        "question_ask_user": question_ask_user,
        "requires_follow_up": requires_follow_up,
        "final_answer": True # Signals the end of the ReAct loop in main.py
    }


# =============================================================================
# TOOL REGISTRATION
# =============================================================================

def get_all_plan_tools() -> List[tool]:
    """
    Returns a list of all tools available to the Budget Advisor agent.
    This function is used to bind the tools to the LLM, enabling their use
    within the ReAct framework.
    """
    return [
        transaction_fetcher,
        get_jar,
        get_plan,
        create_plan,
        adjust_plan,
        respond
    ]



