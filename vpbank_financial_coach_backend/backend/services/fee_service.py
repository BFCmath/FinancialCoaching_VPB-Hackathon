"""
Fee Management Service - Complete Implementation from Lab
=======================================================

This module implements the complete fee management service ported from the lab
with database backend, maintaining exact same interface and behavior.
Covers all recurring fee operations from lab utils.py and service.py:
- save_recurring_fee, get_recurring_fee, get_all_recurring_fees, get_active_recurring_fees, delete_recurring_fee
- calculate_next_fee_occurrence, get_fees_due_today
- create_recurring_fee, adjust_recurring_fee, delete_recurring_fee, list_recurring_fees
All methods are async where appropriate.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models.fee import RecurringFeeInDB, RecurringFeeCreate, RecurringFeeBase
from .core_services import CalculationService
from .confidence_service import ConfidenceService

class FeeManagementService:
    """
    Recurring fee management service.
    """
    
    @staticmethod
    async def save_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, fee_data: RecurringFeeCreate) -> RecurringFeeInDB:
        """Save recurring fee to database."""
        return await db_utils.create_fee_in_db(db, user_id, fee_data)
    
    @staticmethod
    async def get_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, fee_name: str) -> Optional[RecurringFeeInDB]:
        """Get recurring fee by name."""
        return await db_utils.get_fee_by_name(db, user_id, fee_name)
    
    @staticmethod
    async def get_all_recurring_fees(db: AsyncIOMotorDatabase, user_id: str) -> List[RecurringFeeInDB]:
        """Get all recurring fees."""
        return await db_utils.get_all_fees_for_user(db, user_id)
    
    @staticmethod
    async def get_active_recurring_fees(db: AsyncIOMotorDatabase, user_id: str) -> List[RecurringFeeInDB]:
        """Get only active recurring fees."""
        fees = await FeeManagementService.get_all_recurring_fees(db, user_id)
        return [f for f in fees if f.is_active]
    
    @staticmethod
    async def delete_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, fee_name: str) -> bool:
        """Delete recurring fee from database."""
        return await db_utils.delete_fee_by_name(db, user_id, fee_name)
    
    @staticmethod
    def calculate_next_fee_occurrence(pattern_type: str, pattern_details: Optional[List[int]], from_date: Optional[datetime] = None) -> datetime:
        """Calculate when fee should next occur based on pattern."""
        if from_date is None:
            from_date = datetime.now()
        
        if pattern_type == "daily":
            return from_date + timedelta(days=1)
        
        elif pattern_type == "weekly":
            if not pattern_details:  # Every day
                return from_date + timedelta(days=1)
            else:
                current_weekday = from_date.weekday() + 1  # 1=Monday, 7=Sunday
                next_days = [d for d in pattern_details if d > current_weekday]
                if next_days:
                    days_until = min(next_days) - current_weekday
                else:
                    days_until = 7 - current_weekday + min(pattern_details)
                return from_date + timedelta(days=days_until)
        
        elif pattern_type == "monthly":
            if not pattern_details:  # Every day
                return from_date + timedelta(days=1)
            else:
                current_day = from_date.day
                next_dates_this_month = [d for d in pattern_details if d > current_day]
                if next_dates_this_month:
                    target_date = min(next_dates_this_month)
                    try:
                        return from_date.replace(day=target_date)
                    except ValueError:
                        pass
                
                next_month = from_date.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                target_date = min(pattern_details)
                try:
                    return next_month.replace(day=target_date)
                except ValueError:
                    month_after = next_month.replace(day=1) + timedelta(days=32)
                    last_day = (month_after.replace(day=1) - timedelta(days=1)).day
                    return next_month.replace(day=min(target_date, last_day))
        
        return from_date + timedelta(days=1)
    
    @staticmethod
    async def get_fees_due_today(db: AsyncIOMotorDatabase, user_id: str) -> List[RecurringFeeInDB]:
        """Get fees that are due today."""
        active_fees = await FeeManagementService.get_active_recurring_fees(db, user_id)
        today = datetime.now().date()
        return [f for f in active_fees if f.next_occurrence.date() <= today]
    
    @staticmethod
    async def create_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, 
                                   name: str, amount: float, description: str, pattern_type: str,
                                   pattern_details: Optional[List[int]], target_jar: str, 
                                   confidence: int = 85) -> str:
        """Create recurring fee with scheduling."""
        # Validate fee name
        is_valid, error_msg = await FeeManagementService._validate_fee_name(db, user_id, name)
        if not is_valid:
            return f"❌ {error_msg}"
        
        # Validate target jar
        jar = await db_utils.get_jar_by_name(db, user_id, target_jar.lower().replace(' ', '_'))
        if not jar:
            return f"❌ Target jar '{target_jar}' not found"
        
        # Validate amount
        if not CalculationService.validate_positive_amount(amount):
            return f"❌ Amount must be positive, got {CalculationService.format_currency(amount)}"
        
        # Validate pattern type
        if pattern_type not in ["daily", "weekly", "monthly"]:
            return f"❌ Pattern type must be 'daily', 'weekly', or 'monthly', got '{pattern_type}'"
        
        next_occurrence = FeeManagementService.calculate_next_fee_occurrence(pattern_type, pattern_details)
        
        fee_data = RecurringFeeInDB(
            name=name,
            amount=amount,
            description=description,
            target_jar=jar.name,
            pattern_type=pattern_type,
            pattern_details=pattern_details or [],
            next_occurrence=next_occurrence,
            is_active=True
        )
        
        await FeeManagementService.save_recurring_fee(db, user_id, fee_data)
        
        pattern_desc = FeeManagementService._format_pattern_description(pattern_type, pattern_details)
        result = f"Created recurring fee '{name}': {CalculationService.format_currency(amount)} {pattern_desc} → {jar.name} jar. Next: {next_occurrence.strftime('%Y-%m-%d')}"
        return ConfidenceService.format_confidence_response(result, confidence)
    
    @staticmethod
    async def adjust_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, 
                                   fee_name: str, new_amount: Optional[float] = None,
                                   new_description: Optional[str] = None, new_pattern_type: Optional[str] = None,
                                   new_pattern_details: Optional[List[int]] = None, new_target_jar: Optional[str] = None,
                                   disable: bool = False, confidence: int = 85) -> str:
        """Update recurring fee."""
        fee = await FeeManagementService.get_recurring_fee(db, user_id, fee_name)
        if not fee:
            return f"❌ Fee '{fee_name}' not found"
        
        update_data = RecurringFeeInDB()
        changes = []
        
        if new_amount is not None:
            if not CalculationService.validate_positive_amount(new_amount):
                return f"❌ Amount must be positive, got {CalculationService.format_currency(new_amount)}"
            old_amount = fee.amount
            update_data.amount = new_amount
            changes.append(f"amount: {CalculationService.format_currency(old_amount)} → {CalculationService.format_currency(new_amount)}")
        
        if new_description is not None:
            update_data.description = new_description
            changes.append("description updated")
        
        if new_pattern_type is not None:
            if new_pattern_type not in ["daily", "weekly", "monthly"]:
                return f"❌ Pattern type must be 'daily', 'weekly', or 'monthly'"
            update_data.pattern_type = new_pattern_type
            changes.append(f"pattern: {new_pattern_type}")
        
        if new_pattern_details is not None:
            update_data.pattern_details = new_pattern_details
            changes.append("pattern details updated")
        
        if new_target_jar is not None:
            jar = await db_utils.get_jar_by_name(db, user_id, new_target_jar.lower().replace(' ', '_'))
            if not jar:
                return f"❌ Target jar '{new_target_jar}' not found"
            old_jar = fee.target_jar
            update_data.target_jar = jar.name
            changes.append(f"target: {old_jar} → {jar.name}")
        
        if disable:
            update_data.is_active = False
            changes.append("disabled")
        
        if new_pattern_type is not None or new_pattern_details is not None:
            final_type = new_pattern_type or fee.pattern_type
            final_details = new_pattern_details if new_pattern_details is not None else fee.pattern_details
            update_data.next_occurrence = FeeManagementService.calculate_next_fee_occurrence(final_type, final_details)
            changes.append(f"next occurrence: {update_data.next_occurrence.strftime('%Y-%m-%d')}")
        
        if changes:
            await db_utils.update_fee_in_db(db, user_id, fee_name, update_data)
        
        changes_str = ", ".join(changes) if changes else "no changes"
        result = f"Updated fee '{fee_name}': {changes_str}"
        return ConfidenceService.format_confidence_response(result, confidence)
    
    @staticmethod
    async def delete_recurring_fee(db: AsyncIOMotorDatabase, user_id: str, fee_name: str, reason: str) -> str:
        """Delete recurring fee."""
        fee = await FeeManagementService.get_recurring_fee(db, user_id, fee_name)
        if not fee:
            return f"❌ Fee '{fee_name}' not found"
        
        deleted = await FeeManagementService.delete_recurring_fee(db, user_id, fee_name)
        if deleted:
            return f"✅ Deleted recurring fee '{fee_name}'. Reason: {reason}"
        return f"❌ Failed to delete fee '{fee_name}'"
    
    @staticmethod
    async def list_recurring_fees(db: AsyncIOMotorDatabase, user_id: str, 
                                  active_only: bool = True, target_jar: Optional[str] = None) -> str:
        """List recurring fees with optional filtering."""
        fees = await FeeManagementService.get_all_recurring_fees(db, user_id)
        
        if active_only:
            fees = [f for f in fees if f.is_active]
        
        if target_jar:
            jar = await db_utils.get_jar_by_name(db, user_id, target_jar.lower().replace(' ', '_'))
            if jar:
                fees = [f for f in fees if f.target_jar == jar.name]
            else:
                return f"❌ Jar '{target_jar}' not found"
        
        if not fees:
            status_desc = "active" if active_only else "all"
            jar_desc = f" in {target_jar} jar" if target_jar else ""
            return f"📋 No {status_desc} recurring fees{jar_desc}"
        
        # Group by jar
        by_jar = {}
        total_monthly = 0.0
        
        for fee in fees:
            by_jar.setdefault(fee.target_jar, []).append(fee)
            
            # Rough monthly calculation
            if fee.pattern_type == "daily":
                total_monthly += fee.amount * 30
            elif fee.pattern_type == "weekly":
                days_count = len(fee.pattern_details) if fee.pattern_details else 7
                total_monthly += fee.amount * days_count * 4
            elif fee.pattern_type == "monthly":
                days_count = len(fee.pattern_details) if fee.pattern_details else 30
                total_monthly += fee.amount * days_count
        
        summary = f"📋 Fee Summary ({len(fees)} active fees):\n"
        
        for jar_name, jar_fees in by_jar.items():
            summary += f"\n{jar_name.upper()} JAR ({len(jar_fees)} fees):\n"
            for fee in jar_fees:
                pattern_desc = FeeManagementService._format_pattern_description(fee.pattern_type, fee.pattern_details)
                summary += f"  • {fee.name}: {fee.description} - {CalculationService.format_currency(fee.amount)} {pattern_desc}"
                summary += f" | Next: {fee.next_occurrence.strftime('%Y-%m-%d')}\n"
        
        summary += f"\n💰 Estimated monthly total: {CalculationService.format_currency(total_monthly)}"
        
        return summary
    
    @staticmethod
    async def _validate_fee_name(db: AsyncIOMotorDatabase, user_id: str, name: str) -> Tuple[bool, str]:
        """Validate fee name for uniqueness and format."""
        if not name or not name.strip():
            return False, "Fee name cannot be empty"
        
        clean_name = name.strip()
        if len(clean_name) < 3:
            return False, "Fee name too short (minimum 3 characters)"
        
        existing = await FeeManagementService.get_recurring_fee(db, user_id, clean_name)
        if existing:
            return False, f"Fee name '{clean_name}' already exists"
        
        return True, ""
    
    @staticmethod
    def _format_pattern_description(pattern_type: str, pattern_details: Optional[List[int]]) -> str:
        """Format pattern for human-readable description."""
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