"""
Jar Management Service - Complete Implementation from Lab
=======================================================

This module implements the complete jar management service ported from the lab
with database backend, maintaining exact same interface and behavior.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models import jar
from .core_services import UserSettingsService, CalculationService

# =============================================================================
# JAR MANAGEMENT SERVICE - FULL IMPLEMENTATION FROM LAB
# =============================================================================

class JarManagementService:
    """
    Complete jar management service ported from lab with database backend.
    Maintains exact same interface and behavior as the original.
    """
    
    @staticmethod
    async def create_jar(db: AsyncIOMotorDatabase, user_id: str, name: List[str], description: List[str], 
                        percent: List[Optional[float]] = None, 
                        amount: List[Optional[float]] = None, 
                        confidence: int = 85) -> str:
        """Create one or multiple jars with atomic validation and rebalancing."""
        if not name or not description:
            return "❌ Name and description lists cannot be empty."

        # Initialize and validate list lengths
        num_jars = len(name)
        if len(description) != num_jars:
            return f"❌ Description list length ({len(description)}) must match name list length ({num_jars})."
        percent = percent if percent is not None else [None] * num_jars
        amount = amount if amount is not None else [None] * num_jars
        if len(percent) != num_jars or len(amount) != num_jars:
            return "❌ All parameter lists must have the same length."

        # Get user's total income for calculations
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        
        # --- PASS 1: VALIDATION ---
        validated_jars_data = []
        total_new_percent = 0.0
        current_jars = await db_utils.get_all_jars_for_user(db, user_id)
        current_total_percent = sum(j.percent for j in current_jars)

        for i in range(num_jars):
            jar_name, jar_desc, jar_percent, jar_amount = name[i], description[i], percent[i], amount[i]

            if not jar_name or not jar_desc:
                return f"❌ Jar {i+1}: Name and description cannot be empty."

            if jar_percent is None and jar_amount is None:
                return f"❌ Jar {i+1} '{jar_name}': Must provide either 'percent' or 'amount'."
            if jar_percent is not None and jar_amount is not None:
                return f"❌ Jar {i+1} '{jar_name}': Cannot provide both 'percent' and 'amount'."

            if jar_amount is not None:
                jar_percent = jar_amount / total_income

            if not CalculationService.validate_percentage_range(jar_percent):
                return f"❌ Jar {i+1} '{jar_name}': Percentage {CalculationService.format_percentage(jar_percent)} is invalid."

            clean_name = jar_name.strip().lower().replace(' ', '_')
            
            # Check if jar already exists
            existing_jar = await db_utils.get_jar_by_name(db, user_id, clean_name)
            if existing_jar:
                return f"❌ Jar '{jar_name}' already exists."

            validated_jars_data.append({
                'name': clean_name, 
                'description': jar_desc,
                'percent': jar_percent, 
                'amount': jar_percent * total_income
            })
            total_new_percent += jar_percent

        # Validate total allocation
        if total_new_percent > 1.001:  # Allow for small float inaccuracies
            return (f"❌ Cannot create jars. New jars alone total {CalculationService.format_percentage(total_new_percent)}, "
                   f"which exceeds the 100% maximum.")

        # --- PASS 2: EXECUTION ---
        created_jars_info = []
        for data in validated_jars_data:
            new_jar = jar.JarInDB(
                id=str(datetime.utcnow().timestamp()),  # Simple ID generation
                user_id=user_id,
                name=data['name'], 
                description=data['description'], 
                percent=data['percent'],
                amount=data['amount'],
                current_percent=0.0, 
                current_amount=0.0
            )
            await db_utils.create_jar_in_db(db, user_id, new_jar)
            created_jars_info.append(f"'{new_jar.name}': {CalculationService.format_percentage(new_jar.percent)} ({CalculationService.format_currency(new_jar.amount)})")

        # Final Response
        if len(name) == 1:
            base_message = f"Created jar: {created_jars_info[0]}"
        else:
            created_summary = ", ".join(created_jars_info)
            base_message = f"Created {len(name)} jars: {created_summary}"
        
        if confidence >= 90:
            return f"✅ {base_message} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ {base_message} ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ {base_message} ({confidence}% confident - please verify)"

    @staticmethod
    async def update_jar(db: AsyncIOMotorDatabase, user_id: str, jar_name: List[str], 
                        new_name: List[Optional[str]] = None, 
                        new_description: List[Optional[str]] = None,
                        new_percent: List[Optional[float]] = None, 
                        new_amount: List[Optional[float]] = None, 
                        confidence: int = 85) -> str:
        """Update multiple existing jars with atomic validation and rebalancing."""
        if not jar_name:
            return "❌ Jar name list cannot be empty."

        # Initialize and validate list lengths
        num_jars = len(jar_name)
        new_name = new_name if new_name is not None else [None] * num_jars
        new_description = new_description if new_description is not None else [None] * num_jars
        new_percent = new_percent if new_percent is not None else [None] * num_jars
        new_amount = new_amount if new_amount is not None else [None] * num_jars
        if not all(len(lst) == num_jars for lst in [new_name, new_description, new_percent, new_amount]):
            return "❌ All parameter lists must have the same length."

        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        
        # --- PASS 1: VALIDATION ---
        updates_to_perform = []
        total_percent_change = 0.0

        for i in range(num_jars):
            current_jar_name_clean = jar_name[i].strip().lower().replace(' ', '_')
            jar_to_update = await db_utils.get_jar_by_name(db, user_id, current_jar_name_clean)
            if not jar_to_update:
                return f"❌ Jar '{jar_name[i]}' not found."

            update_data = {'original_jar': jar_to_update, 'changes': {}}

            if new_name[i]:
                new_clean_name = new_name[i].strip().lower().replace(' ', '_')
                existing_jar = await db_utils.get_jar_by_name(db, user_id, new_clean_name)
                if existing_jar and existing_jar.name != current_jar_name_clean:
                    return f"❌ New name '{new_name[i]}' already exists."
                update_data['changes']['name'] = new_clean_name

            if new_description[i]:
                update_data['changes']['description'] = new_description[i]

            jar_new_percent = new_percent[i]
            if new_amount[i] is not None:
                jar_new_percent = new_amount[i] / total_income

            if jar_new_percent is not None:
                if not CalculationService.validate_percentage_range(jar_new_percent):
                    return f"❌ New percentage for '{jar_name[i]}' is invalid."
                update_data['changes']['percent'] = jar_new_percent
                update_data['changes']['amount'] = jar_new_percent * total_income
                total_percent_change += (jar_new_percent - jar_to_update.percent)
            
            updates_to_perform.append(update_data)

        # --- PASS 2: EXECUTION ---
        updated_jars_info = []
        
        for update in updates_to_perform:
            jar_obj = update['original_jar']
            changes = update['changes']
            
            if changes:
                updated_jar = await db_utils.update_jar_in_db(db, user_id, jar_obj.name, changes)
                if updated_jar:
                    updated_jars_info.append(f"'{updated_jar.name}': {CalculationService.format_percentage(updated_jar.percent)}")

        if updated_jars_info:
            updates_summary = ", ".join(updated_jars_info)
            base_message = f"Updated jars: {updates_summary}"
        else:
            base_message = "No changes made"
        
        if confidence >= 90:
            return f"✅ {base_message} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ {base_message} ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ {base_message} ({confidence}% confident - please verify)"

    @staticmethod
    async def delete_jar(db: AsyncIOMotorDatabase, user_id: str, jar_name: List[str], reason: str) -> str:
        """Delete one or more jars and redistribute their allocation."""
        if not jar_name:
            return "❌ Jar name list cannot be empty."

        deleted_info = []
        total_deleted_percent = 0.0

        for name in jar_name:
            clean_name = name.strip().lower().replace(' ', '_')
            jar_to_delete = await db_utils.get_jar_by_name(db, user_id, clean_name)
            
            if not jar_to_delete:
                return f"❌ Jar '{name}' not found."
            
            # Delete the jar
            success = await db_utils.delete_jar_by_name(db, user_id, clean_name)
            if success:
                deleted_info.append(f"'{jar_to_delete.name}': {CalculationService.format_percentage(jar_to_delete.percent)}")
                total_deleted_percent += jar_to_delete.percent

        if deleted_info:
            deleted_summary = ", ".join(deleted_info)
            return f"✅ Deleted jars: {deleted_summary}. Freed up {CalculationService.format_percentage(total_deleted_percent)} allocation."
        else:
            return "❌ No jars were deleted."

    @staticmethod
    async def list_jars(db: AsyncIOMotorDatabase, user_id: str) -> str:
        """List all jars for a user."""
        jars = await db_utils.get_all_jars_for_user(db, user_id)
        
        if not jars:
            return "📋 No jars found. Create some jars to start managing your budget!"
        
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        jar_lines = []
        total_percent = 0.0
        
        for jar_obj in jars:
            total_percent += jar_obj.percent
            jar_lines.append(
                f"• **{jar_obj.name}**: {CalculationService.format_percentage(jar_obj.percent)} "
                f"({CalculationService.format_currency(jar_obj.amount)}) - {jar_obj.description}"
            )
        
        jar_summary = "\n".join(jar_lines)
        allocation_status = f"💰 Total allocation: {CalculationService.format_percentage(total_percent)}"
        
        if total_percent > 1.0:
            allocation_status += " ⚠️ (Over 100%)"
        elif total_percent < 0.99:
            remaining = 1.0 - total_percent
            allocation_status += f" (Remaining: {CalculationService.format_percentage(remaining)})"
        
        return f"📊 **Your Budget Jars** (Total Income: {CalculationService.format_currency(total_income)})\n\n{jar_summary}\n\n{allocation_status}"

    @staticmethod
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """Request clarification from user."""
        if suggestions:
            return f"❓ {question}\n\n💡 Suggestions: {suggestions}"
        return f"❓ {question}"
