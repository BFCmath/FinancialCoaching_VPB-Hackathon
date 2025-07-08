"""
Tools for the BudgetAdvisor Agent.
Provides read-only financial data access for planning purposes.
"""

from langchain_core.tools import tool


@tool
def get_income() -> float:
    """Retrieves the user's total monthly income."""
    return 5000.0  # Mock monthly income


# Note: BudgetAdvisor also uses get_all_jars, get_transaction_history, 
# and get_all_fees from other tool modules, but they're imported in __init__.py 