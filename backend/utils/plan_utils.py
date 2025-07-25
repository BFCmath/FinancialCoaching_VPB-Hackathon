from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

# Import all Pydantic models
from backend.models import plan
from backend.utils.general_utils import PLANS_COLLECTION

async def get_all_plans_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[plan.BudgetPlanInDB]:
    """Retrieves all budget plans for a specific user."""
    plans = []
    plans_cursor = db[PLANS_COLLECTION].find({"user_id": user_id})
    async for p in plans_cursor:
        p["_id"] = str(p["_id"])
        plans.append(plan.BudgetPlanInDB(**p))
    return plans

async def get_plan_by_name(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> Optional[plan.BudgetPlanInDB]:
    """Retrieves a single plan by its name for a specific user."""
    plan_doc = await db[PLANS_COLLECTION].find_one({"user_id": user_id, "name": {"$regex": f"^{plan_name}$", "$options": "i"}})
    if plan_doc:
        plan_doc["_id"] = str(plan_doc["_id"])
        return plan.BudgetPlanInDB(**plan_doc)
    return None

async def create_plan_in_db(db: AsyncIOMotorDatabase, plan_dict: Dict[str, Any]) -> plan.BudgetPlanInDB:
    """Creates a new budget plan document from a dictionary in the database."""
    result = await db[PLANS_COLLECTION].insert_one(plan_dict)
    created_doc = await db[PLANS_COLLECTION].find_one({"_id": result.inserted_id})
    if created_doc:
        created_doc["_id"] = str(created_doc["_id"])
    return plan.BudgetPlanInDB(**created_doc)

async def update_plan_in_db(db: AsyncIOMotorDatabase, user_id: str, plan_name: str, update_data: Dict[str, Any]) -> Optional[plan.BudgetPlanInDB]:
    """Updates an existing plan document."""
    result = await db[PLANS_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": plan_name},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    if result:
        result["_id"] = str(result["_id"])
        return plan.BudgetPlanInDB(**result)
    return None

async def delete_plan_by_name(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> bool:
    """Deletes a plan by its name for a specific user."""
    result = await db[PLANS_COLLECTION].delete_one({"user_id": user_id, "name": plan_name})
    return result.deleted_count > 0

async def get_plans_by_status_for_user(db: AsyncIOMotorDatabase, user_id: str, status: str) -> List[plan.BudgetPlanInDB]:
    """Get budget plans by status for a specific user."""
    plans = []
    plans_cursor = db[PLANS_COLLECTION].find({"user_id": user_id, "status": status})
    async for p in plans_cursor:
        p["_id"] = str(p["_id"])
        plans.append(plan.BudgetPlanInDB(**p))
    return plans
