from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

# Import all Pydantic models
from backend.models import jar
from backend.utils.general_utils import JARS_COLLECTION, validate_percentage_range, calculate_amount_from_percent
from backend.utils.transaction_utils import get_transactions_by_jar_for_user

async def get_all_jars_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[jar.JarInDB]:
    """Retrieves all jars for a specific user."""
    jars = []
    jars_cursor = db[JARS_COLLECTION].find({"user_id": user_id})
    async for j in jars_cursor:
        # This is the crucial step: convert ObjectId to string
        j["_id"] = str(j["_id"])
        jars.append(jar.JarInDB(**j))
    return jars


async def get_jar_by_name(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> Optional[jar.JarInDB]:
    """Retrieves a single jar by its name for a specific user."""
    # Case-insensitive search for the name
    jar_doc = await db[JARS_COLLECTION].find_one({"user_id": user_id, "name": {"$regex": f"^{jar_name}$", "$options": "i"}})
    if jar_doc:
        jar_doc["_id"] = str(jar_doc["_id"])
        return jar.JarInDB(**jar_doc)
    return None

async def create_jar_in_db(db: AsyncIOMotorDatabase, jar_dict: Dict[str, Any]) -> jar.JarInDB:
    """Creates a new jar document from a dictionary in the database."""
    # Insert the dictionary and get the result
    result = await db[JARS_COLLECTION].insert_one(jar_dict)
    
    # Fetch the newly created document from the database
    created_doc = await db[JARS_COLLECTION].find_one({"_id": result.inserted_id})
    
    # Convert its ObjectId to a string before validation
    if created_doc and "_id" in created_doc:
        created_doc["_id"] = str(created_doc["_id"])
    
    # Return a valid Pydantic model
    return jar.JarInDB(**created_doc)

async def update_jar_in_db(db: AsyncIOMotorDatabase, user_id: str, original_jar_name: str, update_data: Dict[str, Any]) -> Optional[jar.JarInDB]:
    """Updates an existing jar document."""
    result = await db[JARS_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": original_jar_name},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    if result:
        # This is the crucial fix: convert ObjectId to string
        result["_id"] = str(result["_id"])
        return jar.JarInDB(**result)
    return None

async def delete_jar_by_name(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> bool:
    """Deletes a jar by its name for a specific user."""
    result = await db[JARS_COLLECTION].delete_one({"user_id": user_id, "name": jar_name})
    return result.deleted_count > 0

def validate_jar_data(jar_data: dict, total_income: float = 5000.0) -> Tuple[bool, List[str]]:
    """Validate jar data for consistency."""
    errors = []
    
    if not jar_data.get('name', '').strip():
        errors.append("Jar name cannot be empty")
    
    percent = jar_data.get('percent', 0.0)
    if not validate_percentage_range(percent):
        errors.append(f"Percent {percent} must be between 0.0 and 1.0")
    
    current_percent = jar_data.get('current_percent', 0.0)
    if not validate_percentage_range(current_percent):
        errors.append(f"Current percent {current_percent} must be between 0.0 and 1.0")
    
    # Check if calculated amounts match
    amount = jar_data.get('amount', 0.0)
    expected_amount = calculate_amount_from_percent(percent, total_income)
    if abs(amount - expected_amount) > 0.01:  # Allow small rounding differences
        errors.append(f"Amount {amount} doesn't match percent calculation {expected_amount}")
    
    return len(errors) == 0, errors

async def recalculate_jar_amounts_for_user(db: AsyncIOMotorDatabase, user_id: str, new_total_income: float) -> List[jar.JarInDB]:
    """
    Recalculate all jar amounts for a user based on new total income.
    Updates all jars to maintain the same percentages but with new amounts.
    
    Args:
        db: Database connection
        user_id: User's ID
        new_total_income: New total income amount
        
    Returns:
        List of updated jar objects
        
    Raises:
        ValueError: If new_total_income is not positive
    """
    if new_total_income <= 0:
        raise ValueError("Total income must be positive")
    
    # Get all current jars for the user
    current_jars = await get_all_jars_for_user(db, user_id)
    
    if not current_jars:
        # No jars to update
        return []
    
    updated_jars = []
    
    for current_jar in current_jars:
        # Calculate new amount based on existing percentage
        new_amount = current_jar.percent * new_total_income
        
        # Calculate new current_percent (current_amount / new_amount)
        new_current_percent = current_jar.current_amount / new_amount if new_amount > 0 else 0.0
        
        # Ensure current_percent doesn't exceed 1.0
        new_current_percent = min(new_current_percent, 1.0)
        
        # Update the jar with new amounts
        update_data = {
            "amount": new_amount,
            "current_percent": new_current_percent
        }
        
        updated_jar = await update_jar_in_db(db, user_id, current_jar.name, update_data)
        if updated_jar:
            updated_jars.append(updated_jar)
    
    return updated_jars

async def calculate_jar_spending_total(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> float:
    """Calculate total spending for a specific jar."""
    transactions = await get_transactions_by_jar_for_user(db, user_id, jar_name)
    return sum(t.amount for t in transactions)

async def add_money_to_jar(db: AsyncIOMotorDatabase, user_id: str, jar_name: str, amount: float) -> Optional[jar.JarInDB]:
    """Add money to a specific jar's current_amount."""
    from pymongo import ReturnDocument
    
    result = await db[JARS_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": jar_name},
        {"$inc": {"current_amount": amount}},
        return_document=ReturnDocument.AFTER
    )
    
    if result:
        result["_id"] = str(result["_id"])
        return jar.JarInDB(**result)
    return None

async def subtract_money_from_jar(db: AsyncIOMotorDatabase, user_id: str, jar_name: str, amount: float) -> Optional[jar.JarInDB]:
    """Subtract money from a specific jar's current_amount."""
    from pymongo import ReturnDocument
    
    # First check if jar has enough money
    current_jar = await get_jar_by_name(db, user_id, jar_name)
    if not current_jar:
        return None
    
    if current_jar.current_amount < amount:
        raise ValueError(f"Insufficient funds in jar '{jar_name}'. Available: {current_jar.current_amount}, Requested: {amount}")
    
    result = await db[JARS_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": jar_name},
        {"$inc": {"current_amount": -amount}},
        return_document=ReturnDocument.AFTER
    )
    
    if result:
        result["_id"] = str(result["_id"])
        return jar.JarInDB(**result)
    return None

async def rebalance_jars_to_100_percent(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    """
    Rebalance all jars to ensure total allocation equals 100%.
    
    This function:
    1. Calculates current total allocation
    2. If not 100%, proportionally adjusts all jars to sum to 100%
    3. Updates jar amounts based on user's total income
    4. Handles rounding errors by adjusting the largest jar
    
    Args:
        db: Database connection
        user_id: User's ID
        
    Returns:
        bool: True if rebalancing was performed, False if no rebalancing needed
        
    Raises:
        ValueError: If user has no jars to rebalance
    """
    from backend.utils.user_setting_utils import get_user_total_income
    
    # Get all user's jars
    jars = await get_all_jars_for_user(db, user_id)
    
    if not jars:
        raise ValueError("No jars found for user - cannot rebalance")
    
    # Calculate current total allocation
    current_total_percent = sum(jar.percent for jar in jars)
    
    # If already at 100% (within tolerance), no rebalancing needed
    if abs(current_total_percent - 1.0) <= 0.001:
        return False
    
    # Get user's total income for amount calculations
    total_income = await get_user_total_income(db, user_id)
    
    # Calculate scaling factor to make total = 100%
    if current_total_percent > 0:
        scale_factor = 1.0 / current_total_percent
    else:
        # If all jars are 0%, distribute equally
        scale_factor = 1.0
        equal_percent = 1.0 / len(jars)
        for jar in jars:
            jar.percent = equal_percent
    
    # Apply scaling to all jars
    updated_jars = []
    total_after_scaling = 0.0
    
    for jar in jars:
        if current_total_percent > 0:
            new_percent = jar.percent * scale_factor
        else:
            new_percent = equal_percent
            
        new_amount = new_percent * total_income
        
        # Calculate new current_percent (preserve ratio if possible)
        if jar.amount > 0:
            current_ratio = jar.current_amount / jar.amount
            new_current_percent = min(current_ratio, 1.0)
        else:
            new_current_percent = jar.current_percent
        
        update_data = {
            "percent": new_percent,
            "amount": new_amount,
            "current_percent": new_current_percent
        }
        
        updated_jar = await update_jar_in_db(db, user_id, jar.name, update_data)
        if updated_jar:
            updated_jars.append(updated_jar)
            total_after_scaling += updated_jar.percent
    
    # Handle rounding errors - adjust the largest jar to make total exactly 1.0
    if updated_jars and abs(total_after_scaling - 1.0) > 0.001:
        largest_jar = max(updated_jars, key=lambda j: j.percent)
        adjustment = 1.0 - total_after_scaling
        new_percent = largest_jar.percent + adjustment
        new_amount = new_percent * total_income
        
        # Ensure percent stays within valid range
        new_percent = max(0.0, min(1.0, new_percent))
        new_amount = new_percent * total_income
        
        update_data = {
            "percent": new_percent,
            "amount": new_amount
        }
        
        await update_jar_in_db(db, user_id, largest_jar.name, update_data)
    
    return True
