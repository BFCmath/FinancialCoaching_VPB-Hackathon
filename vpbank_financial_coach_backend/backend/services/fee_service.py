"""
Fee Management Service - Complete Implementation from Lab
=======================================================

This module implements the complete fee management service ported from the lab
with database backend, maintaining exact same interface and behavior.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models import fee
from .core_services import UserSettingsService, CalculationService

# =============================================================================
# FEE MANAGEMENT SERVICE - FROM LAB  
# =============================================================================

class FeeManagementService:
    """
    Fee management service ported from lab with database backend.
    Maintains exact same interface and behavior as the original.
    """
    
    @staticmethod
    async def create_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, 
                                  name: str, amount: float, description: str, pattern_type: str,
                                  pattern_details: Optional[List[int]], target_jar: str, 
                                  confidence: int = 85) -> str:
        """Create recurring fee with scheduling - matches lab interface exactly."""
        
        # Validate fee name uniqueness
        existing_fees = await db_utils.get_all_fees_for_user(db, user_id)
        existing_names = [fee.name.lower() for fee in existing_fees]
        if name.lower() in existing_names:
            return f"❌ Fee name '{name}' already exists"
        
        # Validate target jar exists
        jar_obj = await db_utils.get_jar_by_name(db, user_id, target_jar.lower().replace(' ', '_'))
        if not jar_obj:
            return f"❌ Target jar '{target_jar}' not found"
        
        # Validate amount
        if not CalculationService.validate_positive_amount(amount):
            return f"❌ Amount must be positive, got ${amount:.2f}"
        
        # Validate pattern type
        if pattern_type not in ["daily", "weekly", "monthly"]:
            return f"❌ Pattern type must be 'daily', 'weekly', or 'monthly', got '{pattern_type}'"
        
        # Calculate next occurrence using lab logic
        next_occurrence = FeeManagementService._calculate_next_occurrence(pattern_type, pattern_details)
        
        # Create fee object
        new_fee = fee.FeeInDB(
            id=str(datetime.utcnow().timestamp()),
            user_id=user_id,
            name=name,
            amount=amount,
            description=description,
            target_jar=jar_obj.name,
            pattern_type=pattern_type,
            pattern_details=pattern_details,
            created_date=datetime.now(),
            next_occurrence=next_occurrence,
            is_active=True
        )
        
        # Save to database
        await db_utils.create_fee_in_db(db, user_id, new_fee)
        
        # Format pattern description for response
        pattern_desc = FeeManagementService._format_pattern_description(pattern_type, pattern_details)
        
        # Format response based on confidence (matches lab format)
        if confidence >= 90:
            return f"✅ Created recurring fee: {name} - ${amount} {pattern_desc} → {jar_obj.name} jar. Next: {next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ Created recurring fee: {name} - ${amount} {pattern_desc} → {jar_obj.name} jar. Next: {next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ Created recurring fee: {name} - ${amount} {pattern_desc} → {jar_obj.name} jar. Next: {next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - please verify)"
    
    @staticmethod
    async def adjust_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, 
                                 fee_name: str, new_amount: Optional[float] = None,
                                 new_description: Optional[str] = None, new_pattern_type: Optional[str] = None,
                                 new_pattern_details: Optional[List[int]] = None, new_target_jar: Optional[str] = None,
                                 disable: bool = False, confidence: int = 85) -> str:
        """Update recurring fee - matches lab interface exactly."""
        
        # Find fee by name
        fee_obj = await db_utils.get_fee_by_name(db, user_id, fee_name)
        if not fee_obj:
            return f"❌ Fee '{fee_name}' not found"
        
        changes = []
        update_data = {}
        
        # Update amount
        if new_amount is not None:
            if not CalculationService.validate_positive_amount(new_amount):
                return f"❌ Amount must be positive, got ${new_amount:.2f}"
            old_amount = fee_obj.amount
            update_data['amount'] = new_amount
            changes.append(f"amount: ${old_amount} → ${new_amount}")
        
        # Update description
        if new_description is not None:
            update_data['description'] = new_description
            changes.append("description updated")
        
        # Update target jar
        if new_target_jar is not None:
            jar_obj = await db_utils.get_jar_by_name(db, user_id, new_target_jar.lower().replace(' ', '_'))
            if not jar_obj:
                return f"❌ Target jar '{new_target_jar}' not found"
            old_jar = fee_obj.target_jar
            update_data['target_jar'] = jar_obj.name
            changes.append(f"jar: {old_jar} → {jar_obj.name}")
        
        # Update pattern
        if new_pattern_type is not None:
            if new_pattern_type not in ["daily", "weekly", "monthly"]:
                return f"❌ Pattern type must be 'daily', 'weekly', or 'monthly'"
            update_data['pattern_type'] = new_pattern_type
            changes.append(f"pattern: {new_pattern_type}")
        
        if new_pattern_details is not None:
            update_data['pattern_details'] = new_pattern_details
            changes.append("pattern details updated")
        
        # Disable/enable
        if disable:
            update_data['is_active'] = False
            changes.append("disabled")
        
        # Recalculate next occurrence if pattern changed
        if new_pattern_type is not None or new_pattern_details is not None:
            final_pattern_type = new_pattern_type or fee_obj.pattern_type
            final_pattern_details = new_pattern_details if new_pattern_details is not None else fee_obj.pattern_details
            update_data['next_occurrence'] = FeeManagementService._calculate_next_occurrence(
                final_pattern_type, final_pattern_details
            )
            changes.append(f"next occurrence: {update_data['next_occurrence'].strftime('%Y-%m-%d')}")
        
        # Save updates
        if update_data:
            await db_utils.update_fee_in_db(db, user_id, fee_name, update_data)
        
        changes_str = ", ".join(changes) if changes else "no changes"
        
        # Format response based on confidence
        if confidence >= 90:
            return f"✅ Updated fee '{fee_name}': {changes_str}"
        elif confidence >= 70:
            return f"⚠️ Updated fee '{fee_name}': {changes_str} ({confidence}% confident)"
        else:
            return f"❓ Updated fee '{fee_name}': {changes_str} ({confidence}% confident - please verify)"
    
    @staticmethod
    async def delete_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, fee_name: str, reason: str) -> str:
        """Delete recurring fee - matches lab interface exactly."""
        
        # Find and delete fee
        fee_obj = await db_utils.get_fee_by_name(db, user_id, fee_name)
        if not fee_obj:
            return f"❌ Fee '{fee_name}' not found"
        
        success = await db_utils.delete_fee_by_name(db, user_id, fee_name)
        if success:
            return f"✅ Deleted recurring fee '{fee_name}' (${fee_obj.amount} {fee_obj.pattern_type}). Reason: {reason}"
        else:
            return f"❌ Failed to delete fee '{fee_name}'"
    
    @staticmethod
    async def list_recurring_fees(db: AsyncIOMotorDatabase, user_id: str, 
                                active_only: bool = True, target_jar: Optional[str] = None) -> str:
        """List recurring fees with optional filtering - matches lab interface exactly."""
        
        fees = await db_utils.get_all_fees_for_user(db, user_id)
        
        # Filter by active status
        if active_only:
            fees = [f for f in fees if f.is_active]
        
        # Filter by target jar
        if target_jar:
            jar_obj = await db_utils.get_jar_by_name(db, user_id, target_jar.lower().replace(' ', '_'))
            if jar_obj:
                fees = [f for f in fees if f.target_jar == jar_obj.name]
            else:
                return f"❌ Jar '{target_jar}' not found"
        
        if not fees:
            status_desc = "active" if active_only else "all"
            jar_desc = f" in {target_jar} jar" if target_jar else ""
            return f"📋 No {status_desc} recurring fees{jar_desc}"
        
        # Sort by next occurrence
        fees.sort(key=lambda f: f.next_occurrence)
        
        result = f"📋 Recurring Fees ({len(fees)} found):\n"
        for fee_obj in fees:
            status = "✅" if fee_obj.is_active else "❌"
            pattern_desc = FeeManagementService._format_pattern_description(fee_obj.pattern_type, fee_obj.pattern_details)
            result += f"{status} {fee_obj.name} - ${fee_obj.amount} {pattern_desc} → {fee_obj.target_jar} jar"
            result += f" | Next: {fee_obj.next_occurrence.strftime('%Y-%m-%d')}\n"
        
        return result.strip()
    
    @staticmethod
    def _calculate_next_occurrence(pattern_type: str, pattern_details: Optional[List[int]], from_date: datetime = None) -> datetime:
        """Calculate when fee should next occur based on pattern - matches lab logic exactly."""
        if from_date is None:
            from_date = datetime.now()
        
        if pattern_type == "daily":
            return from_date + timedelta(days=1)
            
        elif pattern_type == "weekly":
            if pattern_details is None:
                return from_date + timedelta(days=1)
            else:
                # Specific days of the week
                current_weekday = from_date.weekday() + 1  # Monday=1, ..., Sunday=7
                next_days = [d for d in pattern_details if d > current_weekday]
                if next_days:
                    days_until = min(next_days) - current_weekday
                else:
                    # Next week, first day
                    days_until = 7 - current_weekday + min(pattern_details)
                return from_date + timedelta(days=days_until)
            
        elif pattern_type == "monthly":
            if pattern_details is None:
                return from_date + timedelta(days=1)
            else:
                # Specific days of the month
                current_day = from_date.day
                next_dates_this_month = [d for d in pattern_details if d > current_day]
                if next_dates_this_month:
                    target_date = min(next_dates_this_month)
                    try:
                        return from_date.replace(day=target_date)
                    except ValueError:
                        pass
                
                # Next month, first target date
                next_month = from_date.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                target_date = min(pattern_details)
                try:
                    return next_month.replace(day=target_date)
                except ValueError:
                    # Target date doesn't exist, use last day of month
                    month_after = next_month.replace(day=1) + timedelta(days=32)
                    last_day = (month_after.replace(day=1) - timedelta(days=1)).day
                    return next_month.replace(day=min(target_date, last_day))
        
        # Default fallback
        return from_date + timedelta(days=1)
    
    @staticmethod
    def _format_pattern_description(pattern_type: str, pattern_details: Optional[List[int]]) -> str:
        """Format pattern for human-readable description - matches lab logic exactly."""
        if pattern_type == "daily":
            return "daily"
        elif pattern_type == "weekly":
            if not pattern_details:
                return "every day"
            else:
                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                day_names = [days[d-1] for d in pattern_details if 1 <= d <= 7]
                return f"weekly on {', '.join(day_names)}"
        elif pattern_type == "monthly":
            if not pattern_details:
                return "every day"
            else:
                day_strs = [f"{d}{('th' if 10 <= d <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th'))}" 
                           for d in pattern_details]
                return f"monthly on {', '.join(day_strs)}"
        
        return pattern_type
