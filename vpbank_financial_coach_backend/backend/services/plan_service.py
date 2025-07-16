"""
Plan Management Service - Complete Implementation from Lab
========================================================

This module implements the complete plan management service ported from the lab
with database backend, maintaining exact same interface and behavior.
Covers all budget plan operations from lab utils.py and service.py:
- save_budget_plan, get_budget_plan, get_all_budget_plans, get_budget_plans_by_status, delete_budget_plan
- create_plan, adjust_plan, get_plan, delete_plan
All methods are async where appropriate.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import plan_utils
from backend.models.plan import BudgetPlanInDB, BudgetPlanCreate, BudgetPlanUpdate

class PlanManagementService:
    """
    Budget plan management service.
    """
    
    @staticmethod
    async def save_budget_plan(db: AsyncIOMotorDatabase, user_id: str, plan_data: BudgetPlanCreate) -> BudgetPlanInDB:
        """Save budget plan to database."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if plan_data is None:
            raise ValueError("Plan data cannot be None")
        
        plan_dict = plan_data.model_dump()
        plan_dict["user_id"] = user_id
        return await plan_utils.create_plan_in_db(db, plan_dict)
    
    @staticmethod
    async def get_budget_plan(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> Optional[BudgetPlanInDB]:
        """Get budget plan by name."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not plan_name or not plan_name.strip():
            raise ValueError("Plan name cannot be empty")
        
        return await plan_utils.get_plan_by_name(db, user_id, plan_name)
    
    @staticmethod
    async def get_all_budget_plans(db: AsyncIOMotorDatabase, user_id: str) -> List[BudgetPlanInDB]:
        """Get all budget plans."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        
        return await plan_utils.get_all_plans_for_user(db, user_id)
    
    @staticmethod
    async def get_budget_plans_by_status(db: AsyncIOMotorDatabase, user_id: str, status: str) -> List[BudgetPlanInDB]:
        """Get budget plans by status."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not status or not status.strip():
            raise ValueError("Status cannot be empty")
        
        plans = await PlanManagementService.get_all_budget_plans(db, user_id)
        return [p for p in plans if p.status == status]
    
    @staticmethod
    async def delete_budget_plan(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> bool:
        """Delete budget plan from database."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not plan_name or not plan_name.strip():
            raise ValueError("Plan name cannot be empty")
        
        return await plan_utils.delete_plan_by_name(db, user_id, plan_name)
    
    @staticmethod
    async def create_plan(db: AsyncIOMotorDatabase, user_id: str, name: str, description: str, 
                          status: str = "active", jar_propose_adjust_details: Optional[str] = None) -> str:
        """Create new budget plan with jar recommendations."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not name or not name.strip():
            raise ValueError("Plan name cannot be empty")
        if not description or not description.strip():
            raise ValueError("Plan description cannot be empty")
        if not status or not status.strip():
            raise ValueError("Plan status cannot be empty")
        
        # Check for valid status values
        valid_statuses = ["active", "inactive", "completed", "pending"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")
        
        existing = await PlanManagementService.get_budget_plan(db, user_id, name)
        if existing:
            raise ValueError(f"Plan '{name}' already exists")
        
        plan_data = BudgetPlanCreate(
            name=name,
            detail_description=description,
            day_created=datetime.now().strftime("%Y-%m-%d"),
            status=status,
            jar_recommendations=jar_propose_adjust_details
        )
        
        await PlanManagementService.save_budget_plan(db, user_id, plan_data)
        
        result = f"Created plan '{name}' with status '{status}'"
        if jar_propose_adjust_details:
            result += f". Jar recommendations: {jar_propose_adjust_details}"
        
        return result
    
    @staticmethod
    async def adjust_plan(db: AsyncIOMotorDatabase, user_id: str, name: str, 
                          description: Optional[str] = None, status: Optional[str] = None, 
                          jar_propose_adjust_details: Optional[str] = None) -> str:
        """Modify existing budget plan."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not name or not name.strip():
            raise ValueError("Plan name cannot be empty")
        
        # Validate status if provided
        if status is not None:
            status = status.strip()
            valid_statuses = ["active", "inactive", "completed", "pending"]
            if status not in valid_statuses:
                raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")
        
        # Validate description if provided
        if description is not None and not description.strip():
            raise ValueError("Plan description cannot be empty when provided")
        
        plan = await PlanManagementService.get_budget_plan(db, user_id, name)
        if not plan:
            raise ValueError(f"Plan '{name}' not found")
        
        update_data = BudgetPlanUpdate()
        changes = []
        
        if description is not None:
            update_data.detail_description = description.strip()
            changes.append("description updated")
        
        if status is not None:
            update_data.status = status
            changes.append(f"status updated to {status}")
        
        if jar_propose_adjust_details is not None:
            update_data.jar_recommendations = jar_propose_adjust_details
            changes.append("jar recommendations updated")
        
        if changes:
            await plan_utils.update_plan_in_db(db, user_id, name, update_data.model_dump(exclude_unset=True))
        
        result = f"Updated plan '{name}': {', '.join(changes) if changes else 'no changes'}"
        return result

    @staticmethod
    async def get_plan(db: AsyncIOMotorDatabase, user_id: str, status: str = "active", 
                       description: str = "") -> Dict[str, Any]:
        """Retrieve budget plans by status."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not status or not status.strip():
            raise ValueError("Status cannot be empty")
        
        # Validate status
        valid_statuses = ["active", "inactive", "completed", "pending", "all"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")
        
        if status == "all":
            plans = await PlanManagementService.get_all_budget_plans(db, user_id)
        else:
            plans = await PlanManagementService.get_budget_plans_by_status(db, user_id, status)
        
        plan_dicts = [p.model_dump() for p in plans]
        auto_desc = description or f"retrieved {len(plan_dicts)} {status} plans"
        return {"data": plan_dicts, "description": auto_desc}
    
    @staticmethod
    async def delete_plan(db: AsyncIOMotorDatabase, user_id: str, plan_name: str, reason: str = "") -> str:
        """Delete budget plan."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not plan_name or not plan_name.strip():
            raise ValueError("Plan name cannot be empty")
        
        # Check if plan exists before attempting deletion
        plan = await PlanManagementService.get_budget_plan(db, user_id, plan_name)
        if not plan:
            raise ValueError(f"Plan '{plan_name}' not found")
        
        deleted = await PlanManagementService.delete_budget_plan(db, user_id, plan_name)
        if not deleted:
            raise ValueError(f"Failed to delete plan '{plan_name}' - database operation failed")
        
        result = f"Deleted plan '{plan_name}'"
        if reason:
            result += f". Reason: {reason}"
        return result