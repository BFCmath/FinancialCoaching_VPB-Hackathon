"""
Jar Manager Agent Prompts
===============================

Prompts for LLM-powered multi-jar CRUD operations and T. Harv Eker's 6-jar budget management system.
"""
from typing import List, Optional
from database import ConversationTurn

def build_jar_manager_prompt(
    user_input: str,
    existing_jars: list,
    total_income: float,
    conversation_history: Optional[List] = None,
    is_follow_up: bool = False
) -> str:
    """
    Build complete prompt for LLM multi-jar management with T. Harv Eker's 6-jar system.
    
    Args:
        user_input: User's jar request input
        existing_jars: List of current jars with decimal percentages
        total_income: Sample income for percentage calculations
        conversation_history: Previous conversation turns for context
        is_follow_up: Whether this is a follow-up response to a clarification
        
    Returns:
        Complete prompt with context data and multi-jar tool instructions
    """
    
    # Format existing jars with enhanced decimal percentage display
    jars_info = ""
    if existing_jars:
        total_percent = sum(jar.percent for jar in existing_jars)
        total_current_percent = sum(jar.current_percent for jar in existing_jars)
        
        jar_lines = []
        for jar in existing_jars:
            current_amount = jar.current_percent * total_income
            budget_amount = jar.percent * total_income
            percent_display = f"{jar.percent * 100:.1f}%"
            current_display = f"{jar.current_percent * 100:.1f}%"
            jar_lines.append(f"""NAME: {jar.name}
DESCRIPTION: {jar.description[:30]}...
CURRENT AMOUNT: ${budget_amount:.2f}
BUDGET PERCENT: {percent_display}
CURRENT PERCENT: {current_display}\n""")
        jars_info = "\n".join(jar_lines)
        jars_info += f"\n💰 Totals: {total_current_percent * 100:.1f}%/{total_percent * 100:.1f}% allocated"
    else:
        jars_info = "• No existing jars (T. Harv Eker's 6-jar system will be initialized)"
    
    # Add conversation history context for follow-ups
    context = ""
    if is_follow_up and conversation_history:
        # Get the last few relevant turns
        relevant_history = [turn for turn in conversation_history
                          if 'jar' in turn.agent_list]
        if relevant_history:
            history_lines = []
            for turn in relevant_history:
                history_lines.append(f"User: {turn.user_input}")
                history_lines.append(f"Assistant: {turn.agent_output}")
            context = "\nPREVIOUS CONVERSATION:\n" + "\n".join(history_lines)

    # Build complete prompt with multi-jar capabilities
    prompt = f"""You are an advanced multi-jar budget manager implementing T. Harv Eker's proven 6-jar money management system. Analyze the user's input and take appropriate action using multi-jar operations.

YOUR TASK:
Analyze the input and understand what the user wants to do with budget jars. Support both SINGLE and MULTI-JAR operations. Take the most appropriate action using the available tools.

IMPORTANT VALIDATION RULES:
1. ALWAYS use List inputs even for single operations: ["vacation"] not "vacation"
2. List lengths must match: same number of names, descriptions, and percentages/amounts
3. Percentages are 0.0-1.0 format: 15% = 0.15, not 15
4. Either percent OR amount lists, never both in same operation
5. System maintains 100% total allocation through automatic rebalancing
6. Overflow allowed for current_percent but prevented for budget percent
7. You MUST NOT ask the user for clarification in your direct response. If you need to ask a question, you MUST use the `request_clarification` tool.

REBALANCING AWARENESS:
- When creating new jars, existing jars automatically scale down proportionally
- When deleting jars, freed percentage redistributes to remaining jars proportionally
- Multi-jar operations use batch validation and atomic execution
- System provides detailed rebalancing messages showing before/after percentages

Think step by step about what the user wants:
1. Identify if it's single or multi-jar operation
2. Determine operation type (create/update/delete/add_money/list)
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
    print(prompt)
    return prompt

# Enhanced function with total income parameter
def build_enhanced_jar_prompt(user_input: str, existing_jars: list, total_income: float) -> str:
    """Enhanced version with explicit total income parameter"""
    return build_jar_manager_prompt(user_input, existing_jars, total_income)

# Legacy function name for compatibility
def get_jar_parsing_prompt(user_input: str, existing_jars: list) -> str:
    """Legacy function - use build_jar_manager_prompt instead"""
    return build_jar_manager_prompt(user_input, existing_jars)
