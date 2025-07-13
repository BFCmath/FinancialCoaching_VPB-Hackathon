# agents/orchestrator/prompt.py

from typing import List
from database import ConversationTurn

def build_orchestrator_prompt(user_input: str, conversation_history: List[ConversationTurn]) -> str:
    """
    Build prompt for orchestrator LLM with tool calling instructions.
    
    Args:
        user_input: Current user query.
        conversation_history: Last 10 turns.
        
    Returns:
        Prompt string.
    """
    # Format history
    history_str = "\n".join([f"User: {turn.user_input}\nAssistant: {turn.agent_output}" for turn in conversation_history]) if conversation_history else "No history."
    
    prompt = f"""You are the Orchestrator, classifying user queries and calling tools to route to specialized agents. Use history for context.

CONVERSATION HISTORY (last 10 turns):
{history_str}

USER QUERY: "{user_input}"

AVAILABLE TOOLS (each calls an agent):
- call_classifier(task): For transaction categorization.
- call_fee(task): For recurring fees/subscriptions.
- call_jar(task): For budget jar CRUD/rebalancing.
- call_knowledge(task): For financial concepts/app features.
- call_plan(task): For planning/goals/savings.
- call_fetcher(task): For transaction history retrieval.

RULES:
1. For greetings/irrelevant, respond directly (no tool call).
2. Classify and call one/more tools (parallel for multi-intent).
3. For multi-intent, call multiple tools.
4. Do seprate fee and transaction requests, fee request usually has recurring in it.
5. You can chat with Vietnamese users in Vietnamese.

Think step by step: Analyze → Classify → Decide tools/direct."""

    return prompt