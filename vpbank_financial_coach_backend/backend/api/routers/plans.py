import sys
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query


from backend.api import deps
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import plan as plan_model
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.post("/", response_model=plan_model.BudgetPlanInDB, status_code=status.HTTP_201_CREATED)
async def create_budget_plan(
    plan_in: plan_model.BudgetPlanCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Creates a new budget plan for the current user.
    """
    user_id = str(current_user.id)

    # Check if a plan with the same name already exists for this user
    existing_plan = await db[db_utils.PLANS_COLLECTION].find_one({"user_id": user_id, "name": plan_in.name})
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A budget plan with the name '{plan_in.name}' already exists."
        )

    plan_to_save = plan_model.BudgetPlanInDB(
        user_id=user_id,
        **plan_in.model_dump()
    )

    await db[db_utils.PLANS_COLLECTION].insert_one(plan_to_save.model_dump(by_alias=True))
    return plan_to_save


@router.get("/", response_model=List[plan_model.BudgetPlanInDB])
async def list_budget_plans(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user),
    status: Optional[plan_model.PlanStatus] = Query(None, description="Filter plans by their status.")
):
    """
    Lists budget plans for the current user, with an optional filter for status.
    """
    user_id = str(current_user.id)
    query_filter = {"user_id": user_id}

    if status:
        query_filter["status"] = status

    cursor = db[db_utils.PLANS_COLLECTION].find(query_filter).sort("day_created", -1)
    plans = await cursor.to_list(length=100)
    return [plan_model.BudgetPlanInDB(**p) for p in plans]


@router.put("/{plan_name}", response_model=plan_model.BudgetPlanInDB)
async def update_budget_plan(
    plan_name: str,
    plan_in: plan_model.BudgetPlanUpdate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Updates an existing budget plan by its name.
    """
    user_id = str(current_user.id)
    
    # Create a dictionary of the fields to update, excluding any that were not set
    update_data = plan_in.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )

    updated_plan = await db[db_utils.PLANS_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": plan_name},
        {"$set": update_data},
        return_document=True # This ensures the updated document is returned
    )

    if not updated_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_name}' not found."
        )

    return plan_model.BudgetPlanInDB(**updated_plan)


@router.delete("/{plan_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_plan(
    plan_name: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Deletes a budget plan by its name.
    """
    user_id = str(current_user.id)
    result = await db[db_utils.PLANS_COLLECTION].delete_one({"user_id": user_id, "name": plan_name})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_name}' not found."
        )
    
    return