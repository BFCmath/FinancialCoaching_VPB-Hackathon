"""
Prompt Building for LLM Transaction Classifier
===============================================

Creates complete prompts with context data and tool instructions for Gemini.
"""

from typing import List, Dict, Any
from tools import fetch_jar_information, fetch_past_transactions


def build_classification_prompt(user_input: str, number_of_transactions: int = 5) -> str:
    """
    Build complete prompt for LLM transaction classification.
    
    Args:
        user_input: User's transaction input (e.g., "meal 20 dollar")
        
    Returns:
        Complete prompt with context data and tool instructions
    """
    # Fetch context data
    jars = fetch_jar_information()
    past_transactions = fetch_past_transactions()
    
    # Format jar information
    jar_info = "\n".join([
        f"• {jar['name']}: ${jar['current']}/${jar['budget']} - {jar['description']}"
        for jar in jars
    ])
    
    # Format recent transactions (last 5 for context)
    transaction_info = "\n".join([
        f"• ${tx['amount']} → {tx['jar']}: '{tx['description']}' ({tx['date']})"
        for tx in past_transactions[-number_of_transactions:]
    ])
    
    # Build complete prompt
    prompt = f"""You are a Vietnamese financial transaction classifier. Analyze the user's transaction input and take appropriate action.

USER INPUT: "{user_input}"

RECENT TRANSACTION PATTERNS:
{transaction_info}

AVAILABLE JARS:
{jar_info}

YOUR TASK:
Analyze the input and identify ALL transactions present. If there are multiple transactions (separated by commas, semicolons, "and", or listed separately), you MUST make multiple tool calls - one for each transaction.

AVAILABLE TOOLS (call multiple times if needed):
1. add_money_to_jar_with_confidence(amount, jar_name, confidence) - Add money with confidence score (0-100)
2. report_no_suitable_jar(description, suggestion) - Use when no jar fits the transaction
3. request_more_info(question) - Use when transaction lacks essential information

CONFIDENCE SCORING GUIDELINES for add_money_to_jar_with_confidence:
- 90-100%: Very certain (exact keyword match, clear transaction type)
  Example: "gas 50" → gas jar (95% confident)
- 70-89%: Moderately certain (good match but some ambiguity)
  Example: "snack 10" → groceries jar (80% confident, could be meals)
- 50-69%: Uncertain (multiple possible jars)
  Example: "coffee 5" → meals jar (65% confident, could be entertainment)

GUIDELINES:
- Process EVERY transaction you find in the input
- Make separate tool calls for each transaction
- For transactions that clearly belong to a jar, use add_money_to_jar_with_confidence with appropriate confidence
- Extract amounts from various formats (dollar, đô la, k = thousand, etc.)
- Use transaction patterns to recognize similar purchases
- Consider jar descriptions to find the best match
- Support Vietnamese language inputs and cultural context
- Ask for more information when individual transactions are unclear
- Make sure the jar name called is correct and match the jar name in the AVAILABLE JARS section

Think step by step, make sure the jar existed and the amount is correct, calling tools now."""

    return prompt


def build_simple_prompt(user_input: str) -> str:
    """Build a simpler prompt for basic testing."""
    return f"""Classify this transaction: "{user_input}"

Available jars: rent, groceries, utilities, gas, meals, transport

Call the appropriate tool:
- add_money_to_jar_with_confidence(amount, jar_name, confidence) - with confidence 0-100
- report_no_suitable_jar(description, suggestion) if no match
- request_more_info(question) if need more details

Confidence guidelines:
- 90-100%: Very certain (clear match)
- 70-89%: Moderately certain (some ambiguity)  
- 50-69%: Uncertain (multiple options)"""
