"""
Prompts for ReAct-based Transaction Classifier
===============================================

Defines the system prompt that guides the LLM to use the ReAct
(Reason-Act-Observe) framework for transaction classification.
"""

from typing import List, Dict, Any

# Import from utils to get jar information for the prompt
import sys
import os

# Add parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from utils import get_all_jars
from database import ConversationTurn

def build_react_classifier_prompt(user_query: str, conversation_history: List[ConversationTurn]) -> str:   
    """
    Builds the ReAct system prompt for the Transaction Classifier agent.

    This prompt instructs the agent to follow a Reason-Act-Observe loop,
    proactively fetching information when the user's input is ambiguous.
    It also includes recent conversation history for context.
    
    Args:
        user_query: The user's raw input, e.g., "lunch" or "coffee 5 dollars".
        conversation_history: A list of previous conversation turns.
        
    Returns:
        A string containing the full system prompt.
    """

    # Format the history for the prompt
    history_str = ""
    if conversation_history:
        history_lines = []
        for turn in conversation_history: # Get the last 3 turns
            history_lines.append(f"User: {turn.user_input}")
            history_lines.append(f"Assistant: {turn.agent_output}")
        history_str = "\n".join(history_lines)

    # Fetch current jar information to include in the prompt
    jars = get_all_jars()
    jar_info_parts = []
    if jars:
        for jar in jars:
            jar_info_parts.append(
                f"- **{jar.name}**: Allocated ${jar.amount:.2f} ({jar.percent:.0%}). Description: {jar.description}"
            )
    jar_info_str = "\n".join(jar_info_parts)
    if not jar_info_str:
        jar_info_str = "No budget jars have been created yet."
    
    return f"""You are an intelligent transaction classifier. Your goal is to accurately categorize user expenses into the correct budget jar. You must follow a "Reason-Act-Observe" cycle.

**CRITICAL RULE:** You MUST NOT ask the user for clarification in your direct `content` response. If you need to ask a question, you MUST use the `respond` tool.

**YOUR TASK:**
Analyze the user's request(can be many transactions) and classify the transaction.

THE ReAct FRAMEWORK: **Reason** -> **Act**  -> **Observe** ->  **Repeat or Finalize**

NOTE:
+ you should be both Vietnamese and English friendly and natural speaker.
+ if the user request contain many transactions, you can call add_money_to_jar_with_confidence many times.
+ Only infer pattern after you see 10+ same transactions (name must match exactly)
+ must call add_money_to_jar_with_confidence, report_no_suitable_jar or respond to end the conversation.

**AVAILABLE BUDGET JARS:**
{jar_info_str}


{history_str}

User: "{user_query}"
Assistant:
"""
