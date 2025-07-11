"""
Classification Tools for LLM-Powered Transaction Classifier
============================================================

Tools that the LLM can call to handle transaction classification actions.
"""

from langchain_core.tools import tool
from typing import List, Dict, Any

# Mock data for testing budget tracking
MOCK_JARS = [
    # --- Essential & High-Priority Expenses ---
    {
        "name": "rent",
        "budget": 1250,
        "current": 1250,  # Covers February 1st payment
        "description": "Monthly rent or mortgage payment for housing"
    },
    {
        "name": "groceries",
        "budget": 400,
        "current": 270,  # Total of February grocery purchases ($70 + $80 + $120)
        "description": "Food and household essentials from supermarkets"
    },
    {
        "name": "utilities",
        "budget": 200,
        "current": 65,  # Reflects February 2nd internet bill
        "description": "Essential services like electricity, water, and internet"
    },
    {
        "name": "gas",
        "budget": 200,
        "current": 103,  # Total of February gas station fill-ups ($55 + $48)
        "description": "Fuel and vehicle-related expenses"
    },

    # --- Daily & Variable Expenses ---
    {
        "name": "meals",
        "budget": 500,
        "current": 212,  # Total of February dining and takeout expenses
        "description": "Dining out, food delivery, and coffee shop purchases"
    },
    {
        "name": "transport",
        "budget": 100,
        "current": 18,  # Public transit and rideshare costs
        "description": "Public transportation, taxis, and rideshare services"
    },

    # # --- Lifestyle & Discretionary Expenses ---
    # {
    #     "name": "shopping",
    #     "budget": 150,
    #     "current": 35,  # Reflects February 7th gift purchase
    #     "description": "Clothing, electronics, and household goods"
    # },
    # {
    #     "name": "entertainment",
    #     "budget": 150,
    #     "current": 75,  # Total of February entertainment costs ($45 + $30)
    #     "description": "Movies, concerts, and recreational activities"
    # },
    # {
    #     "name": "personal_care",
    #     "budget": 100,
    #     "current": 55,  # Reflects February 16th skincare purchase
    #     "description": "Haircuts, toiletries, and personal care products"
    # },
    # {
    #     "name": "health",
    #     "budget": 75,
    #     "current": 15,  # Reflects February 15th vitamins purchase
    #     "description": "Medical expenses, prescriptions, and wellness products"
    # },
    # {
    #     "name": "subscriptions",
    #     "budget": 50,
    #     "current": 27.98,  # Includes Netflix ($15.99) and Spotify ($11.99)
    #     "description": "Streaming services, software, and recurring memberships"
    # }
]

MOCK_TRANSACTIONS = [
    # --- Start of January ---
    {"amount": 1250, "jar": "rent", "description": "January Rent Payment", "date": "2024-01-01"},
    {"amount": 65, "jar": "utilities", "description": "Internet Bill", "date": "2024-01-02"},
    {"amount": 15, "jar": "meals", "description": "Lunch at work cafe", "date": "2024-01-02"},
    {"amount": 6, "jar": "meals", "description": "Morning coffee", "date": "2024-01-03"},
    {"amount": 12, "jar": "meals", "description": "Sandwich for lunch", "date": "2024-01-03"},
    {"amount": 85, "jar": "groceries", "description": "Weekly grocery shopping", "date": "2024-01-04"},
    {"amount": 15.99, "jar": "subscriptions", "description": "Netflix Subscription", "date": "2024-01-05"},
    {"amount": 45, "jar": "meals", "description": "Dinner with a friend", "date": "2024-01-05"},
    {"amount": 55, "jar": "gas", "description": "Fill up gas tank", "date": "2024-01-06"},
    {"amount": 35, "jar": "shopping", "description": "New sweater", "date": "2024-01-06"},
    {"amount": 22, "jar": "meals", "description": "Sunday brunch", "date": "2024-01-07"},
    {"amount": 7, "jar": "meals", "description": "Coffee and a pastry", "date": "2024-01-08"},
    {"amount": 14, "jar": "meals", "description": "Burrito bowl for lunch", "date": "2024-01-08"},
    {"amount": 30, "jar": "meals", "description": "Pizza delivery", "date": "2024-01-09"},
    {"amount": 8, "jar": "groceries", "description": "Milk and bread", "date": "2024-01-10"},
    {"amount": 11.99, "jar": "subscriptions", "description": "Spotify Premium", "date": "2024-01-10"},
    {"amount": 12, "jar": "transport", "description": "Taxi ride", "date": "2024-01-11"},
    {"amount": 16, "jar": "meals", "description": "Sushi lunch", "date": "2024-01-11"},
    {"amount": 50, "jar": "gas", "description": "Fill up tank", "date": "2024-01-12"},
    {"amount": 38, "jar": "entertainment", "description": "Drinks with coworkers", "date": "2024-01-12"},
    {"amount": 45, "jar": "groceries", "description": "Weekly shopping", "date": "2024-01-13"},
    {"amount": 30, "jar": "personal_care", "description": "Haircut", "date": "2024-01-13"},
    {"amount": 15, "jar": "meals", "description": "Lunch takeout", "date": "2024-01-14"},
    {"amount": 25, "jar": "meals", "description": "Dinner at restaurant", "date": "2024-01-15"},
    {"amount": 18, "jar": "meals", "description": "Lunch at cafe", "date": "2024-01-15"},
    {"amount": 6, "jar": "meals", "description": "Morning coffee", "date": "2024-01-16"},
    {"amount": 15, "jar": "meals", "description": "Salad bar lunch", "date": "2024-01-16"},
    {"amount": 28, "jar": "meals", "description": "Thai food delivery", "date": "2024-01-17"},
    {"amount": 5, "jar": "meals", "description": "Coffee run", "date": "2024-01-18"},
    {"amount": 20, "jar": "meals", "description": "Team lunch", "date": "2024-01-19"},
    {"amount": 115, "jar": "groceries", "description": "Big grocery haul", "date": "2024-01-20"},
    {"amount": 32, "jar": "entertainment", "description": "Movie tickets and snacks", "date": "2024-01-20"},
    {"amount": 25, "jar": "shopping", "description": "New book", "date": "2024-01-21"},
    {"amount": 52, "jar": "gas", "description": "Fill up tank", "date": "2024-01-22"},
    {"amount": 13, "jar": "meals", "description": "Pho for lunch", "date": "2024-01-22"},
    {"amount": 18, "jar": "health", "description": "Pharmacy - cold medicine", "date": "2024-01-23"},
    {"amount": 7, "jar": "meals", "description": "Coffee and bagel", "date": "2024-01-24"},
    {"amount": 75, "jar": "utilities", "description": "Electricity Bill", "date": "2024-01-25"},
    {"amount": 17, "jar": "meals", "description": "Lunch with coworker", "date": "2024-01-25"},
    {"amount": 60, "jar": "meals", "description": "Date night dinner", "date": "2024-01-26"},
    {"amount": 25, "jar": "transport", "description": "Uber to event", "date": "2024-01-26"},
    {"amount": 95, "jar": "groceries", "description": "Weekly groceries", "date": "2024-01-27"},
    {"amount": 40, "jar": "shopping", "description": "Kitchen supplies", "date": "2024-01-28"},
    {"amount": 6, "jar": "meals", "description": "Morning coffee", "date": "2024-01-29"},
    {"amount": 16, "jar": "meals", "description": "Lunch takeout", "date": "2024-01-29"},
    {"amount": 22, "jar": "meals", "description": "Chinese food for dinner", "date": "2024-01-30"},
    {"amount": 12, "jar": "groceries", "description": "Snacks and drinks", "date": "2024-01-31"},

    # --- Start of February ---
    {"amount": 1250, "jar": "rent", "description": "February Rent Payment", "date": "2024-02-01"},
    {"amount": 65, "jar": "utilities", "description": "Internet Bill", "date": "2024-02-02"},
    {"amount": 14, "jar": "meals", "description": "Sandwich and soup", "date": "2024-02-02"},
    {"amount": 55, "jar": "gas", "description": "Fill up tank", "date": "2024-02-03"},
    {"amount": 70, "jar": "groceries", "description": "Weekend grocery run", "date": "2024-02-03"},
    {"amount": 15.99, "jar": "subscriptions", "description": "Netflix Subscription", "date": "2024-02-05"},
    {"amount": 7, "jar": "meals", "description": "Coffee and a muffin", "date": "2024-02-05"},
    {"amount": 13, "jar": "meals", "description": "Work cafe lunch", "date": "2024-02-06"},
    {"amount": 35, "jar": "shopping", "description": "Gift for friend's birthday", "date": "2024-02-07"},
    {"amount": 26, "jar": "meals", "description": "Indian takeout", "date": "2024-02-08"},
    {"amount": 45, "jar": "entertainment", "description": "Bowling with friends", "date": "2024-02-09"},
    {"amount": 11.99, "jar": "subscriptions", "description": "Spotify Premium", "date": "2024-02-10"},
    {"amount": 80, "jar": "groceries", "description": "Weekly shopping", "date": "2024-02-10"},
    {"amount": 25, "jar": "meals", "description": "Brunch with family", "date": "2024-02-11"},
    {"amount": 6, "jar": "meals", "description": "Morning coffee", "date": "2024-02-12"},
    {"amount": 17, "jar": "meals", "description": "Lunch meeting", "date": "2024-02-12"},
    {"amount": 48, "jar": "gas", "description": "Fill up tank", "date": "2024-02-13"},
    {"amount": 75, "jar": "meals", "description": "Valentine's Day dinner", "date": "2024-02-14"},
    {"amount": 15, "jar": "health", "description": "Vitamins and supplements", "date": "2024-02-15"},
    {"amount": 14, "jar": "meals", "description": "Lunch at sandwich shop", "date": "2024-02-15"},
    {"amount": 55, "jar": "personal_care", "description": "Skincare products", "date": "2024-02-16"},
    {"amount": 40, "jar": "meals", "description": "Friday night pizza", "date": "2024-02-16"},
    {"amount": 120, "jar": "groceries", "description": "Stock up on groceries", "date": "2024-02-17"},
    {"amount": 18, "jar": "transport", "description": "Round trip train ticket", "date": "2024-02-18"},
    {"amount": 30, "jar": "entertainment", "description": "Museum admission", "date": "2024-02-18"},
    {"amount": 7, "jar": "meals", "description": "Coffee to go", "date": "2024-02-19"},
    {"amount": 16, "jar": "meals", "description": "Pasta for lunch", "date": "2024-02-19"}
]


# Utility functions for fetching data
def fetch_jar_information() -> List[Dict[str, Any]]:
    """Fetch current jar information with budgets and descriptions."""
    return MOCK_JARS.copy()


def fetch_past_transactions() -> List[Dict[str, Any]]:
    """Fetch recent transaction history for pattern recognition."""
    return MOCK_TRANSACTIONS.copy()


# LLM Classification Tools
@tool
def add_money_to_jar_with_confidence(amount: float, jar_name: str, confidence: int) -> str:
    """Add money to the specified jar with confidence score (0-100)."""
    # Mock implementation - would update jar balance in real system
    jar_found = any(jar["name"] == jar_name for jar in MOCK_JARS)
    if not jar_found:
        return f"❌ Error: Jar '{jar_name}' not found"
    
    # Format output based on confidence level
    if confidence >= 90:
        return f"✅ Added ${amount} to {jar_name} jar ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ Added ${amount} to {jar_name} jar ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ Added ${amount} to {jar_name} jar ({confidence}% confident - please verify)"


@tool
def report_no_suitable_jar(description: str, suggestion: str) -> str:
    """Report when no existing jar matches the transaction."""
    return f"❌ Cannot classify '{description}'. {suggestion}"


@tool
def request_more_info(question: str) -> str:
    """Ask user for more information when input is ambiguous."""
    return f"❓ {question}"


# List of all tools for LLM binding
CLASSIFICATION_TOOLS = [
    add_money_to_jar_with_confidence,
    report_no_suitable_jar,
    request_more_info
]
