"""
Plan Management Service - Complete Implementation from Lab
========================================================

This module implements the complete plan management service ported from the lab
with database backend, maintaining exact same interface and behavior.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models import plan
from .core_services import CalculationService

# =============================================================================
# PLAN MANAGEMENT SERVICE - COMPLETE FROM LAB
# =============================================================================

class PlanManagementService:
    """
    Complete plan management service from lab with database backend.
    Maintains exact same interface and behavior as the original.
    """
    
    @staticmethod
    async def create_plan(db: AsyncIOMotorDatabase, user_id: str, name: str, description: str, 
                         status: str = "active", jar_propose_adjust_details: Optional[str] = None, 
                         confidence: int = 85) -> str:
        """Create new budget plan with jar recommendations - matches lab interface exactly."""
        
        # Check if plan already exists
        existing_plan = await db_utils.get_plan_by_name(db, user_id, name)
        if existing_plan:
            return f"❌ Plan '{name}' already exists"
        
        # Validate name
        if not name or not name.strip():
            return "❌ Plan name cannot be empty"
        
        if len(name.strip()) < 3:
            return "❌ Plan name too short (minimum 3 characters)"
        
        # Validate status
        if status not in ["active", "completed", "cancelled", "on_hold"]:
            status = "active"
        
        # Create plan
        new_plan = plan.BudgetPlanInDB(
            id=str(datetime.utcnow().timestamp()),
            user_id=user_id,
            name=name.strip(),
            detail_description=description,
            day_created=date.today().isoformat(),
            status=status,
            jar_recommendations=jar_propose_adjust_details
        )
        
        await db_utils.create_plan_in_db(db, user_id, new_plan)
        
        # Build response
        response_parts = [f"Created plan '{name}' with status '{status}'"]
        
        if jar_propose_adjust_details:
            response_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
        
        response = " | ".join(response_parts)
        
        # Format response based on confidence
        if confidence >= 90:
            return f"✅ {response}"
        elif confidence >= 70:
            return f"⚠️ {response} ({confidence}% confident)"
        else:
            return f"❓ {response} ({confidence}% confident - please verify)"
    
    @staticmethod
    async def adjust_plan(db: AsyncIOMotorDatabase, user_id: str, name: str, 
                         description: Optional[str] = None, status: Optional[str] = None, 
                         jar_propose_adjust_details: Optional[str] = None, 
                         confidence: int = 85) -> str:
        """Modify existing budget plan - matches lab interface exactly."""
        
        # Find plan
        plan_obj = await db_utils.get_plan_by_name(db, user_id, name)
        if not plan_obj:
            return f"❌ Plan '{name}' not found"
        
        changes = []
        update_data = {}
        
        # Update description
        if description is not None:
            old_desc = plan_obj.detail_description
            update_data['detail_description'] = description
            changes.append("description updated")
        
        # Update status
        if status is not None:
            if status not in ["active", "completed", "cancelled", "on_hold"]:
                return f"❌ Invalid status '{status}'. Use: active, completed, cancelled, on_hold"
            old_status = plan_obj.status
            update_data['status'] = status
            changes.append(f"status: {old_status} → {status}")
        
        # Update jar recommendations
        if jar_propose_adjust_details is not None:
            update_data['jar_recommendations'] = jar_propose_adjust_details
            changes.append("jar recommendations updated")
        
        # Save updates
        if update_data:
            await db_utils.update_plan_in_db(db, user_id, name, update_data)
        
        # Build response
        changes_str = ", ".join(changes) if changes else "no changes made"
        response = f"Updated plan '{name}': {changes_str}"
        
        if jar_propose_adjust_details:
            response += f" | jar recommendations: {jar_propose_adjust_details}"
        
        # Format response based on confidence
        if confidence >= 90:
            return f"✅ {response}"
        elif confidence >= 70:
            return f"⚠️ {response} ({confidence}% confident)"
        else:
            return f"❓ {response} ({confidence}% confident - please verify)"
    
    @staticmethod
    async def get_plan(db: AsyncIOMotorDatabase, user_id: str, status: str = "active", 
                      name_filter: Optional[str] = None) -> str:
        """Retrieve budget plans by status - matches lab interface exactly."""
        
        all_plans = await db_utils.get_all_plans_for_user(db, user_id)
        
        # Filter by status
        if status == "all":
            plans = all_plans
        else:
            plans = [p for p in all_plans if p.status == status]
        
        # Filter by name if provided
        if name_filter:
            plans = [p for p in plans if name_filter.lower() in p.name.lower()]
        
        if not plans:
            status_desc = status if status != "all" else "any status"
            name_desc = f" matching '{name_filter}'" if name_filter else ""
            return f"📋 No plans found with {status_desc}{name_desc}"
        
        # Sort by creation date (newest first)
        plans.sort(key=lambda p: p.day_created, reverse=True)
        
        # Build summary
        result = f"📋 Budget Plans ({len(plans)} found):\n"
        
        for plan_obj in plans:
            status_icon = {
                "active": "🟢",
                "completed": "✅", 
                "cancelled": "❌",
                "on_hold": "⏸️"
            }.get(plan_obj.status, "📋")
            
            result += f"{status_icon} {plan_obj.name} ({plan_obj.status})\n"
            result += f"   Created: {plan_obj.day_created}\n"
            result += f"   Description: {plan_obj.detail_description}\n"
            
            if plan_obj.jar_recommendations:
                result += f"   Jar Recommendations: {plan_obj.jar_recommendations}\n"
            
            result += "\n"
        
        return result.strip()
    
    @staticmethod
    async def delete_plan(db: AsyncIOMotorDatabase, user_id: str, name: str, reason: str = "") -> str:
        """Delete budget plan - matches lab interface exactly."""
        
        # Find plan
        plan_obj = await db_utils.get_plan_by_name(db, user_id, name)
        if not plan_obj:
            return f"❌ Plan '{name}' not found"
        
        # Delete plan
        success = await db_utils.delete_plan_by_name(db, user_id, name)
        if success:
            response = f"Deleted plan '{name}'"
            if reason:
                response += f". Reason: {reason}"
            return f"✅ {response}"
        else:
            return f"❌ Failed to delete plan '{name}'"
    
    @staticmethod
    async def list_plans(db: AsyncIOMotorDatabase, user_id: str, active_only: bool = True) -> str:
        """List all budget plans for a user - enhanced version."""
        
        if active_only:
            return await PlanManagementService.get_plan(db, user_id, "active")
        else:
            return await PlanManagementService.get_plan(db, user_id, "all")
    
    @staticmethod
    async def create_budget_plan(db: AsyncIOMotorDatabase, user_id: str,
                               title: str, description: str, 
                               target_amount: float, target_date: str) -> str:
        """Create a budget plan - legacy interface compatibility."""
        
        # Create plan with enhanced description
        enhanced_description = f"{description} | Target: {CalculationService.format_currency(target_amount)} by {target_date}"
        
        return await PlanManagementService.create_plan(
            db, user_id, title, enhanced_description, "active"
        )
        
        plan_list = []
        for p in plans:
            status = "🎯 Active" if p.is_active else "⏸️ Paused"
            progress = f"{CalculationService.format_currency(p.current_amount)}/{CalculationService.format_currency(p.target_amount)}"
            plan_list.append(f"{status} **{p.title}**: {progress} (Due: {p.target_date})")
        
        return "📋 **Your Budget Plans:**\n" + "\n".join(plan_list)
    
    @staticmethod
    async def update_plan_progress(db: AsyncIOMotorDatabase, user_id: str,
                                 plan_title: str, amount_to_add: float) -> str:
        """Update progress on a budget plan."""
        plans = await db_utils.get_user_plans(db, user_id)
        target_plan = None
        
        for p in plans:
            if p.title.lower() == plan_title.lower():
                target_plan = p
                break
        
        if not target_plan:
            return f"❌ Budget plan '{plan_title}' not found."
        
        new_amount = target_plan.current_amount + amount_to_add
        target_plan.current_amount = min(new_amount, target_plan.target_amount)
        
        await db_utils.update_plan_in_db(db, user_id, target_plan)
        
        progress_percent = (target_plan.current_amount / target_plan.target_amount) * 100
        return f"📈 Updated '{plan_title}': {CalculationService.format_currency(target_plan.current_amount)}/{CalculationService.format_currency(target_plan.target_amount)} ({progress_percent:.1f}%)"
    
    @staticmethod
    async def delete_plan(db: AsyncIOMotorDatabase, user_id: str, plan_title: str) -> str:
        """Delete a budget plan."""
        success = await db_utils.delete_plan_from_db(db, user_id, plan_title)
        
        if success:
            return f"✅ Deleted budget plan '{plan_title}'"
        else:
            return f"❌ Budget plan '{plan_title}' not found"
    
    # =============================================================================
    # LAB-COMPATIBLE INTERFACE METHODS (from _service_old.py)
    # =============================================================================
    
    @staticmethod
    async def create_plan(db: AsyncIOMotorDatabase, user_id: str, 
                         name: str, description: str, status: str = "active", 
                         jar_propose_adjust_details: str = None) -> Dict[str, Any]:
        """Create new budget plan with jar recommendations - lab compatible interface."""
        # Check if plan already exists
        existing_plans = await db_utils.get_user_plans(db, user_id)
        for existing_plan in existing_plans:
            if existing_plan.title.lower() == name.lower():
                return {"data": {}, "description": f"plan {name} already exists"}
        
        # Create new plan using the backend model
        new_plan = plan.BudgetPlanInDB(
            id=str(datetime.utcnow().timestamp()),
            user_id=user_id,
            title=name,
            description=description,
            target_amount=0.0,  # Default, can be updated later
            current_amount=0.0,
            target_date=datetime.now().strftime("%Y-%m-%d"),
            day_created=datetime.now().strftime("%Y-%m-%d"),
            is_active=(status == "active"),
            jar_recommendations=jar_propose_adjust_details
        )
        
        await db_utils.create_plan_in_db(db, user_id, new_plan)
        
        # Build response data
        response_data = {
            "name": new_plan.title,
            "detail_description": new_plan.description,
            "day_created": new_plan.day_created,
            "status": status,
            "jar_recommendations": jar_propose_adjust_details
        }
        
        description_parts = [f"created plan {name} with status {status}"]
        if jar_propose_adjust_details:
            description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
        
        return {
            "data": response_data,
            "description": " | ".join(description_parts)
        }
    
    @staticmethod
    async def adjust_plan(db: AsyncIOMotorDatabase, user_id: str,
                         name: str, description: str = None, status: str = None, 
                         jar_propose_adjust_details: str = None) -> Dict[str, Any]:
        """Modify existing budget plan - lab compatible interface."""
        # Find existing plan
        plans = await db_utils.get_user_plans(db, user_id)
        target_plan = None
        
        for p in plans:
            if p.title.lower() == name.lower():
                target_plan = p
                break
        
        if not target_plan:
            return {"data": {}, "description": f"plan {name} not found"}
        
        changes = []
        
        # Update description
        if description is not None:
            target_plan.description = description
            changes.append("description updated")
        
        # Update status
        if status is not None:
            old_status = "active" if target_plan.is_active else "paused"
            target_plan.is_active = (status == "active")
            changes.append(f"status: {old_status} → {status}")
        
        # Update jar recommendations
        if jar_propose_adjust_details is not None:
            target_plan.jar_recommendations = jar_propose_adjust_details
            changes.append("jar recommendations updated")
        
        # Save updated plan
        await db_utils.update_plan_in_db(db, user_id, target_plan)
        
        # Build response data
        response_data = {
            "name": target_plan.title,
            "detail_description": target_plan.description,
            "day_created": target_plan.day_created,
            "status": "active" if target_plan.is_active else "paused",
            "jar_recommendations": target_plan.jar_recommendations
        }
        
        description_parts = [f"updated plan {name}: {', '.join(changes) if changes else 'no changes made'}"]
        if jar_propose_adjust_details:
            description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
        
        return {
            "data": response_data,
            "description": " | ".join(description_parts)
        }
    
    @staticmethod
    async def get_plan(db: AsyncIOMotorDatabase, user_id: str,
                      status: str = "active", description: str = "") -> Dict[str, Any]:
        """Retrieve budget plans by status - lab compatible interface."""
        all_plans = await db_utils.get_user_plans(db, user_id)
        
        if status == "all":
            plans = all_plans
        else:
            plans = [p for p in all_plans if (p.is_active and status == "active") or (not p.is_active and status == "paused")]
        
        # Convert to lab-compatible dict format
        plan_dicts = []
        for p in plans:
            plan_dict = {
                "name": p.title,
                "detail_description": p.description,
                "day_created": p.day_created,
                "status": "active" if p.is_active else "paused",
                "jar_recommendations": p.jar_recommendations
            }
            plan_dicts.append(plan_dict)
        
        return {
            "data": plan_dicts,
            "description": description or f"retrieved {len(plan_dicts)} {status} plans"
        }
    
    @staticmethod
    async def delete_plan_lab_compatible(db: AsyncIOMotorDatabase, user_id: str,
                                        name: str, reason: str = "") -> Dict[str, Any]:
        """Delete budget plan - lab compatible interface."""
        # Find and delete plan
        plans = await db_utils.get_user_plans(db, user_id)
        target_plan = None
        
        for p in plans:
            if p.title.lower() == name.lower():
                target_plan = p
                break
        
        if not target_plan:
            return {"data": {}, "description": f"plan {name} not found"}
        
        success = await db_utils.delete_plan_from_db(db, user_id, name)
        
        if success:
            return {
                "data": {"deleted": True},
                "description": f"deleted plan {name}. Reason: {reason}"
            }
        else:
            return {"data": {}, "description": f"failed to delete plan {name}"}
