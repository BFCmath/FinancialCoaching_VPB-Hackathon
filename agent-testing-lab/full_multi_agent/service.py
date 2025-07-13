"""
Unified Service Layer for VPBank AI Financial Coach
==================================================

Provides all services that tools need across the 7-agent system.
Based on analysis of all tools.py files in plan_service.md.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, asdict
import json
import re

# Import from our unified database and utils
from database import (
    # Data structures
    Jar, Transaction, RecurringFee, BudgetPlan, ConversationTurn,
    # Storage
    JARS_STORAGE, TRANSACTIONS_STORAGE, FEES_STORAGE, 
    BUDGET_PLANS_STORAGE, CONVERSATION_HISTORY,
    # Configuration
    TOTAL_INCOME, APP_INFO
)

from utils import (
    # Database operations
    save_jar, get_jar, get_all_jars, delete_jar,
    save_transaction, get_all_transactions, get_transactions_by_jar,
    save_recurring_fee, get_recurring_fee, get_all_recurring_fees, delete_recurring_fee,
    save_budget_plan, get_budget_plan, get_all_budget_plans, delete_budget_plan,
    add_conversation_turn, get_conversation_history,
    # Calculations
    calculate_percent_from_amount, calculate_amount_from_percent,
    format_currency, format_percentage, validate_percentage_range, validate_positive_amount,
    # Utilities  
    calculate_next_fee_occurrence, get_database_stats
)

# =============================================================================
# 1. JAR MANAGEMENT SERVICE - REFACTORED WITH CORRECT REBALANCING
# =============================================================================

class JarManagementService:
    """
    Unified jar management service supporting multi-jar operations.
    This version implements the correct, atomic, two-pass rebalancing logic
    from the experimental lab documentation.
    """
    
    @staticmethod
    def create_jar(name: List[str], description: List[str], 
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

        # --- PASS 1: VALIDATION ---
        validated_jars_data = []
        total_new_percent = 0.0
        current_jars = get_all_jars()
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
                jar_percent = calculate_percent_from_amount(jar_amount)

            if not validate_percentage_range(jar_percent):
                return f"❌ Jar {i+1} '{jar_name}': Percentage {format_percentage(jar_percent)} is invalid."

            clean_name = jar_name.strip().lower().replace(' ', '_')
            is_valid, error_msg = JarManagementService.validate_jar_name(clean_name)
            if not is_valid:
                return f"❌ Jar {i+1} '{jar_name}': {error_msg}"

            validated_jars_data.append({
                'name': clean_name, 'description': jar_desc,
                'percent': jar_percent, 'amount': calculate_amount_from_percent(jar_percent)
            })
            total_new_percent += jar_percent

        # Corrected Validation: Only fail if the new jars THEMSELVES exceed 100%.
        # Rebalancing will handle making space if the existing jars are at 100%.
        if total_new_percent > 1.001: # Allow for small float inaccuracies
             return (f"❌ Cannot create jars. New jars alone total {format_percentage(total_new_percent)}, "
                     f"which exceeds the 100% maximum.")

        # --- PASS 2: EXECUTION ---
        created_jars_info = []
        newly_created_names = []
        for data in validated_jars_data:
            new_jar = Jar(
                name=data['name'], description=data['description'], percent=data['percent'],
                current_percent=0.0, current_amount=0.0, amount=data['amount']
            )
            save_jar(new_jar)
            newly_created_names.append(new_jar.name)
            created_jars_info.append(f"'{new_jar.name}': {format_percentage(new_jar.percent)} (${new_jar.amount:.2f})")

        # --- REBALANCING ---
        rebalance_msg = JarManagementService._rebalance_after_creation(newly_created_names)

        # Final Response Formatting to match tools.py
        if len(name) == 1:
            base_message = f"Created jar: {created_jars_info[0]}"
        else:
            created_summary = ", ".join(created_jars_info)
            base_message = f"Created {len(name)} jars: {created_summary}"
        
        if confidence >= 90:
            return f"✅ {base_message} ({confidence}% confident)\n{rebalance_msg}"
        elif confidence >= 70:
            return f"⚠️ {base_message} ({confidence}% confident - moderate certainty)\n{rebalance_msg}"
        else:
            return f"❓ {base_message} ({confidence}% confident - please verify)\n{rebalance_msg}"
    
    @staticmethod
    def update_jar(jar_name: List[str], new_name: List[Optional[str]] = None, 
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

        # --- PASS 1: VALIDATION ---
        updates_to_perform = []
        total_percent_change = 0.0

        for i in range(num_jars):
            current_jar_name_clean = jar_name[i].strip().lower().replace(' ', '_')
            jar_to_update = get_jar(current_jar_name_clean)
            if not jar_to_update:
                return f"❌ Jar '{jar_name[i]}' not found."

            update_data = {'original_jar': jar_to_update, 'changes': {}}

            if new_name[i]:
                new_clean_name = new_name[i].strip().lower().replace(' ', '_')
                is_valid, error_msg = JarManagementService.validate_jar_name(new_clean_name, exclude_current=current_jar_name_clean)
                if not is_valid:
                    return f"❌ New name for '{jar_name[i]}': {error_msg}"
                update_data['changes']['name'] = new_clean_name

            if new_description[i]:
                update_data['changes']['description'] = new_description[i]

            jar_new_percent = new_percent[i]
            if new_amount[i] is not None:
                jar_new_percent = calculate_percent_from_amount(new_amount[i])

            if jar_new_percent is not None:
                if not validate_percentage_range(jar_new_percent):
                    return f"❌ New percentage for '{jar_name[i]}' is invalid."
                update_data['changes']['percent'] = jar_new_percent
                total_percent_change += (jar_new_percent - jar_to_update.percent)
            
            updates_to_perform.append(update_data)

        # Reverted Validation Logic to match tools.py
        if total_percent_change > 1.0:
            return f"❌ Cannot update jars - percentage increase of {format_percentage(total_percent_change)} exceeds 100%"

        # --- PASS 2: EXECUTION ---
        final_updated_names = []
        update_summaries = []
        
        for update in updates_to_perform:
            jar = update['original_jar']
            original_name = jar.name
            changes = []
            
            if 'name' in update['changes']:
                old_name_key = jar.name
                jar.name = update['changes']['name']
                changes.append(f"name: {old_name_key} → {jar.name}")
                delete_jar(old_name_key) # Must remove old key
                save_jar(jar)

            if 'description' in update['changes']:
                jar.description = update['changes']['description']
                changes.append("description updated")

            if 'percent' in update['changes']:
                old_percent = jar.percent
                jar.percent = update['changes']['percent']
                jar.amount = calculate_amount_from_percent(jar.percent)
                changes.append(f"allocation: {format_percentage(old_percent)} → {format_percentage(jar.percent)}")
            
            save_jar(jar)
            final_updated_names.append(jar.name)
            update_summaries.append(f"'{original_name}': {', '.join(changes) if changes else 'no changes'}")

        # --- REBALANCING ---
        rebalance_msg = ""
        if total_percent_change != 0:
            rebalance_msg = JarManagementService._rebalance_after_update(final_updated_names)

        # Final Response Formatting to match tools.py
        if len(jar_name) == 1:
            base_message = f"Updated jar: {update_summaries[0]}"
        else:
            updated_summary = "; ".join(update_summaries)
            base_message = f"Updated {len(update_summaries)} jars: {updated_summary}"

        if rebalance_msg:
            base_message += f"\n{rebalance_msg}"
            
        if confidence >= 90:
            return f"✅ {base_message} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ {base_message} ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ {base_message} ({confidence}% confident - please verify)"

    
    @staticmethod
    def delete_jar(jar_name: List[str], reason: str) -> str:
        """Delete multiple jars with atomic validation and rebalancing."""
        if not jar_name:
            return "❌ Jar name list cannot be empty."

        # --- PASS 1: VALIDATION ---
        jars_to_delete = []
        total_deleted_percent = 0.0
        for name in jar_name:
            jar = get_jar(name.lower().replace(' ', '_'))
            if not jar:
                return f"❌ Jar '{name}' not found."
            jars_to_delete.append(jar)
            total_deleted_percent += jar.percent

        # --- PASS 2: EXECUTION ---
        deleted_jars_summary = []
        for jar in jars_to_delete:
            delete_jar(jar.name)
            deleted_jars_summary.append(f"'{jar.name}' ({format_percentage(jar.percent)})")

        # --- REBALANCING ---
        rebalance_msg = JarManagementService._redistribute_deleted_percentage(total_deleted_percent)

        summary = ", ".join(deleted_jars_summary)
        return f"✅ Deleted {len(jar_name)} jars: {summary}. Reason: {reason}. {rebalance_msg}"
    
    @staticmethod
    def list_jars() -> str:
        """List all jars with current status"""
        
        jars = get_all_jars()
        
        if not jars:
            return "📊 No budget jars found. Create your first jar to start budgeting!"
        
        jars.sort(key=lambda j: j.percent, reverse=True)
        jar_list = []
        total_percent = 0.0
        total_amount = 0.0
        
        for jar in jars:
            status = f"{format_percentage(jar.percent)} (${jar.amount:.2f})"
            if jar.current_amount > 0:
                status += f" | Current: ${jar.current_amount:.2f} ({format_percentage(jar.current_percent)})"
            
            jar_list.append(f"🏺 {jar.name}: {status} - {jar.description}")
            total_percent += jar.percent
            total_amount += jar.amount
        
        summary = f"📊 Total allocation: {format_percentage(total_percent)} (${total_amount:.2f}) from ${TOTAL_INCOME:.2f} income"
        
        return "\n".join(jar_list) + f"\n\n{summary}"

    @staticmethod  
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """Request clarification from user"""
        response = f"❓ {question}"
        if suggestions:
            response += f"\n💡 Suggestions: {suggestions}"
        return response
    
    @staticmethod
    def validate_jar_name(name: str, exclude_current: str = None) -> Tuple[bool, str]:
        """Validate jar name for uniqueness and format"""
        
        if not name or not name.strip():
            return False, "Jar name cannot be empty"
        
        clean_name = name.strip().lower().replace(' ', '_')
        if len(clean_name) < 2:
            return False, "Jar name too short (minimum 2 characters)"
        
        existing_names = [j.name.lower() for j in get_all_jars() if j.name.lower() != (exclude_current.lower() if exclude_current else None)]
        
        if clean_name in existing_names:
            return False, f"Jar name '{clean_name}' already exists"
        
        return True, ""

    @staticmethod
    def _rebalance_after_creation(new_jar_names: List[str]) -> str:
        """Correct Rebalancing Logic from lab: Scale down other jars with rounding correction."""
        all_jars = get_all_jars()
        new_jars = [j for j in all_jars if j.name in new_jar_names]
        other_jars = [j for j in all_jars if j.name not in new_jar_names]
        
        if not other_jars:
            return "📊 No other jars to rebalance."

        total_new_percent = sum(j.percent for j in new_jars)
        other_jars_total_percent = sum(j.percent for j in other_jars)
        
        if other_jars_total_percent == 0:
            return "📊 No rebalancing needed as other jars have 0% allocation."

        remaining_space = 1.0 - total_new_percent
        
        # Handle case where new jars take all the space
        if remaining_space < 0:
            remaining_space = 0

        scale_factor = remaining_space / other_jars_total_percent
        
        rebalanced_list = []
        for jar in other_jars:
            old_percent = jar.percent
            new_percent = jar.percent * scale_factor
            jar.percent = max(0.0, new_percent) # Safeguard: Ensure not negative
            jar.amount = calculate_amount_from_percent(jar.percent)
            save_jar(jar)
            rebalanced_list.append(f"{jar.name}: {format_percentage(old_percent)} → {format_percentage(jar.percent)}")

        # Crucial Rounding Correction from lab
        current_total = sum(j.percent for j in get_all_jars())
        if abs(current_total - 1.0) > 0.001 and other_jars:
            largest_jar = max(other_jars, key=lambda j: j.percent)
            largest_jar.percent += (1.0 - current_total)
            save_jar(largest_jar)
        
        return f"📊 Rebalanced other jars: {', '.join(rebalanced_list)}"

    @staticmethod
    def _rebalance_after_update(updated_jars_names: List[str]) -> str:
        """Correct Rebalancing Logic from lab: Scale non-updated jars with rounding correction."""
        all_jars = get_all_jars()
        updated_jars = [j for j in all_jars if j.name in updated_jars_names]
        other_jars = [j for j in all_jars if j.name not in updated_jars_names]
        
        if not other_jars:
            return "📊 No other jars to rebalance."
            
        updated_total_percent = sum(j.percent for j in updated_jars)
        other_jars_total_percent = sum(j.percent for j in other_jars)
        
        remaining_space = 1.0 - updated_total_percent
        if remaining_space < 0:
            remaining_space = 0
        
        if other_jars_total_percent > 0.001:
            scale_factor = remaining_space / other_jars_total_percent
            for jar in other_jars:
                jar.percent *= scale_factor
        elif len(other_jars) > 0:
            equal_share = remaining_space / len(other_jars)
            for jar in other_jars:
                jar.percent = equal_share
        
        rebalanced_list = []
        for jar in other_jars:
            jar.percent = max(0.0, jar.percent) # Safeguard
            jar.amount = calculate_amount_from_percent(jar.percent)
            save_jar(jar)
            rebalanced_list.append(f"{jar.name} → {format_percentage(jar.percent)}")

        # Crucial Rounding Correction from lab
        current_total = sum(j.percent for j in get_all_jars())
        if abs(current_total - 1.0) > 0.001 and other_jars:
            largest_jar = max(other_jars, key=lambda j: j.percent)
            largest_jar.percent += (1.0 - current_total)
            save_jar(largest_jar)
        
        return f"📊 Rebalanced other jars: {', '.join(rebalanced_list)}"

    @staticmethod
    def _redistribute_deleted_percentage(deleted_percent: float) -> str:
        """Correct Rebalancing Logic from lab: Scale up remaining jars with rounding correction."""
        remaining_jars = get_all_jars()
        
        if not remaining_jars:
            return "📊 No jars remaining."
        
        remaining_total_percent = sum(j.percent for j in remaining_jars)
        
        if remaining_total_percent < 0.001:
            # Distribute the freed percentage equally
            if len(remaining_jars) > 0:
                equal_share = (deleted_percent + remaining_total_percent) / len(remaining_jars)
                for jar in remaining_jars:
                    jar.percent = equal_share
        else:
            # Scale up proportionally
            for jar in remaining_jars:
                proportion = jar.percent / remaining_total_percent
                jar.percent += (deleted_percent * proportion)
        
        rebalanced_list = []
        for jar in remaining_jars:
            jar.amount = calculate_amount_from_percent(jar.percent)
            save_jar(jar)
            rebalanced_list.append(f"{jar.name} → {format_percentage(jar.percent)}")

        # Crucial Rounding Correction from lab
        current_total = sum(j.percent for j in get_all_jars())
        if abs(current_total - 1.0) > 0.001 and remaining_jars:
            largest_jar = max(remaining_jars, key=lambda j: j.percent)
            largest_jar.percent += (1.0 - current_total)
            save_jar(largest_jar)
        
        return f"📊 Redistributed freed percentage: {', '.join(rebalanced_list)}"

# =============================================================================
# 2. TRANSACTION SERVICE
# =============================================================================

class TransactionService:
    """
    Unified transaction service combining functionality from classifier_test and transaction_fetcher
    """
    
    @staticmethod
    def add_money_to_jar_with_confidence(amount: float, jar_name: str, confidence: int) -> str:
        """Add money to jar with confidence-based formatting"""
        
        # Find jar
        jar = get_jar(jar_name.lower().replace(' ', '_'))
        if not jar:
            return f"❌ Error: Jar '{jar_name}' not found"
        
        # Create transaction
        transaction = Transaction(
            amount=amount,
            jar=jar.name,
            description=f"Transaction classified to {jar.name}",
            date=datetime.now().strftime("%Y-%m-%d"),
            time=datetime.now().strftime("%H:%M"),
            source="manual_input"
        )
        
        save_transaction(transaction)
        
        # Update jar current amount
        jar.current_amount += amount
        jar.current_percent = calculate_percent_from_amount(jar.current_amount)
        save_jar(jar)
        
        # Format output based on confidence level
        if confidence >= 90:
            return f"✅ Added {format_currency(amount)} to {jar.name} jar ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ Added {format_currency(amount)} to {jar.name} jar ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ Added {format_currency(amount)} to {jar.name} jar ({confidence}% confident - please verify)"
    
    @staticmethod
    def report_no_suitable_jar(description: str, suggestion: str) -> str:
        """Report when no existing jar matches the transaction"""
        return f"❌ Cannot classify '{description}'. {suggestion}"
    
    @staticmethod
    def request_more_info(question: str) -> str:
        """Ask user for more information when input is ambiguous"""
        return f"❓ {question}"

# =============================================================================
# 3. TRANSACTION QUERY SERVICE
# =============================================================================

class TransactionQueryService:
    """
    Advanced transaction querying service from transaction_fetcher/tools.py
    """
    
    @staticmethod
    def get_jar_transactions(jar_name: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """Get transactions filtered by jar"""
        
        if jar_name:
            # Get transactions for specific jar
            jar = get_jar(jar_name.lower().replace(' ', '_'))
            if not jar:
                return {
                    "data": [],
                    "description": f"jar '{jar_name}' not found"
                }
            
            transactions = get_transactions_by_jar(jar.name)
        else:
            # Get all transactions
            transactions = get_all_transactions()
        
        # Convert to dictionaries and limit results
        transaction_dicts = [t.to_dict() for t in transactions[:limit]]
        
        auto_description = description or (
            f"{jar_name} transactions" if jar_name else "all transactions"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    def get_time_period_transactions(jar_name: str = None, start_date: str = "last_month", 
                                    end_date: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """Get transactions within date range"""
        
        # Parse dates
        start_date_parsed = TransactionQueryService.parse_flexible_date(start_date)
        if end_date:
            end_date_parsed = TransactionQueryService.parse_flexible_date(end_date)
        else:
            end_date_parsed = datetime.now().date()
        
        # Get base transactions
        if jar_name:
            jar = get_jar(jar_name.lower().replace(' ', '_'))
            if not jar:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            transactions = get_transactions_by_jar(jar.name)
        else:
            transactions = get_all_transactions()
        
        # Filter by date range
        filtered_transactions = []
        for t in transactions:
            try:
                t_date = datetime.strptime(t.date, "%Y-%m-%d").date()
                if start_date_parsed <= t_date <= end_date_parsed:
                    filtered_transactions.append(t)
            except ValueError:
                continue  # Skip invalid dates
        
        # Limit results
        limited_transactions = filtered_transactions[:limit]
        transaction_dicts = [t.to_dict() for t in limited_transactions]
        
        auto_description = description or (
            f"{jar_name} transactions from {start_date} to {end_date}" if jar_name 
            else f"all transactions from {start_date} to {end_date}"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    def get_amount_range_transactions(jar_name: str = None, min_amount: float = None, 
                                     max_amount: float = None, limit: int = 50, 
                                     description: str = "") -> Dict[str, Any]:
        """Get transactions within amount range"""
        
        # Get base transactions
        if jar_name:
            jar = get_jar(jar_name.lower().replace(' ', '_'))
            if not jar:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            transactions = get_transactions_by_jar(jar.name)
        else:
            transactions = get_all_transactions()
        
        # Filter by amount range
        filtered_transactions = []
        for t in transactions:
            amount_match = True
            if min_amount is not None and t.amount < min_amount:
                amount_match = False
            if max_amount is not None and t.amount > max_amount:
                amount_match = False
            
            if amount_match:
                filtered_transactions.append(t)
        
        # Limit results
        limited_transactions = filtered_transactions[:limit]
        transaction_dicts = [t.to_dict() for t in limited_transactions]
        
        range_desc = f"${min_amount or 0:.2f} - ${max_amount or 'unlimited'}"
        auto_description = description or (
            f"{jar_name} transactions in range {range_desc}" if jar_name 
            else f"all transactions in range {range_desc}"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    def get_hour_range_transactions(jar_name: str = None, start_hour: int = 6, 
                                   end_hour: int = 22, limit: int = 50, 
                                   description: str = "") -> Dict[str, Any]:
        """Get transactions within hour range"""
        
        # Get base transactions
        if jar_name:
            jar = get_jar(jar_name.lower().replace(' ', '_'))
            if not jar:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            transactions = get_transactions_by_jar(jar.name)
        else:
            transactions = get_all_transactions()
        
        # Filter by hour range
        filtered_transactions = []
        for t in transactions:
            if TransactionQueryService.time_in_range(t.time, start_hour, end_hour):
                filtered_transactions.append(t)
        
        # Limit results
        limited_transactions = filtered_transactions[:limit]
        transaction_dicts = [t.to_dict() for t in limited_transactions]
        
        def format_hour(hour):
            return f"{hour:02d}:00"
        
        time_range = f"{format_hour(start_hour)} - {format_hour(end_hour)}"
        auto_description = description or (
            f"{jar_name} transactions between {time_range}" if jar_name 
            else f"all transactions between {time_range}"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    def get_source_transactions(jar_name: str = None, source_type: str = "vpbank_api", 
                               limit: int = 50, description: str = "") -> Dict[str, Any]:
        """Get transactions by source type"""
        
        # Get base transactions
        if jar_name:
            jar = get_jar(jar_name.lower().replace(' ', '_'))
            if not jar:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            transactions = get_transactions_by_jar(jar.name)
        else:
            transactions = get_all_transactions()
        
        # Filter by source
        filtered_transactions = [t for t in transactions if t.source == source_type]
        
        # Limit results
        limited_transactions = filtered_transactions[:limit]
        transaction_dicts = [t.to_dict() for t in limited_transactions]
        
        auto_description = description or (
            f"{jar_name} transactions from {source_type}" if jar_name 
            else f"all transactions from {source_type}"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    def parse_flexible_date(date_str: str) -> date:
        """Parse various date formats including relative dates"""
        
        if not date_str:
            return datetime.now().date()
        
        date_str = date_str.lower().strip()
        today = datetime.now().date()
        
        relative_dates = {
            "today": today,
            "yesterday": today - timedelta(days=1),
            "last_week": today - timedelta(weeks=1),
            "last_month": today - timedelta(days=30),
            "this_month": today.replace(day=1),
            "last_year": today - timedelta(days=365),
            "this_week": today - timedelta(days=today.weekday())
        }
        
        if date_str in relative_dates:
            return relative_dates[date_str]
        
        # Try parsing as YYYY-MM-DD
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
        
        # Default to today
        return today
    
    @staticmethod
    def time_in_range(transaction_time: str, start_hour: int, end_hour: int) -> bool:
        """Check if transaction time falls within hour range"""
        
        try:
            hour = int(transaction_time.split(":")[0])
            
            if start_hour <= end_hour:  # Normal range (e.g., 9-17)
                return start_hour <= hour <= end_hour
            else:  # Overnight range (e.g., 22-6)
                return hour >= start_hour or hour <= end_hour
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def get_complex_transaction(
        jar_name: str = None,
        start_date: str = None,
        end_date: str = None,
        min_amount: float = None,
        max_amount: float = None,
        start_hour: int = None,
        end_hour: int = None,
        source_type: str = None,
        limit: int = 50,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        **COMPLEX MULTI-DIMENSIONAL TRANSACTION FILTERING**
        
        Handle complex queries that require multiple filters simultaneously.
        Supports Vietnamese queries like "cho tôi xem thông tin ăn trưa (11h sáng ->2h chiều) dưới 20 đô"
        """
        
        filtered = []
        all_transactions = get_all_transactions()
        
        # Apply all filters step by step
        for transaction in all_transactions:
            # 1. Check jar filter
            if jar_name is not None:
                jar = get_jar(jar_name.lower().replace(' ', '_'))
                if not jar or transaction.jar_name != jar.name:
                    continue
            
            # 2. Check date range filter
            if start_date is not None:
                parsed_start = TransactionQueryService.parse_flexible_date(start_date)
                parsed_end = TransactionQueryService.parse_flexible_date(end_date) if end_date else datetime.now().date()
                
                if not (parsed_start <= transaction.date <= parsed_end):
                    continue
            
            # 3. Check amount range filter
            amount = transaction.amount
            if min_amount is not None and amount < min_amount:
                continue
            if max_amount is not None and amount > max_amount:
                continue
            
            # 4. Check hour range filter
            if start_hour is not None and end_hour is not None:
                if not TransactionQueryService.time_in_range(transaction.time, start_hour, end_hour):
                    continue
            elif start_hour is not None:
                # Only start hour specified
                try:
                    hour = int(transaction.time.split(":")[0])
                    if hour < start_hour:
                        continue
                except (ValueError, IndexError):
                    continue
            elif end_hour is not None:
                # Only end hour specified
                try:
                    hour = int(transaction.time.split(":")[0])
                    if hour > end_hour:
                        continue
                except (ValueError, IndexError):
                    continue
            
            # 5. Check source filter
            if source_type is not None and transaction.source != source_type:
                continue
            
            # If we get here, transaction passed all filters
            filtered.append({
                "amount": transaction.amount,
                "jar": transaction.jar_name,
                "description": transaction.description,
                "date": transaction.date.strftime("%Y-%m-%d"),
                "time": transaction.time,
                "source": transaction.source
            })
        
        # Sort by date (newest first) and limit
        filtered.sort(key=lambda t: t["date"], reverse=True)
        limited_filtered = filtered[:limit]
        
        # Use provided description or generate comprehensive one
        if description.strip():
            final_description = description.strip()
        else:
            # Auto-generate comprehensive description based on active filters
            filter_parts = []
            
            if jar_name:
                filter_parts.append(f"{jar_name} transactions")
            else:
                filter_parts.append("all transactions")
            
            if start_date or end_date:
                if start_date and end_date:
                    filter_parts.append(f"from {start_date} to {end_date}")
                elif start_date:
                    filter_parts.append(f"from {start_date}")
                elif end_date:
                    filter_parts.append(f"until {end_date}")
            
            if min_amount is not None and max_amount is not None:
                filter_parts.append(f"between ${min_amount}-${max_amount}")
            elif min_amount is not None:
                filter_parts.append(f"over ${min_amount}")
            elif max_amount is not None:
                filter_parts.append(f"under ${max_amount}")
            
            if start_hour is not None and end_hour is not None:
                filter_parts.append(f"between {start_hour}:00-{end_hour}:00")
            elif start_hour is not None:
                filter_parts.append(f"after {start_hour}:00")
            elif end_hour is not None:
                filter_parts.append(f"before {end_hour}:00")
            
            if source_type:
                source_names = {
                    "vpbank_api": "bank data",
                    "manual_input": "manual entries",
                    "text_input": "voice input",
                    "image_input": "scanned receipts"
                }
                filter_parts.append(f"from {source_names.get(source_type, source_type)}")
            
            final_description = "Complex filtering: " + " ".join(filter_parts)
            
            if limit < len(filtered):
                final_description += f" (showing {limit} of {len(filtered)} matches)"
        
        return {
            "data": limited_filtered,
            "description": final_description
        }

# =============================================================================
# 4. FEE MANAGEMENT SERVICE
# =============================================================================

class FeeManagementService:
    """
    Unified fee management service from fee_test/tools.py
    """
    
    @staticmethod
    def create_recurring_fee(name: str, amount: float, description: str, pattern_type: str,
                            pattern_details: Optional[List[int]], target_jar: str, 
                            confidence: int = 85) -> str:
        """Create recurring fee with scheduling"""
        
        # Validate fee name
        is_valid, error_msg = FeeManagementService.validate_fee_name(name)
        if not is_valid:
            return f"❌ {error_msg}"
        
        # Validate target jar
        jar = get_jar(target_jar.lower().replace(' ', '_'))
        if not jar:
            return f"❌ Target jar '{target_jar}' not found"
        
        # Validate amount
        if not validate_positive_amount(amount):
            return f"❌ Amount must be positive, got ${amount:.2f}"
        
        # Validate pattern type
        if pattern_type not in ["daily", "weekly", "monthly"]:
            return f"❌ Pattern type must be 'daily', 'weekly', or 'monthly', got '{pattern_type}'"
        
        # Calculate next occurrence
        next_occurrence = calculate_next_fee_occurrence(pattern_type, pattern_details)
        
        # Create fee
        fee = RecurringFee(
            name=name,
            amount=amount,
            description=description,
            target_jar=jar.name,
            pattern_type=pattern_type,
            pattern_details=pattern_details,
            created_date=datetime.now(),
            next_occurrence=next_occurrence,
            is_active=True
        )
        
        save_recurring_fee(fee)
        
        # Format pattern description
        pattern_desc = FeeManagementService._format_pattern_description(pattern_type, pattern_details)
        
        # Format response based on confidence
        if confidence >= 90:
            return f"✅ Created recurring fee '{name}': {format_currency(amount)} {pattern_desc} → {jar.name} jar. Next: {next_occurrence.strftime('%Y-%m-%d')}"
        elif confidence >= 70:
            return f"⚠️ Created recurring fee '{name}': {format_currency(amount)} {pattern_desc} → {jar.name} jar ({confidence}% confident). Next: {next_occurrence.strftime('%Y-%m-%d')}"
        else:
            return f"❓ Created recurring fee '{name}': {format_currency(amount)} {pattern_desc} → {jar.name} jar ({confidence}% confident - please verify). Next: {next_occurrence.strftime('%Y-%m-%d')}"
    
    @staticmethod
    def adjust_recurring_fee(fee_name: str, new_amount: Optional[float] = None,
                            new_description: Optional[str] = None, new_pattern_type: Optional[str] = None,
                            new_pattern_details: Optional[List[int]] = None, new_target_jar: Optional[str] = None,
                            disable: bool = False, confidence: int = 85) -> str:
        """Update recurring fee"""
        
        fee = get_recurring_fee(fee_name)
        if not fee:
            return f"❌ Fee '{fee_name}' not found"
        
        changes = []
        
        # Update amount
        if new_amount is not None:
            if not validate_positive_amount(new_amount):
                return f"❌ Amount must be positive, got ${new_amount:.2f}"
            old_amount = fee.amount
            fee.amount = new_amount
            changes.append(f"amount: {format_currency(old_amount)} → {format_currency(new_amount)}")
        
        # Update description
        if new_description is not None:
            fee.description = new_description
            changes.append("description updated")
        
        # Update pattern
        if new_pattern_type is not None:
            if new_pattern_type not in ["daily", "weekly", "monthly"]:
                return f"❌ Pattern type must be 'daily', 'weekly', or 'monthly'"
            fee.pattern_type = new_pattern_type
            changes.append(f"pattern: {new_pattern_type}")
        
        if new_pattern_details is not None:
            fee.pattern_details = new_pattern_details
            changes.append("pattern details updated")
        
        # Update target jar
        if new_target_jar is not None:
            jar = get_jar(new_target_jar.lower().replace(' ', '_'))
            if not jar:
                return f"❌ Target jar '{new_target_jar}' not found"
            old_jar = fee.target_jar
            fee.target_jar = jar.name
            changes.append(f"target: {old_jar} → {jar.name}")
        
        # Disable/enable
        if disable:
            fee.is_active = False
            changes.append("disabled")
        
        # Recalculate next occurrence if pattern changed
        if new_pattern_type is not None or new_pattern_details is not None:
            fee.next_occurrence = calculate_next_fee_occurrence(fee.pattern_type, fee.pattern_details)
            changes.append(f"next occurrence: {fee.next_occurrence.strftime('%Y-%m-%d')}")
        
        save_recurring_fee(fee)
        
        changes_str = ", ".join(changes) if changes else "no changes"
        
        # Format response based on confidence
        if confidence >= 90:
            return f"✅ Updated fee '{fee_name}': {changes_str}"
        elif confidence >= 70:
            return f"⚠️ Updated fee '{fee_name}': {changes_str} ({confidence}% confident)"
        else:
            return f"❓ Updated fee '{fee_name}': {changes_str} ({confidence}% confident - please verify)"
    
    @staticmethod
    def delete_recurring_fee(fee_name: str, reason: str) -> str:
        """Delete recurring fee"""
        
        fee = get_recurring_fee(fee_name)
        if not fee:
            return f"❌ Fee '{fee_name}' not found"
        
        delete_recurring_fee(fee_name)
        
        return f"✅ Deleted recurring fee '{fee_name}'. Reason: {reason}"
    
    @staticmethod
    def list_recurring_fees(active_only: bool = True, target_jar: Optional[str] = None) -> str:
        """List recurring fees with optional filtering"""
        
        fees = get_all_recurring_fees()
        
        # Filter by active status
        if active_only:
            fees = [f for f in fees if f.is_active]
        
        # Filter by target jar
        if target_jar:
            jar = get_jar(target_jar.lower().replace(' ', '_'))
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
            if fee.target_jar not in by_jar:
                by_jar[fee.target_jar] = []
            by_jar[fee.target_jar].append(fee)
            
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
                summary += f"  • {fee.name}: {fee.description} - {format_currency(fee.amount)} {pattern_desc}"
                summary += f" | Next: {fee.next_occurrence.strftime('%Y-%m-%d')}\n"
        
        summary += f"\n💰 Estimated monthly total: {format_currency(total_monthly)}"
        
        return summary
    
    @staticmethod
    def validate_fee_name(name: str) -> Tuple[bool, str]:
        """Validate fee name for uniqueness and format"""
        
        if not name or not name.strip():
            return False, "Fee name cannot be empty"
        
        clean_name = name.strip()
        if len(clean_name) < 3:
            return False, "Fee name too short (minimum 3 characters)"
        
        existing_names = [fee.name.lower() for fee in get_all_recurring_fees()]
        if clean_name.lower() in existing_names:
            return False, f"Fee name '{clean_name}' already exists"
        
        return True, ""
    
    @staticmethod
    def _format_pattern_description(pattern_type: str, pattern_details: Optional[List[int]]) -> str:
        """Format pattern for human-readable description"""
        
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

# =============================================================================
# 5. PLAN MANAGEMENT SERVICE
# =============================================================================

class PlanManagementService:
    """
    Unified plan management service from plan_test/tools.py
    """
    
    @staticmethod
    def create_plan(name: str, description: str, status: str = "active", 
                   jar_propose_adjust_details: str = None) -> Dict[str, Any]:
        """Create new budget plan with jar recommendations"""
        
        if get_budget_plan(name):
            return {"data": {}, "description": f"plan {name} already exists"}
        
        plan = BudgetPlan(
            name=name,
            detail_description=description,
            day_created=datetime.now().strftime("%Y-%m-%d"),
            status=status,
            jar_recommendations=jar_propose_adjust_details
        )
        
        save_budget_plan(plan)
        
        # Build response
        response_data = plan.to_dict()
        description_parts = [f"created plan {name} with status {status}"]
        
        if jar_propose_adjust_details:
            description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
        
        return {
            "data": response_data,
            "description": " | ".join(description_parts)
        }
    
    @staticmethod
    def adjust_plan(name: str, description: str = None, status: str = None, 
                   jar_propose_adjust_details: str = None) -> Dict[str, Any]:
        """Modify existing budget plan"""
        
        plan = get_budget_plan(name)
        if not plan:
            return {"data": {}, "description": f"plan {name} not found"}
        
        changes = []
        
        # Update description
        if description is not None:
            old_desc = plan.detail_description
            plan.detail_description = description
            changes.append(f"description updated")
        
        # Update status
        if status is not None:
            old_status = plan.status
            plan.status = status
            changes.append(f"status: {old_status} → {status}")
        
        # Update jar recommendations
        if jar_propose_adjust_details is not None:
            plan.jar_recommendations = jar_propose_adjust_details
            changes.append("jar recommendations updated")
        
        # Save updated plan
        updated_plan = BudgetPlan(
            name=plan.name,
            detail_description=plan.detail_description,
            day_created=plan.day_created,
            status=plan.status,
            jar_recommendations=plan.jar_recommendations
        )
        save_budget_plan(updated_plan)
        
        # Build response
        response_data = updated_plan.to_dict()
        description_parts = [f"updated plan {name}: {', '.join(changes) if changes else 'no changes made'}"]
        
        if jar_propose_adjust_details:
            description_parts.append(f"jar recommendations: {jar_propose_adjust_details}")
        
        return {
            "data": response_data,
            "description": " | ".join(description_parts)
        }
    
    @staticmethod
    def get_plan(status: str = "active", description: str = "") -> Dict[str, Any]:
        """Retrieve budget plans by status"""
        
        all_plans = get_all_budget_plans()
        
        if status == "all":
            plans = all_plans
        else:
            plans = [p for p in all_plans if p.status == status]
        
        # Convert to dictionaries
        plan_dicts = [p.to_dict() for p in plans]
        
        return {
            "data": plan_dicts,
            "description": description or f"retrieved {len(plan_dicts)} {status} plans"
        }
    
    @staticmethod
    def delete_plan(name: str, reason: str = "") -> Dict[str, Any]:
        """Delete budget plan"""
        
        plan = get_budget_plan(name)
        if not plan:
            return {"data": {}, "description": f"plan {name} not found"}
        
        delete_budget_plan(name)
        
        return {
            "data": {"deleted": True},
            "description": f"deleted plan {name}. Reason: {reason}"
        }

# =============================================================================
# 6. KNOWLEDGE SERVICE
# =============================================================================

class KnowledgeService:
    """
    Knowledge and search service from knowledge_test/tools.py
    """
    
    @staticmethod
    def get_application_information(description: str = "") -> Dict[str, Any]:
        """Get app documentation"""
        
        # Parse APP_INFO JSON
        try:
            app_info = json.loads(APP_INFO)
        except json.JSONDecodeError:
            app_info = {"error": "Could not parse app information"}
        
        return {
            "data": {
                "complete_app_info": app_info,
                "source": "app_documentation"
            },
            "description": description or "complete app information and features"
        }
    
    @staticmethod
    def respond(answer: str, description: str = "") -> Dict[str, Any]:
        """Provide final response (for ReAct completion)"""
        
        return {
            "data": {
                "final_answer": answer,
                "response_type": "complete",
                "source": "knowledge"
            },
            "description": description or "final response to user question"
        }

# =============================================================================
# 7. CONFIDENCE SERVICE
# =============================================================================

class ConfidenceService:
    """
    Confidence handling service used across multiple agents
    """
    
    @staticmethod
    def format_confidence_response(result: str, confidence: int) -> str:
        """Format response based on confidence level"""
        
        if confidence >= 90:
            return f"✅ {result} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ {result} ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ {result} ({confidence}% confident - please verify)"
    
    @staticmethod
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """Request clarification from user"""
        
        base_msg = f"❓ {question}"
        if suggestions:
            base_msg += f" {suggestions}"
        
        return base_msg
    
    @staticmethod
    def determine_confidence_level(confidence_score: int) -> str:
        """Convert confidence score to level description"""
        
        if confidence_score >= 90:
            return "high"
        elif confidence_score >= 70:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def should_ask_for_confirmation(confidence: int) -> bool:
        """Determine if confirmation is needed based on confidence"""
        
        return confidence < 70

# =============================================================================
# 8. AGENT COMMUNICATION SERVICE
# =============================================================================

class AgentCommunicationService:
    """
    Cross-agent communication service for plan_test integration
    """
    
    @staticmethod
    def call_transaction_fetcher(user_query: str, description: str = "") -> Dict[str, Any]:
        """Call transaction fetcher service"""
        
        # Use our TransactionQueryService to handle the query
        # For now, default to getting all transactions matching the query context
        
        return TransactionQueryService.get_jar_transactions(
            jar_name=None,  # Could parse jar from query
            limit=50,
            description=description or f"transaction query: {user_query}"
        )
    
    @staticmethod
    def call_jar_agent(jar_name: str = None, description: str = "") -> Dict[str, Any]:
        """Get jar information"""
        
        if jar_name:
            jar = get_jar(jar_name.lower().replace(' ', '_'))
            if not jar:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            
            jar_data = [jar.to_dict()]
            description_text = f"jar {jar_name} information"
        else:
            jars = get_all_jars()
            jar_data = [jar.to_dict() for jar in jars]
            description_text = "all jars information"
        
        return {
            "data": jar_data,
            "description": description or description_text
        }
    
    @staticmethod
    def format_cross_agent_request(target_agent: str, request: Dict) -> Dict:
        """Format request for another agent"""
        
        return {
            "target_agent": target_agent,
            "request": request,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def handle_cross_agent_response(response: Dict) -> Dict:
        """Handle response from another agent"""
        
        return {
            "processed": True,
            "data": response.get("data", {}),
            "description": response.get("description", ""),
            "processed_at": datetime.now().isoformat()
        }

# =============================================================================
# 9. UNIFIED SERVICE MANAGER
# =============================================================================

class ServiceManager:
    """
    Unified manager providing access to all services
    """
    
    def __init__(self):
        self.jar_service = JarManagementService()
        self.transaction_service = TransactionService()
        self.query_service = TransactionQueryService()
        self.fee_service = FeeManagementService()
        self.plan_service = PlanManagementService()
        self.knowledge_service = KnowledgeService()
        self.confidence_service = ConfidenceService()
        self.communication_service = AgentCommunicationService()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        
        return {
            "services_available": [
                "jar_service",
                "transaction_service", 
                "query_service",
                "fee_service",
                "plan_service",
                "knowledge_service",
                "confidence_service",
                "communication_service"
            ],
            "database_stats": get_database_stats(),
            "timestamp": datetime.now().isoformat()
        }

# =============================================================================
# 10. CONVENIENCE FUNCTIONS FOR TOOLS
# =============================================================================

# Global service manager instance
_service_manager = ServiceManager()

# Convenience functions that tools can import directly
def get_jar_service() -> JarManagementService:
    """Get jar management service"""
    return _service_manager.jar_service

def get_transaction_service() -> TransactionService:
    """Get transaction service"""
    return _service_manager.transaction_service

def get_query_service() -> TransactionQueryService:
    """Get transaction query service"""
    return _service_manager.query_service

def get_fee_service() -> FeeManagementService:
    """Get fee management service"""
    return _service_manager.fee_service

def get_plan_service() -> PlanManagementService:
    """Get plan management service"""
    return _service_manager.plan_service

def get_knowledge_service() -> KnowledgeService:
    """Get knowledge service"""
    return _service_manager.knowledge_service

def get_confidence_service() -> ConfidenceService:
    """Get confidence service"""
    return _service_manager.confidence_service

def get_communication_service() -> AgentCommunicationService:
    """Get agent communication service"""
    return _service_manager.communication_service

def get_service_manager() -> ServiceManager:
    """Get the global service manager"""
    return _service_manager
