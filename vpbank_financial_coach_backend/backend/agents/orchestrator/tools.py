# backend/agents/orchestrator/tools.py

from typing import Dict, Any, List
from langchain_core.tools import tool
from motor.motor_asyncio import AsyncIOMotorDatabase

# Global variables to store db and user_id (set by orchestrator main)
_db: AsyncIOMotorDatabase = None
_user_id: str = None
_conversation_history: List = None

def set_orchestrator_context(db: AsyncIOMotorDatabase, user_id: str, conversation_history: List = None):
    """Set the context for orchestrator tools - called by main orchestrator."""
    global _db, _user_id, _conversation_history
    _db = db
    _user_id = user_id
    _conversation_history = conversation_history or []

# =============================================================================
# DIRECT RESPONSE TOOL
# =============================================================================

@tool
def provide_direct_response(response_text: str) -> dict:
    """
    Provide a direct response to the user when no worker routing is needed.
    
    Use this when:
    - User greeting (hello, hi, etc.)
    - Simple questions that don't require specific worker expertise
    - General conversation that doesn't need advanced tool usage
    
    Args:
        response_text: The direct response to give to the user
        
    Returns:
        Direct response action
    """
    return {
        "action": "direct_response",
        "response": response_text
    }

# =============================================================================
# SINGLE WORKER ROUTING TOOLS
# =============================================================================

@tool
def route_to_transaction_classifier(task_description: str) -> dict:
    """
    Route to transaction classifier for logging one-time expenses into jars.
    
    Use this when user mentions spending money on something specific:
    - One-time purchases (meal, gas, groceries, shopping, etc.)
    - Any expense that needs to be classified and allocated to jars
    - "$X on Y" type messages
    
    Args:
        task_description: Clear description of the one-time expense to classify
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "classifier",
        "task": task_description
    }

@tool
def route_to_jar_manager(task_description: str) -> dict:
    """
    Route to jar manager for jar CRUD operations (Create, Read, Update, Delete).
    
    Use this when user wants to manage their budget jars:
    - Create new jars ("add vacation jar", "create emergency fund")
    - Modify existing jars ("reduce Save jar to 2%", "increase vacation jar")
    - Delete or view jars
    - Any jar management operations (user may not explicitly mention "jar")
    
    Args:
        task_description: Clear description of the jar management operation
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing", 
        "worker": "jar",
        "task": task_description
    }

@tool
def route_to_fee_manager(task_description: str) -> dict:
    """
    Route to fee manager for recurring expense management.
    
    Use this when user wants to manage recurring fees:
    - Add recurring fees ("$10 monthly Netflix", "$2 daily coffee", "weekly commute $15")
    - Modify or delete subscriptions/bills
    - List existing recurring fees
    
    Args:
        task_description: Clear description of the recurring fee operation
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "fee",
        "task": task_description
    }

@tool
def route_to_budget_advisor(task_description: str) -> dict:
    """
    Route to budget advisor for financial planning and budgeting advice.
    
    Use this when user wants budget planning help:
    - Creating savings plans ("save money for my parents")
    - Budget optimization and financial advice
    - Strategic financial planning questions
    - "How can I..." budget-related questions
    
    Args:
        task_description: Clear description of the planning request
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "plan",
        "task": task_description
    }

@tool
def route_to_insight_generator(task_description: str) -> dict:
    """
    Route to insight generator for transaction queries.

    Use this when user wants see transaction history, a list of transactions.
    
    Args:
        task_description: Clear description of what transaction they want to see
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "fetcher", 
        "task": task_description
    }

@tool
def route_to_knowledge_base(task_description: str) -> dict:
    """
    Route to knowledge base for educational content and financial concepts.
    
    Use this when user wants to learn:
    - Financial concept explanations ("what is compound interest?")
    - App feature explanations
    - Educational content about budgeting, investing, etc.
    
    Args:
        task_description: Clear description of the knowledge request
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "knowledge",
        "task": task_description
    }

# =============================================================================
# MULTIPLE WORKER ROUTING TOOL
# =============================================================================

@tool
def route_to_multiple_workers(tasks_json: str) -> dict:
    """
    Route to multiple workers when request has multiple distinct tasks.
    
    Use this when user request has multiple distinct tasks that need different workers:
    - "I spent $50 on groceries and want to create a vacation jar" (classifier + jar)
    - "Add Netflix subscription and check my spending patterns" (fee + fetcher)

    # worker available:
    + "classifier", "jar", "fee", "plan", "fetcher", "knowledge"
    
    Args:
        tasks_json: JSON string with format: '[{"worker": "worker_name", "task": "task_description"}]'
        
    Example:
        '[{"worker": "classifier", "task": "spent $50 on groceries"}, {"worker": "jar", "task": "create vacation jar"}]'
        
    Returns:
        Multiple worker routing decision
    """
    return {
        "action": "multiple_worker_routing",
        "tasks": tasks_json
    }

def get_all_orchestrator_tools() -> List[tool]:
    """Returns all tools for the orchestrator LLM."""
    return [
        provide_direct_response,
        route_to_transaction_classifier,
        route_to_jar_manager,
        route_to_fee_manager,
        route_to_budget_advisor,
        route_to_insight_generator,
        route_to_knowledge_base,
        route_to_multiple_workers
    ]