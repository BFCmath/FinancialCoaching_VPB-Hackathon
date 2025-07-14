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
from backend.utils import db_utils
from backend.models.plan import BudgetPlanInDB, BudgetPlanCreate, BudgetPlanUpdate
from .confidence_service import ConfidenceService

class PlanManagementService:
    """
    Budget plan management service.
    """
    
    @staticmethod
    async def save_budget_plan(db: AsyncIOMotorDatabase, user_id: str, plan_data: BudgetPlanCreate) -> BudgetPlanInDB:
        """Save budget plan to database."""
        return await db_utils.create_plan_in_db(db, user_id, plan_data)
    
    @staticmethod
    async def get_budget_plan(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> Optional[BudgetPlanInDB]:
        """Get budget plan by name."""
        return await db_utils.get_plan_by_name(db, user_id, plan_name)
    
    @staticmethod
    async def get_all_budget_plans(db: AsyncIOMotorDatabase, user_id: str) -> List[BudgetPlanInDB]:
        """Get all budget plans."""
        return await db_utils.get_all_plans_for_user(db, user_id)
    
    @staticmethod
    async def get_budget_plans_by_status(db: AsyncIOMotorDatabase, user_id: str, status: str) -> List[BudgetPlanInDB]:
        """Get budget plans by status."""
        plans = await PlanManagementService.get_all_budget_plans(db, user_id)
        return [p for p in plans if p.status == status]
    
    @staticmethod
    async def delete_budget_plan(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> bool:
        """Delete budget plan from database."""
        return await db_utils.delete_plan_by_name(db, user_id, plan_name)
    
    @staticmethod
    async def create_plan(db: AsyncIOMotorDatabase, user_id: str, name: str, description: str, 
                          status: str = "active", jar_propose_adjust_details: Optional[str] = None,
                          confidence: int = 85) -> str:
        """Create new budget plan with jar recommendations."""
        existing = await PlanManagementService.get_budget_plan(db, user_id, name)
        if existing:
            return f"❌ Plan '{name}' already exists"
        
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
        
        return ConfidenceService.format_confidence_response(result, confidence)
    
    @staticmethod
    async def adjust_plan(db: AsyncIOMotorDatabase, user_id: str, name: str, 
                          description: Optional[str] = None, status: Optional[str] = None, 
                          jar_propose_adjust_details: Optional[str] = None,
                          confidence: int = 85) -> str:
        """Modify existing budget plan."""
        plan = await PlanManagementService.get_budget_plan(db, user_id, name)
        if not plan:
            return f"❌ Plan '{name}' not found"
        
        update_data = BudgetPlanUpdate()
        changes = []
        
        if description is not None:
            update_data.detail_description = description
            changes.append("description updated")
        
        if status is not None:
            update_data.status = status
            changes.append(f"status updated to {status}")
        
        if jar_propose_adjust_details is not None:
            update_data.jar_recommendations = jar_propose_adjust_details
            changes.append("jar recommendations updated")
        
        if changes:
            await db_utils.update_plan_in_db(db, user_id, name, update_data)
        
        result = f"Updated plan '{name}': {', '.join(changes) if changes else 'no changes'}"
        return ConfidenceService.format_confidence_response(result, confidence)
    
    @staticmethod
    async def get_plan(db: AsyncIOMotorDatabase, user_id: str, status: str = "active", 
                       description: str = "") -> Dict[str, Any]:
        """Retrieve budget plans by status."""
        if status == "all":
            plans = await PlanManagementService.get_all_budget_plans(db, user_id)
        else:
            plans = await PlanManagementService.get_budget_plans_by_status(db, user_id, status)
        
        plan_dicts = [p.dict() for p in plans]
        auto_desc = description or f"retrieved {len(plan_dicts)} {status} plans"
        return {"data": plan_dicts, "description": auto_desc}
    
    @staticmethod
    async def delete_plan(db: AsyncIOMotorDatabase, user_id: str, plan_name: str, reason: str = "") -> str:
        """Delete budget plan."""
        deleted = await PlanManagementService.delete_budget_plan(db, user_id, plan_name)
        if deleted:
            result = f"Deleted plan '{plan_name}'"
            if reason:
                result += f". Reason: {reason}"
            return f"✅ {result}"
        return f"❌ Failed to delete plan '{plan_name}'"