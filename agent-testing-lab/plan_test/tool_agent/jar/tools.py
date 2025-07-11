"""
Jar Manager Tools - LLM Tool Definitions
========================================

Tools that the LLM can call to manage budget jars.
"""

import json
from langchain_core.tools import tool
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json

# Global storage for jars (mock database) - keyed by name instead of ID
JARS_STORAGE: Dict[str, Dict] = {}

# Sample total income for percentage calculations and budget simulation
TOTAL_INCOME = 5000.0  # Monthly income example

# Default jar database - users can add more jars dynamically
DEFAULT_JARS_DATABASE = [
    # Essential 6-jar system from T. Harv Eker (official standard names)
    {
        "name": "necessities",
        "current_percent": 0.33,  # 33% of income currently allocated
        "percent": 0.55,          # 55% target allocation
        "description": "Essential living expenses like food, rent, utilities, and bills (55% of income)"
    },
    {
        "name": "long_term_savings",
        "current_percent": 0.04,  # 4% currently allocated
        "percent": 0.10,          # 10% target allocation
        "description": "For emergencies, big purchases, and major expenses (10% of income)"
    },
    {
        "name": "play",
        "current_percent": 0.06,  # 6% currently allocated
        "percent": 0.10,          # 10% target allocation
        "description": "Entertainment, fun activities, and treats for yourself (10% of income)"
    },
    {
        "name": "education",
        "current_percent": 0.03,  # 3% currently allocated
        "percent": 0.10,          # 10% target allocation
        "description": "Learning, courses, books, and personal development (10% of income)"
    },
    {
        "name": "financial_freedom",
        "current_percent": 0.015, # 1.5% currently allocated
        "percent": 0.10,          # 10% target allocation
        "description": "Investments for passive income and financial independence (10% of income)"
    },
    {
        "name": "give",
        "current_percent": 0.005, # 0.5% currently allocated
        "percent": 0.05,          # 5% target allocation
        "description": "Charity, donations, and helping others (5% of income)"
    }
]

def validate_jar_name(name: str, exclude_current: str = None) -> tuple[bool, str]:
    """Validate jar name for uniqueness and format"""
    if not name or not name.strip():
        return False, "Jar name cannot be empty"
    
    clean_name = name.strip().lower().replace(' ', '_')
    if len(clean_name) < 2:
        return False, "Jar name too short (minimum 2 characters)"
    
    # Check for duplicates (case insensitive)
    existing_names = [jar_name.lower() for jar_name in JARS_STORAGE.keys() 
                     if jar_name.lower() != (exclude_current.lower() if exclude_current else None)]
    
    if clean_name in existing_names:
        return False, f"Jar name '{clean_name}' already exists"
    
    return True, ""

def fetch_existing_jars() -> List[Dict]:
    """Get all current jars"""
    return list(JARS_STORAGE.values())

def get_jar_by_name(jar_name: str) -> Optional[Dict]:
    """Find jar by name (case insensitive) or description keywords"""
    jar_name_clean = jar_name.lower().replace(' ', '_')
    
    # First try exact name match
    if jar_name_clean in JARS_STORAGE:
        return JARS_STORAGE[jar_name_clean]
    
    # Then try partial name match
    for jar_key, jar in JARS_STORAGE.items():
        if jar_name_clean in jar_key.lower():
            return jar
    
    # Finally try description keywords
    for jar in JARS_STORAGE.values():
        if jar_name.lower() in jar["description"].lower():
            return jar
    
    return None

def save_jar(jar_dict: Dict):
    """Save jar to storage"""
    jar_name = jar_dict["name"].lower().replace(' ', '_')
    JARS_STORAGE[jar_name] = jar_dict

def delete_jar_from_storage(jar_name: str):
    """Permanently remove jar from storage"""
    jar_name_clean = jar_name.lower().replace(' ', '_')
    if jar_name_clean in JARS_STORAGE:
        del JARS_STORAGE[jar_name_clean]

def get_jar_names() -> List[str]:
    """Get list of jar names only"""
    return [jar["name"] for jar in JARS_STORAGE.values()]

def calculate_budget_from_percent(percent: float) -> float:
    """Calculate budget amount from percentage of total income"""
    return TOTAL_INCOME * percent

def calculate_current_amount_from_percent(current_percent: float) -> float:
    """Calculate current amount from percentage of total income"""
    return TOTAL_INCOME * current_percent

def calculate_percent_from_amount(amount: float) -> float:
    """Calculate percentage from dollar amount"""
    return amount / TOTAL_INCOME

def validate_percent_total(jars: List[Dict], exclude_names: List[str] = None) -> tuple[bool, float]:
    """Check if total percentage allocation doesn't exceed 1.0 (100%)"""
    exclude_names = exclude_names or []
    total = sum(jar['percent'] for jar in jars if jar['name'] not in exclude_names)
    return total <= 1.0, total

def format_percent_display(percent: float) -> str:
    """Format percentage for user display (0.55 -> 55%)"""
    return f"{percent * 100:.1f}%"

def rebalance_jar_percentages(new_jar_percent: float) -> str:
    """Rebalance all jar percentages to maintain 1.0 (100%) total after adding new jar"""
    
    # Get all jars except the newly created one (which already has its percent set)
    all_jars = list(JARS_STORAGE.values())
    
    if len(all_jars) <= 1:
        return f"📊 No rebalancing needed - only one jar exists."
    
    # Find the newly created jar (last one added)
    new_jar = all_jars[-1]  # Assume the last jar is the new one
    existing_jars = [jar for jar in all_jars if jar != new_jar]
    
    # Calculate current total of existing jars
    existing_total = sum(jar['percent'] for jar in existing_jars)
    remaining_percent = 1.0 - new_jar_percent
    
    if remaining_percent <= 0:
        return f"⚠️ WARNING: New jar takes {format_percent_display(new_jar_percent)} - no room for other jars!"
    
    if existing_total == 0:
        # All existing jars had 0%, distribute remaining evenly
        equal_share = remaining_percent / len(existing_jars)
        
        for jar in existing_jars:
            jar['percent'] = equal_share
        
        return f"📊 Redistributed {format_percent_display(remaining_percent)} equally among {len(existing_jars)} existing jars."
    else:
        # Normalize existing percentages to fit in remaining space
        scale_factor = remaining_percent / existing_total
        rebalanced_jars = []
        
        for jar in existing_jars:
            old_percent = jar['percent']
            new_percent = jar['percent'] * scale_factor
            jar['percent'] = max(0.01, new_percent)  # Ensure minimum 1%
            rebalanced_jars.append(f"{jar['name']}: {format_percent_display(old_percent)} → {format_percent_display(jar['percent'])}")
        
        # Verify total and adjust if needed due to rounding
        current_total = sum(jar['percent'] for jar in all_jars)
        if abs(current_total - 1.0) > 0.001:  # Allow small rounding errors
            # Adjust the largest jar to make total exactly 1.0
            largest_jar = max(existing_jars, key=lambda j: j['percent'])
            largest_jar['percent'] += (1.0 - current_total)
        
        changes_summary = ", ".join(rebalanced_jars)
        return f"📊 Rebalanced existing jars to fit remaining {format_percent_display(remaining_percent)}: {changes_summary}"

def rebalance_existing_jars_after_update(updated_jar_name: str, old_percent: float, new_percent: float) -> str:
    """Rebalance other jars after one jar's percentage was updated"""
    
    # Get all jars except the updated one
    all_jars = list(JARS_STORAGE.values())
    other_jars = [jar for jar in all_jars if jar['name'] != updated_jar_name]
    
    if not other_jars:
        return f"📊 No other jars to rebalance."
    
    # Calculate the percentage change
    percent_difference = new_percent - old_percent
    remaining_percent = 1.0 - new_percent
    
    if remaining_percent <= 0:
        return f"⚠️ WARNING: Updated jar takes {format_percent_display(new_percent)} - no room for other jars!"
    
    # Calculate current total of other jars
    other_total = sum(jar['percent'] for jar in other_jars)
    
    if other_total == 0:
        # Distribute remaining evenly among other jars
        equal_share = remaining_percent / len(other_jars)
        
        for jar in other_jars:
            jar['percent'] = equal_share
        
        return f"📊 Redistributed {format_percent_display(remaining_percent)} equally among {len(other_jars)} other jars."
    else:
        # Normalize other jars to fit in remaining space
        scale_factor = remaining_percent / other_total
        rebalanced_jars = []
        
        for jar in other_jars:
            old_jar_percent = jar['percent']
            new_jar_percent = jar['percent'] * scale_factor
            jar['percent'] = max(0.01, new_jar_percent)  # Ensure minimum 1%
            rebalanced_jars.append(f"{jar['name']}: {format_percent_display(old_jar_percent)} → {format_percent_display(jar['percent'])}")
        
        # Verify total and adjust if needed due to rounding
        current_total = sum(jar['percent'] for jar in all_jars)
        if abs(current_total - 1.0) > 0.001:  # Allow small rounding errors
            # Adjust the largest other jar to make total exactly 1.0
            largest_jar = max(other_jars, key=lambda j: j['percent'])
            largest_jar['percent'] += (1.0 - current_total)
        
        changes_summary = ", ".join(rebalanced_jars)
        return f"📊 Rebalanced other jars to fit remaining {format_percent_display(remaining_percent)}: {changes_summary}"

def redistribute_deleted_jar_percentage(deleted_percent: float) -> str:
    """Redistribute percentage from deleted jar to remaining jars proportionally"""
    
    # Get all remaining jars
    remaining_jars = list(JARS_STORAGE.values())
    
    if not remaining_jars:
        return f"📊 No jars remaining - deleted jar's {format_percent_display(deleted_percent)} is lost."
    
    # Calculate current total of remaining jars
    current_total = sum(jar['percent'] for jar in remaining_jars)
    
    if current_total == 0:
        # All remaining jars had 0%, distribute deleted percentage evenly
        equal_share = deleted_percent / len(remaining_jars)
        
        redistributed_jars = []
        for jar in remaining_jars:
            old_percent = jar['percent']
            jar['percent'] += equal_share
            redistributed_jars.append(f"{jar['name']}: {format_percent_display(old_percent)} → {format_percent_display(jar['percent'])}")
        
        changes_summary = ", ".join(redistributed_jars)
        return f"📊 Redistributed deleted jar's {format_percent_display(deleted_percent)} equally: {changes_summary}"
    else:
        # Redistribute proportionally based on existing percentages
        redistributed_jars = []
        
        for jar in remaining_jars:
            # Calculate proportional share of deleted percentage
            proportion = jar['percent'] / current_total
            additional_percent = deleted_percent * proportion
            
            old_percent = jar['percent']
            jar['percent'] += additional_percent
            redistributed_jars.append(f"{jar['name']}: {format_percent_display(old_percent)} → {format_percent_display(jar['percent'])}")
        
        # Verify total and adjust if needed due to rounding
        new_total = sum(jar['percent'] for jar in remaining_jars)
        if abs(new_total - 1.0) > 0.001:  # Allow small rounding errors
            # Adjust the largest jar to make total exactly 1.0
            largest_jar = max(remaining_jars, key=lambda j: j['percent'])
            largest_jar['percent'] += (1.0 - new_total)
        
        changes_summary = ", ".join(redistributed_jars)
        return f"📊 Redistributed deleted jar's {format_percent_display(deleted_percent)} proportionally: {changes_summary}"

def rebalance_multiple_new_jars(total_new_percent: float) -> str:
    """Rebalance existing jars after adding multiple new jars"""
    
    # Get all jars - find existing jars (exclude the newly created ones)
    all_jars = list(JARS_STORAGE.values())
    
    # Separate new jars (those with 0 current_percent) from existing jars
    new_jars = [jar for jar in all_jars if jar['current_percent'] == 0.0]
    existing_jars = [jar for jar in all_jars if jar['current_percent'] > 0.0 or jar not in new_jars]
    
    if not existing_jars:
        return f"📊 No existing jars to rebalance."
    
    # Calculate remaining percentage for existing jars
    remaining_percent = 1.0 - total_new_percent
    existing_total = sum(jar['percent'] for jar in existing_jars)
    
    if remaining_percent <= 0:
        return f"⚠️ WARNING: New jars take {format_percent_display(total_new_percent)} - no room for existing jars!"
    
    if existing_total == 0:
        return f"📊 No rebalancing needed - existing jars had 0% allocation."
    
    # Rebalance existing jars proportionally
    scale_factor = remaining_percent / existing_total
    rebalanced_jars = []
    
    for jar in existing_jars:
        old_percent = jar['percent']
        new_percent = jar['percent'] * scale_factor
        jar['percent'] = max(0.01, new_percent)  # Ensure minimum 1%
        rebalanced_jars.append(f"{jar['name']}: {format_percent_display(old_percent)} → {format_percent_display(jar['percent'])}")
    
    # Verify total and adjust if needed
    current_total = sum(jar['percent'] for jar in all_jars)
    if abs(current_total - 1.0) > 0.001:
        largest_existing_jar = max(existing_jars, key=lambda j: j['percent'])
        largest_existing_jar['percent'] += (1.0 - current_total)
    
    changes_summary = ", ".join(rebalanced_jars)
    return f"📊 Rebalanced existing jars to fit remaining {format_percent_display(remaining_percent)}: {changes_summary}"

def rebalance_after_multiple_updates(updated_jars: List[tuple], total_percent_change: float) -> str:
    """Rebalance other jars after multiple jar updates with percentage changes"""
    
    if total_percent_change == 0:
        return ""
    
    # Get all jars and identify which ones were updated
    all_jars = list(JARS_STORAGE.values())
    updated_jar_names = [jar_name for jar_name, old_p, new_p in updated_jars]
    other_jars = [jar for jar in all_jars if jar['name'] not in updated_jar_names]
    
    if not other_jars:
        return "📊 No other jars to rebalance."
    
    # Calculate remaining percentage for other jars
    updated_total = sum(jar['percent'] for jar in all_jars if jar['name'] in updated_jar_names)
    remaining_percent = 1.0 - updated_total
    
    if remaining_percent <= 0:
        return f"⚠️ WARNING: Updated jars now take {format_percent_display(updated_total)} - no room for other jars!"
    
    other_total = sum(jar['percent'] for jar in other_jars)
    
    if other_total == 0:
        # Other jars had 0%, distribute remaining evenly
        equal_share = remaining_percent / len(other_jars)
        rebalanced_jars = []
        
        for jar in other_jars:
            old_percent = jar['percent']
            jar['percent'] = equal_share
            rebalanced_jars.append(f"{jar['name']}: {format_percent_display(old_percent)} → {format_percent_display(jar['percent'])}")
        
        changes_summary = ", ".join(rebalanced_jars)
        return f"📊 Redistributed {format_percent_display(remaining_percent)} equally among other jars: {changes_summary}"
    else:
        # Scale other jars proportionally to fit remaining space
        scale_factor = remaining_percent / other_total
        rebalanced_jars = []
        
        for jar in other_jars:
            old_percent = jar['percent']
            new_percent = jar['percent'] * scale_factor
            jar['percent'] = max(0.01, new_percent)  # Ensure minimum 1%
            rebalanced_jars.append(f"{jar['name']}: {format_percent_display(old_percent)} → {format_percent_display(jar['percent'])}")
        
        # Verify total and adjust if needed
        current_total = sum(jar['percent'] for jar in all_jars)
        if abs(current_total - 1.0) > 0.001:
            largest_other_jar = max(other_jars, key=lambda j: j['percent'])
            largest_other_jar['percent'] += (1.0 - current_total)
        
        changes_summary = ", ".join(rebalanced_jars)
        return f"📊 Rebalanced other jars to fit remaining {format_percent_display(remaining_percent)}: {changes_summary}"

# === LLM TOOLS ===

@tool
def create_jar(
    name: List[str],
    description: List[str],
    percent: List[Optional[float]] = None,
    amount: List[Optional[float]] = None,
    confidence: int = 85
) -> str:
    """Create one or multiple budget jars with percentage or amount. Supports multi-jar creation.
    
    Args:
        name: List of unique jar names (e.g., ["vacation", "emergency"])
        description: List of human-readable descriptions for each jar
        percent: List of target percentage allocations (0.0-1.0, e.g., [0.15, 0.20])
        amount: List of target dollar amounts (will calculate percentages automatically)
        confidence: LLM confidence in operation understanding (0-100)
    
    Note: For each jar, provide either percent OR amount, not both.
    All lists must have the same length.
    """
    # Validate that we have at least one jar to create
    if not name or len(name) == 0:
        return f"❌ Must provide at least one jar name"
    
    # Validate list lengths match
    num_jars = len(name)
    if len(description) != num_jars:
        return f"❌ Description list length ({len(description)}) must match name list length ({num_jars})"
    
    # Initialize percent and amount lists if not provided
    if percent is None:
        percent = [None] * num_jars
    if amount is None:
        amount = [None] * num_jars
    
    # Validate percent and amount list lengths
    if len(percent) != num_jars:
        return f"❌ Percent list length ({len(percent)}) must match name list length ({num_jars})"
    if len(amount) != num_jars:
        return f"❌ Amount list length ({len(amount)}) must match name list length ({num_jars})"
    
    # Validate each jar specification
    validated_jars = []
    total_new_percent = 0.0
    
    for i in range(num_jars):
        jar_name = name[i]
        jar_desc = description[i]
        jar_percent = percent[i]
        jar_amount = amount[i]
        
        # Validate required fields
        if not jar_name or not jar_name.strip():
            return f"❌ Jar {i+1} name cannot be empty"
        if not jar_desc or not jar_desc.strip():
            return f"❌ Jar {i+1} description cannot be empty"
        
        # Validate percent/amount input for this jar
        if jar_percent is None and jar_amount is None:
            return f"❌ Jar {i+1} '{jar_name}' must have either 'percent' or 'amount'"
        if jar_percent is not None and jar_amount is not None:
            return f"❌ Jar {i+1} '{jar_name}' cannot have both 'percent' and 'amount'"
        
        # Calculate percentage from amount if provided
        if jar_amount is not None:
            if jar_amount <= 0:
                return f"❌ Amount for jar {i+1} '{jar_name}' must be positive, got ${jar_amount}"
            jar_percent = calculate_percent_from_amount(jar_amount)
        
        # Validate percent range
        if jar_percent <= 0 or jar_percent > 1.0:
            return f"❌ Percent for jar {i+1} '{jar_name}' must be between 0.01-1.0, got {jar_percent}"
        
        # Clean name for storage
        clean_name = jar_name.strip().lower().replace(' ', '_')
        
        # Validate jar name uniqueness
        is_valid, error_msg = validate_jar_name(clean_name)
        if not is_valid:
            return f"❌ Jar {i+1} '{jar_name}': {error_msg}"
        
        validated_jars.append({
            'name': clean_name,
            'description': jar_desc.strip(),
            'percent': jar_percent,
            'amount': jar_amount
        })
        total_new_percent += jar_percent
    
    # Check if new jars alone would exceed 100% (which would be impossible even with rebalancing)
    if total_new_percent > 1.0:
        return f"❌ Cannot create jars - new jars alone would use {format_percent_display(total_new_percent)} (maximum possible: 100.0%)"
    
    # Create all jars
    created_jars = []
    for jar_spec in validated_jars:
        jar_dict = {
            "name": jar_spec['name'],
            "current_percent": 0.0,  # Start with 0 balance
            "percent": jar_spec['percent'],
            "description": jar_spec['description']
        }
        save_jar(jar_dict)
        
        budget = calculate_budget_from_percent(jar_spec['percent'])
        created_jars.append(f"{jar_spec['name']} ({format_percent_display(jar_spec['percent'])}, ${budget:.2f})")
    
    # Rebalance existing jars to maintain 100% total
    if num_jars == 1:
        rebalance_message = rebalance_jar_percentages(new_jar_percent=validated_jars[0]['percent'])
    else:
        rebalance_message = rebalance_multiple_new_jars(total_new_percent)
    
    # Format response
    if num_jars == 1:
        base_message = f"Created jar: {created_jars[0]}"
    else:
        created_summary = ", ".join(created_jars)
        base_message = f"Created {num_jars} jars: {created_summary}"
    
    if confidence >= 90:
        return f"✅ {base_message} ({confidence}% confident)\n{rebalance_message}"
    elif confidence >= 70:
        return f"⚠️ {base_message} ({confidence}% confident - moderate certainty)\n{rebalance_message}"
    else:
        return f"❓ {base_message} ({confidence}% confident - please verify)\n{rebalance_message}"

@tool
def update_jar(
    jar_name: List[str],
    new_name: List[Optional[str]] = None,
    new_description: List[Optional[str]] = None,
    new_percent: List[Optional[float]] = None,
    new_amount: List[Optional[float]] = None,
    confidence: int = 85
) -> str:
    """Update one or multiple existing jars with new parameters and rebalance percentages if needed.
    
    Args:
        jar_name: List of jar names to update
        new_name: List of new jar names (optional for each)
        new_description: List of new descriptions (optional for each)
        new_percent: List of new percentage allocations (0.0-1.0, optional for each)
        new_amount: List of new dollar amounts (will calculate percentages, optional for each)
        confidence: LLM confidence (0-100)
    
    Note: All lists must have the same length as jar_name.
    For each jar, provide either new_percent OR new_amount, not both.
    """
    
    # Validate that we have at least one jar to update
    if not jar_name or len(jar_name) == 0:
        return f"❌ Must provide at least one jar name"
    
    num_jars = len(jar_name)
    
    # Initialize optional lists if not provided
    if new_name is None:
        new_name = [None] * num_jars
    if new_description is None:
        new_description = [None] * num_jars
    if new_percent is None:
        new_percent = [None] * num_jars
    if new_amount is None:
        new_amount = [None] * num_jars
    
    # Validate list lengths match
    if len(new_name) != num_jars:
        return f"❌ new_name list length ({len(new_name)}) must match jar_name list length ({num_jars})"
    if len(new_description) != num_jars:
        return f"❌ new_description list length ({len(new_description)}) must match jar_name list length ({num_jars})"
    if len(new_percent) != num_jars:
        return f"❌ new_percent list length ({len(new_percent)}) must match jar_name list length ({num_jars})"
    if len(new_amount) != num_jars:
        return f"❌ new_amount list length ({len(new_amount)}) must match jar_name list length ({num_jars})"
    
    # Find and validate all jars first
    jars_to_update = []
    total_percent_change = 0.0
    
    for i in range(num_jars):
        current_jar_name = jar_name[i]
        jar = get_jar_by_name(current_jar_name)
        if not jar:
            return f"❌ Jar {i+1} '{current_jar_name}' not found"
        
        # Validate percent/amount input for this jar
        jar_new_percent = new_percent[i]
        jar_new_amount = new_amount[i]
        
        if jar_new_percent is not None and jar_new_amount is not None:
            return f"❌ Jar {i+1} '{current_jar_name}' cannot have both new_percent and new_amount"
        
        # Calculate percentage from amount if provided
        if jar_new_amount is not None:
            if jar_new_amount <= 0:
                return f"❌ new_amount for jar {i+1} '{current_jar_name}' must be positive, got ${jar_new_amount}"
            jar_new_percent = calculate_percent_from_amount(jar_new_amount)
        
        # Validate percent range if provided
        if jar_new_percent is not None:
            if jar_new_percent <= 0 or jar_new_percent > 1.0:
                return f"❌ new_percent for jar {i+1} '{current_jar_name}' must be between 0.01-1.0, got {jar_new_percent}"
        
        # Validate new name if provided
        jar_new_name = new_name[i]
        if jar_new_name is not None:
            new_clean_name = jar_new_name.strip().lower().replace(' ', '_')
            is_valid, error_msg = validate_jar_name(new_clean_name, exclude_current=jar["name"])
            if not is_valid:
                return f"❌ Jar {i+1} '{current_jar_name}': {error_msg}"
        
        jars_to_update.append({
            'jar': jar,
            'original_name': current_jar_name,
            'new_name': jar_new_name,
            'new_description': new_description[i],
            'new_percent': jar_new_percent,
            'new_amount': jar_new_amount
        })
        
        # Track percent changes for rebalancing
        if jar_new_percent is not None:
            total_percent_change += (jar_new_percent - jar['percent'])
    
    # Only reject if the net increase alone would exceed 100% (impossible even with rebalancing)
    if total_percent_change > 1.0:
        return f"❌ Cannot update jars - percentage increase of {format_percent_display(total_percent_change)} exceeds 100%"
    
    # Apply all updates
    updated_jars = []
    jars_with_percent_changes = []
    
    for jar_update in jars_to_update:
        jar = jar_update['jar']
        changes = []
        
        # Update name
        if jar_update['new_name'] is not None:
            old_jar_key = jar["name"].lower().replace(' ', '_')
            new_clean_name = jar_update['new_name'].strip().lower().replace(' ', '_')
            
            jar["name"] = new_clean_name
            del JARS_STORAGE[old_jar_key]
            JARS_STORAGE[new_clean_name] = jar
            
            changes.append(f"name: '{jar_update['original_name']}' → '{new_clean_name}'")
        
        # Update description
        if jar_update['new_description'] is not None:
            jar["description"] = jar_update['new_description'].strip()
            changes.append("description updated")
        
        # Update percentage
        if jar_update['new_percent'] is not None:
            old_percent = jar["percent"]
            jar["percent"] = jar_update['new_percent']
            changes.append(f"percent: {format_percent_display(old_percent)} → {format_percent_display(jar['percent'])}")
            jars_with_percent_changes.append((jar['name'], old_percent, jar['percent']))
        
        if changes:
            change_summary = ", ".join(changes)
            updated_jars.append(f"{jar['name']}: {change_summary}")
    
    # Handle rebalancing if any percentages changed
    rebalance_message = ""
    if jars_with_percent_changes and total_percent_change != 0:
        rebalance_message = rebalance_after_multiple_updates(jars_with_percent_changes, total_percent_change)
    
    if not updated_jars:
        return f"ℹ️ No changes made to any jars"
    
    # Format response
    if num_jars == 1:
        base_message = f"Updated jar: {updated_jars[0]}"
    else:
        updated_summary = "; ".join(updated_jars)
        base_message = f"Updated {len(updated_jars)} jars: {updated_summary}"
    
    if rebalance_message:
        base_message += f"\n{rebalance_message}"
    
    if confidence >= 90:
        return f"✅ {base_message} ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ {base_message} ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ {base_message} ({confidence}% confident - please verify)"

@tool
def delete_jar(jar_name: List[str], reason: str) -> str:
    """Delete (remove) one or multiple jars permanently and redistribute their percentages to remaining jars.
    
    Args:
        jar_name: List of jar names to delete
        reason: Reason for deletion
    """
    # Validate that we have at least one jar to delete
    if not jar_name or len(jar_name) == 0:
        return f"❌ Must provide at least one jar name"
    
    # Find and validate all jars first
    jars_to_delete = []
    total_deleted_percent = 0.0
    
    for i, current_jar_name in enumerate(jar_name):
        jar = get_jar_by_name(current_jar_name)
        if not jar:
            return f"❌ Jar {i+1} '{current_jar_name}' not found"
        
        jars_to_delete.append(jar)
        total_deleted_percent += jar["percent"]
    
    # Delete all jars and collect info
    deleted_jars_info = []
    
    for jar in jars_to_delete:
        # Store jar info before deletion
        deleted_percent = jar["percent"]
        deleted_budget = calculate_budget_from_percent(deleted_percent)
        deleted_name = jar["name"]
        
        # Remove from storage
        delete_jar_from_storage(jar["name"])
        
        deleted_jars_info.append({
            'name': deleted_name,
            'percent': deleted_percent,
            'budget': deleted_budget
        })
    
    # Rebalance remaining jars if deleted jars had percentage allocation
    rebalance_message = ""
    if total_deleted_percent > 0:
        rebalance_message = redistribute_deleted_jar_percentage(total_deleted_percent)
    
    # Format response
    if len(deleted_jars_info) == 1:
        jar_info = deleted_jars_info[0]
        base_message = f"✅ Deleted {jar_info['name']} jar (${jar_info['budget']:.2f} budget, {format_percent_display(jar_info['percent'])}). Reason: {reason}"
    else:
        deleted_summaries = []
        for jar_info in deleted_jars_info:
            deleted_summaries.append(f"{jar_info['name']} ({format_percent_display(jar_info['percent'])}, ${jar_info['budget']:.2f})")
        
        deleted_summary = ", ".join(deleted_summaries)
        base_message = f"✅ Deleted {len(deleted_jars_info)} jars: {deleted_summary}. Total freed: {format_percent_display(total_deleted_percent)}. Reason: {reason}"
    
    if rebalance_message:
        return f"{base_message}\n{rebalance_message}"
    else:
        return base_message

@tool
def list_jars() -> str:
    """List all budget jars with their current balances, budgets, and percentages."""
    
    jars = fetch_existing_jars()
    
    if not jars:
        return f"📋 No jars found. Total income: ${TOTAL_INCOME:.2f}"
    
    # Sort by percentage allocation (descending)
    jars.sort(key=lambda j: j["percent"], reverse=True)
    
    # Format jar list
    jar_list = []
    total_current_percent = 0.0
    total_percent = 0.0
    
    for jar in jars:
        # Calculate dollar amounts from percentages
        current_amount = calculate_current_amount_from_percent(jar['current_percent'])
        budget_amount = calculate_budget_from_percent(jar['percent'])
        
        # Format display
        current_display = format_percent_display(jar['current_percent'])
        percent_display = format_percent_display(jar['percent'])
        
        jar_list.append(
            f"• {jar['name']}: ${current_amount:.2f}/${budget_amount:.2f} "
            f"({current_display}/{percent_display}) - {jar['description']}"
        )
        
        total_current_percent += jar["current_percent"]
        total_percent += jar["percent"]
    
    # Calculate total amounts
    total_current_amount = calculate_current_amount_from_percent(total_current_percent)
    total_budget_amount = calculate_budget_from_percent(total_percent)
    
    header = f"📋 Budget Jars ({len(jars)} jars) - Total Income: ${TOTAL_INCOME:.2f}"
    footer = (f"\n💰 Totals: ${total_current_amount:.2f}/${total_budget_amount:.2f} "
              f"({format_percent_display(total_current_percent)}/{format_percent_display(total_percent)})")
    
    return header + "\n" + "\n".join(jar_list) + footer



@tool
def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
    """Ask user for clarification when input is unclear.
    
    Args:
        question: Question to ask for clarification
        suggestions: Optional suggestions to help user
    """
    
    result = f"❓ {question}"
    if suggestions:
        result += f"\n💡 Suggestions: {suggestions}"
    
    return result

# === MOCK DATA FOR TESTING ===

def initialize_mock_data():
    """Initialize default jars based on T. Harv Eker's 6-jar system"""
    
    # Clear existing data
    JARS_STORAGE.clear()
    
    # Initialize with default jars (users can add more)
    for jar_data in DEFAULT_JARS_DATABASE:
        save_jar(jar_data.copy())

# Initialize mock data when module is imported
if not JARS_STORAGE:
    initialize_mock_data()

# === TOOLS LIST FOR LLM BINDING ===

JAR_MANAGER_TOOLS = [
    create_jar,
    update_jar,
    delete_jar,
    list_jars,
    request_clarification
]
