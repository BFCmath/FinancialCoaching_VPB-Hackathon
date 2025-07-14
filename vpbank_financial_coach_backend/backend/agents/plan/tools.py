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

# Import service adapters
from backend.services.adapters import PlanAdapter, JarAdapter

class PlanServiceContainer:
    """
    Request-scoped service container for plan agent.
    Provides clean dependency injection for tools.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        self._plan_adapter = None
        self._jar_adapter = None
    
    @property
    def plan_adapter(self) -> PlanAdapter:
        """Lazy-loaded plan adapter."""
        if self._plan_adapter is None:
            self._plan_adapter = PlanAdapter(self.db, self.user_id)
        return self._plan_adapter
    
    @property
    def jar_adapter(self) -> JarAdapter:
        """Lazy-loaded jar adapter for jar operations."""
        if self._jar_adapter is None:
            self._jar_adapter = JarAdapter(self.db, self.user_id)
        return self._jar_adapter


def get_stage1_tools(services: PlanServiceContainer) -> List[tool]:
    """
    Stage 1 tools: Information gathering and clarification.
    """
    
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
        return services.plan_adapter.call_transaction_fetcher(
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
        try:
            # Get jar information using jar adapter
            jar_result = services.jar_adapter.list_jars()
            
            # Parse the jar information (assuming it returns formatted string)
            if "No jars found" in jar_result:
                return {
                    "data": [],
                    "total_income": 0,
                    "description": description or "no jars configured"
                }
            
            # For now, return basic structure - this would need real jar parsing logic
            return {
                "data": jar_result,
                "total_income": 0,  # This would need to be fetched from user profile
                "description": description or f"jar spending data{'for ' + jar_name if jar_name else ''}"
            }
            
        except Exception as e:
            return {
                "data": [],
                "total_income": 0,
                "description": f"Error fetching jar data: {str(e)}"
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
        return services.plan_adapter.get_plan(status=status, description=description)

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
        return {"response": response, "requires_follow_up": True, "stage": "1"}

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
        return {"financial_plan": financial_plan, "jar_changes": jar_changes, "requires_follow_up": True, "stage": "2"}


    return [transaction_fetcher, get_jar, get_plan, request_clarification, propose_plan]


def get_stage2_tools(services: PlanServiceContainer) -> List[tool]:
    """
    Stage 2 tools: Plan refinement.
    """
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
        return services.plan_adapter.call_transaction_fetcher(
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
        try:
            # Get jar information using jar adapter
            jar_result = services.jar_adapter.list_jars()
            
            # Parse the jar information (assuming it returns formatted string)
            if "No jars found" in jar_result:
                return {
                    "data": [],
                    "total_income": 0,
                    "description": description or "no jars configured"
                }
            
            # For now, return basic structure - this would need real jar parsing logic
            return {
                "data": jar_result,
                "total_income": 0,  # This would need to be fetched from user profile
                "description": description or f"jar spending data{'for ' + jar_name if jar_name else ''}"
            }
            
        except Exception as e:
            return {
                "data": [],
                "total_income": 0,
                "description": f"Error fetching jar data: {str(e)}"
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
        return services.plan_adapter.get_plan(status=status, description=description)

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
        return {"financial_plan": financial_plan, "jar_changes": jar_changes, "requires_follow_up": True, "stage": "2"}


    return [transaction_fetcher, get_jar, get_plan, propose_plan]


def get_stage3_tools(services: PlanServiceContainer) -> List[tool]:
    """
    Stage 3 tools: Plan implementation.
    """
    
    @tool
    def create_plan(name: str, description: str, jar_changes: Optional[str] = None) -> Dict[str, Any]:
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
        result = services.plan_adapter.create_plan(
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
            "stage": "3"
        }

    @tool
    def adjust_plan(name: str,  description: str, jar_changes: str, status: Optional[str] = "active") -> Dict[str, Any]:
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
        result = services.plan_adapter.adjust_plan(
            name=name,
            description=description,
            status=status,
            jar_propose_adjust_details=jar_changes
        )
        
        return {
            "response": f"✅ Your plan '{name}' has been adjusted successfully!",
            "plan_details": result,
            "requires_follow_up": False,
            "stage": "3"
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
