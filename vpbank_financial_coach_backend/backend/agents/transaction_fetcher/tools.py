"""
Transaction Fetcher Tools - Enhanced Pattern 2
==============================================

Tools that the LLM can call to retrieve transaction history.
Enhanced Pattern 2 implementation with dependency injection for production-ready multi-user support.
"""

import sys
import os

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import services directly
from backend.services.transaction_service import TransactionQueryService

class TransactionFetcherServiceContainer:
    """
    Request-scoped service container for transaction fetcher agent.
    Provides direct access to async services.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id

def get_all_transaction_tools(services: TransactionFetcherServiceContainer) -> List[tool]:
    """
    Create transaction fetcher tools with injected service dependencies.
    
    Args:
        services: Service container with user context
        
    Returns:
        List of configured tools for the fetcher agent
    """

    @tool
    async def get_jar_transactions(jar_name: Optional[str] = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """
        Retrieve all transactions for a specific budget jar/category or all jars.
        
        Purpose: Get transactions filtered by spending category (jar). Most commonly used tool.
        
        Args:
            jar_name: Budget jar name or None
                - Specific jar: "necessities", "long_term_savings", "play", "education", "financial_freedom", "give"
                - None: Get all transactions across all jars
                
            limit: Maximum number of transactions to return (default: 50)
            
            description: Human-readable description of what you're trying to retrieve
                - Example: "groceries spending", "all my transactions", "entertainment expenses"
                - This will be returned to help users and other agents understand the data
        
        Returns:
            Dictionary containing:
            - data: List of transaction dictionaries
            - description: The description you provided, or auto-generated if empty
            
            Each transaction contains:
            - amount: float (transaction amount)
            - jar: str (budget category)
            - description: str (transaction description)
            - date: str (YYYY-MM-DD format)
            - time: str (HH:MM format)
            - source: str (vpbank_api, manual_input, text_input, image_input)
            
            Sorted by date (newest first)
        
        Common Usage:
            - "Show me necessities spending" → jar_name="necessities", description="necessities spending"
            - "All my spending" → jar_name=None, description="all my transactions"
            - "Play transactions" → jar_name="play", description="play expenses"
        """
        try:
            return await TransactionQueryService.get_jar_transactions(
                services.db, services.user_id, jar_name=jar_name, limit=limit, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch jar transactions: {str(e)}",
                "description": f"Error while {description}" if description else "Error fetching jar transactions"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error fetching jar transactions"
            }

    @tool
    async def get_time_period_transactions(jar_name: Optional[str] = None, start_date: str = "last_month", end_date: Optional[str] = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """
        Retrieve transactions within a specific time period, optionally filtered by jar.

        Purpose: Filter transactions by date range. Supports relative dates and specific dates.

        Args:
            jar_name: Budget jar name or None
                - Specific jar: "necessities", "long_term_savings", "play", "education", "financial_freedom", "give"
                - None: All jars
                
            start_date: Start date for filtering
                - Relative dates: "today", "yesterday", "last_week", "last_month", "this_month", "last_year"
                - Specific dates: "2024-03-01" (YYYY-MM-DD format)
                - Default: "last_month"
                
            end_date: End date for filtering (optional)
                - Same formats as start_date
                - None: Defaults to today
                
            limit: Maximum number of transactions to return (default: 50)
            
            description: Human-readable description of what you're trying to retrieve

        Returns:
            Dictionary containing:
            - data: List of transaction dictionaries matching the time period
            - description: The description you provided, or auto-generated if empty

        Common Usage:
            - "Show me necessities from last week" → jar_name="necessities", start_date="last_week"
            - "All spending this month" → jar_name=None, start_date="this_month"
            - "Play expenses from March 1st to March 15th" → jar_name="play", start_date="2024-03-01", end_date="2024-03-15"
        """
        try:
            return await TransactionQueryService.get_time_period_transactions(
                services.db, services.user_id, jar_name=jar_name, start_date=start_date, end_date=end_date, limit=limit, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch time period transactions: {str(e)}",
                "description": f"Error while {description}" if description else "Error fetching time period transactions"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error fetching time period transactions"
            }

    @tool
    async def get_amount_range_transactions(jar_name: Optional[str] = None, min_amount: Optional[float] = None, max_amount: Optional[float] = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """
        Retrieve transactions within a specific amount range, optionally filtered by jar.

        Purpose: Filter transactions by spending amount. Useful for finding large/small expenses.

        Args:
            jar_name: Budget jar name or None
                - Specific jar: "necessities", "long_term_savings", "play", "education", "financial_freedom", "give"
                - None: All jars
                
            min_amount: Minimum transaction amount (optional)
                - Example: 50.0 for "transactions over $50"
                - None: No minimum limit
                
            max_amount: Maximum transaction amount (optional)
                - Example: 20.0 for "transactions under $20"
                - None: No maximum limit
                
            limit: Maximum number of transactions to return (default: 50)
            
            description: Human-readable description of what you're trying to retrieve

        Returns:
            Dictionary containing:
            - data: List of transaction dictionaries matching the amount range
            - description: The description you provided, or auto-generated if empty

        Common Usage:
            - "Large necessity purchases" → jar_name="necessities", min_amount=100.0
            - "Small play expenses" → jar_name="play", max_amount=25.0
            - "Mid-range spending" → min_amount=20.0, max_amount=100.0
            - "All expensive purchases" → min_amount=200.0
        """
        try:
            return await TransactionQueryService.get_amount_range_transactions(
                services.db, services.user_id, jar_name=jar_name, min_amount=min_amount, max_amount=max_amount, limit=limit, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch amount range transactions: {str(e)}",
                "description": f"Error while {description}" if description else "Error fetching amount range transactions"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error fetching amount range transactions"
            }

    @tool
    async def get_hour_range_transactions(jar_name: Optional[str] = None, start_hour: int = 6, end_hour: int = 22, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """
        Retrieve transactions within a specific hour range, optionally filtered by jar.
        
        Purpose: Filter transactions by time of day. Useful for understanding spending patterns.
        
        Args:
            jar_name: Budget jar name or None
                - Specific jar: "necessities", "long_term_savings", "play", "education", "financial_freedom", "give"
                - None: All jars
                
            start_hour: Starting hour (24-hour format, 0-23)
                - Example: 9 for "9:00 AM and later"
                - Default: 6 (6:00 AM)
                
            end_hour: Ending hour (24-hour format, 0-23)
                - Example: 17 for "until 5:00 PM"
                - Default: 22 (10:00 PM)
                
            limit: Maximum number of transactions to return (default: 50)
            
            description: Human-readable description of what you're trying to retrieve
        
        Returns:
            Dictionary containing:
            - data: List of transaction dictionaries matching the hour range
            - description: The description you provided, or auto-generated if empty
        
        Common Usage:
            - "Morning necessity purchases" → jar_name="necessities", start_hour=6, end_hour=11
            - "Lunch transactions" → jar_name="necessities", start_hour=11, end_hour=14
            - "Evening play activities" → jar_name="play", start_hour=18, end_hour=23
            - "Business hours spending" → start_hour=9, end_hour=17
        """
        try:
            return await TransactionQueryService.get_hour_range_transactions(
                services.db, services.user_id, jar_name=jar_name, start_hour=start_hour, end_hour=end_hour, limit=limit, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch hour range transactions: {str(e)}",
                "description": f"Error while {description}" if description else "Error fetching hour range transactions"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error fetching hour range transactions"
            }

    @tool
    async def get_source_transactions(jar_name: Optional[str] = None, source_type: str = "vpbank_api", limit: int = 50, description: str = "") -> Dict[str, Any]:
        """
        Retrieve transactions from a specific source, optionally filtered by jar.
        
        Purpose: Filter transactions by how they were recorded/entered into the system.
        
        Args:
            jar_name: Budget jar name or None
                - Specific jar: "necessities", "long_term_savings", "play", "education", "financial_freedom", "give"
                - None: All jars
                
            source_type: Source of transaction data
                - "vpbank_api": Transactions from VPBank API (automatic bank data)
                - "manual_input": Manually entered transactions
                - "text_input": Voice/text input transactions
                - "image_input": Transactions from scanned receipts/images
                - Default: "vpbank_api"
                
            limit: Maximum number of transactions to return (default: 50)
            
            description: Human-readable description of what you're trying to retrieve
        
        Returns:
            Dictionary containing:
            - data: List of transaction dictionaries from the specified source
            - description: The description you provided, or auto-generated if empty
        
        Common Usage:
            - "Bank transactions" → source_type="vpbank_api"
            - "Manually entered necessities" → jar_name="necessities", source_type="manual_input"
            - "Scanned receipts" → source_type="image_input"
            - "Voice input transactions" → source_type="text_input"
        """
        try:
            return await TransactionQueryService.get_source_transactions(
                services.db, services.user_id, jar_name=jar_name, source_type=source_type, limit=limit, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch source transactions: {str(e)}",
                "description": f"Error while {description}" if description else "Error fetching source transactions"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error fetching source transactions"
            }

    @tool
    async def get_complex_transaction(
        jar_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        source_type: Optional[str] = None,
        limit: int = 50,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        **COMPLEX MULTI-DIMENSIONAL TRANSACTION FILTERING**
        
        Use this tool ONLY for complex queries that require multiple filters simultaneously.
        For simple single-filter queries, use the specific tools instead.
        
        Purpose: Handle complex queries like Vietnamese "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
        Translation: "show me lunch information (11am -> 2pm) under $20"
        → jar_name="meals", start_hour=11, end_hour=14, max_amount=20
        
        Args:
            jar_name: Budget jar name or None
                - Specific jar: "necessities", "long_term_savings", "play", "education", "financial_freedom", "give"
                - None: All jars
                
            start_date: Start date filter (optional)
                - Format: "YYYY-MM-DD" or relative dates like "last_month", "last_week", "today"
                - None: No start date filter
                
            end_date: End date filter (optional)
                - Format: "YYYY-MM-DD" or relative dates
                - None: Defaults to today if start_date is provided
                
            min_amount: Minimum amount filter (optional)
                - Example: 20.0 for "over $20"
                - None: No minimum amount filter
                
            max_amount: Maximum amount filter (optional)
                - Example: 50.0 for "under $50"
                - None: No maximum amount filter
                
            start_hour: Starting hour filter (24-hour format, 0-23, optional)
                - Example: 11 for "after 11 AM"
                - None: No start hour filter
                
            end_hour: Ending hour filter (24-hour format, 0-23, optional)
                - Example: 14 for "before 2 PM"
                - None: No end hour filter
                
            source_type: Transaction source filter (optional)
                - "vpbank_api", "manual_input", "text_input", "image_input"
                - None: All sources
                
            limit: Maximum number of transactions to return (default: 50)
            
            description: Human-readable description of what you're trying to retrieve
                - Example: "lunch transactions between 11am-2pm under $20"
                - This will be returned to help users understand the complex filtering
        
        Returns:
            Dictionary containing:
            - data: List of transactions matching ALL specified filters
            - description: The description you provided, or auto-generated if empty
            
        **WHEN TO USE THIS TOOL:**
        - Queries with 3+ different filter types (jar + time + amount + hour)
        - Complex Vietnamese/multilingual queries with multiple conditions
        - Queries like "breakfast spending last week under $10 from manual entries"
        - Time-specific category queries like "evening entertainment over $30"
        
        **WHEN NOT TO USE (use specific tools instead):**
        - Simple single-filter queries: "necessities spending" → use get_jar_transactions
        - Simple two-filter queries: "necessities last month" → use get_time_period_transactions
        - Simple amount queries: "purchases over $50" → use get_amount_range_transactions
        
        **Example Complex Queries:**
        1. Vietnamese: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
        → jar_name="necessities", start_hour=11, end_hour=14, max_amount=20, description="lunch transactions 11am-2pm under $20"
        
        2. "Show me manual play entries from last week over $30"
        → jar_name="play", start_date="last_week", min_amount=30, source_type="manual_input", description="manual play entries last week over $30"
        
        3. "Morning necessity shopping under $100 from bank data"
        → jar_name="necessities", start_hour=6, end_hour=12, max_amount=100, source_type="vpbank_api", description="morning necessity shopping under $100 from bank"
        """
        try:
            return await TransactionQueryService.get_complex_transaction(
                services.db, services.user_id, jar_name=jar_name, start_date=start_date, end_date=end_date,
                min_amount=min_amount, max_amount=max_amount, start_hour=start_hour,
                end_hour=end_hour, source_type=source_type, limit=limit, description=description
            )
        except ValueError as e:
            # Service validation errors
            return {
                "data": [],
                "error": f"Failed to fetch complex transaction query: {str(e)}",
                "description": f"Error while {description}" if description else "Error executing complex transaction query"
            }
        except Exception as e:
            # Unexpected errors
            return {
                "data": [],
                "error": f"An unexpected error occurred: {str(e)}",
                "description": f"Error while {description}" if description else "Unexpected error executing complex transaction query"
            }

    return [
        get_jar_transactions,
        get_time_period_transactions,
        get_amount_range_transactions,
        get_hour_range_transactions,
        get_source_transactions,
        get_complex_transaction
    ]