"""
Fee Manager Agent Prompts
=========================

Prompts for LLM-powered fee pattern recognition and management.
Updated to use backend models and async database calls following classifier pattern.
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import backend models instead of lab models (following classifier pattern)
import sys
import os

# Add parent directories to path to import from backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from backend.models.conversation import ConversationTurnInDB
from backend.utils.general_utils import get_all_jars_for_user, get_all_fees_for_user

async def build_fee_manager_prompt(
    user_input: str,
    conversation_history: List[ConversationTurnInDB],
    db: AsyncIOMotorDatabase, 
    user_id: str,
    is_follow_up: bool = False
) -> str:
    """
    Build complete prompt for LLM fee management with backend database integration.
    
    Args:
        user_input: User's fee request input
        conversation_history: Previous conversation turns for context  
        db: Database connection
        user_id: User ID for database queries
        is_follow_up: Whether this is a follow-up response to a clarification
        
    Returns:
        Complete prompt with context data, history, and tool instructions
    """
    
    # Fetch fresh data from backend database (following classifier pattern)
    existing_fees = await get_all_fees_for_user(db, user_id)
    available_jars = await get_all_jars_for_user(db, user_id)
    
    # Format existing fees
    fees_info = ""
    if existing_fees:
        active_fees = [f for f in existing_fees if f.is_active]
        if active_fees:
            fees_info = "\n".join([
                f""" 
                FEE NAME: {fee.name}
                FEE DESCRIPTION: {fee.description}
                FEE AMOUNT: ${fee.amount}
                FEE PATTERN: {fee.pattern_type}
                FEE TARGET JAR: {fee.target_jar}
                """
                for fee in active_fees
            ])
        else:
            fees_info = "• No active fees"
    else:
        fees_info = "• No existing fees"
    
    # Format jar information to match classifier format
    jar_info_parts = []
    if available_jars:
        for jar in available_jars:
            jar_info_parts.append(
                f"- **{jar.name}**: Allocated ${jar.amount:.2f} ({jar.percent:.0%}). Description: {jar.description}"
            )
    jar_info_str = "\n".join(jar_info_parts)
    if not jar_info_str:
        jar_info_str = "No budget jars have been created yet."

    # Format conversation history for context (following classifier pattern)
    history_str = ""
    if conversation_history:
        history_lines = []
        for turn in conversation_history[-3:]:  # Get the last 3 turns
            history_lines.append(f"User: {turn.user_input}")
            history_lines.append(f"Assistant: {turn.agent_output}")
        history_str = "\n".join(history_lines)
    
    # Build complete prompt with backend data (following classifier pattern)
    prompt = f"""You are a Vietnamese recurring fee manager. Analyze the user's input and take appropriate action.

**CRITICAL RULE:** You MUST NOT ask the user for clarification in your direct response. If you need to ask a question, you MUST use the `request_clarification` tool.

YOUR TASK:
Analyze the input and understand what the user wants to do with recurring fees. Take the most appropriate action using the available tools.

Spend time thinking step by step to decide pattern based on the user input and context.
PATTERN TYPES & DETAILS:
- "daily": pattern_details=None (every day)
- "weekly": pattern_details=None (every day) or [1,2,3,4,5] (weekdays: Mon=1, Tue=2, ..., Sun=7)
- "monthly": pattern_details=None (every day) or [1,15] (1st and 15th of each month)

WHEN TO ASK:
- If the user does not specify an amount, ask for it.
- If the user does not specify a fee schedule, ask for it.
- Ask in vietnamese if the input is in vietnamese.

WHEN YOU CAN CREATE A FEE:
- You have read PREVIOUS CONVERSATION and gathered enough context, decide the fee name and target jar based on the context if enough information is available.
- Decide the fee name and target jar based on the context if enough information is available.
Think step by step about what the user wants

AVAILABLE JARS:
{jar_info_str}

EXISTING RECURRING FEES:
{fees_info}

{history_str}

USER INPUT: "{user_input}"

"""

    return prompt

# Legacy function name for compatibility
def get_fee_parsing_prompt(user_input: str, existing_fees: list, available_jars: list) -> str:
    """Legacy function - use build_fee_manager_prompt instead"""
    # This is kept for backward compatibility but should use the new async version
    return f"Legacy function - use build_fee_manager_prompt with database context instead"
