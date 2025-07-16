from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.utils import jar_utils
from backend.utils import user_setting_utils
from backend.models import user as user_model
from backend.models import jar as jar_model

router = APIRouter()

@router.get("/", response_model=List[jar_model.JarInDB])
async def list_user_jars(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Get all jars for the current user.
    """
    user_id = str(current_user.id)
    jars = await jar_utils.get_all_jars_for_user(db, user_id)
    return jars

@router.post("/", response_model=jar_model.JarInDB, status_code=status.HTTP_201_CREATED)
async def create_jar(
    jar_in: jar_model.JarCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Create a new jar for the current user.
    """
    user_id = str(current_user.id)
    
    # Check if jar already exists
    existing_jar = await jar_utils.get_jar_by_name(db, user_id, jar_in.name)
    if existing_jar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A jar with the name '{jar_in.name}' already exists."
        )
    
    # Get user's total income for calculations
    user_settings = await user_setting_utils.get_user_settings(db, user_id)
    total_income = user_settings.total_income if user_settings else 5000.0
    
    # Validate that either percent or amount is provided
    if jar_in.percent is None and jar_in.amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'percent' or 'amount' must be provided."
        )
    
    # Calculate missing field - ensure both percent and amount are always defined
    if jar_in.percent is not None and jar_in.amount is None:
        # Only percent provided, calculate amount
        percent = jar_in.percent
        amount = jar_in.percent * total_income
    elif jar_in.amount is not None and jar_in.percent is None:
        # Only amount provided, calculate percent
        percent = jar_in.amount / total_income if total_income > 0 else 0.0
        amount = jar_in.amount
    else:
        # Both provided, use as-is
        percent = jar_in.percent
        amount = jar_in.amount
    
    # Create jar dictionary
    jar_dict = jar_in.model_dump()
    jar_dict['user_id'] = user_id
    jar_dict['percent'] = percent
    jar_dict['amount'] = amount
    jar_dict['current_amount'] = 0.0  # Start with zero balance
    
    # Use utils to create jar
    created_jar = await jar_utils.create_jar_in_db(db, jar_dict)
    
    # Rebalance all jars to ensure total allocation is 100%
    await jar_utils.rebalance_jars_to_100_percent(db, user_id)
    
    # Return the updated jar after rebalancing
    return await jar_utils.get_jar_by_name(db, user_id, created_jar.name)

@router.get("/{jar_name}", response_model=jar_model.JarInDB)
async def get_jar(
    jar_name: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Get a specific jar by its name.
    """
    user_id = str(current_user.id)
    jar = await jar_utils.get_jar_by_name(db, user_id, jar_name)
    
    if not jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jar '{jar_name}' not found."
        )
    
    return jar

@router.put("/{jar_name}", response_model=jar_model.JarInDB)
async def update_jar(
    jar_name: str,
    jar_update: jar_model.JarUpdate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Update an existing jar by its name.
    """
    user_id = str(current_user.id)
    
    update_data = jar_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )
    
    # Get user's total income for calculations if percent/amount is being updated
    if "percent" in update_data or "amount" in update_data:
        user_settings = await user_setting_utils.get_user_settings(db, user_id)
        total_income = user_settings.total_income if user_settings else 5000.0
        
        # Recalculate complementary field
        if "percent" in update_data and "amount" not in update_data:
            update_data["amount"] = update_data["percent"] * total_income
        elif "amount" in update_data and "percent" not in update_data:
            update_data["percent"] = update_data["amount"] / total_income if total_income > 0 else 0.0
    
    updated_jar = await jar_utils.update_jar_in_db(db, user_id, jar_name, update_data)
    
    if not updated_jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jar '{jar_name}' not found."
        )
    
    # Rebalance all jars to ensure total allocation is 100%
    await jar_utils.rebalance_jars_to_100_percent(db, user_id)
    
    # Return the updated jar after rebalancing
    return await jar_utils.get_jar_by_name(db, user_id, updated_jar.name)

@router.delete("/{jar_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_jar(
    jar_name: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Delete a jar by its name.
    """
    user_id = str(current_user.id)
    deleted = await jar_utils.delete_jar_by_name(db, user_id, jar_name)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jar '{jar_name}' not found."
        )
    
    # Rebalance remaining jars to ensure total allocation is 100%
    try:
        await jar_utils.rebalance_jars_to_100_percent(db, user_id)
    except ValueError:
        # No jars left to rebalance, which is fine
        pass
    
    return
