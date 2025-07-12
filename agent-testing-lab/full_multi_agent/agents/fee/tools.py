"""
Fee Manager Tools - LLM Tool Definitions
========================================

Tools that the LLM can call to manage recurring fees.
Integrated with the unified service layer.
"""
import os
import sys
# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)
from langchain_core.tools import tool
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict

# Import from our unified service layer
from service import get_fee_service
from database import set_active_agent_context

# Get service instance
fee_service = get_fee_service()

# Define which tools are considered "final actions" that end the ReAct loop
FINAL_ACTION_TOOLS = [
    "create_recurring_fee",
    "adjust_recurring_fee",
    "delete_recurring_fee",
    "list_recurring_fees"
]

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
    # Lock conversation to fee_manager - ONLY place where lock is set
    set_active_agent_context("fee_manager")
    
    response = f"{question}"
    # if suggestions:
        # response += f"\n\nSuggestions: {suggestions}"
    
    return response

# =============================================================================
# FEE MANAGEMENT TOOLS - SERVICE INTEGRATED
# =============================================================================

@tool
def create_recurring_fee(
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
        pattern_details: Pattern specifics (e.g., [1,15] for monthly on 1st and 15th)
        target_jar: Which jar this fee should come from (Agent should reason based on the jar provided)
        confidence: Confidence in the decision (0-100)
    """
    # This is a final action - does not manage locks
    return fee_service.create_recurring_fee(
        name=name,
        amount=amount,
        description=description,
        pattern_type=pattern_type,
        pattern_details=pattern_details,
        target_jar=target_jar,
        confidence=confidence
    )

@tool
def adjust_recurring_fee(
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
    # This is a final action - does not manage locks
    return fee_service.adjust_recurring_fee(
        fee_name=fee_name,
        new_amount=new_amount,
        new_description=new_description,
        new_pattern_type=new_pattern_type,
        new_pattern_details=new_pattern_details,
        new_target_jar=new_target_jar,
        disable=disable,
        confidence=confidence
    )

@tool
def delete_recurring_fee(fee_name: str, reason: str) -> str:
    """
    FINAL ACTION: Deletes (deactivates) a recurring fee.
    
    Args:
        fee_name: Name of fee to delete
        reason: Reason for deletion
    """
    # This is a final action - does not manage locks
    return fee_service.delete_recurring_fee(fee_name=fee_name, reason=reason)

@tool
def list_recurring_fees(active_only: bool = True, target_jar: Optional[str] = None) -> str:
    """
    FINAL ACTION: Lists all recurring fees with optional filters.
    This is a terminal tool that provides information without needing clarification.
    
    Args:
        active_only: Only show active fees if True
        target_jar: Optional jar name to filter by
    """
    # This is a final action - does not manage locks
    return fee_service.list_recurring_fees(active_only=active_only, target_jar=target_jar)

# List of all tools for the agent
FEE_MANAGER_TOOLS = [
    create_recurring_fee,
    adjust_recurring_fee,
    delete_recurring_fee,
    list_recurring_fees,
    request_clarification
]

def get_all_fee_tools():
    """Get all tools available to the fee manager"""
    return FEE_MANAGER_TOOLS
