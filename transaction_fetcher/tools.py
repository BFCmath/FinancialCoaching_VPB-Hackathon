"""
Transaction Retrieval Tools for History Fetcher
===============================================

5 specialized tools for retrieving transaction data with LangChain tool binding.
Each tool provides different filtering capabilities for comprehensive data access.
"""

from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import re

# Mock database of budget jars (matches classifier system structure)
JARS_DATABASE = [
    # --- Essential & High-Priority Expenses ---
    {
        "name": "rent",
        "budget": 1250,
        "current": 1250,
        "description": "Monthly rent or mortgage payment for housing"
    },
    {
        "name": "groceries", 
        "budget": 400,
        "current": 270,
        "description": "Food and household essentials from supermarkets"
    },
    {
        "name": "utilities",
        "budget": 200,
        "current": 65,
        "description": "Essential services like electricity, water, and internet"
    },
    {
        "name": "transportation",
        "budget": 200,
        "current": 103,
        "description": "Fuel, parking, and vehicle-related expenses"
    },
    # --- Daily & Variable Expenses ---
    {
        "name": "meals",
        "budget": 500,
        "current": 212,
        "description": "Dining out, food delivery, and coffee shop purchases"
    },
    {
        "name": "entertainment",
        "budget": 150,
        "current": 85,
        "description": "Movies, games, subscriptions, and leisure activities"
    },
    {
        "name": "health",
        "budget": 100,
        "current": 45,
        "description": "Medical expenses, pharmacy, and wellness"
    },
]

def fetch_available_jars() -> List[Dict]:
    """Get available budget jars from database (same structure as classifier)"""
    return JARS_DATABASE.copy()

def get_jar_names() -> List[str]:
    """Get list of jar names only"""
    return [jar["name"] for jar in JARS_DATABASE]

# Enhanced mock transaction data for testing
MOCK_TRANSACTIONS = [
    # January 2024 transactions
    {"amount": 1250, "jar": "rent", "description": "January Rent Payment", "date": "2024-01-01", "time": "09:00", "source": "vpbank_api"},
    {"amount": 65, "jar": "utilities", "description": "Internet Bill", "date": "2024-01-02", "time": "14:30", "source": "vpbank_api"},
    {"amount": 15, "jar": "meals", "description": "Lunch at work cafe", "date": "2024-01-02", "time": "12:15", "source": "manual_input"},
    {"amount": 6, "jar": "meals", "description": "Morning coffee", "date": "2024-01-03", "time": "08:30", "source": "manual_input"},
    {"amount": 85, "jar": "groceries", "description": "Weekly grocery shopping", "date": "2024-01-04", "time": "10:45", "source": "vpbank_api"},
    {"amount": 15.99, "jar": "entertainment", "description": "Netflix Subscription", "date": "2024-01-05", "time": "16:00", "source": "vpbank_api"},
    {"amount": 45, "jar": "meals", "description": "Dinner with a friend", "date": "2024-01-05", "time": "19:30", "source": "text_input"},
    {"amount": 55, "jar": "transportation", "description": "Fill up gas tank", "date": "2024-01-06", "time": "17:45", "source": "vpbank_api"},
    {"amount": 22, "jar": "meals", "description": "Sunday brunch", "date": "2024-01-07", "time": "11:00", "source": "manual_input"},
    {"amount": 30, "jar": "meals", "description": "Pizza delivery", "date": "2024-01-09", "time": "20:15", "source": "text_input"},
    {"amount": 11.99, "jar": "entertainment", "description": "Spotify Premium", "date": "2024-01-10", "time": "10:00", "source": "vpbank_api"},
    {"amount": 12, "jar": "transportation", "description": "Taxi ride", "date": "2024-01-11", "time": "14:20", "source": "manual_input"},
    {"amount": 50, "jar": "transportation", "description": "Fill up tank", "date": "2024-01-12", "time": "18:00", "source": "vpbank_api"},
    {"amount": 95, "jar": "groceries", "description": "Weekly groceries", "date": "2024-01-13", "time": "09:30", "source": "image_input"},
    {"amount": 30, "jar": "health", "description": "Pharmacy visit", "date": "2024-01-15", "time": "16:45", "source": "manual_input"},
    {"amount": 75, "jar": "utilities", "description": "Electricity Bill", "date": "2024-01-25", "time": "15:00", "source": "vpbank_api"},
    {"amount": 25, "jar": "transportation", "description": "Uber to event", "date": "2024-01-26", "time": "19:00", "source": "manual_input"},
    {"amount": 120, "jar": "groceries", "description": "Monthly stock-up", "date": "2024-01-27", "time": "10:15", "source": "vpbank_api"},
    
    # February 2024 transactions
    {"amount": 1250, "jar": "rent", "description": "February Rent Payment", "date": "2024-02-01", "time": "09:00", "source": "vpbank_api"},
    {"amount": 65, "jar": "utilities", "description": "Internet Bill", "date": "2024-02-02", "time": "14:30", "source": "vpbank_api"},
    {"amount": 14, "jar": "meals", "description": "Sandwich and soup", "date": "2024-02-02", "time": "12:30", "source": "manual_input"},
    {"amount": 55, "jar": "transportation", "description": "Fill up tank", "date": "2024-02-03", "time": "08:15", "source": "vpbank_api"},
    {"amount": 70, "jar": "groceries", "description": "Weekend grocery run", "date": "2024-02-03", "time": "10:30", "source": "vpbank_api"},
    {"amount": 7, "jar": "meals", "description": "Coffee and a muffin", "date": "2024-02-05", "time": "08:45", "source": "manual_input"},
    {"amount": 26, "jar": "meals", "description": "Indian takeout", "date": "2024-02-08", "time": "19:45", "source": "text_input"},
    {"amount": 45, "jar": "entertainment", "description": "Bowling with friends", "date": "2024-02-09", "time": "20:00", "source": "manual_input"},
    {"amount": 80, "jar": "groceries", "description": "Weekly shopping", "date": "2024-02-10", "time": "09:15", "source": "image_input"},
    {"amount": 25, "jar": "meals", "description": "Brunch with family", "date": "2024-02-11", "time": "11:30", "source": "manual_input"},
    {"amount": 48, "jar": "transportation", "description": "Fill up tank", "date": "2024-02-13", "time": "17:30", "source": "vpbank_api"},
    {"amount": 75, "jar": "meals", "description": "Valentine's Day dinner", "date": "2024-02-14", "time": "19:00", "source": "manual_input"},
    {"amount": 15, "jar": "health", "description": "Vitamins and supplements", "date": "2024-02-15", "time": "16:30", "source": "manual_input"},
    {"amount": 40, "jar": "meals", "description": "Friday night pizza", "date": "2024-02-16", "time": "20:30", "source": "text_input"},
    {"amount": 120, "jar": "groceries", "description": "Stock up on groceries", "date": "2024-02-17", "time": "10:00", "source": "vpbank_api"},
    {"amount": 18, "jar": "transportation", "description": "Round trip train ticket", "date": "2024-02-18", "time": "14:00", "source": "vpbank_api"},
    {"amount": 30, "jar": "entertainment", "description": "Museum admission", "date": "2024-02-18", "time": "15:30", "source": "manual_input"},
    {"amount": 16, "jar": "meals", "description": "Pasta for lunch", "date": "2024-02-19", "time": "12:45", "source": "manual_input"},
    
    # March 2024 transactions (current month)
    {"amount": 1250, "jar": "rent", "description": "March Rent Payment", "date": "2024-03-01", "time": "09:00", "source": "vpbank_api"},
    {"amount": 8, "jar": "meals", "description": "Morning coffee", "date": "2024-03-02", "time": "08:00", "source": "manual_input"},
    {"amount": 85, "jar": "groceries", "description": "Weekend grocery shopping", "date": "2024-03-02", "time": "10:30", "source": "vpbank_api"},
    {"amount": 12, "jar": "meals", "description": "Quick lunch", "date": "2024-03-03", "time": "12:15", "source": "manual_input"},
    {"amount": 60, "jar": "transportation", "description": "Gas station fill-up", "date": "2024-03-04", "time": "18:00", "source": "vpbank_api"},
    {"amount": 22, "jar": "meals", "description": "Dinner takeout", "date": "2024-03-05", "time": "19:15", "source": "text_input"},
    {"amount": 95, "jar": "groceries", "description": "Weekly grocery trip", "date": "2024-03-06", "time": "09:45", "source": "image_input"},
    {"amount": 35, "jar": "entertainment", "description": "Movie tickets", "date": "2024-03-07", "time": "19:30", "source": "manual_input"},
    {"amount": 7.50, "jar": "meals", "description": "Coffee break", "date": "2024-03-08", "time": "15:30", "source": "manual_input"},
    {"amount": 42, "jar": "meals", "description": "Friday lunch special", "date": "2024-03-08", "time": "12:00", "source": "manual_input"},
]

def parse_flexible_date(date_str: str) -> date:
    """Parse various date formats including relative dates."""
    if not date_str:
        return datetime.now().date()
    
    date_str = date_str.lower().strip()
    today = datetime.now().date()
    
    relative_dates = {
        "today": today,
        "yesterday": today - timedelta(days=1),
        "last_week": today - timedelta(weeks=1),
        "last_month": today - timedelta(days=30),
        "this_month": today.replace(day=1),
        "last_year": today - timedelta(days=365),
        "this_week": today - timedelta(days=today.weekday())
    }
    
    if date_str in relative_dates:
        return relative_dates[date_str]
    
    # Try parsing as YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Default to today
    return today

def time_in_range(transaction_time: str, start_hour: int, end_hour: int) -> bool:
    """Check if transaction time falls within hour range."""
    try:
        hour = int(transaction_time.split(":")[0])
        
        if start_hour <= end_hour:  # Normal range (e.g., 9-17)
            return start_hour <= hour <= end_hour
        else:  # Overnight range (e.g., 22-6)
            return hour >= start_hour or hour <= end_hour
    except (ValueError, IndexError):
        return False

# ==========================================
# TRANSACTION RETRIEVAL TOOLS (5 Core Tools)
# ==========================================

@tool
def get_jar_transactions(jar_name: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
    """
    Retrieve all transactions for a specific budget jar/category or all jars.
    
    Purpose: Get transactions filtered by spending category (jar). Most commonly used tool.
    
    Args:
        jar_name: Budget jar name or None
            - Specific jar: "groceries", "meals", "entertainment", "transportation", "health", "utilities", "rent"
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
        - "Show me groceries" → jar_name="groceries", description="groceries spending"
        - "All my spending" → jar_name=None, description="all my transactions"
        - "Entertainment transactions" → jar_name="entertainment", description="entertainment expenses"
    """
    matches = []
    
    for transaction in MOCK_TRANSACTIONS:
        # If jar_name is None, include all transactions
        if jar_name is None or transaction["jar"].lower() == jar_name.lower():
            matches.append(transaction.copy())
    
    # Sort by date (newest first) and limit results
    matches.sort(key=lambda t: t["date"], reverse=True)
    limited_matches = matches[:limit]
    
    # Use provided description or generate one if empty
    if description.strip():
        final_description = description.strip()
    else:
        # Fallback auto-generation
        if jar_name is None:
            final_description = "All transactions across all budget categories"
        else:
            final_description = f"All {jar_name} transactions"
        
        if limit < len(matches):
            final_description += f" (showing {limit} most recent)"
    
    return {
        "data": limited_matches,
        "description": final_description
    }

@tool
def get_time_period_transactions(jar_name: str = None, start_date: str = "last_month", end_date: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
    """
    Retrieve transactions within a specific time period, optionally filtered by jar.
    
    Purpose: Filter transactions by date range. Supports relative dates and specific dates.
    
    Args:
        jar_name: Budget jar name or None
            - Specific jar: "groceries", "meals", "entertainment", etc.
            - None: All jars
            
        start_date: Start date for filtering
            - Relative: "today", "yesterday", "last_week", "last_month", "this_month", "last_year", "this_week"
            - Specific: "2024-02-01" (YYYY-MM-DD format)
            - Default: "last_month"
            
        end_date: End date for filtering (optional)
            - Same formats as start_date
            - None: Defaults to today
            
        limit: Maximum number of transactions to return (default: 50)
        
        description: Human-readable description of what you're trying to retrieve
            - Example: "last month's spending", "yesterday's meals", "February transactions"
            - This will be returned to help users and other agents understand the data
    
    Returns:
        Dictionary containing:
        - data: List of transactions within the date range, sorted by date (newest first)
        - description: The description you provided, or auto-generated if empty
        
        Same transaction structure as get_jar_transactions
    
    Common Usage:
        - "Last month spending" → start_date="last_month", description="last month's spending"
        - "Yesterday's meals" → jar_name="meals", start_date="yesterday", description="yesterday's meals"
        - "February transactions" → start_date="2024-02-01", end_date="2024-02-28", description="February transactions"
        - "This week's groceries" → jar_name="groceries", start_date="this_week", description="this week's groceries"
    """
    parsed_start = parse_flexible_date(start_date)
    parsed_end = parse_flexible_date(end_date) if end_date else datetime.now().date()
    
    # Ensure start is before end
    if parsed_start > parsed_end:
        parsed_start, parsed_end = parsed_end, parsed_start
    
    filtered = []
    for transaction in MOCK_TRANSACTIONS:
        # Check jar match (None means all jars)
        jar_match = jar_name is None or transaction["jar"].lower() == jar_name.lower()
        
        if jar_match:
            # Check time match
            trans_date = datetime.strptime(transaction["date"], "%Y-%m-%d").date()
            if parsed_start <= trans_date <= parsed_end:
                filtered.append(transaction.copy())
    
    # Sort by date (newest first) and limit
    filtered.sort(key=lambda t: t["date"], reverse=True)
    limited_filtered = filtered[:limit]
    
    # Use provided description or generate one if empty
    if description.strip():
        final_description = description.strip()
    else:
        # Fallback auto-generation
        if jar_name is None:
            jar_desc = "all transactions"
        else:
            jar_desc = f"{jar_name} transactions"
        
        # Format time period description
        if end_date is None:
            time_desc = f"from {start_date}"
        else:
            time_desc = f"from {start_date} to {end_date}"
        
        final_description = f"Transactions {time_desc} - {jar_desc}"
        
        if limit < len(filtered):
            final_description += f" (showing {limit} most recent)"
    
    return {
        "data": limited_filtered,
        "description": final_description
    }

@tool
def get_amount_range_transactions(jar_name: str = None, min_amount: float = None, max_amount: float = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
    """
    Retrieve transactions within a specific amount range, optionally filtered by jar.
    
    Purpose: Filter transactions by spending amount. Useful for finding large/small purchases.
    
    Args:
        jar_name: Budget jar name or None
            - Specific jar: "groceries", "meals", "entertainment", etc.
            - None: All jars
            
        min_amount: Minimum transaction amount (inclusive)
            - Number: 50.0 (transactions >= $50)
            - None: No minimum limit (gets all amounts down to $0)
            
        max_amount: Maximum transaction amount (inclusive)
            - Number: 100.0 (transactions <= $100)  
            - None: No maximum limit (gets all amounts up to highest)
            
        limit: Maximum number of transactions to return (default: 50)
        
        description: Human-readable description of what you're trying to retrieve
            - Example: "transactions under $10", "large purchases over $100", "medium-sized expenses"
            - This will be returned to help users and other agents understand the data
    
    Returns:
        Dictionary containing:
        - data: List of transactions within amount range, sorted by amount (highest first)
        - description: The description you provided, or auto-generated if empty
        
        Same transaction structure as get_jar_transactions
    
    Common Usage:
        - "Transactions over $100" → min_amount=100, max_amount=None, description="transactions over $100"
        - "Purchases under $15" → min_amount=None, max_amount=15, description="purchases under $15"
        - "Between $25-75" → min_amount=25, max_amount=75, description="transactions between $25-75"
    """
    filtered = []
    
    for transaction in MOCK_TRANSACTIONS:
        # Check jar match (None means all jars)
        jar_match = jar_name is None or transaction["jar"].lower() == jar_name.lower()
        
        if jar_match:
            amount = transaction["amount"]
            
            # Check amount range - None means no limit for that bound
            amount_match = True
            if min_amount is not None and amount < min_amount:
                amount_match = False
            if max_amount is not None and amount > max_amount:
                amount_match = False
                
            if amount_match:
                filtered.append(transaction.copy())
    
    # Sort by amount (highest first) and limit
    filtered.sort(key=lambda t: t["amount"], reverse=True)
    limited_filtered = filtered[:limit]
    
    # Use provided description or generate one if empty
    if description.strip():
        final_description = description.strip()
    else:
        # Fallback auto-generation
        if jar_name is None:
            jar_desc = "all transactions"
        else:
            jar_desc = f"{jar_name} transactions"
        
        # Format amount range description
        if min_amount is not None and max_amount is not None:
            amount_desc = f"between ${min_amount:.2f} and ${max_amount:.2f}"
        elif min_amount is not None:
            amount_desc = f"over ${min_amount:.2f}"
        elif max_amount is not None:
            amount_desc = f"under ${max_amount:.2f}"
        else:
            amount_desc = "all amounts"
        
        final_description = f"Transactions {amount_desc} - {jar_desc}"
        
        if limit < len(filtered):
            final_description += f" (showing {limit} largest)"
    
    return {
        "data": limited_filtered,
        "description": final_description
    }

@tool
def get_hour_range_transactions(jar_name: str = None, start_hour: int = 6, end_hour: int = 22, limit: int = 50, description: str = "") -> Dict[str, Any]:
    """
    Retrieve transactions within specific hours of the day, optionally filtered by jar.
    
    Purpose: Analyze spending behavior by time of day. Useful for behavioral insights.
    
    Args:
        jar_name: Budget jar name or None
            - Specific jar: "groceries", "meals", "entertainment", etc.
            - None: All jars
            
        start_hour: Starting hour (24-hour format, 0-23)
            - Examples: 6 (6 AM), 18 (6 PM), 9 (9 AM)
            
        end_hour: Ending hour (24-hour format, 0-23, inclusive)
            - Examples: 12 (12 PM), 23 (11 PM), 17 (5 PM)
            
        limit: Maximum number of transactions to return (default: 50)
        
        description: Human-readable description of what you're trying to retrieve
            - Example: "morning purchases", "evening spending", "lunch time meals"
            - This will be returned to help users and other agents understand the data
    
    Returns:
        Dictionary containing:
        - data: List of transactions within time range, sorted by time
        - description: The description you provided, or auto-generated if empty
        
        Same transaction structure as get_jar_transactions
    
    Common Usage:
        - "Morning purchases" → start_hour=6, end_hour=12, description="morning purchases"
        - "Evening spending" → start_hour=18, end_hour=23, description="evening spending"
        - "Business hours" → start_hour=9, end_hour=17, description="business hours transactions"
        - "Late night transactions" → start_hour=22, end_hour=6, description="late night transactions"
        - "Lunch time meals" → jar_name="meals", start_hour=11, end_hour=14, description="lunch time meals"
        - "After work entertainment" → jar_name="entertainment", start_hour=17, end_hour=23, description="after work entertainment"
    
    Note: For overnight ranges (e.g., 22-6), transactions from 22:00-23:59 and 00:00-06:00 are included.
    """
    filtered = []
    
    for transaction in MOCK_TRANSACTIONS:
        # Check jar match (None means all jars)
        jar_match = jar_name is None or transaction["jar"].lower() == jar_name.lower()
        
        if jar_match:
            if "time" in transaction and time_in_range(transaction["time"], start_hour, end_hour):
                filtered.append(transaction.copy())
    
    # Sort by time and limit
    filtered.sort(key=lambda t: t.get("time", "00:00"))
    limited_filtered = filtered[:limit]
    
    # Use provided description or generate one if empty
    if description.strip():
        final_description = description.strip()
    else:
        # Fallback auto-generation
        if jar_name is None:
            jar_desc = "all transactions"
        else:
            jar_desc = f"{jar_name} transactions"
        
        # Format time range description
        def format_hour(hour):
            if hour == 0:
                return "midnight"
            elif hour < 12:
                return f"{hour}:00 AM"
            elif hour == 12:
                return "noon"
            else:
                return f"{hour-12}:00 PM"
        
        if start_hour <= end_hour:
            time_desc = f"from {format_hour(start_hour)} to {format_hour(end_hour)}"
        else:
            time_desc = f"from {format_hour(start_hour)} to {format_hour(end_hour)} (overnight)"
        
        final_description = f"Transactions {time_desc} - {jar_desc}"
        
        if limit < len(filtered):
            final_description += f" (showing {limit} transactions)"
    
    return {
        "data": limited_filtered,
        "description": final_description
    }

@tool
def get_source_transactions(jar_name: str = None, source_type: str = "vpbank_api", limit: int = 50, description: str = "") -> Dict[str, Any]:
    """
    Retrieve transactions by input source/method, optionally filtered by jar.
    
    Purpose: Analyze data quality and entry patterns. Compare different input methods.
    
    Args:
        jar_name: Budget jar name or None
            - Specific jar: "groceries", "meals", "entertainment", etc.
            - None: All jars
            
        source_type: Transaction input source
            - "vpbank_api": Bank-imported transactions (most reliable)
            - "manual_input": Manually typed entries
            - "text_input": Voice-to-text or text input
            - "image_input": Receipt scanning or image recognition
            
        limit: Maximum number of transactions to return (default: 50)
        
        description: Human-readable description of what you're trying to retrieve
            - Example: "bank imported transactions", "manual entries", "scanned receipts"
            - This will be returned to help users and other agents understand the data
    
    Returns:
        Dictionary containing:
        - data: List of transactions from specified source, sorted by date (newest first)
        - description: The description you provided, or auto-generated if empty
        
        Same transaction structure as get_jar_transactions
        
        Returns empty data list if invalid source_type provided
    
    Common Usage:
        - "Bank imported data" → source_type="vpbank_api", description="bank imported transactions"
        - "Manual entries" → source_type="manual_input", description="manual entries"
        - "Voice input transactions" → source_type="text_input", description="voice input transactions"
        - "Scanned receipts" → source_type="image_input", description="scanned receipts"
        - "Manual meal entries" → jar_name="meals", source_type="manual_input", description="manual meal entries"
        - "Bank entertainment data" → jar_name="entertainment", source_type="vpbank_api", description="bank entertainment data"
    
    Use Cases:
        - Data quality analysis: Compare manual vs automated entries
        - Entry method preferences: Which sources are used most?
        - Accuracy verification: Cross-check manual entries with bank data
    """
    valid_sources = ["vpbank_api", "manual_input", "text_input", "image_input"]
    
    if source_type not in valid_sources:
        return {
            "data": [],
            "description": f"Invalid source type: {source_type}"
        }
    
    filtered = []
    for transaction in MOCK_TRANSACTIONS:
        # Check jar match (None means all jars)
        jar_match = jar_name is None or transaction["jar"].lower() == jar_name.lower()
        
        if jar_match:
            if transaction.get("source") == source_type:
                filtered.append(transaction.copy())
    
    # Sort by date (newest first) and limit
    filtered.sort(key=lambda t: t["date"], reverse=True)
    limited_filtered = filtered[:limit]
    
    # Use provided description or generate one if empty
    if description.strip():
        final_description = description.strip()
    else:
        # Fallback auto-generation
        if jar_name is None:
            jar_desc = "all transactions"
        else:
            jar_desc = f"{jar_name} transactions"
        
        # Format source description
        source_descriptions = {
            "vpbank_api": "bank-imported",
            "manual_input": "manually entered", 
            "text_input": "voice/text input",
            "image_input": "receipt scanning"
        }
        
        source_desc = source_descriptions.get(source_type, source_type)
        final_description = f"Transactions from {source_desc} - {jar_desc}"
        
        if limit < len(filtered):
            final_description += f" (showing {limit} most recent)"
    
    return {
        "data": limited_filtered,
        "description": final_description
    }

# Helper function for LangChain tool binding
def get_all_transaction_tools():
    """Return all transaction retrieval tools for LLM binding."""
    return [
        get_jar_transactions,
        get_time_period_transactions,
        get_amount_range_transactions,
        get_hour_range_transactions,
        get_source_transactions,
        get_complex_transaction
    ]

@tool
def get_complex_transaction(
    jar_name: str = None,
    start_date: str = None,
    end_date: str = None,
    min_amount: float = None,
    max_amount: float = None,
    start_hour: int = None,
    end_hour: int = None,
    source_type: str = None,
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
            - Specific jar: "groceries", "meals", "entertainment", "transportation", "health", "utilities", "rent"
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
    - Simple single-filter queries: "groceries spending" → use get_jar_transactions
    - Simple two-filter queries: "groceries last month" → use get_time_period_transactions
    - Simple amount queries: "purchases over $50" → use get_amount_range_transactions
    
    **Example Complex Queries:**
    1. Vietnamese: "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
       → jar_name="meals", start_hour=11, end_hour=14, max_amount=20, description="lunch transactions 11am-2pm under $20"
    
    2. "Show me manual entertainment entries from last week over $30"
       → jar_name="entertainment", start_date="last_week", min_amount=30, source_type="manual_input", description="manual entertainment entries last week over $30"
    
    3. "Morning grocery shopping under $100 from bank data"
       → jar_name="groceries", start_hour=6, end_hour=12, max_amount=100, source_type="vpbank_api", description="morning grocery shopping under $100 from bank"
    """
    
    filtered = []
    
    # Apply all filters step by step
    for transaction in MOCK_TRANSACTIONS:
        # 1. Check jar filter
        if jar_name is not None and transaction["jar"].lower() != jar_name.lower():
            continue
            
        # 2. Check date range filter
        if start_date is not None:
            parsed_start = parse_flexible_date(start_date)
            parsed_end = parse_flexible_date(end_date) if end_date else datetime.now().date()
            
            transaction_date = datetime.strptime(transaction["date"], "%Y-%m-%d").date()
            if not (parsed_start <= transaction_date <= parsed_end):
                continue
        
        # 3. Check amount range filter
        amount = transaction["amount"]
        if min_amount is not None and amount < min_amount:
            continue
        if max_amount is not None and amount > max_amount:
            continue
            
        # 4. Check hour range filter
        if start_hour is not None and end_hour is not None:
            if "time" not in transaction or not time_in_range(transaction["time"], start_hour, end_hour):
                continue
        elif start_hour is not None:
            # Only start hour specified
            try:
                hour = int(transaction["time"].split(":")[0])
                if hour < start_hour:
                    continue
            except (ValueError, IndexError, KeyError):
                continue
        elif end_hour is not None:
            # Only end hour specified
            try:
                hour = int(transaction["time"].split(":")[0])
                if hour > end_hour:
                    continue
            except (ValueError, IndexError, KeyError):
                continue
        
        # 5. Check source filter
        if source_type is not None and transaction.get("source") != source_type:
            continue
            
        # If we get here, transaction passed all filters
        filtered.append(transaction.copy())
    
    # Sort by date (newest first) and limit
    filtered.sort(key=lambda t: t["date"], reverse=True)
    limited_filtered = filtered[:limit]
    
    # Use provided description or generate comprehensive one if empty
    if description.strip():
        final_description = description.strip()
    else:
        # Auto-generate comprehensive description based on active filters
        filter_parts = []
        
        if jar_name:
            filter_parts.append(f"{jar_name} transactions")
        else:
            filter_parts.append("all transactions")
            
        if start_date or end_date:
            if start_date and end_date:
                filter_parts.append(f"from {start_date} to {end_date}")
            elif start_date:
                filter_parts.append(f"from {start_date}")
            elif end_date:
                filter_parts.append(f"until {end_date}")
        
        if min_amount is not None and max_amount is not None:
            filter_parts.append(f"between ${min_amount}-${max_amount}")
        elif min_amount is not None:
            filter_parts.append(f"over ${min_amount}")
        elif max_amount is not None:
            filter_parts.append(f"under ${max_amount}")
            
        if start_hour is not None and end_hour is not None:
            filter_parts.append(f"between {start_hour}:00-{end_hour}:00")
        elif start_hour is not None:
            filter_parts.append(f"after {start_hour}:00")
        elif end_hour is not None:
            filter_parts.append(f"before {end_hour}:00")
            
        if source_type:
            source_names = {
                "vpbank_api": "bank data",
                "manual_input": "manual entries", 
                "text_input": "voice input",
                "image_input": "scanned receipts"
            }
            filter_parts.append(f"from {source_names.get(source_type, source_type)}")
        
        final_description = "Complex filtering: " + " ".join(filter_parts)
        
        if limit < len(filtered):
            final_description += f" (showing {limit} of {len(filtered)} matches)"
    
    return {
        "data": limited_filtered,
        "description": final_description
    }
