"""
Jar Management Service - Refactored Implementation
================================================

This module implements jar management service using utility functions.
Refactored to use utility functions directly and remove confidence dependencies.
"""

from typing import List, Optional, Tuple, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import jar_utils, user_setting_utils
from backend.utils.general_utils import validate_percentage_range, calculate_amount_from_percent, format_percentage, format_currency, calculate_percent_from_amount
from backend.models.jar import JarInDB, JarCreate, JarUpdate

class JarManagementService:
    """
    Jar management service supporting multi-jar operations.
    Implements atomic, two-pass rebalancing logic.
    """

    @staticmethod
    async def _get_total_income(db: AsyncIOMotorDatabase, user_id: str) -> float:
        """Helper method to get user's total income with validation."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        return await user_setting_utils.get_user_total_income(db, user_id)

    @staticmethod
    async def _calculate_percent_from_amount(db: AsyncIOMotorDatabase, user_id: str, amount: float) -> float:
        """Convert dollar amount to percentage of total income."""
        if amount < 0:
            raise ValueError(f"Amount cannot be negative, got {amount}")
        total_income = await JarManagementService._get_total_income(db, user_id)
        return calculate_percent_from_amount(amount, total_income)
    
    @staticmethod
    async def _calculate_amount_from_percent(db: AsyncIOMotorDatabase, user_id: str, percent: float) -> float:
        """Convert percentage to dollar amount based on total income."""
        if not validate_percentage_range(percent):
            raise ValueError(f"Percentage must be between 0 and 1, got {percent}")
        total_income = await JarManagementService._get_total_income(db, user_id)
        return calculate_amount_from_percent(percent, total_income)
    
    @staticmethod
    async def _calculate_jar_total_allocation(db: AsyncIOMotorDatabase, user_id: str) -> float:
        """Calculate total percentage allocation across all jars."""
        await JarManagementService._get_total_income(db, user_id)  # Validation only
        jars = await jar_utils.get_all_jars_for_user(db, user_id)
        return sum(jar.percent for jar in jars)
    
    @staticmethod
    async def create_jar(db: AsyncIOMotorDatabase, user_id: str,
                         name: List[str], description: List[str], 
                         percent: List[Optional[float]] = None, 
                         amount: List[Optional[float]] = None) -> str:
        """Create one or multiple jars with atomic validation and rebalancing."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not name or not description:
            raise ValueError("Name and description lists cannot be empty")

        num_jars = len(name)
        if len(description) != num_jars:
            raise ValueError(f"Description list length ({len(description)}) must match name list length ({num_jars})")
        
        percent = percent if percent is not None else [None] * num_jars
        amount = amount if amount is not None else [None] * num_jars
        if len(percent) != num_jars or len(amount) != num_jars:
            raise ValueError("All parameter lists must have the same length")

        total_income = await JarManagementService._get_total_income(db, user_id)

        # --- PASS 1: VALIDATION ---
        validated_jars_data = []
        total_new_percent = 0.0

        for i in range(num_jars):
            jar_name, jar_desc, jar_percent, jar_amount = name[i], description[i], percent[i], amount[i]

            if not jar_name or not jar_desc:
                raise ValueError(f"Jar {i+1}: Name and description cannot be empty")

            if jar_percent is None and jar_amount is None:
                raise ValueError(f"Jar {i+1} '{jar_name}': Must provide either 'percent' or 'amount'")
                
            if jar_percent is not None and jar_amount is not None:
                raise ValueError(f"Jar {i+1} '{jar_name}': Cannot provide both 'percent' and 'amount'")

            if jar_amount is not None:
                jar_percent = await JarManagementService._calculate_percent_from_amount(db, user_id, jar_amount)

            if not validate_percentage_range(jar_percent):
                raise ValueError(f"Jar {i+1} '{jar_name}': Percentage {format_percentage(jar_percent)} is invalid")

            clean_name = jar_name.strip().lower().replace(' ', '_')
            await JarManagementService._validate_jar_name(db, user_id, clean_name)

            validated_jars_data.append({
                'name': clean_name, 'description': jar_desc,
                'percent': jar_percent, 
                'amount': await JarManagementService._calculate_amount_from_percent(db, user_id, jar_percent)
            })
            total_new_percent += jar_percent

        if total_new_percent > 1.001:
            raise ValueError(f"Cannot create jars. New jars alone total {format_percentage(total_new_percent)}, which exceeds the 100% maximum")

        # --- PASS 2: EXECUTION ---
        newly_created_names = []
        for data in validated_jars_data:
            # Create a simple dictionary with all required fields
            jar_dict_to_create = {
                "user_id": user_id,
                "name": data['name'],
                "description": data['description'],
                "percent": data['percent'],
                "amount": data['amount'],
                "current_percent": 0.0,
                "current_amount": 0.0
            }

            # Call the db_utils function with the correct 2 arguments
            created_jar = await jar_utils.create_jar_in_db(db, jar_dict_to_create)
            newly_created_names.append(created_jar.name)

        # --- REBALANCING ---
        rebalance_msg = await JarManagementService._rebalance_after_creation(db, user_id, newly_created_names)

        # VERIFICATION: Ensure newly created jars still have their intended percentages
        for i, created_name in enumerate(newly_created_names):
            created_jar = await jar_utils.get_jar_by_name(db, user_id, created_name)
            intended_percent = validated_jars_data[i]['percent']
            if abs(created_jar.percent - intended_percent) > 0.001:
                raise ValueError(f"Rebalancing error: Jar '{created_name}' percent changed from intended {format_percentage(intended_percent)} to {format_percentage(created_jar.percent)}")

        if len(name) == 1:
            allocation_str = f"{format_percentage(validated_jars_data[0]['percent'])} ({format_currency(validated_jars_data[0]['amount'])})"
            result = f"✅ Created jar '{newly_created_names[0]}' with allocation {allocation_str}"
            if rebalance_msg:
                result += f"\n{rebalance_msg}"
            return result
        else:
            result = f"✅ Created {len(name)} jars: {', '.join(newly_created_names)}"
            if rebalance_msg:
                result += f"\n{rebalance_msg}"
            return result

    @staticmethod
    async def _validate_jar_name(db: AsyncIOMotorDatabase, user_id: str, name: str, exclude_current: Optional[str] = None) -> None:
        """Validate jar name for uniqueness and format."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not name or not name.strip():
            raise ValueError("Jar name cannot be empty")
        
        clean_name = name.strip().lower().replace(' ', '_')
        if len(clean_name) < 2:
            raise ValueError("Jar name too short (minimum 2 characters)")
        
        jars = await jar_utils.get_all_jars_for_user(db, user_id)
        existing_names = [j.name.lower() for j in jars if j.name.lower() != (exclude_current.lower() if exclude_current else "")]
        
        if clean_name in existing_names:
            raise ValueError(f"Jar name '{clean_name}' already exists")

    @staticmethod
    async def update_jar(db: AsyncIOMotorDatabase, user_id: str,
                         jar_name: List[str], new_name: List[Optional[str]] = None, 
                         new_description: List[Optional[str]] = None,
                         new_percent: List[Optional[float]] = None, 
                         new_amount: List[Optional[float]] = None) -> str:
        """Update multiple existing jars with atomic validation and rebalancing."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not jar_name:
            raise ValueError("Jar name list cannot be empty")

        num_jars = len(jar_name)
        new_name = new_name if new_name is not None else [None] * num_jars
        new_description = new_description if new_description is not None else [None] * num_jars
        new_percent = new_percent if new_percent is not None else [None] * num_jars
        new_amount = new_amount if new_amount is not None else [None] * num_jars
        if not all(len(lst) == num_jars for lst in [new_name, new_description, new_percent, new_amount]):
            raise ValueError("All parameter lists must have the same length")

        # --- PASS 1: VALIDATION ---
        updates_to_perform = []
        total_percent_change = 0.0

        for i in range(num_jars):
            current_jar_name_clean = jar_name[i].strip().lower().replace(' ', '_')
            jar_to_update = await jar_utils.get_jar_by_name(db, user_id, current_jar_name_clean)
            if not jar_to_update:
                raise ValueError(f"Jar '{jar_name[i]}' not found")

            update_data = JarUpdate()
            changes = []

            if new_name[i]:
                new_clean_name = new_name[i].strip().lower().replace(' ', '_')
                await JarManagementService._validate_jar_name(db, user_id, new_clean_name, exclude_current=current_jar_name_clean)
                update_data.name = new_clean_name
                changes.append("name")

            if new_description[i]:
                update_data.description = new_description[i]
                changes.append("description")

            jar_new_percent = new_percent[i]
            if new_amount[i] is not None:
                jar_new_percent = await JarManagementService._calculate_percent_from_amount(db, user_id, new_amount[i])

            if jar_new_percent is not None:
                if not validate_percentage_range(jar_new_percent):
                    raise ValueError(f"New percentage for '{jar_name[i]}' is invalid")
                update_data.percent = jar_new_percent
                update_data.amount = await JarManagementService._calculate_amount_from_percent(db, user_id, jar_new_percent)
                total_percent_change += (jar_new_percent - jar_to_update.percent)
                changes.append("allocation")

            if changes:
                updates_to_perform.append((current_jar_name_clean, update_data, changes))

        if total_percent_change > 1.0:
            raise ValueError(f"Cannot update jars - percentage increase of {format_percentage(total_percent_change)} exceeds 100%")

        # --- PASS 2: EXECUTION ---
        final_updated_names = []
        update_summaries = []
        
        for original_name, update_data, changes in updates_to_perform:
            updated_jar = await jar_utils.update_jar_in_db(db, user_id, original_name, update_data.model_dump(exclude_unset=True))
            final_updated_names.append(updated_jar.name)
            update_summaries.append(f"'{original_name}': {', '.join(changes)}")

        # --- REBALANCING ---
        rebalance_msg = ""
        if total_percent_change != 0:
            rebalance_msg = await JarManagementService._rebalance_after_update(db, user_id, final_updated_names)
            
            # VERIFICATION: Ensure updated jars still have their intended percentages
            for original_name, update_data, changes in updates_to_perform:
                if "allocation" in changes:  # Only check if allocation was changed
                    current_jar = await jar_utils.get_jar_by_name(db, user_id, update_data.name if update_data.name else original_name)
                    intended_percent = update_data.percent
                    if abs(current_jar.percent - intended_percent) > 0.001:
                        raise ValueError(f"Rebalancing error: Updated jar '{current_jar.name}' percent changed from intended {format_percentage(intended_percent)} to {format_percentage(current_jar.percent)}")

        if len(update_summaries) == 1:
            result = f"✅ Updated jar '{final_updated_names[0]}' - changes: {', '.join(updates_to_perform[0][2])}"
            if rebalance_msg:
                result += f"\n{rebalance_msg}"
            return result
        else:
            result = f"✅ Successfully updated {len(update_summaries)} jars: {'; '.join(update_summaries)}"
            if rebalance_msg:
                result += f"\n{rebalance_msg}"
            return result

    @staticmethod
    async def delete_jar(db: AsyncIOMotorDatabase, user_id: str, jar_name: List[str], reason: str) -> str:
        """Delete multiple jars with atomic validation and rebalancing."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not jar_name:
            raise ValueError("Jar name list cannot be empty")

        # --- PASS 1: VALIDATION ---
        jars_to_delete = []
        total_deleted_percent = 0.0
        
        for i, name in enumerate(jar_name):
            clean_name = name.strip().lower().replace(' ', '_')
            jar = await jar_utils.get_jar_by_name(db, user_id, clean_name)
            if not jar:
                raise ValueError(f"Jar '{name}' not found")
            jars_to_delete.append(jar)
            total_deleted_percent += jar.percent

        # --- PASS 2: EXECUTION ---
        deleted_jars_summary = []
        for jar in jars_to_delete:
            await jar_utils.delete_jar_by_name(db, user_id, jar.name)
            deleted_jars_summary.append(f"'{jar.name}' ({format_percentage(jar.percent)})")

        # --- REBALANCING ---
        rebalance_msg = await JarManagementService._redistribute_deleted_percentage(db, user_id, total_deleted_percent)

        if len(jar_name) == 1:
            result = f"✅ Deleted jar '{jars_to_delete[0].name}'. Reason: {reason}"
            if rebalance_msg:
                result += f"\n{rebalance_msg}"
            return result
        else:
            result = f"✅ Successfully deleted {len(jar_name)} jars: {', '.join(deleted_jars_summary)}. Reason: {reason}"
            if rebalance_msg:
                result += f"\n{rebalance_msg}"
            return result
            
    @staticmethod
    async def get_jars(db: AsyncIOMotorDatabase, user_id: str, jar_name: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        """
        Gets a specific jar or all jars, returning a structured dictionary.

        Args:
            jar_name: The name of the jar. If None, all jars are returned.
            description: A user-provided description for the query's purpose.
        
        Returns:
            A dictionary containing the list of jars and a descriptive summary.
        """
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
            
        if jar_name:
            # Case 1: Fetch a single jar
            jar = await jar_utils.get_jar_by_name(db, user_id, jar_name)
            
            if jar:
                jar_list = [jar]
                auto_desc = f"Successfully retrieved details for the '{jar.name}' jar."
            else:
                jar_list = []
                auto_desc = f"Could not find a jar with the name '{jar_name}'."
        else:
            # Case 2: Fetch all jars
            jar_list = await jar_utils.get_all_jars_for_user(db, user_id)
            auto_desc = f"Successfully retrieved all {len(jar_list)} jars."

        # Convert the Pydantic objects to dictionaries for the final output
        jar_dicts = [j.model_dump() for j in jar_list]
        
        # Use the user's description if provided, otherwise use the auto-generated one
        final_desc = description or auto_desc
        
        return {"data": jar_dicts, "description": final_desc}

    @staticmethod
    async def list_jars(db: AsyncIOMotorDatabase, user_id: str) -> str:
        """List all jars with current status."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
            
        jars = await jar_utils.get_all_jars_for_user(db, user_id)
        
        if not jars:
            return "📊 No budget jars found. Create your first jar to start budgeting!"
        
        jars.sort(key=lambda j: j.percent, reverse=True)
        jar_list = []
        total_percent = 0.0
        total_amount = 0.0
        
        for jar in jars:
            status = f"{format_percentage(jar.percent)} ({format_currency(jar.amount)})"
            if jar.current_amount > 0:
                status += f" | Current: {format_currency(jar.current_amount)} ({format_percentage(jar.current_percent)})"
            
            jar_list.append(f"🏺 {jar.name}: {status} - {jar.description}")
            total_percent += jar.percent
            total_amount += jar.amount
        
        total_income = await JarManagementService._get_total_income(db, user_id)
        summary = f"📊 Total allocation: {format_percentage(total_percent)} ({format_currency(total_amount)}) from {format_currency(total_income)} income"
        
        return "\n".join(jar_list) + f"\n\n{summary}"

    @staticmethod
    async def find_jar_by_keywords(db: AsyncIOMotorDatabase, user_id: str, keywords: str) -> Optional[JarInDB]:
        """Find jar by matching keywords in name or description."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not keywords or not keywords.strip():
            raise ValueError("Keywords cannot be empty")
            
        keywords_lower = keywords.lower()
        
        jars = await jar_utils.get_all_jars_for_user(db, user_id)
        
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
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """Request clarification from user."""
        response = f"❓ {question}"
        if suggestions:
            response += f"\n💡 Suggestions: {suggestions}"
        return response
    
    @staticmethod
    async def validate_jar_data(db: AsyncIOMotorDatabase, user_id: str, jar_data: JarCreate) -> None:
        """Validate jar data for consistency."""
        if user_id is None or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if jar_data is None:
            raise ValueError("Jar data cannot be None")
            
        if not jar_data.name or not jar_data.name.strip():
            raise ValueError("Jar name cannot be empty")
        
        if not validate_percentage_range(jar_data.percent):
            raise ValueError(f"Percent {jar_data.percent} must be between 0.0 and 1.0")
        
        if not validate_percentage_range(jar_data.current_percent):
            raise ValueError(f"Current percent {jar_data.current_percent} must be between 0.0 and 1.0")
        
        total_income = await JarManagementService._get_total_income(db, user_id)
        expected_amount = jar_data.percent * total_income
        if abs(jar_data.amount - expected_amount) > 0.01:
            raise ValueError(f"Amount {jar_data.amount} doesn't match percent calculation {expected_amount}")

    @staticmethod
    async def _rebalance_after_creation(db: AsyncIOMotorDatabase, user_id: str, new_jar_names: List[str]) -> str:
        """Scale down other jars with rounding correction."""
        all_jars = await jar_utils.get_all_jars_for_user(db, user_id)
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
        total_income = await JarManagementService._get_total_income(db, user_id)
        for jar in other_jars:
            old_percent = jar.percent
            new_percent = max(0.0, jar.percent * scale_factor)
            update_data = JarUpdate(
                percent=new_percent,
                amount=new_percent * total_income
            )
            updated_jar = await jar_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))
            rebalanced_list.append(f"{updated_jar.name}: {format_percentage(old_percent)} → {format_percentage(updated_jar.percent)}")

        # Rounding correction - only adjust jars that are NOT the newly created ones
        current_total = await JarManagementService._calculate_jar_total_allocation(db, user_id)
        if abs(current_total - 1.0) > 0.001:
            # Get fresh data for OTHER jars only (exclude newly created jars)
            all_current_jars = await jar_utils.get_all_jars_for_user(db, user_id)
            other_current_jars = [j for j in all_current_jars if j.name not in new_jar_names]
            
            if other_current_jars:
                largest_other_jar = max(other_current_jars, key=lambda j: j.percent)
                new_percent = largest_other_jar.percent + (1.0 - current_total)
                update_data = JarUpdate(
                    percent=new_percent,
                    amount=new_percent * total_income
                )
                await jar_utils.update_jar_in_db(db, user_id, largest_other_jar.name, update_data.model_dump(exclude_unset=True))

        return f"📊 Rebalanced other jars: {', '.join(rebalanced_list)}"

    @staticmethod
    async def _rebalance_after_update(db: AsyncIOMotorDatabase, user_id: str, updated_jars_names: List[str]) -> str:
        """Scale non-updated jars with rounding correction."""
        all_jars = await jar_utils.get_all_jars_for_user(db, user_id)
        updated_jars = [j for j in all_jars if j.name in updated_jars_names]
        other_jars = [j for j in all_jars if j.name not in updated_jars_names]
        
        if not other_jars:
            return "📊 No other jars to rebalance."
            
        updated_total_percent = sum(j.percent for j in updated_jars)
        other_jars_total_percent = sum(j.percent for j in other_jars)
        
        remaining_space = 1.0 - updated_total_percent
        if remaining_space < 0:
            remaining_space = 0
        
        total_income = await JarManagementService._get_total_income(db, user_id)
        if other_jars_total_percent > 0.001:
            scale_factor = remaining_space / other_jars_total_percent
            for jar in other_jars:
                new_percent = jar.percent * scale_factor
                update_data = JarUpdate(
                    percent=max(0.0, new_percent),
                    amount=new_percent * total_income
                )
                await jar_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))
        elif len(other_jars) > 0:
            equal_share = remaining_space / len(other_jars)
            for jar in other_jars:
                update_data = JarUpdate(
                    percent=equal_share,
                    amount=equal_share * total_income
                )
                await jar_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))
        
        # Reload other_jars for updated values
        other_jars = [j for j in await jar_utils.get_all_jars_for_user(db, user_id) if j.name not in updated_jars_names]
        rebalanced_list = [f"{jar.name} → {format_percentage(jar.percent)}" for jar in other_jars]

        # Rounding correction - only adjust jars that are NOT the updated ones
        current_total = await JarManagementService._calculate_jar_total_allocation(db, user_id)
        if abs(current_total - 1.0) > 0.001:
            # Get fresh data for OTHER jars only (exclude updated jars)
            all_current_jars = await jar_utils.get_all_jars_for_user(db, user_id)
            other_current_jars = [j for j in all_current_jars if j.name not in updated_jars_names]
            
            if other_current_jars:
                largest_other_jar = max(other_current_jars, key=lambda j: j.percent)
                new_percent = largest_other_jar.percent + (1.0 - current_total)
                update_data = JarUpdate(
                    percent=new_percent,
                    amount=new_percent * total_income
                )
                await jar_utils.update_jar_in_db(db, user_id, largest_other_jar.name, update_data.model_dump(exclude_unset=True))

        
        return f"📊 Rebalanced other jars: {', '.join(rebalanced_list)}"

    @staticmethod
    async def _redistribute_deleted_percentage(db: AsyncIOMotorDatabase, user_id: str, deleted_percent: float) -> str:
        """Scale up remaining jars with rounding correction."""
        remaining_jars = await jar_utils.get_all_jars_for_user(db, user_id)
        
        if not remaining_jars:
            return "📊 No jars remaining."
        
        remaining_total_percent = sum(j.percent for j in remaining_jars)
        
        total_income = await JarManagementService._get_total_income(db, user_id)
        if remaining_total_percent < 0.001:
            # Equal distribution if all jars have 0% allocation
            if len(remaining_jars) > 0:
                equal_share = (deleted_percent + remaining_total_percent) / len(remaining_jars)
                for jar in remaining_jars:
                    update_data = JarUpdate(
                        percent=equal_share,
                        amount=equal_share * total_income
                    )
                    await jar_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))

        else:
            for jar in remaining_jars:
                proportion = jar.percent / remaining_total_percent
                new_percent = jar.percent + (deleted_percent * proportion)
                update_data = JarUpdate(
                    percent=new_percent,
                    amount=new_percent * total_income
                )
                await jar_utils.update_jar_in_db(db, user_id, jar.name, update_data.model_dump(exclude_unset=True))

        # Reload remaining_jars
        remaining_jars = await jar_utils.get_all_jars_for_user(db, user_id)
        rebalanced_list = [f"{jar.name} → {format_percentage(jar.percent)}" for jar in remaining_jars]

        # Rounding correction
        current_total = await JarManagementService._calculate_jar_total_allocation(db, user_id)
        if abs(current_total - 1.0) > 0.001 and remaining_jars:
            largest_jar = max(remaining_jars, key=lambda j: j.percent)
            new_percent = largest_jar.percent + (1.0 - current_total)
            update_data = JarUpdate(
                percent=new_percent,
                amount=new_percent * total_income
            )
            await jar_utils.update_jar_in_db(db, user_id, largest_jar.name, update_data.model_dump(exclude_unset=True))

        return f"📊 Redistributed freed percentage: {', '.join(rebalanced_list)}"