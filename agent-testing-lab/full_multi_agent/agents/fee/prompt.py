"""
Fee Manager Agent Prompts
=========================

Prompts for LLM-powered fee pattern recognition and management.
"""

from typing import List, Optional
from database import ConversationTurn

def build_fee_manager_prompt(
    user_input: str,
    existing_fees: list,
    available_jars: list,
    conversation_history: Optional[List[ConversationTurn]] = None,
    is_follow_up: bool = False
) -> str:
    """
    Build complete prompt for LLM fee management with follow-up support.
    
    Args:
        user_input: User's fee request input
        existing_fees: List of current recurring fees
        available_jars: List of available budget jars
        conversation_history: Previous conversation turns for context
        is_follow_up: Whether this is a follow-up response to a clarification
        
    Returns:
        Complete prompt with context data, history, and tool instructions
    """
    
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
    
    # Format jar information (same structure as classifier)
    jar_info = "\n".join([
        f"""NAME: {jar.name}:
            DESCRIPTION: {jar.description}
            AMOUNT: ${jar.amount:.2f}
            CURRENT AMOUNT: ${jar.current_amount:.2f}"""
        for jar in available_jars
    ])

    # Add conversation history context for follow-ups
    context = ""
    if is_follow_up and conversation_history:
        # Get the last few relevant turns
        relevant_history = [turn for turn in conversation_history[-3:] 
                          if 'fee' in turn.agent_list]
        if relevant_history:
            history_lines = []
            for turn in relevant_history:
                history_lines.append(f"User: {turn.user_input}")
                history_lines.append(f"Assistant: {turn.agent_output}")
            context = "\nPREVIOUS CONVERSATION:\n" + "\n".join(history_lines)
    print("Context:", context)
    # Build complete prompt with follow-up awareness
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
{jar_info}

EXISTING RECURRING FEES:
{fees_info}

{context}
USER INPUT: "{user_input}"

"""

    return prompt

# Legacy function name for compatibility
def get_fee_parsing_prompt(user_input: str, existing_fees: list, available_jars: list) -> str:
    """Legacy function - use build_fee_manager_prompt instead"""
    return build_fee_manager_prompt(user_input, existing_fees, available_jars)
