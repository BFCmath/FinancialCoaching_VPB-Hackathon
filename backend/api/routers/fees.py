import sys
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.api import deps
from backend.utils import fee_utils
from backend.utils import jar_utils
from backend.models import user as user_model
from backend.models import fee as fee_model
from motor.motor_asyncio import AsyncIOMotorDatabase

from datetime import datetime, timedelta

router = APIRouter()

# In backend/api/routers/fees.py

@router.post("/", response_model=fee_model.RecurringFeeInDB, status_code=status.HTTP_201_CREATED)
async def create_recurring_fee(
    fee_in: fee_model.RecurringFeeCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Creates a new recurring fee for the current user.
    """
    user_id = str(current_user.id)

    # Check if fee already exists
    existing_fee = await fee_utils.get_fee_by_name(db, user_id, fee_in.name)
    if existing_fee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A recurring fee with the name '{fee_in.name}' already exists."
        )
    
    # Validate target jar exists
    target_jar = await jar_utils.get_jar_by_name(db, user_id, fee_in.target_jar)
    if not target_jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target jar '{fee_in.target_jar}' not found."
        )

    # Calculate the first occurrence date
    next_occurrence = fee_utils.calculate_next_fee_occurrence(fee_in.pattern_type, fee_in.pattern_details)

    # Create fee dictionary
    fee_dict_to_save = fee_in.model_dump()
    fee_dict_to_save['user_id'] = user_id
    fee_dict_to_save['next_occurrence'] = next_occurrence
    fee_dict_to_save['is_active'] = True
    fee_dict_to_save['created_date'] = datetime.utcnow()

    # Use utils function to create fee
    saved_fee = await fee_utils.create_fee_in_db(db, fee_dict_to_save)
    return saved_fee


@router.get("/", response_model=List[fee_model.RecurringFeeInDB])
async def list_recurring_fees(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user),
    active_only: bool = Query(True, description="Filter for only active fees."),
    target_jar: Optional[str] = Query(None, description="Filter fees by target jar name.")
):
    """
    Lists recurring fees for the current user with optional filters.
    """
    user_id = str(current_user.id)
    
    if active_only and target_jar:
        # Filter by both active status and target jar
        fees = await fee_utils.get_active_fees_for_user(db, user_id)
        fees = [f for f in fees if f.target_jar == target_jar]
    elif active_only:
        # Filter by active status only
        fees = await fee_utils.get_active_fees_for_user(db, user_id)
    elif target_jar:
        # Filter by target jar only
        all_fees = await fee_utils.get_all_fees_for_user(db, user_id)
        fees = [f for f in all_fees if f.target_jar == target_jar]
    else:
        # No filters, get all fees
        fees = await fee_utils.get_all_fees_for_user(db, user_id)
    
    return fees


@router.delete("/{fee_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_fee(
    fee_name: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Deletes a recurring fee by its name.
    """
    user_id = str(current_user.id)
    deleted = await fee_utils.delete_fee_by_name(db, user_id, fee_name)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee '{fee_name}' not found."
        )
    
    return # Returns 204 No Content on success

@router.put("/{fee_name}", response_model=fee_model.RecurringFeeInDB)
async def update_recurring_fee(
    fee_name: str,
    fee_update: fee_model.RecurringFeeUpdate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Updates an existing recurring fee by its name.
    """
    user_id = str(current_user.id)
    
    update_data = fee_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )
    
    # If target_jar is being updated, validate it exists
    if "target_jar" in update_data:
        target_jar = await jar_utils.get_jar_by_name(db, user_id, update_data["target_jar"])
        if not target_jar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target jar '{update_data['target_jar']}' not found."
            )
    
    updated_fee = await fee_utils.update_fee_in_db(db, user_id, fee_name, update_data)
    
    if not updated_fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee '{fee_name}' not found."
        )
    
    return updated_fee

@router.get("/{fee_name}", response_model=fee_model.RecurringFeeInDB)
async def get_recurring_fee(
    fee_name: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Gets a specific recurring fee by its name.
    """
    user_id = str(current_user.id)
    fee = await fee_utils.get_fee_by_name(db, user_id, fee_name)
    
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee '{fee_name}' not found."
        )
    
    return fee

@router.get("/due/today", response_model=List[fee_model.RecurringFeeInDB])
async def get_fees_due_today(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Gets all fees that are due today for the current user.
    """
    user_id = str(current_user.id)
    fees_due = await fee_utils.get_fees_due_today(db, user_id)
    return fees_due
