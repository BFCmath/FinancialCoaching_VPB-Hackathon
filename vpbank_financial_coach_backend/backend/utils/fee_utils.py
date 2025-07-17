from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from pymongo import ReturnDocument

# Import all Pydantic models
from backend.models import fee
from backend.utils.general_utils import FEES_COLLECTION

async def get_all_fees_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Retrieves all recurring fees for a specific user."""
    fees = []
    fees_cursor = db[FEES_COLLECTION].find({"user_id": user_id})
    async for f in fees_cursor:
        f["_id"] = str(f["_id"])
        fees.append(fee.RecurringFeeInDB(**f))
    return fees

async def get_fee_by_name(db: AsyncIOMotorDatabase, user_id: str, fee_name: str) -> Optional[fee.RecurringFeeInDB]:
    """Retrieves a single fee by its name for a specific user."""
    fee_doc = await db[FEES_COLLECTION].find_one({"user_id": user_id, "name": {"$regex": f"^{fee_name}$", "$options": "i"}})
    if fee_doc:
        fee_doc["_id"] = str(fee_doc["_id"])
        return fee.RecurringFeeInDB(**fee_doc)
    return None

async def create_fee_in_db(db: AsyncIOMotorDatabase, fee_dict: Dict[str, Any]) -> fee.RecurringFeeInDB:
    """Creates a new recurring fee document from a dictionary in the database."""
    # Insert the dictionary and get the result
    result = await db[FEES_COLLECTION].insert_one(fee_dict)

    # Fetch the newly created document from the database
    created_doc = await db[FEES_COLLECTION].find_one({"_id": result.inserted_id})

    # Convert its ObjectId to a string before validation
    if created_doc and "_id" in created_doc:
        created_doc["_id"] = str(created_doc["_id"])
    
    # Return a valid Pydantic model
    return fee.RecurringFeeInDB(**created_doc)

async def update_fee_in_db(db: AsyncIOMotorDatabase, user_id: str, fee_name: str, update_data: Dict[str, Any]) -> Optional[fee.RecurringFeeInDB]:
    """Updates an existing fee document."""
    result = await db[FEES_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": fee_name},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    if result:
        result["_id"] = str(result["_id"])
        return fee.RecurringFeeInDB(**result)
    return None

async def delete_fee_by_name(db: AsyncIOMotorDatabase, user_id: str, fee_name: str) -> bool:
    """Deletes a fee by its name for a specific user."""
    fee_to_delete = await db[FEES_COLLECTION].find_one({"user_id": user_id, "name": fee_name})

    if not fee_to_delete: return False
    
    result = await db[FEES_COLLECTION].delete_one({"user_id": user_id, "name": fee_name})
    return result.deleted_count > 0

async def get_active_fees_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Get only active recurring fees for a specific user."""
    fees = []
    fees_cursor = db[FEES_COLLECTION].find({"user_id": user_id, "is_active": True})
    async for f in fees_cursor:
        f["_id"] = str(f["_id"])
        fees.append(fee.RecurringFeeInDB(**f))
    return fees


async def get_user_recurring_fees(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Get recurring fees for a specific user (alias for get_all_fees_for_user)."""
    return await get_all_fees_for_user(db, user_id)

async def get_fees_due_today(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Get fees that are due today."""
    from datetime import datetime
    today = datetime.utcnow().replace(hour=23, minute=59, second=59)
    fees = []
    fees_cursor = db[FEES_COLLECTION].find({
        "user_id": user_id,
        "is_active": True,
        "next_occurrence": {"$lte": today}
    })
    async for f in fees_cursor:
        f["_id"] = str(f["_id"])
        fees.append(fee.RecurringFeeInDB(**f))
    return fees


def calculate_next_fee_occurrence(pattern_type: str, pattern_details: List[int], from_date: datetime = None) -> datetime:
    """Calculate when fee should next occur based on pattern."""
    if from_date is None:
        from_date = datetime.utcnow()
    
    if pattern_type == "daily":
        return from_date + timedelta(days=1)
        
    elif pattern_type == "weekly":
        if not pattern_details:  # Every day
            return from_date + timedelta(days=1)
        else:
            # Specific days of the week [1=Monday, 7=Sunday]
            days = pattern_details
            current_weekday = from_date.weekday() + 1
            
            # Find next occurrence
            next_days = [d for d in days if d > current_weekday]
            if next_days:
                days_until = min(next_days) - current_weekday
            else:
                # Next week, first day
                days_until = 7 - current_weekday + min(days)
            return from_date + timedelta(days=days_until)
        
    elif pattern_type == "monthly":
        if not pattern_details:  # Every day
            return from_date + timedelta(days=1)
        else:
            # Specific days of the month
            target_dates = pattern_details
            current_day = from_date.day
            
            # Find next occurrence this month
            next_dates_this_month = [d for d in target_dates if d > current_day]
            if next_dates_this_month:
                target_date = min(next_dates_this_month)
                try:
                    return from_date.replace(day=target_date)
                except ValueError:
                    pass  # Fall through to next month
            
            # Next month, first target date
            next_month = from_date.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            target_date = min(target_dates)
            try:
                return next_month.replace(day=target_date)
            except ValueError:
                # Target date doesn't exist (e.g., Feb 31st)
                month_after = next_month.replace(day=1) + timedelta(days=32)
                last_day = (month_after.replace(day=1) - timedelta(days=1)).day
                return next_month.replace(day=min(target_date, last_day))
    
    # Default fallback
    return from_date + timedelta(days=1)