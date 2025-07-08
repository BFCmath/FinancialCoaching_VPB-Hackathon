"""
Tools for the JarManager Agent.
Handles budget jar CRUD operations with mocked data.
"""

from langchain_core.tools import tool
from typing import Optional


# Mock data storage for jars
MOCK_JARS = [
    {
        "jar_id": "jar_nec",
        "name": "Necessities", 
        "percentage": 55.0,
        "type": "spending",
        "balance": 2750.0
    },
    {
        "jar_id": "jar_lts", 
        "name": "Long-Term Savings",
        "percentage": 10.0,
        "type": "investing", 
        "balance": 500.0
    },
    {
        "jar_id": "jar_ffa",
        "name": "Financial Freedom",
        "percentage": 10.0, 
        "type": "investing",
        "balance": 500.0
    },
    {
        "jar_id": "jar_edu",
        "name": "Education",
        "percentage": 10.0,
        "type": "investing",
        "balance": 500.0
    },
    {
        "jar_id": "jar_play",
        "name": "Play", 
        "percentage": 10.0,
        "type": "spending",
        "balance": 500.0
    },
    {
        "jar_id": "jar_give",
        "name": "Give",
        "percentage": 5.0,
        "type": "spending", 
        "balance": 250.0
    }
]


@tool
def get_all_jars() -> list:
    """Retrieves a list of all current jar objects for the user."""
    return MOCK_JARS.copy()


@tool  
def add_jar(name: str, percentage: float, type: str) -> dict:
    """
    Creates a new budget jar.
    
    Args:
        name: Name of the jar
        percentage: Percentage allocation (0-100)
        type: 'spending' or 'investing'
    
    Returns:
        Success status and new jar details
    """
    # Check if total percentage would exceed 100
    current_total = sum(jar["percentage"] for jar in MOCK_JARS)
    if current_total + percentage > 100:
        return {
            "success": False,
            "error": f"Adding {percentage}% would exceed 100% total allocation"
        }
    
    # Generate new jar ID
    new_jar_id = f"jar_{name.lower().replace(' ', '_')}"
    
    # Create new jar
    new_jar = {
        "jar_id": new_jar_id,
        "name": name,
        "percentage": percentage, 
        "type": type,
        "balance": percentage * 50  # Mock calculation based on 5000 income
    }
    
    MOCK_JARS.append(new_jar)
    
    return {
        "success": True,
        "jar": new_jar,
        "message": f"Created '{name}' jar with {percentage}% allocation"
    }


@tool
def update_jar(jar_id: str, name: Optional[str] = None, percentage: Optional[float] = None) -> dict:
    """
    Modifies a jar's name or percentage allocation.
    
    Args:
        jar_id: ID of the jar to update
        name: New name (optional)
        percentage: New percentage (optional)
    
    Returns:
        Success status and updated jar details
    """
    # Find jar to update
    jar_to_update = None
    for jar in MOCK_JARS:
        if jar["jar_id"] == jar_id:
            jar_to_update = jar
            break
    
    if not jar_to_update:
        return {
            "success": False,
            "error": f"Jar with ID '{jar_id}' not found"
        }
    
    # Check percentage constraint if updating percentage
    if percentage is not None:
        current_total = sum(jar["percentage"] for jar in MOCK_JARS if jar["jar_id"] != jar_id)
        if current_total + percentage > 100:
            return {
                "success": False,
                "error": f"New percentage {percentage}% would exceed 100% total allocation"
            }
        
        jar_to_update["percentage"] = percentage
        jar_to_update["balance"] = percentage * 50  # Recalculate balance
    
    if name is not None:
        jar_to_update["name"] = name
    
    return {
        "success": True,
        "jar": jar_to_update,
        "message": f"Updated jar '{jar_to_update['name']}'"
    }


@tool
def delete_jar(jar_id: str) -> dict:
    """
    Removes a budget jar.
    
    Args:
        jar_id: ID of the jar to delete
    
    Returns:
        Success status and message
    """
    # Find jar to delete
    jar_to_delete = None
    jar_index = None
    for i, jar in enumerate(MOCK_JARS):
        if jar["jar_id"] == jar_id:
            jar_to_delete = jar
            jar_index = i
            break
    
    if not jar_to_delete:
        return {
            "success": False,
            "error": f"Jar with ID '{jar_id}' not found"
        }
    
    # Check if deletion would leave total percentage less than 100
    remaining_total = sum(jar["percentage"] for jar in MOCK_JARS if jar["jar_id"] != jar_id)
    if remaining_total < 100:
        return {
            "success": False,
            "error": "Cannot delete jar - total percentage would be less than 100%. Adjust other jars first."
        }
    
    # Remove jar
    deleted_jar_name = jar_to_delete["name"]
    MOCK_JARS.pop(jar_index)
    
    return {
        "success": True,
        "message": f"Deleted jar '{deleted_jar_name}'"
    } 