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

    existing_plan = await db_utils.get_plan_by_name(db, user_id, plan_in.name)
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A budget plan with the name '{plan_in.name}' already exists."
        )

    plan_dict_to_save = plan_in.model_dump()
    plan_dict_to_save['user_id'] = user_id
    
    saved_plan = await db_utils.create_plan_in_db(db, plan_dict_to_save)
    return saved_plan


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
    
    all_plans = await db_utils.get_all_plans_for_user(db, user_id)

    if status:
        return [p for p in all_plans if p.status == status]
    
    return all_plans


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
    
    update_data = plan_in.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )

    updated_plan = await db_utils.update_plan_in_db(db, user_id, plan_name, update_data)

    if not updated_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_name}' not found."
        )

    return updated_plan


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
    deleted = await db_utils.delete_plan_by_name(db, user_id, plan_name)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_name}' not found."
        )
    
    return