"""
Tools for the FeeManager Agent.
Handles recurring fees and subscriptions with mocked data.
"""

from langchain_core.tools import tool
from typing import Optional
import uuid


# Mock data storage for recurring fees
MOCK_FEES = [
    {
        "fee_id": "fee_001",
        "name": "Netflix subscription",
        "amount": 15.99,
        "jar_id": "jar_play",
        "recurrence": {"unit": "monthly", "days": [1]}
    },
    {
        "fee_id": "fee_002",
        "name": "Gym membership", 
        "amount": 50.00,
        "jar_id": "jar_nec",
        "recurrence": {"unit": "monthly", "days": [15]}
    }
]


@tool
def get_all_fees() -> list:
    """Retrieves a list of all recurring fees."""
    return MOCK_FEES.copy()


@tool
def add_recurring_fee(name: str, amount: float, jar_id: str, recurrence: dict) -> dict:
    """
    Adds a new recurring fee.
    
    Args:
        name: Name of the recurring fee
        amount: Fee amount  
        jar_id: ID of the jar to charge this fee to
        recurrence: Recurrence pattern like {"unit": "monthly", "days": [15]}
    
    Returns:
        Success status and new fee details
    """
    # Validate recurrence structure
    valid_units = ["daily", "weekly", "monthly"]
    if recurrence.get("unit") not in valid_units:
        return {
            "success": False,
            "error": f"Invalid recurrence unit. Must be one of: {valid_units}"
        }
    
    # Create new fee
    new_fee = {
        "fee_id": f"fee_{uuid.uuid4().hex[:8]}",
        "name": name,
        "amount": amount,
        "jar_id": jar_id,
        "recurrence": recurrence
    }
    
    MOCK_FEES.append(new_fee)
    
    return {
        "success": True,
        "fee": new_fee,
        "message": f"Created recurring fee '{name}' for ${amount}"
    }


@tool
def update_recurring_fee(
    fee_id: str, 
    name: Optional[str] = None,
    amount: Optional[float] = None, 
    jar_id: Optional[str] = None,
    recurrence: Optional[dict] = None
) -> dict:
    """
    Modifies an existing fee.
    
    Args:
        fee_id: ID of the fee to update
        name: New name (optional)
        amount: New amount (optional)
        jar_id: New jar ID (optional)
        recurrence: New recurrence pattern (optional)
    
    Returns:
        Success status and updated fee details
    """
    # Find fee to update
    fee_to_update = None
    for fee in MOCK_FEES:
        if fee["fee_id"] == fee_id:
            fee_to_update = fee
            break
    
    if not fee_to_update:
        return {
            "success": False,
            "error": f"Fee with ID '{fee_id}' not found"
        }
    
    # Update fields if provided
    if name is not None:
        fee_to_update["name"] = name
    if amount is not None:
        fee_to_update["amount"] = amount
    if jar_id is not None:
        fee_to_update["jar_id"] = jar_id
    if recurrence is not None:
        # Validate recurrence structure
        valid_units = ["daily", "weekly", "monthly"]
        if recurrence.get("unit") not in valid_units:
            return {
                "success": False,
                "error": f"Invalid recurrence unit. Must be one of: {valid_units}"
            }
        fee_to_update["recurrence"] = recurrence
    
    return {
        "success": True,
        "fee": fee_to_update,
        "message": f"Updated recurring fee '{fee_to_update['name']}'"
    }


@tool
def delete_recurring_fee(fee_id: str) -> dict:
    """
    Deletes a recurring fee.
    
    Args:
        fee_id: ID of the fee to delete
    
    Returns:
        Success status and message
    """
    # Find fee to delete
    fee_to_delete = None
    fee_index = None
    for i, fee in enumerate(MOCK_FEES):
        if fee["fee_id"] == fee_id:
            fee_to_delete = fee
            fee_index = i
            break
    
    if not fee_to_delete:
        return {
            "success": False,
            "error": f"Fee with ID '{fee_id}' not found"
        }
    
    # Remove fee
    deleted_fee_name = fee_to_delete["name"]
    MOCK_FEES.pop(fee_index)
    
    return {
        "success": True,
        "message": f"Deleted recurring fee '{deleted_fee_name}'"
    } 