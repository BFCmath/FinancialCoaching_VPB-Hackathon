"""
Jar Manager Agent Prompts - Backend Migration
============================================

Prompts for LLM-powered multi-jar CRUD operations and T. Harv Eker's 6-jar budget management system.
Updated to use backend database integration following classifier pattern.
"""

import sys
import os
from typing import List, Optional

# Add parent directories to path to import from backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.models.conversation import ConversationTurnInDB
from backend.utils.db_utils import get_all_jars_for_user, get_user_settings

async def build_jar_manager_prompt(
    user_input: str,
    conversation_history: List[ConversationTurnInDB],
    db: AsyncIOMotorDatabase,
    user_id: str,
    is_follow_up: bool = False
) -> str:
    """
    Build complete prompt for LLM multi-jar management with backend database integration.
    
    Args:
        user_input: User's jar request input
        conversation_history: Previous conversation turns for context
        db: Database connection
        user_id: User ID for database queries
        is_follow_up: Whether this is a follow-up response to a clarification
        
    Returns:
        Complete prompt with context data and multi-jar tool instructions
    """
    
    # Fetch fresh data from backend database (following classifier pattern)
    existing_jars = await get_all_jars_for_user(db, user_id)
    user_settings_obj = await get_user_settings(db, user_id)
    total_income = user_settings_obj.total_income # Default fallback
    
    # Format existing jars with enhanced display
    jars_info = ""
    if existing_jars:
        total_percent = sum(jar.percent for jar in existing_jars)
        
        jar_lines = []
        for jar in existing_jars:
            budget_amount = jar.percent * total_income
            percent_display = f"{jar.percent * 100:.1f}%"
            jar_lines.append(f"""NAME: {jar.name}
DESCRIPTION: {jar.description}
CURRENT AMOUNT: ${jar.amount:.2f}
BUDGET PERCENT: {percent_display}
TARGET AMOUNT: ${budget_amount:.2f}
""")
        jars_info = "\n".join(jar_lines)
        jars_info += f"\n💰 Total allocation: {total_percent * 100:.1f}%"
    else:
        jars_info = "• No existing jars (T. Harv Eker's 6-jar system will be initialized)"
    
    # Format conversation history for context (following classifier pattern)
    context = ""
    if is_follow_up and conversation_history:
        # Get the last few relevant turns
        relevant_history = [turn for turn in conversation_history[-3:] 
                          if 'jar' in turn.agent_list]
        if relevant_history:
            history_lines = []
            for turn in relevant_history:
                history_lines.append(f"User: {turn.user_input}")
                history_lines.append(f"Assistant: {turn.agent_output}")
            context = "\nPREVIOUS CONVERSATION:\n" + "\n".join(history_lines)

    # Build complete prompt with multi-jar capabilities following classifier pattern
    prompt = f"""You are an advanced multi-jar budget manager implementing T. Harv Eker's proven 6-jar money management system. Analyze the user's input and take appropriate action using multi-jar operations.

**CRITICAL RULE:** You MUST NOT ask the user for clarification in your direct response. If you need to ask a question, you MUST use the `request_clarification` tool.

YOUR TASK:
Analyze the input and understand what the user wants to do with budget jars. Support both SINGLE and MULTI-JAR operations. Take the most appropriate action using the available tools.

IMPORTANT VALIDATION RULES:
1. ALWAYS use List inputs even for single operations: ["vacation"] not "vacation"
2. List lengths must match: same number of names, descriptions, and percentages/amounts
3. Percentages are 0.0-1.0 format: 15% = 0.15, not 15
4. Either percent OR amount lists, never both in same operation
5. System maintains 100% total allocation through automatic rebalancing
6. You MUST NOT ask the user for clarification in your direct response. If you need to ask a question, you MUST use the `request_clarification` tool.

REBALANCING AWARENESS:
- When creating new jars, existing jars automatically scale down proportionally
- When deleting jars, freed percentage redistributes to remaining jars proportionally
- Multi-jar operations use batch validation and atomic execution
- System provides detailed rebalancing messages showing before/after percentages

Think step by step about what the user wants:
1. Identify if it's single or multi-jar operation
2. Determine operation type (create/update/delete/list)
3. Extract amounts/percentages and convert to proper format
4. Use appropriate List inputs with matching lengths
5. Call the appropriate tool with proper confidence scoring
6. Expect automatic rebalancing for create/update/delete operations
7. Support Vietnamese language

CURRENT JAR SYSTEM (Total Income: ${total_income:,.2f}):
{jars_info}

{context}

USER INPUT: "{user_input}"
"""

    return prompt

# Legacy function name for compatibility
def get_jar_parsing_prompt(user_input: str, existing_jars: list) -> str:
    """Legacy function - use build_jar_manager_prompt instead"""
    return build_jar_manager_prompt(user_input, existing_jars)
