"""
Jar Manager Tools - LLM Tool Definitions
========================================

Tools that the LLM can call to manage budget jars.
Integrated with the unified service layer.
"""

import sys
import os

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

import json
from langchain_core.tools import tool
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json

# Import from our unified service layer
from service import get_jar_service

# Get service instance
jar_service = get_jar_service()

# Helper functions for fetching data
def fetch_existing_jars() -> List[Dict]:
    """Get all current jars from service layer"""
    from utils import get_all_jars
    
    jars = get_all_jars()
    
    # Convert jar objects to dict format expected by tools
    jar_dicts = []
    for jar in jars:
        jar_dicts.append({
            "name": jar.name,
            "current_percent": jar.current_percent,
            "percent": jar.percent,
            "current_amount": jar.current_amount,
            "amount": jar.amount,
            "description": jar.description
        })
    
    return jar_dicts

def get_jar_names() -> List[str]:
    """Get list of jar names only"""
    jars = fetch_existing_jars()
    return [jar["name"] for jar in jars]

# =============================================================================
# JAR MANAGEMENT TOOLS - SERVICE INTEGRATED WITH MULTI-JAR SUPPORT
# =============================================================================

@tool
def create_jar(
    name: List[str],
    description: List[str],
    percent: List[Optional[float]] = None,
    amount: List[Optional[float]] = None,
    confidence: int = 85
) -> str:
    """
    Create one or multiple budget jars with percentage or amount. Supports multi-jar creation.
    
    Args:
        name: List of unique jar names (e.g., ["vacation", "emergency"])
        description: Must be informative 
        percent: List of target percentage allocations (0.0-1.0, e.g., [0.15, 0.20])
        amount: List of target dollar amounts (will calculate percentages automatically)
        confidence: LLM confidence in operation understanding (0-100)
    
    Note: For each jar, provide either percent OR amount, not both.
    All lists must have the same length.
    """
    
    return jar_service.create_jar(
        name=name,
        description=description,
        percent=percent,
        amount=amount,
        confidence=confidence
    )


@tool
def update_jar(
    jar_name: List[str],
    new_name: List[Optional[str]] = None,
    new_description: List[Optional[str]] = None,
    new_percent: List[Optional[float]] = None,
    new_amount: List[Optional[float]] = None,
    confidence: int = 85
) -> str:
    """Update one or multiple existing jars with new parameters and rebalance percentages if needed.
    
    Args:
        jar_name: List of jar names to update
        new_name: List of new jar names (optional for each)
        new_description: List of new descriptions (optional for each)
        new_percent: List of new percentage allocations (0.0-1.0, optional for each)
        new_amount: List of new dollar amounts (will calculate percentages, optional for each)
        confidence: LLM confidence (0-100)
    
    Note: All lists must have the same length as jar_name.
    For each jar, provide either new_percent OR new_amount, not both.
    """
    
    return jar_service.update_jar(
        jar_name=jar_name,
        new_name=new_name,
        new_description=new_description,
        new_percent=new_percent,
        new_amount=new_amount,
        confidence=confidence
    )


@tool
def delete_jar(jar_name: List[str], reason: str) -> str:
    """Delete (remove) one or multiple jars permanently and redistribute their percentages to remaining jars.
    
    Args:
        jar_name: List of jar names to delete
        reason: Reason for deletion
    """
    
    return jar_service.delete_jar(jar_name=jar_name, reason=reason)


@tool
def list_jars() -> str:
    """List all budget jars with their current balances, budgets, and percentages."""
    
    return jar_service.list_jars()


@tool
def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
    """
    Ask user for clarification when input is unclear.
    Engages a conversation lock to ensure the user's next response is routed back to this agent.
    Stop asking when you have:
    + purpose/name of the jar(s)
    + percentage or amount (not both)
    
    Args:
        question: Question to ask for clarification
        suggestions: Optional suggestions to help user
    """
    from database import set_active_agent_context
    set_active_agent_context("jar") # Lock conversation to this agent

    # The main loop will interpret this return and format it for the user
    # It will also know to set requires_follow_up to True
    response = f"Clarification needed: {question}"
    if suggestions:
        response += f"\nSuggestions: {suggestions}"
    return response


# List of all tools for LLM binding
JAR_TOOLS = [
    create_jar,
    update_jar,
    delete_jar,
    list_jars,
    request_clarification
]