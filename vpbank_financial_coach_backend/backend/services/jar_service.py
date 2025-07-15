"""
Jar Management Service - Complete Implementation from Lab
=======================================================

This module implements the complete jar management service ported from the lab
with database backend, maintaining exact same interface and behavior.
Extended to cover all jar operations from lab utils.py and service.py:
- create_jar, update_jar, delete_jar, list_jars
- find_jar_by_keywords, calculate_jar_total_allocation, validate_jar_percentages
- validate_jar_data, request_clarification, validate_jar_name
All methods are async where appropriate.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models.jar import JarInDB, JarCreate, JarUpdate
from .core_services import CalculationService, UserSettingsService
from .confidence_service import ConfidenceService
from .service_responses import ServiceResult, JarOperationResult, ServiceError

class JarManagementService:
    """
    Jar management service supporting multi-jar operations.
    Implements atomic, two-pass rebalancing logic.
    """
    
    @staticmethod
    async def create_jar(db: AsyncIOMotorDatabase, user_id: str,
                         name: List[str], description: List[str], 
                         percent: List[Optional[float]] = None, 
                         amount: List[Optional[float]] = None, 
                         confidence: int = 85) -> JarOperationResult:
        """Create one or multiple jars with atomic validation and rebalancing."""
        if not name or not description:
            return JarOperationResult.error("Name and description lists cannot be empty", code="MISSING_REQUIRED_FIELDS")

        num_jars = len(name)
        if len(description) != num_jars:
            return JarOperationResult.error(
                f"Description list length ({len(description)}) must match name list length ({num_jars})",
                code="PARAMETER_MISMATCH"
            )
        
        percent = percent if percent is not None else [None] * num_jars
        amount = amount if amount is not None else [None] * num_jars
        if len(percent) != num_jars or len(amount) != num_jars:
            return JarOperationResult.error("All parameter lists must have the same length", code="PARAMETER_MISMATCH")

        total_income = await UserSettingsService.get_user_total_income(db, user_id)

        # --- PASS 1: VALIDATION ---
        validated_jars_data = []
        total_new_percent = 0.0
        validation_errors = []

        for i in range(num_jars):
            jar_name, jar_desc, jar_percent, jar_amount = name[i], description[i], percent[i], amount[i]

            if not jar_name or not jar_desc:
                validation_errors.append(ServiceError(
                    code="EMPTY_FIELD",
                    message=f"Jar {i+1}: Name and description cannot be empty",
                    field=f"jar_{i+1}"
                ))
                continue

            if jar_percent is None and jar_amount is None:
                validation_errors.append(ServiceError(
                    code="MISSING_ALLOCATION",
                    message=f"Jar {i+1} '{jar_name}': Must provide either 'percent' or 'amount'",
                    field=f"jar_{i+1}_allocation"
                ))
                continue
                
            if jar_percent is not None and jar_amount is not None:
                validation_errors.append(ServiceError(
                    code="CONFLICTING_ALLOCATION",
                    message=f"Jar {i+1} '{jar_name}': Cannot provide both 'percent' and 'amount'",
                    field=f"jar_{i+1}_allocation"
                ))
                continue

            if jar_amount is not None:
                jar_percent = await CalculationService.calculate_percent_from_amount(db, user_id, jar_amount)

            if not CalculationService.validate_percentage_range(jar_percent):
                validation_errors.append(ServiceError(
                    code="INVALID_PERCENTAGE",
                    message=f"Jar {i+1} '{jar_name}': Percentage {CalculationService.format_percentage(jar_percent)} is invalid",
                    field=f"jar_{i+1}_percent"
                ))
                continue

            clean_name = jar_name.strip().lower().replace(' ', '_')
            is_valid, error_msg = await JarManagementService.validate_jar_name(db, user_id, clean_name)
            if not is_valid:
                validation_errors.append(ServiceError(
                    code="INVALID_NAME",
                    message=f"Jar {i+1} '{jar_name}': {error_msg}",
                    field=f"jar_{i+1}_name"
                ))
                continue

            validated_jars_data.append({
                'name': clean_name, 'description': jar_desc,
                'percent': jar_percent, 
                'amount': await CalculationService.calculate_amount_from_percent(db, user_id, jar_percent)
            })
            total_new_percent += jar_percent

        if validation_errors:
            return JarOperationResult(
                status="error",
                message="Validation failed for jar creation",
                errors=validation_errors
            )

        if total_new_percent > 1.001:
            return JarOperationResult.error(
                f"Cannot create jars. New jars alone total {CalculationService.format_percentage(total_new_percent)}, which exceeds the 100% maximum",
                code="ALLOCATION_EXCEEDED"
            )

        # --- PASS 2: EXECUTION ---
        created_jars_info = []
        newly_created_names = []
        for data in validated_jars_data:
             # 1. Create a simple dictionary with all required fields
            jar_dict_to_create = {
                "user_id": user_id,
                "name": data['name'],
                "description": data['description'],
                "percent": data['percent'],
                "amount": data['amount'],
                "current_percent": 0.0,
                "current_amount": 0.0
            }

            # 2. Call the db_utils function with the correct 2 arguments
            created_jar = await db_utils.create_jar_in_db(db, jar_dict_to_create)
            
            newly_created_names.append(created_jar.name)
            created_jars_info.append(f"'{created_jar.name}': {CalculationService.format_percentage(created_jar.percent)} ({CalculationService.format_currency(created_jar.amount)})")

        # --- REBALANCING ---
        rebalance_msg = await JarManagementService._rebalance_after_creation(db, user_id, newly_created_names)

        if len(name) == 1:
            return JarOperationResult.jar_created(
                jar_name=newly_created_names[0],
                allocation=f"{CalculationService.format_percentage(validated_jars_data[0]['percent'])} ({CalculationService.format_currency(validated_jars_data[0]['amount'])})",
                rebalance_info=rebalance_msg if rebalance_msg else None
            )
        else:
            return JarOperationResult.jars_created(
                jar_count=len(name),
                jar_names=newly_created_names,
                rebalance_info=rebalance_msg if rebalance_msg else None
            )
    
    @staticmethod
    async def update_jar(db: AsyncIOMotorDatabase, user_id: str,
                         jar_name: List[str], new_name: List[Optional[str]] = None, 
                         new_description: List[Optional[str]] = None,
                         new_percent: List[Optional[float]] = None, 
                         new_amount: List[Optional[float]] = None, 
                         confidence: int = 85) -> JarOperationResult:
        """Update multiple existing jars with atomic validation and rebalancing."""
        if not jar_name:
            return JarOperationResult.error("Jar name list cannot be empty", code="MISSING_REQUIRED_FIELDS")

        num_jars = len(jar_name)
        new_name = new_name if new_name is not None else [None] * num_jars
        new_description = new_description if new_description is not None else [None] * num_jars
        new_percent = new_percent if new_percent is not None else [None] * num_jars
        new_amount = new_amount if new_amount is not None else [None] * num_jars
        if not all(len(lst) == num_jars for lst in [new_name, new_description, new_percent, new_amount]):
            return JarOperationResult.error("All parameter lists must have the same length", code="PARAMETER_MISMATCH")

        # --- PASS 1: VALIDATION ---
        updates_to_perform = []
        total_percent_change = 0.0
        validation_errors = []

        for i in range(num_jars):
            current_jar_name_clean = jar_name[i].strip().lower().replace(' ', '_')
            jar_to_update = await db_utils.get_jar_by_name(db, user_id, current_jar_name_clean)
            if not jar_to_update:
                validation_errors.append(ServiceError(
                    code="NOT_FOUND",
                    message=f"Jar '{jar_name[i]}' not found",
                    field=f"jar_{i+1}_name"
                ))
                continue

            update_data = JarUpdate()
            changes = []

            if new_name[i]:
                new_clean_name = new_name[i].strip().lower().replace(' ', '_')
                is_valid, error_msg = await JarManagementService.validate_jar_name(db, user_id, new_clean_name, exclude_current=current_jar_name_clean)
                if not is_valid:
                    validation_errors.append(ServiceError(
                        code="INVALID_NAME",
                        message=f"New name for '{jar_name[i]}': {error_msg}",
                        field=f"jar_{i+1}_new_name"
                    ))
                    continue
                update_data.name = new_clean_name
                changes.append("name")

            if new_description[i]:
                update_data.description = new_description[i]
                changes.append("description")

            jar_new_percent = new_percent[i]
            if new_amount[i] is not None:
                jar_new_percent = await CalculationService.calculate_percent_from_amount(db, user_id, new_amount[i])

            if jar_new_percent is not None:
                if not CalculationService.validate_percentage_range(jar_new_percent):
                    validation_errors.append(ServiceError(
                        code="INVALID_PERCENTAGE",
                        message=f"New percentage for '{jar_name[i]}' is invalid",
                        field=f"jar_{i+1}_percent"
                    ))
                    continue
                update_data.percent = jar_new_percent
                update_data.amount = await CalculationService.calculate_amount_from_percent(db, user_id, jar_new_percent)
                total_percent_change += (jar_new_percent - jar_to_update.percent)
                changes.append("allocation")

            if changes:
                updates_to_perform.append((current_jar_name_clean, update_data, changes))

        if validation_errors:
            return JarOperationResult(
                status="error",
                message="Validation failed for jar updates",
                errors=validation_errors
            )

        if total_percent_change > 1.0:
            return JarOperationResult.error(
                f"Cannot update jars - percentage increase of {CalculationService.format_percentage(total_percent_change)} exceeds 100%",
                code="ALLOCATION_EXCEEDED"
            )

        # --- PASS 2: EXECUTION ---
        final_updated_names = []
        update_summaries = []
        
        for original_name, update_data, changes in updates_to_perform:
            updated_jar = await db_utils.update_jar_in_db(db, user_id, original_name, update_data.model_dump(exclude_unset=True))
            final_updated_names.append(updated_jar.name)
            update_summaries.append(f"'{original_name}': {', '.join(changes)}")

        # --- REBALANCING ---
        rebalance_msg = ""
        if total_percent_change != 0:
            rebalance_msg = await JarManagementService._rebalance_after_update(db, user_id, final_updated_names)

        if len(update_summaries) == 1:
            return JarOperationResult.jar_updated(
                jar_name=final_updated_names[0],
                changes=updates_to_perform[0][2],
                rebalance_info=rebalance_msg if rebalance_msg else None
            )
        else:
            return JarOperationResult.success(
                message=f"Successfully updated {len(update_summaries)} jars: {'; '.join(update_summaries)}",
                data={"updated_jars": final_updated_names, "changes": update_summaries},
                warnings=[rebalance_msg] if rebalance_msg else None
            )

    @staticmethod
    async def delete_jar(db: AsyncIOMotorDatabase, user_id: str, jar_name: List[str], reason: str) -> JarOperationResult:
        """Delete multiple jars with atomic validation and rebalancing."""
        if not jar_name:
            return JarOperationResult.error("Jar name list cannot be empty", code="MISSING_REQUIRED_FIELDS")

        # --- PASS 1: VALIDATION ---
        jars_to_delete = []
        total_deleted_percent = 0.0
        validation_errors = []
        
        for i, name in enumerate(jar_name):
            clean_name = name.strip().lower().replace(' ', '_')
            jar = await db_utils.get_jar_by_name(db, user_id, clean_name)
            if not jar:
                validation_errors.append(ServiceError(
                    code="NOT_FOUND",
                    message=f"Jar '{name}' not found",
                    field=f"jar_{i+1}_name"
                ))
                continue
            jars_to_delete.append(jar)
            total_deleted_percent += jar.percent

        if validation_errors:
            return JarOperationResult(
                status="error",
                message="Validation failed for jar deletion",
                errors=validation_errors
            )

        # --- PASS 2: EXECUTION ---
        deleted_jars_summary = []
        for jar in jars_to_delete:
            await db_utils.delete_jar_by_name(db, user_id, jar.name)
            deleted_jars_summary.append(f"'{jar.name}' ({CalculationService.format_percentage(jar.percent)})")

        # --- REBALANCING ---
        rebalance_msg = await JarManagementService._redistribute_deleted_percentage(db, user_id, total_deleted_percent)

        if len(jar_name) == 1:
            return JarOperationResult.jar_deleted(
                jar_name=jars_to_delete[0].name,
                reason=reason,
                rebalance_info=rebalance_msg if rebalance_msg else None
            )
        else:
            return JarOperationResult.success(
                message=f"Successfully deleted {len(jar_name)} jars: {', '.join(deleted_jars_summary)}. Reason: {reason}",
                data={"deleted_jars": [jar.name for jar in jars_to_delete], "reason": reason},
                warnings=[rebalance_msg] if rebalance_msg else None
            )

    @staticmethod
    async def list_jars(db: AsyncIOMotorDatabase, user_id: str) -> str:
        """List all jars with current status."""
        jars = await db_utils.get_all_jars_for_user(db, user_id)
        
        if not jars:
            return "📊 No budget jars found. Create your first jar to start budgeting!"
        
        jars.sort(key=lambda j: j.percent, reverse=True)
        jar_list = []
        total_percent = 0.0
        total_amount = 0.0
        
        for jar in jars:
            status = f"{CalculationService.format_percentage(jar.percent)} ({CalculationService.format_currency(jar.amount)})"
            if jar.current_amount > 0:
                status += f" | Current: {CalculationService.format_currency(jar.current_amount)} ({CalculationService.format_percentage(jar.current_percent)})"
            
            jar_list.append(f"🏺 {jar.name}: {status} - {jar.description}")
            total_percent += jar.percent
            total_amount += jar.amount
        
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        summary = f"📊 Total allocation: {CalculationService.format_percentage(total_percent)} ({CalculationService.format_currency(total_amount)}) from {CalculationService.format_currency(total_income)} income"
        
        return "\n".join(jar_list) + f"\n\n{summary}"

    @staticmethod
    async def find_jar_by_keywords(db: AsyncIOMotorDatabase, user_id: str, keywords: str) -> Optional[JarInDB]:
        """Find jar by matching keywords in name or description."""
        keywords_lower = keywords.lower()
        
        jars = await db_utils.get_all_jars_for_user(db, user_id)
        
        # First try exact name match
        for jar in jars:
            if keywords_lower == jar.name.lower():
                return jar
        
        # Then try partial match in name or description
        for jar in jars:
            if keywords_lower in jar.name.lower() or keywords_lower in jar.description.lower():
                return jar
        
        return None

    @staticmethod
    async def validate_jar_name(db: AsyncIOMotorDatabase, user_id: str, name: str, exclude_current: Optional[str] = None) -> Tuple[bool, str]:
        """Validate jar name for uniqueness and format."""
        if not name or not name.strip():
            return False, "Jar name cannot be empty"
        
        clean_name = name.strip().lower().replace(' ', '_')
        if len(clean_name) < 2:
            return False, "Jar name too short (minimum 2 characters)"
        
        jars = await db_utils.get_all_jars_for_user(db, user_id)
        existing_names = [j.name.lower() for j in jars if j.name.lower() != (exclude_current.lower() if exclude_current else "")]
        
        if clean_name in existing_names:
            return False, f"Jar name '{clean_name}' already exists"
        
        return True, ""

    @staticmethod
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """Request clarification from user."""
        response = f"❓ {question}"
        if suggestions:
            response += f"\n💡 Suggestions: {suggestions}"
        return response
    
    @staticmethod
    async def validate_jar_data(db: AsyncIOMotorDatabase, user_id: str, jar_data: JarCreate) -> Tuple[bool, List[str]]:
        """Validate jar data for consistency."""
        errors = []
        
        if not jar_data.name or not jar_data.name.strip():
            errors.append("Jar name cannot be empty")
        
        if not CalculationService.validate_percentage_range(jar_data.percent):
            errors.append(f"Percent {jar_data.percent} must be between 0.0 and 1.0")
        
        if not CalculationService.validate_percentage_range(jar_data.current_percent):
            errors.append(f"Current percent {jar_data.current_percent} must be between 0.0 and 1.0")
        
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        expected_amount = jar_data.percent * total_income
        if abs(jar_data.amount - expected_amount) > 0.01:
            errors.append(f"Amount {jar_data.amount} doesn't match percent calculation {expected_amount}")
        
        return len(errors) == 0, errors

    @staticmethod
    async def _rebalance_after_creation(db: AsyncIOMotorDatabase, user_id: str, new_jar_names: List[str]) -> str:
        """Scale down other jars with rounding correction."""
        all_jars = await db_utils.get_all_jars_for_user(db, user_id)
        new_jars = [j for j in all_jars if j.name in new_jar_names]
        other_jars = [j for j in all_jars if j.name not in new_jar_names]
        
        if not other_jars:
            return "📊 No other jars to rebalance."
        
        total_new_percent = sum(j.percent for j in new_jars)
        other_jars_total_percent = sum(j.percent for j in other_jars)
        
        if other_jars_total_percent == 0:
            return "📊 No rebalancing needed as other jars have 0% allocation."
        
        remaining_space = 1.0 - total_new_percent
        if remaining_space < 0:
            remaining_space = 0
        
        scale_factor = remaining_space / other_jars_total_percent
        
        rebalanced_list = []
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        for jar in other_jars:
            old_percent = jar.percent
            new_percent = max(0.0, jar.percent * scale_factor)
            update_data = JarUpdate(
                percent=new_percent,
                amount=new_percent * total_income
            )
            updated_jar = await db_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))
            rebalanced_list.append(f"{updated_jar.name}: {CalculationService.format_percentage(old_percent)} → {CalculationService.format_percentage(updated_jar.percent)}")

        # Rounding correction
        current_total = await CalculationService.calculate_jar_total_allocation(db, user_id)
        if abs(current_total - 1.0) > 0.001 and other_jars:
            largest_jar = max(other_jars, key=lambda j: j.percent)
            new_percent = largest_jar.percent + (1.0 - current_total)
            update_data = JarUpdate(
                percent=new_percent,
                amount=new_percent * total_income
            )
            await db_utils.update_jar_in_db(db, user_id, largest_jar.name, update_data.model_dump(exclude_unset=True))

        return f"📊 Rebalanced other jars: {', '.join(rebalanced_list)}"

    @staticmethod
    async def _rebalance_after_update(db: AsyncIOMotorDatabase, user_id: str, updated_jars_names: List[str]) -> str:
        """Scale non-updated jars with rounding correction."""
        all_jars = await db_utils.get_all_jars_for_user(db, user_id)
        updated_jars = [j for j in all_jars if j.name in updated_jars_names]
        other_jars = [j for j in all_jars if j.name not in updated_jars_names]
        
        if not other_jars:
            return "📊 No other jars to rebalance."
            
        updated_total_percent = sum(j.percent for j in updated_jars)
        other_jars_total_percent = sum(j.percent for j in other_jars)
        
        remaining_space = 1.0 - updated_total_percent
        if remaining_space < 0:
            remaining_space = 0
        
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        if other_jars_total_percent > 0.001:
            scale_factor = remaining_space / other_jars_total_percent
            for jar in other_jars:
                new_percent = jar.percent * scale_factor
                update_data = JarUpdate(
                    percent=max(0.0, new_percent),
                    amount=new_percent * total_income
                )
                await db_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))
        elif len(other_jars) > 0:
            equal_share = remaining_space / len(other_jars)
            for jar in other_jars:
                update_data = JarUpdate(
                    percent=equal_share,
                    amount=equal_share * total_income
                )
                await db_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))
        
        # Reload other_jars for updated values
        other_jars = [j for j in await db_utils.get_all_jars_for_user(db, user_id) if j.name not in updated_jars_names]
        rebalanced_list = [f"{jar.name} → {CalculationService.format_percentage(jar.percent)}" for jar in other_jars]

        # Rounding correction
        current_total = await CalculationService.calculate_jar_total_allocation(db, user_id)
        if abs(current_total - 1.0) > 0.001 and other_jars:
            largest_jar = max(other_jars, key=lambda j: j.percent)
            new_percent = largest_jar.percent + (1.0 - current_total)
            update_data = JarUpdate(
                percent=new_percent,
                amount=new_percent * total_income
            )
            await db_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))

        
        return f"📊 Rebalanced other jars: {', '.join(rebalanced_list)}"

    @staticmethod
    async def _redistribute_deleted_percentage(db: AsyncIOMotorDatabase, user_id: str, deleted_percent: float) -> str:
        """Scale up remaining jars with rounding correction."""
        remaining_jars = await db_utils.get_all_jars_for_user(db, user_id)
        
        if not remaining_jars:
            return "📊 No jars remaining."
        
        remaining_total_percent = sum(j.percent for j in remaining_jars)
        
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        if remaining_total_percent < 0.001:
            if len(remaining_jars) > 0:
                equal_share = (deleted_percent + remaining_total_percent) / len(remaining_jars)
                for jar in remaining_jars:
                    update_data = JarUpdate(
                        percent=equal_share,
                        amount=equal_share * total_income
                    )
                    await db_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))

        else:
            for jar in remaining_jars:
                proportion = jar.percent / remaining_total_percent
                new_percent = jar.percent + (deleted_percent * proportion)
                update_data = JarUpdate(
                    percent=new_percent,
                    amount=new_percent * total_income
                )
                await db_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))

        # Reload remaining_jars
        remaining_jars = await db_utils.get_all_jars_for_user(db, user_id)
        rebalanced_list = [f"{jar.name} → {CalculationService.format_percentage(jar.percent)}" for jar in remaining_jars]

        # Rounding correction
        current_total = await CalculationService.calculate_jar_total_allocation(db, user_id)
        if abs(current_total - 1.0) > 0.001 and remaining_jars:
            largest_jar = max(remaining_jars, key=lambda j: j.percent)
            new_percent = largest_jar.percent + (1.0 - current_total)
            update_data = JarUpdate(
                percent=new_percent,
                amount=new_percent * total_income
            )
            await db_utils.update_jar_in_db(db, user_id, largest_jar.name, update_data.model_dump(exclude_unset=True))

        return f"📊 Redistributed freed percentage: {', '.join(rebalanced_list)}"