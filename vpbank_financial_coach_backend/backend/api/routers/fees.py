import sys
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from backend.api import deps
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import fee as fee_model
from motor.motor_asyncio import AsyncIOMotorDatabase

# We reuse the original, pure calculation function to avoid re-implementing it.
from backend.services.financial_services import FeeManagementService
from datetime import datetime, timedelta

def calculate_next_fee_occurrence(pattern_type: str, pattern_details: List[int], from_date: datetime = None) -> datetime:
    """Calculate when fee should next occur based on pattern"""
    if from_date is None:
        from_date = datetime.utcnow()
    
    if pattern_type == "daily":
        return from_date + timedelta(days=1)
    elif pattern_type == "weekly":
        # Assume pattern_details contains day numbers (0=Monday, 6=Sunday)
        return from_date + timedelta(weeks=1)
    elif pattern_type == "monthly":
        # Assume pattern_details contains day of month
        return from_date + timedelta(days=30)  # Simplified
    
    # Default fallback
    return from_date + timedelta(days=1)

router = APIRouter()

@router.post("/", response_model=fee_model.RecurringFeeInDB, status_code=status.HTTP_201_CREATED)
async def create_recurring_fee(
    fee_in: fee_model.RecurringFeeCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Creates a new recurring fee for the current user.
    """
    user_id = str(current_user.id)

    # --- Validation ---
    # 1. Check if a fee with the same name already exists for this user
    existing_fee = await db[db_utils.FEES_COLLECTION].find_one({"user_id": user_id, "name": fee_in.name})
    if existing_fee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A recurring fee with the name '{fee_in.name}' already exists."
        )

    # 2. Check if the target jar exists for this user
    target_jar = await db_utils.get_jar_by_name(db, user_id, fee_in.target_jar)
    if not target_jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target jar '{fee_in.target_jar}' not found."
        )

    # --- Logic ---
    # 1. Calculate the first occurrence date using the original utility function
    next_occurrence = calculate_next_fee_occurrence(fee_in.pattern_type, fee_in.pattern_details)

    # 2. Create the full database model
    fee_to_save = fee_model.RecurringFeeInDB(
        user_id=user_id,
        next_occurrence=next_occurrence,
        **fee_in.model_dump()
    )

    # 3. Insert into the database
    await db[db_utils.FEES_COLLECTION].insert_one(fee_to_save.model_dump(by_alias=True))

    return fee_to_save


@router.get("/", response_model=List[fee_model.RecurringFeeInDB])
async def list_recurring_fees(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user),
    active_only: bool = Query(True, description="Filter for only active fees."),
    target_jar: Optional[str] = Query(None, description="Filter fees by target jar name.")
):
    """
    Lists recurring fees for the current user with optional filters.
    """
    user_id = str(current_user.id)
    query_filter = {"user_id": user_id}

    if active_only:
        query_filter["is_active"] = True
    
    if target_jar:
        query_filter["target_jar"] = target_jar

    cursor = db[db_utils.FEES_COLLECTION].find(query_filter).sort("next_occurrence", 1)
    fees = await cursor.to_list(length=100) # Limiting to 100 fees for now
    return [fee_model.RecurringFeeInDB(**f) for f in fees]


@router.delete("/{fee_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_fee(
    fee_name: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Deletes a recurring fee by its name.
    """
    user_id = str(current_user.id)
    result = await db[db_utils.FEES_COLLECTION].delete_one({"user_id": user_id, "name": fee_name})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee '{fee_name}' not found."
        )
    
    return # Returns 204 No Content on success