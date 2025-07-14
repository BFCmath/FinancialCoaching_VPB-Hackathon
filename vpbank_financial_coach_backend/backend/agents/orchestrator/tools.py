# backend/agents/orchestrator/tools.py

from typing import Dict, Any, List
from langchain_core.tools import tool

# Import backend services that replace lab agents
from backend.services.financial_services import (
    JarManagementService,
    TransactionService,
    TransactionQueryService,
    FeeManagementService,
    PlanManagementService,
    KnowledgeService
)

@tool
def call_classifier(task: str) -> Dict[str, Any]:
    """
    Calls the Transaction Classifier functionality for categorizing transactions.
    Use for queries about classifying expenses into jars.
    """
    return {
        "response": "🔍 I can help you classify transactions. Please tell me about the transaction you'd like to categorize, and I'll suggest which jar it should go into based on your spending categories.",
        "requires_follow_up": False
    }

@tool
def call_fee(task: str) -> Dict[str, Any]:
    """
    Calls the Fee Manager functionality for managing recurring fees/subscriptions.
    Use for creating, updating, deleting, or listing subscriptions/bills.
    """
    return {
        "response": "💳 I can help you manage recurring fees and subscriptions. You can create, update, delete, or list your monthly bills and subscriptions. What would you like to do with your fees?",
        "requires_follow_up": True
    }

@tool
def call_jar(task: str) -> Dict[str, Any]:
    """
    Calls the Jar Manager functionality for CRUD on budget jars and rebalancing.
    Use for creating, updating, deleting, or listing jars.
    """
    return {
        "response": "🏺 I can help you manage your budget jars. You can create new jars, update existing ones, delete jars you no longer need, or view all your jars. I can also help with jar rebalancing. What would you like to do with your jars?",
        "requires_follow_up": True
    }

@tool
def call_knowledge(task: str) -> Dict[str, Any]:
    """
    Calls the Knowledge Base functionality for financial concepts and app features.
    Use for general questions about finance or system functionality.
    """
    return {
        "response": "📚 I can help explain financial concepts and app features. I have knowledge about budgeting, saving strategies, jar methodology, transaction management, and how to use this financial coaching system effectively. What would you like to learn about?",
        "requires_follow_up": False
    }

@tool
def call_plan(task: str) -> Dict[str, Any]:
    """
    Calls the Budget Advisor functionality for financial planning and goals.
    Use for creating/adjusting savings plans or budget advice.
    """
    return {
        "response": "📋 I can help you create and manage budget plans and financial goals. Whether you want to set up a savings plan, adjust your budget allocations, or get advice on financial planning, I'm here to assist. What are your financial goals?",
        "requires_follow_up": True
    }

@tool
def call_fetcher(task: str) -> Dict[str, Any]:
    """
    Calls the Transaction Fetcher functionality for retrieving transaction history.
    Use for querying past transactions with filters.
    """
    return {
        "response": "🔍 I can help you search and retrieve your transaction history. You can filter by date range, amount, jar category, or search for specific transactions. What transactions are you looking for?",
        "requires_follow_up": True
    }

def get_all_orchestrator_tools() -> List[tool]:
    """Returns all tools for the orchestrator LLM."""
    return [
        call_classifier,
        call_fee,
        call_jar,
        call_knowledge,
        call_plan,
        call_fetcher
    ]