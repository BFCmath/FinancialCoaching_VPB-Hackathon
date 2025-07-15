# utils.py
USERS_COLLECTION = "users"
JARS_COLLECTION = "jars"
TRANSACTIONS_COLLECTION = "transactions"
FEES_COLLECTION = "fees"
PLANS_COLLECTION = "plans"
CONVERSATION_HISTORY_COLLECTION = "conversation_history"
AGENT_LOCK_COLLECTION = "agent_locks"
USER_SETTINGS_COLLECTION = "user_settings"

def calculate_percent_from_amount(amount: float, total_income: float = 5000.0) -> float:
    """Convert dollar amount to percentage of total income."""
    return amount / total_income if total_income > 0 else 0.0

def calculate_amount_from_percent(percent: float, total_income: float = 5000.0) -> float:
    """Convert percentage to dollar amount based on total income."""
    return percent * total_income

def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    return f"${amount:,.2f}"

def format_percentage(percent: float) -> str:
    """Format percentage for display (0.15 -> 15.0%)."""
    return f"{percent * 100:.1f}%"

def validate_percentage_range(percent: float) -> bool:
    """Validate percentage is within 0.0-1.0 range."""
    return 0.0 <= percent <= 1.0

def validate_positive_amount(amount: float) -> bool:
    """Validate amount is positive."""
    return amount > 0
