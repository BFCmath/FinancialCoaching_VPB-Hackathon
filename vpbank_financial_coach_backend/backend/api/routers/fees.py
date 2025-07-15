import sys
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.api import deps
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import fee as fee_model
from motor.motor_asyncio import AsyncIOMotorDatabase

from datetime import datetime, timedelta
from backend.utils.db_utils import calculate_next_fee_occurrence

router = APIRouter()

# In backend/api/routers/fees.py

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

    # --- Validation (remains the same) ---
    existing_fee = await db[db_utils.FEES_COLLECTION].find_one({"user_id": user_id, "name": fee_in.name})
    if existing_fee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A recurring fee with the name '{fee_in.name}' already exists."
        )
    target_jar = await db_utils.get_jar_by_name(db, user_id, fee_in.target_jar)
    if not target_jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target jar '{fee_in.target_jar}' not found."
        )

    # --- START OF CHANGE ---

    # 1. Calculate the first occurrence date
    next_occurrence = calculate_next_fee_occurrence(fee_in.pattern_type, fee_in.pattern_details)

    # 2. Create a dictionary with all data to be saved
    fee_dict_to_save = fee_in.model_dump()
    fee_dict_to_save['user_id'] = user_id
    fee_dict_to_save['next_occurrence'] = next_occurrence
    fee_dict_to_save['is_active'] = True # Set default active state
    fee_dict_to_save['created_date'] = datetime.utcnow() # Set creation date

    # 3. Insert into the database using the corrected utility and get the final model back
    saved_fee = await db_utils.create_fee_in_db(db, fee_dict_to_save)

    # --- END OF CHANGE ---

    return saved_fee


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
    fees = await cursor.to_list(length=100)

    # --- START OF FIX ---
    # Manually convert ObjectId to string for each document
    for f in fees:
        f["_id"] = str(f["_id"])
    # --- END OF FIX ---
    
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