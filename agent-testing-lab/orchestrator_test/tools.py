"""
Orchestrator Routing Tools - For Multi-Worker Output Testing
===========================================================

Tools to test if the orchestrator can decompose complex requests
and send multiple prompts to specific workers.

The goal: Test prompt quality for multi-worker routing decisions.
"""

from langchain_core.tools import tool


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
    - General conversation that doesn't need tool usage
    
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
    - "I spent $X on Y" type messages
    
    Args:
        task_description: Clear description of the one-time expense to classify
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "transaction_classifier",
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
def route_to_budget_advisor(query: str) -> dict:
    """
    Route to budget advisor for financial planning and budgeting advice.
    
    Use this when user wants budget planning help:
    - Creating savings plans ("save money for my parents")
    - Budget optimization and financial advice
    - Strategic financial planning questions
    - "How can I..." budget-related questions
    
    Args:
        query: The budgeting question or planning request
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "budget", 
        "task": query
    }


@tool
def route_to_insight_generator(request: str) -> dict:
    """
    Route to insight generator for spending analysis and financial insights.
    
    Use this when user wants to understand their financial situation:
    - Spending trend analysis ("my spending trend")
    - Financial projections ("Will I have enough time to save for trip to Thailand?")
    - Understanding spending patterns and financial situation
    - Data-driven insights about their money habits
    
    Args:
        request: Description of the financial insights or analysis needed
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "insight_generator",
        "task": request
    }


@tool
def route_to_fee_manager(task_description: str) -> dict:
    """
    Route to fee manager for recurring fee tracking and management.
    
    Use this when user mentions recurring/repetitive expenses:
    - Subscription fees ("$10 every month for YouTube subscription")
    - Regular commute costs ("$1 every Monday and Friday for commute")
    - Any recurring payments or fees that happen on a schedule
    - Monthly, weekly, daily recurring expenses
    
    Args:
        task_description: Description of the recurring fee to track/manage
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "fee", 
        "task": task_description
    }


@tool
def route_to_knowledge_base(query: str) -> dict:
    """
    Route to knowledge base for educational content and explanations.
    
    Use this when user asks:
    - "What is...?" questions
    - Financial education topics
    - Explanations of financial concepts
    - How-to guides for financial topics
    
    Args:
        query: The educational question or topic to explain
        
    Returns:
        Single worker routing decision
    """
    return {
        "action": "single_worker_routing",
        "worker": "knowledge",
        "task": query
    }


# =============================================================================
# MULTI-WORKER ROUTING TOOLS
# =============================================================================

@tool
def route_to_multiple_workers(task_json: str) -> dict:
    """
    Route to multiple workers for complex requests requiring multiple actions.
    
    Use this when the user's request contains multiple distinct tasks
    that need to be handled by different agents.
    
    Args:
        task_json: JSON string containing list of tasks
                   Example: '[{"worker": "classifier", "task": "Log $100 grocery expense"}, {"worker": "jar", "task": "Add vacation jar with 15%"}]'
    
    Returns:
        Multi-worker routing decision
    """
    import json
    try:
        tasks = json.loads(task_json)
        return {
            "action": "multi_worker_routing",
            "tasks": tasks
        }
    except:
        return {
            "action": "multi_worker_routing", 
            "tasks": [{"worker": "unknown", "task": task_json}]
        }


@tool  
def decompose_complex_request(user_request: str, tasks_json: str) -> dict:
    """
    Decompose a complex user request into multiple sub-tasks.
    
    Use this when you need to break down a complex request before routing.
    
    Args:
        user_request: The original user request
        tasks_json: JSON string of identified sub-tasks
                   Example: '[{"task": "log transaction", "worker": "classifier", "details": "..."}, {"task": "create jar", "worker": "jar", "details": "..."}]'
    
    Returns:
        Decomposition result
    """
    import json
    try:
        sub_tasks = json.loads(tasks_json)
        return {
            "action": "decompose_request",
            "original_request": user_request,
            "sub_tasks": sub_tasks
        }
    except:
        return {
            "action": "decompose_request",
            "original_request": user_request, 
            "sub_tasks": [{"task": tasks_json, "worker": "unknown", "details": ""}]
        }


# =============================================================================
# AVAILABLE TOOLS LIST
# =============================================================================

ALL_TOOLS = [
    # Direct response
    provide_direct_response,
    
    # Single worker routing
    route_to_transaction_classifier,
    route_to_jar_manager,
    route_to_budget_advisor,
    route_to_insight_generator,
    route_to_fee_manager,
    route_to_knowledge_base,
    
    # Multi-worker routing
    route_to_multiple_workers,
    decompose_complex_request,
] 