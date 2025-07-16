"""
Budget Advisor Agent Tools - Enhanced Pattern 2
==============================================

Tools for the ReAct-based financial planning and advisory agent.
Enhanced Pattern 2 implementation with dependency injection for production-ready multi-user support.
"""

import sys
import os

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_core.tools import tool
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import services directly
from backend.services.plan_service import PlanManagementService
from backend.services.jar_service import JarManagementService
from backend.services.communication_service import AgentCommunicationService

class PlanServiceContainer:
    """
    Request-scoped service container for plan agent.
    Provides direct access to async services.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id


def get_stage1_tools(services: PlanServiceContainer) -> List[tool]:
    """
    Stage 1 tools: Information gathering and clarification.
    """
    
    @tool
    async def transaction_fetcher(user_query: str, description: str) -> Dict[str, Any]:
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
        try:
            return await AgentCommunicationService.call_transaction_fetcher(
                services.db, services.user_id, user_query=user_query, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch transactions: {str(e)}",
                "description": f"Error while {description}" if description else "Error fetching transactions"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error fetching transactions"
            }

    @tool
    async def get_jar(jar_name: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        """
        Retrieves the user's current budget jar allocations and balances directly from the database.
        Returns all jars if no name is provided. You MUST use this tool to see the user's budget structure before creating or adjusting plans.
        Also includes the total income for reference in calculations.

        Args:
            jar_name: The specific name of a jar to query. Example: "Savings", "Necessities".
                    If not provided, all jars are returned.
            description: A brief explanation for the query. Example: "Checking current jar allocations for planning."
        
        Returns:
            A dictionary containing the jar details, including balances and allocations.
        """
        try:
            return await JarManagementService.get_jars(
                services.db, services.user_id, jar_name=jar_name, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to get jar information: {str(e)}",
                "description": f"Error while {description}" if description else "Error getting jar information"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error getting jar information"
            }

    @tool
    async def get_plan(status: str = "active", description: str = "") -> Dict[str, Any]:
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
        try:
            return await PlanManagementService.get_plan(
                services.db, services.user_id, status=status, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to get plan information: {str(e)}",
                "description": f"Error while {description}" if description else "Error getting plan information"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error getting plan information"
            }

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
        response = f"❓ {question}"
        if suggestion:
            response += f"\n💡 {suggestion}"
        return {"response": response, "requires_follow_up": True, "plan_stage": "1"}

    @tool
    def propose_plan(financial_plan: str, jar_changes: str) -> Dict[str, Any]:
        """
        Proposes a new financial plan and jar changes plan based on the user's goals and current budget jars.
        This tool MUST BE USED after gathering all necessary information and clarifying the user's needs.
        
        Args:
            financial_plan: A detailed proposal for the plan, including financial goals and strategies.
            jar_changes: A detailed proposal for changes to jars aligned with financial_plan, such as new allocations or adjustments to existing jars.
        """
        # This tool's output is handled specially in main.py to format the two parts
        return {"financial_plan": financial_plan, "jar_changes": jar_changes, "requires_follow_up": True, "plan_stage": "2"}


    return [transaction_fetcher, get_jar, get_plan, request_clarification, propose_plan]


def get_stage2_tools(services: PlanServiceContainer) -> List[tool]:
    """
    Stage 2 tools: Plan refinement.
    """
    @tool
    async def transaction_fetcher(user_query: str, description: str) -> Dict[str, Any]:
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
        try:
            return await AgentCommunicationService.call_transaction_fetcher(
                services.db, services.user_id, user_query=user_query, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch transactions: {str(e)}",
                "description": f"Error while {description}" if description else "Error fetching transactions"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error fetching transactions"
            }

    @tool
    async def get_jar(jar_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves the user's current budget jar allocations and balances directly from the database.
        Returns all jars if no name is provided. You MUST use this tool to see the user's budget structure before creating or adjusting plans.
        Also includes the total income for reference in calculations.

        Args:
            jar_name: The specific name of a jar to query. Example: "Savings", "Necessities".
                    If not provided, all jars are returned.
        """
        try:
            return await JarManagementService.get_jars(
                services.db, services.user_id, jar_name=jar_name
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to get jar information: {str(e)}",
                "description": "Error getting jar information"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": "Unexpected error getting jar information"
            }

    @tool
    async def get_plan(status: str = "active", description: str = "") -> Dict[str, Any]:
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
        try:
            return await PlanManagementService.get_plan(
                services.db, services.user_id, status=status, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to get plan information: {str(e)}",
                "description": f"Error while {description}" if description else "Error getting plan information"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error getting plan information"
            }

    @tool
    def propose_plan(financial_plan: str, jar_changes: str) -> Dict[str, Any]:
        """
        Proposes a new financial plan and jar changes plan based on the user's goals and current budget jars.
        This tool MUST BE USED after gathering all necessary information and clarifying the user's needs.
        
        Args:
            financial_plan: A detailed proposal for the plan, including financial goals and strategies.
            jar_changes: A detailed proposal for changes to jars aligned with financial_plan, such as new allocations or adjustments to existing jars.
        """
        # This tool's output is handled specially in main.py to format the two parts
        return {"financial_plan": financial_plan, "jar_changes": jar_changes, "requires_follow_up": True, "plan_stage": "2"}


    return [transaction_fetcher, get_jar, get_plan, propose_plan]


def get_stage3_tools(services: PlanServiceContainer) -> List[tool]:
    """
    Stage 3 tools: Plan implementation.
    """
    
    @tool
    async def create_plan(name: str, description: str, jar_changes: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a new budget plan, this should be used after the user have accepted the proposed plan and jar changes.
        Use this to establish a new financial goal, such as saving for a vacation or paying off debt.

        Args:
            name: A unique, descriptive name for the plan. Example: "Japan Vacation Fund".
            description: A detailed description of the plan's purpose and goals.
            jar_changes: A DETAILED, ACTIONABLE command for jar changes.

        Returns:
            A standardized dictionary with a success message, the plan details, and state flags for the orchestrator.
        """
        try:
            result = await PlanManagementService.create_plan(
                services.db, services.user_id, 
                name=name,
                description=description,
                status="active",
                jar_propose_adjust_details=jar_changes
            )
            
            # The tool now creates the full response object for the orchestrator
            return {
                "response": f"✅ Your plan '{name}' has been created successfully!",
                "plan_details": result,
                "requires_follow_up": False,
                "plan_stage": "3"
            }
        except ValueError as e:
            # Service validation errors
            return {
                "response": f"❌ Failed to create plan '{name}': {str(e)}",
                "plan_details": None,
                "requires_follow_up": False,
                "plan_stage": "3",
                "error": str(e)
            }
        except Exception as e:
            # Unexpected errors
            return {
                "response": f"❌ An unexpected error occurred while creating plan '{name}': {str(e)}",
                "plan_details": None,
                "requires_follow_up": False,
                "plan_stage": "3",
                "error": str(e)
            }

    @tool
    async def adjust_plan(name: str,  description: str, jar_changes: str, status: Optional[str] = "active") -> Dict[str, Any]:
        """
        Modifies an existing budget plan, this should be used when the user wants to update an existing plan or change jar allocations.
        This is useful for adjusting goals based on new financial data or user feedback.
        Use this to update a plan's details, mark it as complete, or change jar allocations.

        Args:
            name: The name of the existing plan to modify.
            description: A new, updated description for the plan.
            status: A new status for the plan ("active", "completed", "paused").
            jar_changes: A DETAILED, ACTIONABLE command for jar adjustments.

        Returns:
            A standardized dictionary with a success message, the plan details, and state flags for the orchestrator.
        """
        try:
            result = await PlanManagementService.adjust_plan(
                services.db, services.user_id,
                name=name,
                description=description,
                status=status,
                jar_propose_adjust_details=jar_changes
            )
            
            return {
                "response": f"✅ Your plan '{name}' has been adjusted successfully!",
                "plan_details": result,
                "requires_follow_up": False,
                "plan_stage": "3"
            }
        except ValueError as e:
            # Service validation errors
            return {
                "response": f"❌ Failed to adjust plan '{name}': {str(e)}",
                "plan_details": None,
                "requires_follow_up": False,
                "plan_stage": "3",
                "error": str(e)
            }
        except Exception as e:
            # Unexpected errors
            return {
                "response": f"❌ An unexpected error occurred while adjusting plan '{name}': {str(e)}",
                "plan_details": None,
                "requires_follow_up": False,
                "plan_stage": "3",
                "error": str(e)
            }

    return [create_plan, adjust_plan]


# Legacy function wrappers for backward compatibility
def get_stage1_tools_legacy():
    """Legacy wrapper - requires global service setup"""
    raise NotImplementedError("Use Enhanced Pattern 2: get_stage1_tools(services)")

def get_stage2_tools_legacy():
    """Legacy wrapper - requires global service setup"""
    raise NotImplementedError("Use Enhanced Pattern 2: get_stage2_tools(services)")

def get_stage3_tools_legacy():
    """Legacy wrapper - requires global service setup"""
    raise NotImplementedError("Use Enhanced Pattern 2: get_stage3_tools(services)")
