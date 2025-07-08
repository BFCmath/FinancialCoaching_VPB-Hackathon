"""
Tools for the TransactionClassifier Agent.
Handles transaction parsing and logging with mocked data.
"""

from langchain_core.tools import tool
from typing import Optional
from datetime import datetime
import uuid


# Mock data storage for transactions
MOCK_TRANSACTIONS = [
    {
        "transaction_id": "txn_001",
        "description": "Starbucks coffee",
        "amount": 5.50,
        "jar_id": "jar_play",
        "timestamp": "2024-01-15T08:30:00Z"
    },
    {
        "transaction_id": "txn_002", 
        "description": "Grocery shopping",
        "amount": 75.20,
        "jar_id": "jar_nec",
        "timestamp": "2024-01-15T18:45:00Z"
    },
    {
        "transaction_id": "txn_003",
        "description": "Gas station",
        "amount": 45.00,
        "jar_id": "jar_nec", 
        "timestamp": "2024-01-16T12:15:00Z"
    }
]


@tool
def log_transaction(description: str, amount: float, jar_id: str) -> dict:
    """
    Logs a transaction to a specific jar and updates the balance.
    
    Args:
        description: Description of the transaction
        amount: Transaction amount
        jar_id: ID of the jar to categorize this transaction
    
    Returns:
        Success status and transaction details
    """
    # Create new transaction
    new_transaction = {
        "transaction_id": f"txn_{uuid.uuid4().hex[:8]}",
        "description": description,
        "amount": amount,
        "jar_id": jar_id,
        "timestamp": datetime.now().isoformat() + "Z"
    }
    
    # Add to mock storage
    MOCK_TRANSACTIONS.append(new_transaction)
    
    # Mock jar balance update (in real system, would update jar balance)
    return {
        "success": True,
        "transaction": new_transaction,
        "message": f"Logged ${amount} for '{description}' to jar {jar_id}"
    }


@tool
def get_transaction_history(jar_id: Optional[str] = None) -> list:
    """
    Retrieves past transactions to learn from user habits.
    
    Args:
        jar_id: Optional jar ID to filter transactions
    
    Returns:
        List of transaction objects
    """
    if jar_id:
        return [txn for txn in MOCK_TRANSACTIONS if txn["jar_id"] == jar_id]
    return MOCK_TRANSACTIONS.copy()


@tool
def find_historical_categorization(description: str) -> dict:
    """
    Calls the InsightGenerator to get the most likely jar for a transaction 
    description based on history.
    
    Args:
        description: Transaction description to analyze
    
    Returns:
        Categorization confidence and suggested jar
    """
    # Mock analysis of historical patterns
    description_lower = description.lower()
    
    # Simple pattern matching for demo
    if any(word in description_lower for word in ['coffee', 'starbucks', 'cafe']):
        return {
            "is_confident": True,
            "most_likely_jar_id": "jar_play",
            "confidence": 0.9,
            "reason": "User historically categorizes coffee purchases as 'Play'"
        }
    elif any(word in description_lower for word in ['grocery', 'food', 'supermarket']):
        return {
            "is_confident": True,
            "most_likely_jar_id": "jar_nec", 
            "confidence": 0.95,
            "reason": "User historically categorizes grocery purchases as 'Necessities'"
        }
    elif any(word in description_lower for word in ['gas', 'fuel', 'shell', 'exxon']):
        return {
            "is_confident": True,
            "most_likely_jar_id": "jar_nec",
            "confidence": 0.85, 
            "reason": "User historically categorizes gas purchases as 'Necessities'"
        }
    elif any(word in description_lower for word in ['dining', 'restaurant', 'lunch', 'dinner']):
        return {
            "is_confident": False,
            "options": ["jar_nec", "jar_play"],
            "reason": "Dining could be either necessity or entertainment - needs clarification"
        }
    else:
        return {
            "is_confident": False,
            "reason": "No clear historical pattern found for this type of transaction"
        } 