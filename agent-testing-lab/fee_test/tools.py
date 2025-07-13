"""
Fee Manager Tools - LLM Tool Definitions
========================================

Tools that the LLM can call to manage recurring fees.
"""

import json
from langchain_core.tools import tool
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json

# Global storage for fees (mock database) - keyed by name instead of ID
FEES_STORAGE: Dict[str, 'RecurringFee'] = {}

# Mock jar database (matches classifier system structure)
JARS_DATABASE = [
    # --- Essential & High-Priority Expenses ---
    {
        "name": "rent",
        "budget": 1250,
        "current": 1250,
        "description": "Monthly rent or mortgage payment for housing"
    },
    {
        "name": "groceries", 
        "budget": 400,
        "current": 270,
        "description": "Food and household essentials from supermarkets"
    },
    {
        "name": "utilities",
        "budget": 200,
        "current": 65,
        "description": "Essential services like electricity, water, and internet"
    },
    {
        "name": "gas",
        "budget": 200,
        "current": 103,
        "description": "Fuel and vehicle-related expenses"
    },
    # --- Daily & Variable Expenses ---
    {
        "name": "meals",
        "budget": 500,
        "current": 212,
        "description": "Dining out, food delivery, and coffee shop purchases"
    },
    {
        "name": "transport",
        "budget": 100,
        "current": 18,
        "description": "Public transportation, taxis, and rideshare services"
    },
]

@dataclass
class RecurringFee:
    name: str  # Human-friendly name (LLM can remember this)
    amount: float
    description: str
    target_jar: str
    
    pattern_type: str  # "daily", "weekly", "monthly" (simplified for LLM clarity)
    pattern_details: Optional[List[int]] = None  # Simple list of numbers or None
    # For daily: None (every day)
    # For weekly: None (every day) or [1,3,5] (Mon, Wed, Fri) where 1=Monday, 7=Sunday  
    # For monthly: None (every day) or [1,15] (1st and 15th) where numbers are day of month
    
    created_date: datetime = None
    next_occurrence: datetime = None
    last_occurrence: Optional[datetime] = None  # Track when last applied
    end_date: Optional[datetime] = None  # Support for finite fees
    
    is_active: bool = True
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'amount': self.amount,
            'description': self.description,
            'target_jar': self.target_jar,
            'pattern_type': self.pattern_type,
            'pattern_details': self.pattern_details,
            'created_date': self.created_date.isoformat(),
            'next_occurrence': self.next_occurrence.isoformat(),
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active
        }

def calculate_next_occurrence(pattern_type: str, pattern_details: Optional[List[int]], from_date: datetime = None) -> datetime:
    """Calculate when fee should next occur based on pattern
    
    Args:
        pattern_type: "daily", "weekly", "monthly"
        pattern_details: List of numbers or None
            - daily: None (every day)
            - weekly: None (every day) or [1,3,5] (Mon, Wed, Fri) where 1=Monday, 7=Sunday
            - monthly: None (every day) or [1,15] (1st and 15th) where numbers are day of month
        from_date: Starting date (defaults to now)
    """
    if from_date is None:
        from_date = datetime.now()
    
    # Validate pattern_details type
    if pattern_details is not None:
        if not isinstance(pattern_details, list):
            raise TypeError(f"pattern_details must be List[int] or None, got {type(pattern_details)}: {pattern_details}")
        # Ensure all elements are integers
        if not all(isinstance(x, int) for x in pattern_details):
            # Convert floats to ints if they're whole numbers
            try:
                pattern_details = [int(x) for x in pattern_details if x == int(x)]
            except (ValueError, TypeError):
                raise TypeError(f"pattern_details must contain only integers, got: {pattern_details}")
    
    if pattern_type == "daily":
        # Daily pattern: always next day (pattern_details ignored for daily)
        return from_date + timedelta(days=1)
        
    elif pattern_type == "weekly":
        if pattern_details is None:
            # Every day of the week
            return from_date + timedelta(days=1)
        else:
            # Specific days of the week
            days = pattern_details  # [1,3,5] = Monday, Wednesday, Friday
            current_weekday = from_date.weekday() + 1  # Monday=1, ..., Sunday=7
            
            # Find next occurrence of any specified day
            next_days = [d for d in days if d > current_weekday]
            if next_days:
                days_until = min(next_days) - current_weekday
            else:
                # Next week, first day
                days_until = 7 - current_weekday + min(days)
            return from_date + timedelta(days=days_until)
        
    elif pattern_type == "monthly":
        if pattern_details is None:
            # Every day of the month
            return from_date + timedelta(days=1)
        else:
            # Specific days of the month
            target_dates = pattern_details  # [1,15] = 1st and 15th
            current_day = from_date.day
            
            # Find next occurrence this month
            next_dates_this_month = [d for d in target_dates if d > current_day]
            if next_dates_this_month:
                target_date = min(next_dates_this_month)
                try:
                    return from_date.replace(day=target_date)
                except ValueError:
                    # Target date doesn't exist in current month (e.g., Feb 31st)
                    # Fall through to next month
                    pass
            
            # Next month, first target date
            next_month = from_date.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)  # First day of next month
            target_date = min(target_dates)
            try:
                return next_month.replace(day=target_date)
            except ValueError:
                # Target date doesn't exist in next month (e.g., Feb 31st)
                # Use last day of that month
                month_after = next_month.replace(day=1) + timedelta(days=32)
                last_day = (month_after.replace(day=1) - timedelta(days=1)).day
                return next_month.replace(day=min(target_date, last_day))
    
    # Default fallback
    return from_date + timedelta(days=1)

def generate_fee_name(description: str) -> str:
    """Generate a clean, LLM-friendly fee name from description"""
    # Clean up description for name
    clean_name = description.strip()
    
    # If too long, shorten it
    if len(clean_name) > 20:
        clean_name = clean_name[:17] + "..."
    
    return clean_name

def validate_fee_name(name: str) -> tuple[bool, str]:
    """Validate fee name for uniqueness and format"""
    if not name or not name.strip():
        return False, "Fee name cannot be empty"
    
    clean_name = name.strip()
    if len(clean_name) < 3:
        return False, "Fee name too short (minimum 3 characters)"
    
    if clean_name.lower() in [fee.name.lower() for fee in FEES_STORAGE.values()]:
        return False, f"Fee name '{clean_name}' already exists"
    
    return True, ""

# === UTILITY FUNCTIONS (for LLM context) ===

def fetch_existing_fees() -> List[RecurringFee]:
    """Get all current recurring fees"""
    return list(FEES_STORAGE.values())

def fetch_available_jars() -> List[Dict]:
    """Get available budget jars from database (same structure as classifier)"""
    return JARS_DATABASE.copy()

def get_jar_names() -> List[str]:
    """Get list of jar names only"""
    return [jar["name"] for jar in JARS_DATABASE]

def get_fee_by_name(fee_name: str) -> Optional[RecurringFee]:
    """Get fee by name (case-insensitive)"""
    for stored_name, fee in FEES_STORAGE.items():
        if stored_name.lower() == fee_name.lower():
            return fee
    return None

def save_recurring_fee(fee: RecurringFee):
    """Save fee to storage using name as key"""
    FEES_STORAGE[fee.name] = fee

def delete_fee_from_storage(fee_name: str):
    """Remove fee from storage completely"""
    if fee_name in FEES_STORAGE:
        del FEES_STORAGE[fee_name]

# === LLM TOOLS ===

@tool
def create_recurring_fee(
    name: str,
    amount: float, 
    description: str, 
    pattern_type: str,
    pattern_details: Optional[List[int]],
    target_jar: str,
    confidence: int
) -> str:
    """Create a new recurring fee with specified schedule pattern.
    
    Args:
        name: Human-friendly name for the fee (e.g. "Daily coffee", "Weekly commute")
        amount: Amount per occurrence
        description: Detailed description of the fee
        pattern_type: "daily", "weekly", "monthly"
        pattern_details: Simple list of numbers or None
            - daily: None (every day)
            - weekly: None (every day) or [1,3,5] (Mon, Wed, Fri) where 1=Monday, 7=Sunday
            - monthly: None (every day) or [1,15] (1st and 15th) day of month
        target_jar: Budget jar to charge
        confidence: LLM confidence in pattern recognition (0-100)
    """
    
    # Validate pattern_details type - no fallbacks
    if pattern_details is not None:
        if not isinstance(pattern_details, list):
            raise TypeError(f"create_recurring_fee: pattern_details must be List[int] or None, got {type(pattern_details)}: {pattern_details}")
        # Ensure all elements are integers
        if not all(isinstance(x, int) for x in pattern_details):
            # Convert floats to ints if they're whole numbers
            try:
                pattern_details = [int(x) for x in pattern_details if x == int(x)]
            except (ValueError, TypeError):
                raise TypeError(f"create_recurring_fee: pattern_details must contain only integers, got: {pattern_details}")
    
    # Validate fee name
    name_valid, name_error = validate_fee_name(name)
    if not name_valid:
        return f"❌ {name_error}"
    
    # Validate jar exists in database
    jar_names = get_jar_names()
    if target_jar not in jar_names:
        return f"❌ Invalid jar '{target_jar}'. Available: {', '.join(jar_names)}"
    
    # Validate pattern type
    if pattern_type not in ["daily", "weekly", "monthly"]:
        return f"❌ Invalid pattern_type '{pattern_type}'. Must be: daily, weekly, monthly"
    
    # Create fee
    now = datetime.now()
    next_occurrence = calculate_next_occurrence(pattern_type, pattern_details, now)
    
    fee = RecurringFee(
        name=name.strip(),
        amount=amount,
        description=description,
        target_jar=target_jar,
        pattern_type=pattern_type,
        pattern_details=pattern_details,
        created_date=now,
        next_occurrence=next_occurrence,
        last_occurrence=None,
        end_date=None,
        is_active=True
    )
    
    save_recurring_fee(fee)
    
    # Format output based on confidence level (like classifier)
    if confidence >= 90:
        return f"✅ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ Created recurring fee: {name} - ${amount} {pattern_type} → {target_jar} jar. Next: {next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - please verify)"

@tool
def adjust_recurring_fee(
    fee_name: str,
    new_amount: Optional[float] = None,
    new_description: Optional[str] = None,
    new_pattern_type: Optional[str] = None,
    new_pattern_details: Optional[List[int]] = None,
    new_target_jar: Optional[str] = None,
    disable: bool = False,
    confidence: int = 85
) -> str:
    """Adjust an existing recurring fee.
    
    Args:
        fee_name: Name of fee to adjust
        new_amount: New amount per occurrence
        new_description: New description
        new_pattern_type: New pattern type ("daily", "weekly", "monthly")
        new_pattern_details: New pattern details (List[int] or None)
        new_target_jar: New target jar
        disable: Whether to disable the fee
        confidence: LLM confidence in adjustment
    """
    
    # Validate pattern_details type - no fallbacks
    if new_pattern_details is not None:
        if not isinstance(new_pattern_details, list):
            raise TypeError(f"adjust_recurring_fee: new_pattern_details must be List[int] or None, got {type(new_pattern_details)}: {new_pattern_details}")
        # Ensure all elements are integers
        if not all(isinstance(x, int) for x in new_pattern_details):
            # Convert floats to ints if they're whole numbers
            try:
                new_pattern_details = [int(x) for x in new_pattern_details if x == int(x)]
            except (ValueError, TypeError):
                raise TypeError(f"adjust_recurring_fee: new_pattern_details must contain only integers, got: {new_pattern_details}")
    
    # Try to find fee by name first, then by description
    fee = get_fee_by_name(fee_name)
    if not fee:
        return f"❌ Fee {fee_name} not found"
    
    changes = []
    
    # Handle disable
    if disable:
        fee.is_active = False
        changes.append("disabled")
    
    # Update amount
    if new_amount is not None:
        old_amount = fee.amount
        fee.amount = new_amount
        changes.append(f"amount: ${old_amount} → ${new_amount}")
    
    # Update description
    if new_description:
        old_desc = fee.description
        fee.description = new_description
        changes.append(f"description: '{old_desc}' → '{new_description}'")
    
    # Update target jar
    if new_target_jar:
        jar_names = get_jar_names()
        if new_target_jar not in jar_names:
            return f"❌ Invalid jar '{new_target_jar}'. Available: {', '.join(jar_names)}"
        old_jar = fee.target_jar
        fee.target_jar = new_target_jar
        changes.append(f"jar: {old_jar} → {new_target_jar}")
    
    # Update pattern
    if new_pattern_type:
        if new_pattern_type not in ["daily", "weekly", "monthly"]:
            return f"❌ Invalid pattern_type '{new_pattern_type}'. Must be: daily, weekly, monthly"
        
        old_pattern = fee.pattern_type
        fee.pattern_type = new_pattern_type
        if new_pattern_details:
            fee.pattern_details = new_pattern_details
        
        # Recalculate next occurrence
        fee.next_occurrence = calculate_next_occurrence(new_pattern_type, fee.pattern_details)
        changes.append(f"pattern: {old_pattern} → {new_pattern_type}")
    
    save_recurring_fee(fee)
    
    if not changes:
        return f"ℹ️ No changes made to fee: {fee.name}"
    
    changes_str = ", ".join(changes)
    
    # Format output based on confidence level
    if confidence >= 90:
        return f"✅ Adjusted fee: {fee.name}. Changes: {changes_str}. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident)"
    elif confidence >= 70:
        return f"⚠️ Adjusted fee: {fee.name}. Changes: {changes_str}. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - moderate certainty)"
    else:
        return f"❓ Adjusted fee: {fee.name}. Changes: {changes_str}. Next: {fee.next_occurrence.strftime('%Y-%m-%d')} ({confidence}% confident - please verify)"

@tool
def delete_recurring_fee(fee_name: str, reason: str) -> str:
    """Delete (deactivate) a recurring fee.
    
    Args:
        fee_name: Name of fee to delete
        reason: Reason for deletion
    """
    
    # Try to find fee by name first, then by description
    fee = get_fee_by_name(fee_name)
    if not fee:
        return f"❌ Fee {fee_name} not found"
    
    fee.is_active = False
    save_recurring_fee(fee)
    
    return f"✅ Deleted fee: {fee.name} (${fee.amount} {fee.pattern_type}). Reason: {reason}"

@tool
def list_recurring_fees(active_only: bool = True, target_jar: Optional[str] = None) -> str:
    """List all recurring fees with optional filters.
    
    Args:
        active_only: Only show active fees
        target_jar: Filter by target jar
    """
    
    fees = fetch_existing_fees()
    
    if active_only:
        fees = [f for f in fees if f.is_active]
    
    if target_jar:
        fees = [f for f in fees if f.target_jar == target_jar]
    
    if not fees:
        filter_desc = ""
        if target_jar:
            filter_desc += f" in {target_jar} jar"
        if active_only:
            filter_desc += " (active only)"
        return f"📋 No recurring fees found{filter_desc}"
    
    # Sort by next occurrence
    fees.sort(key=lambda f: f.next_occurrence)
    
    result = f"📋 Recurring Fees ({len(fees)} found):\n"
    for fee in fees:
        status = "✅" if fee.is_active else "❌"
        result += f"{status} {fee.name} - ${fee.amount} {fee.pattern_type} → {fee.target_jar} jar"
        result += f" | Next: {fee.next_occurrence.strftime('%Y-%m-%d')}"
        
        # Show additional info if available
        if fee.last_occurrence:
            result += f" | Last: {fee.last_occurrence.strftime('%Y-%m-%d')}"
        if fee.end_date:
            result += f" | Ends: {fee.end_date.strftime('%Y-%m-%d')}"
        
        result += "\n"
    
    return result.strip()

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
    """Initialize some mock fees for testing with improved structure"""
    
    # Clear existing data
    FEES_STORAGE.clear()
    
    now = datetime.now()
    
    # Daily coffee
    next_occurrence = calculate_next_occurrence("daily", None, now)
    fee1 = RecurringFee(
        name="Daily coffee",
        amount=5.0,
        description="Morning coffee from the office cafe",
        target_jar="meals",
        pattern_type="daily",
        pattern_details=None,  # None = every day
        created_date=now,
        next_occurrence=next_occurrence,
        last_occurrence=now - timedelta(days=1),  # Yesterday
        end_date=None,
        is_active=True
    )
    save_recurring_fee(fee1)
    
    # Weekly commute
    next_occurrence = calculate_next_occurrence("weekly", [1, 2, 3, 4, 5], now)
    fee2 = RecurringFee(
        name="Bus fare",
        amount=10.0,
        description="Bus fare for work commute - weekdays only",
        target_jar="transport",
        pattern_type="weekly",
        pattern_details=[1, 2, 3, 4, 5],  # Monday=1 to Friday=5
        created_date=now,
        next_occurrence=next_occurrence,
        last_occurrence=None,
        end_date=None,
        is_active=True
    )
    save_recurring_fee(fee2)
    
    # Monthly subscription
    next_occurrence = calculate_next_occurrence("monthly", [5], now)
    fee3 = RecurringFee(
        name="YouTube Premium",
        amount=15.99,
        description="YouTube Premium subscription for ad-free videos",
        target_jar="utilities",
        pattern_type="monthly",
        pattern_details=[5],  # 5th of every month
        created_date=now,
        next_occurrence=next_occurrence,
        last_occurrence=now - timedelta(days=30),  # Last month
        end_date=None,
        is_active=True
    )
    save_recurring_fee(fee3)

# Initialize mock data when module is imported
if not FEES_STORAGE:
    initialize_mock_data()

# === TOOLS LIST FOR LLM BINDING ===

FEE_MANAGER_TOOLS = [
    create_recurring_fee,
    adjust_recurring_fee,
    delete_recurring_fee,
    list_recurring_fees,
    request_clarification
]