"""
Fee Manager Tools - LLM Tool Definitions  
========================================

Tools that the LLM can call to manage recurring fees.
Enhanced Pattern 2 implementation with dependency injection for production-ready multi-user support.
"""

import os
import sys

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_core.tools import tool
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import direct async services (no adapters)
from backend.services.fee_service import FeeManagementService


class FeeServiceContainer:
    """
    Request-scoped service container for fee agent.
    Provides direct access to async services.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id


def get_all_fee_tools(services: FeeServiceContainer) -> List[tool]:
    """
    Create fee tools with injected service dependencies.
    
    Args:
        services: Service container with user context
        
    Returns:
        List of configured tools for the fee agent
    """
    
    # Define which tools are considered "final actions" that end the ReAct loop
    # FINAL_ACTION_TOOLS = [
    #     "create_recurring_fee",
    #     "adjust_recurring_fee", 
    #     "delete_recurring_fee",
    #     "list_recurring_fees"
    # ]

    # =============================================================================
    # CLARIFICATION AND FOLLOW-UP TOOLS
    # =============================================================================

    @tool
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """
        Request clarification from the user.
        This is the ONLY tool that engages the conversation lock.
        Avoid ask back question about which jar target and the fee name.
        
        Args:
            question: The specific question to ask the user (ask about the amount and the fee schedule)
            suggestions: Optional examples or suggestions to help the user respond
            
        Returns:
            Formatted clarification request
        """
        # Note: Conversation locking handled by orchestrator in backend
        
        response = f"{question}"
        if suggestions:
            response += f"\n\nSuggestions: {suggestions}"
        
        return response

    # =============================================================================
    # FEE MANAGEMENT TOOLS - SERVICE INTEGRATED
    # =============================================================================

    @tool
    async def create_recurring_fee(
        name: str,
        amount: float, 
        description: str, 
        pattern_type: str,
        pattern_details: Optional[List[int]],
        target_jar: str,
        confidence: int
    ) -> str:
        """
        FINAL ACTION: Creates a new recurring fee (subscription, bill, etc.).
        This is a terminal tool - use it when you have all required information.
        Agent should decide the fee name and target jar based on the context.
        
        Args:
            name: Human-friendly name for the fee (Agent should generate this - short and concise)
            amount: Fee amount in dollars
            description: Detailed description of what this fee is for
            pattern_type: When fee occurs - "daily", "weekly", "monthly"
            pattern_details: For custom patterns, list of day numbers (e.g., [1,15] for monthly on 1st and 15th, [1,2,3] for weekly on Mon, Tue, Wed)
            target_jar: Which jar this fee should come from (Agent should reason based on the jar provided)
            confidence: Confidence in the decision (0-100)
        """
        return await FeeManagementService.create_recurring_fee(
            services.db, services.user_id, name, amount, description, 
            pattern_type, pattern_details, target_jar, confidence
        )

    @tool
    async def adjust_recurring_fee(
        fee_name: str,
        new_amount: Optional[float] = None,
        new_description: Optional[str] = None,
        new_pattern_type: Optional[str] = None,
        new_pattern_details: Optional[List[int]] = None,
        new_target_jar: Optional[str] = None,
        disable: bool = False,
        confidence: int = 85
    ) -> str:
        """
        FINAL ACTION: Updates an existing recurring fee's details or disables it.
        
        Args:
            fee_name: Name of the fee to update
            new_amount: New amount (optional)
            new_description: New description (optional)
            new_pattern_type: New pattern type (optional)
            new_pattern_details: New pattern details (optional)
            new_target_jar: New target jar (optional)
            disable: Set to True to disable the fee
            confidence: LLM confidence (0-100)
        """
        return await FeeManagementService.adjust_recurring_fee(
            services.db, services.user_id, fee_name, new_amount, new_description,
            new_pattern_type, new_pattern_details, new_target_jar, disable, confidence
        )

    @tool
    async def delete_recurring_fee(fee_name: str, reason: str) -> str:
        """
        FINAL ACTION: Deletes (deactivates) a recurring fee.
        
        Args:
            fee_name: Name of fee to delete
            reason: Reason for deletion
        """
        return await FeeManagementService.delete_recurring_fee(services.db, services.user_id, fee_name, reason)

    @tool
    @tool
    async def list_recurring_fees(active_only: bool = True, target_jar: Optional[str] = None) -> str:
        """
        FINAL ACTION: Lists all recurring fees with optional filters.
        This is a terminal tool that provides information without needing clarification.
        
        Args:
            active_only: Only show active fees if True
            target_jar: Optional jar name to filter by
        """
        return await FeeManagementService.list_recurring_fees(services.db, services.user_id, active_only, target_jar)

    # =============================================================================
    # TOOL REGISTRATION
    # =============================================================================

    return [
        create_recurring_fee,
        adjust_recurring_fee,
        delete_recurring_fee,
        list_recurring_fees,
        request_clarification
    ]


# Backward compatibility function (deprecated)
def get_all_fee_tools_legacy():
    """
    Legacy function for backward compatibility.
    Raises an error since global services are not production-ready.
    """
    raise RuntimeError(
        "Legacy global service approach is not production-ready. "
        "Use get_all_fee_tools(services) with FeeServiceContainer instead."
    )


