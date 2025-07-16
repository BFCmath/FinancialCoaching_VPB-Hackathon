"""
Transaction History Fetcher Prompts
===================================

Simplified prompts for LangChain tool binding with intelligent tool selection.
This is a DATA RETRIEVAL service - return raw transaction data, no analysis.
"""

from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.utils.jar_utils import get_all_jars_for_user

async def build_history_fetcher_prompt(
    user_query: str,
    db: AsyncIOMotorDatabase,
    user_id: str
) -> str:
    """
    Build prompt for pure data retrieval with intelligent tool selection.
    
    Args:
        user_query: User's question or request
        db: Database connection for fetching context
        user_id: User ID for database queries
        
    Returns:
        Prompt focused on data retrieval with smart tool selection
    """
    
     # Fetch fresh jar data from the backend
    available_jars = await get_all_jars_for_user(db, user_id)
    # Format jar information for the prompt
    jar_info_parts = []
    if available_jars:
        for jar in available_jars:
            jar_info_parts.append(
                f"• {jar.name}: Current Amount: ${jar.amount:.2f} - {jar.description}"
            )
    jar_info = "\n".join(jar_info_parts) if jar_info_parts else "No budget jars have been created yet."

    return f"""You are a transaction history fetcher. Your job is to retrieve and present transaction data using intelligent tool selection. Analyze the user's query complexity and select the most appropriate tools.

USER INPUT: "{user_query}"

AVAILABLE JARS:
{jar_info}

YOUR TASK:
Select appropriate tools to retrieve the requested transaction data. When calling each tool, provide a clear description of what you're trying to retrieve.

**FOR SIMPLE QUERIES (1-2 filters) - USE SPECIFIC TOOLS:**
• get_jar_transactions: Single jar filtering ("groceries spending", "all transactions")
• get_time_period_transactions: Time + optional jar ("groceries last month") 
• get_amount_range_transactions: Amount + optional jar ("purchases over $50")
• get_hour_range_transactions: Time of day + optional jar ("morning purchases")
• get_source_transactions: Input source + optional jar ("manual entries")

**FOR COMPLEX QUERIES (3+ filters) - USE COMPLEX TOOL:**
• get_complex_transaction: Multi-dimensional filtering with ALL filter types
  - Use when query has 3+ different filter types
  - Examples: jar + time period + amount + hour range
  - Vietnamese/multilingual complex queries
  - Time-specific category queries with amounts

**COMPLEXITY DETECTION:**
SIMPLE (use specific tools):
- "groceries spending" → get_jar_transactions
- "last month transactions" → get_time_period_transactions
- "purchases over $50" → get_amount_range_transactions
- "morning purchases" → get_hour_range_transactions
- "manual entries" → get_source_transactions

COMPLEX (use get_complex_transaction):
- "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô" → Vietnamese lunch query with time + amount
- "morning grocery shopping under $100 from bank data" → jar + hour + amount + source
- "manual entertainment entries from last week over $30" → jar + date + amount + source
- "breakfast spending between 6am-10am under $15" → jar + hour + amount

**TOOL USAGE:**
All tools have a 'description' parameter - always provide clear descriptions:
- Example: get_complex_transaction(jar_name="meals", start_hour=11, end_hour=14, max_amount=20, description="lunch transactions 11am-2pm under $20")
- Example: get_jar_transactions(jar_name="groceries", description="groceries spending")

**TOOL RETURN FORMAT:**
Each tool returns:
- data: List of transaction dictionaries
- description: The description you provided when calling the tool

**INSTRUCTIONS:**
1. ANALYZE query complexity first
2. If 3+ different filter types → use get_complex_transaction
3. If 1-2 filter types → use appropriate specific tool
4. Always provide clear description parameter
5. Handle Vietnamese/multilingual queries by translating to appropriate parameters

Think step by step:
1. Count filter types in query (jar, time, amount, hour, source)
2. Select appropriate tool based on complexity
3. Extract parameters correctly (especially for Vietnamese)
4. Provide clear description of what you're retrieving"""
