# backend/agents/orchestrator/prompt.py

from typing import List
from backend.models.conversation import ConversationTurnInDB

def build_orchestrator_prompt(user_input: str, conversation_history: List[ConversationTurnInDB]) -> str:
    """
    Build prompt for orchestrator LLM with routing tool calling instructions.
    
    Args:
        user_input: Current user query.
        conversation_history: Last 10 turns.
        
    Returns:
        Prompt string for routing-based orchestrator.
    """
    # Format history
    history_str = "\n".join([f"User: {turn.user_input}\nAssistant: {turn.agent_output}" for turn in conversation_history]) if conversation_history else "No history."
    
    prompt = f"""You are a financial orchestrator that routes user requests to specialized workers.

AVAILABLE WORKERS:
- transaction_classifier: Classify one-time expenses into jars (meals, gas, groceries, shopping)
- jar_manager: CRUD operations for budget jars (create, modify, delete jars and percentages)
- budget_advisor: Financial planning and budgeting advice (savings plans, budget optimization)
- insight_generator: Use this when user wants see transaction history, a list of transactions.
- fee_manager: Track recurring fees (subscriptions, commute costs, monthly/weekly expenses)
- knowledge_base: Educational content and financial concept explanations

NO WORKER RESPONSES:
- responde_without_agent: Provide a direct response to the user when no worker routing is needed.

CONVERSATION HISTORY:
{history_str}

USER: "{user_input}"

CRITICAL REQUIREMENTS:
1. You MUST ALWAYS call at least one tool - never respond directly without calling a tool
2. Analyze the user's request carefully before deciding which tool(s) to call
3. For greetings or simple conversation, use responde_without_agent
4. For specific financial tasks, route to the appropriate worker
5. For complex requests with multiple tasks, use route_to_multiple_workers

ANALYZE STEP BY STEP THE USER'S REQUEST AND CALL THE APPROPRIATE TOOLS:"""

    return prompt