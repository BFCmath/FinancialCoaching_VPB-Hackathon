"""
Jar Manager Tools - LLM Tool Definitions
========================================

Tools that the LLM can call to manage budget jars.
Enhanced Pattern 2 implementation with dependency injection for production-ready multi-user support.
"""

import sys
import os

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

import json
from langchain_core.tools import tool
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import direct async services (no adapters)
from backend.services.jar_service import JarManagementService


class JarServiceContainer:
    """
    Request-scoped service container for jar agent.
    Provides direct access to async services.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id


def get_all_jar_tools(services: JarServiceContainer) -> List[tool]:
    """
    Create jar tools with injected service dependencies.
    
    Args:
        services: Service container with user context
        
    Returns:
        List of configured tools for the jar agent
    """
    
    # =============================================================================
    # JAR MANAGEMENT TOOLS - SERVICE INTEGRATED
    # =============================================================================

    @tool
    async def create_jar(
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
        return await JarManagementService.create_jar(
            services.db, services.user_id,
            name=name,
            description=description,
            percent=percent,
            amount=amount,
            confidence=confidence
        )

    @tool
    async def update_jar(
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
        return await JarManagementService.update_jar(
            services.db, services.user_id,
            jar_name=jar_name,
            new_name=new_name,
            new_description=new_description,
            new_percent=new_percent,
            new_amount=new_amount,
            confidence=confidence
        )

    @tool
    async def delete_jar(jar_name: List[str], reason: str) -> str:
        """Delete (remove) one or multiple jars permanently and redistribute their percentages to remaining jars.
        
        Args:
            jar_name: List of jar names to delete
            reason: Reason for deletion
        """
        return await JarManagementService.delete_jar(services.db, services.user_id, jar_name=jar_name, reason=reason)

    @tool
    async def list_jars() -> str:
        """List all budget jars with their current balances, budgets, and percentages."""
        return await JarManagementService.list_jars(services.db, services.user_id)

    @tool
    async def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """
        Ask user for clarification when input is unclear.
        Stop asking when you have:
        + purpose/name of the jar(s)
        + percentage or amount (not both)
        
        Args:
            question: Question to ask for clarification
            suggestions: Optional suggestions to help user
        """
        # Note: Conversation locking handled by orchestrator in backend
        
        response = f"Clarification needed: {question}"
        if suggestions:
            response += f"\nSuggestions: {suggestions}"
        return response

    # =============================================================================
    # TOOL REGISTRATION
    # =============================================================================

    return [
        create_jar,
        update_jar,
        delete_jar,
        list_jars,
        request_clarification
    ]


# Backward compatibility function (deprecated)
def get_all_jar_tools_legacy():
    """
    Legacy function for backward compatibility.
    Raises an error since global services are not production-ready.
    """
    raise RuntimeError(
        "Legacy global service approach is not production-ready. "
        "Use get_all_jar_tools(services) with JarServiceContainer instead."
    )