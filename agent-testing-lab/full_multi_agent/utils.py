"""
Database Utilities for VPBank AI Financial Coach
===============================================

Utility functions for database operations, calculations, and helper functions.
Separated from database.py which contains only schema and storage.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json

# Import data structures and storage from database module
from database import (
    # Data structures
    Jar, Transaction, RecurringFee, BudgetPlan, ConversationTurn,
    
    # Storage containers
    JARS_STORAGE, TRANSACTIONS_STORAGE, FEES_STORAGE, 
    BUDGET_PLANS_STORAGE, CONVERSATION_HISTORY,
    
    # Configuration
    TOTAL_INCOME, MAX_MEMORY_TURNS,
    
    # Conversation lock
    ACTIVE_AGENT_CONTEXT, set_active_agent_context, get_active_agent_context
)

# =============================================================================
# CONVERSATION LOCK UTILITIES
# =============================================================================

def parse_confidence_response(response: str, agent_name: str) -> Tuple[str, bool]:
    """
    Parse agent response for requires_follow_up flag.
    
    Args:
        response: Agent response text
        agent_name: Name of the agent that generated the response
        
    Returns:
        Tuple of (cleaned_response, requires_follow_up)
    """
    # Look for follow-up indicators in response
    follow_up_indicators = [
        "?", "please", "clarify", "more information", "follow up",
        "what about", "can you", "would you like", "do you want"
    ]
    
    requires_follow_up = any(indicator in response.lower() for indicator in follow_up_indicators)
    
    return response, requires_follow_up

def check_conversation_lock() -> Optional[str]:
    """Check if conversation is locked to a specific agent"""
    return get_active_agent_context()

def lock_conversation_to_agent(agent_name: str) -> None:
    """Lock conversation to specific agent for multi-turn interaction"""
    set_active_agent_context(agent_name)

def release_conversation_lock() -> None:
    """Release conversation lock to allow orchestrator routing"""
    set_active_agent_context(None)

# =============================================================================
# JAR OPERATIONS
# =============================================================================

def save_jar(jar: Jar) -> None:
    """Save jar to storage"""
    JARS_STORAGE[jar.name] = jar

def get_jar(jar_name: str) -> Optional[Jar]:
    """Get jar by name"""
    return JARS_STORAGE.get(jar_name)

def get_all_jars() -> List[Jar]:
    """Get all jars"""
    return list(JARS_STORAGE.values())

def delete_jar(jar_name: str) -> bool:
    """Delete jar from storage"""
    if jar_name in JARS_STORAGE:
        del JARS_STORAGE[jar_name]
        return True
    return False

def find_jar_by_keywords(keywords: str) -> Optional[Jar]:
    """Find jar by matching keywords in name or description"""
    keywords_lower = keywords.lower()
    
    # First try exact name match
    if keywords_lower in JARS_STORAGE:
        return JARS_STORAGE[keywords_lower]
    
    # Then try partial match in name or description
    for jar in JARS_STORAGE.values():
        if (keywords_lower in jar.name.lower() or 
            keywords_lower in jar.description.lower()):
            return jar
    
    return None

def calculate_jar_total_allocation() -> float:
    """Calculate total percentage allocation across all jars"""
    return sum(jar.percent for jar in JARS_STORAGE.values())

def validate_jar_percentages() -> Tuple[bool, float]:
    """Validate that total jar allocation doesn't exceed 100%"""
    total = calculate_jar_total_allocation()
    return total <= 1.0, total

# =============================================================================
# TRANSACTION OPERATIONS
# =============================================================================

def save_transaction(transaction: Transaction) -> None:
    """Save transaction to storage"""
    TRANSACTIONS_STORAGE.append(transaction)

def get_all_transactions() -> List[Transaction]:
    """Get all transactions"""
    return TRANSACTIONS_STORAGE.copy()

def get_transactions_by_jar(jar_name: str) -> List[Transaction]:
    """Get transactions for specific jar"""
    return [t for t in TRANSACTIONS_STORAGE if t.jar == jar_name]

def get_transactions_by_date_range(start_date: str, end_date: str = None) -> List[Transaction]:
    """Get transactions within date range"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    return [t for t in TRANSACTIONS_STORAGE 
            if start_date <= t.date <= end_date]

def get_transactions_by_amount_range(min_amount: float = None, max_amount: float = None) -> List[Transaction]:
    """Get transactions within amount range"""
    result = TRANSACTIONS_STORAGE.copy()
    
    if min_amount is not None:
        result = [t for t in result if t.amount >= min_amount]
    
    if max_amount is not None:
        result = [t for t in result if t.amount <= max_amount]
    
    return result

def get_transactions_by_source(source: str) -> List[Transaction]:
    """Get transactions by source type"""
    return [t for t in TRANSACTIONS_STORAGE if t.source == source]

def calculate_jar_spending_total(jar_name: str) -> float:
    """Calculate total spending for a specific jar"""
    transactions = get_transactions_by_jar(jar_name)
    return sum(t.amount for t in transactions)

# =============================================================================
# RECURRING FEE OPERATIONS
# =============================================================================

def save_recurring_fee(fee: RecurringFee) -> None:
    """Save recurring fee to storage"""
    FEES_STORAGE[fee.name] = fee

def get_recurring_fee(fee_name: str) -> Optional[RecurringFee]:
    """Get recurring fee by name"""
    return FEES_STORAGE.get(fee_name)

def get_all_recurring_fees() -> List[RecurringFee]:
    """Get all recurring fees"""
    return list(FEES_STORAGE.values())

def get_active_recurring_fees() -> List[RecurringFee]:
    """Get only active recurring fees"""
    return [fee for fee in FEES_STORAGE.values() if fee.is_active]

def delete_recurring_fee(fee_name: str) -> bool:
    """Delete recurring fee from storage"""
    if fee_name in FEES_STORAGE:
        del FEES_STORAGE[fee_name]
        return True
    return False

def calculate_next_fee_occurrence(pattern_type: str, pattern_details: List[int], from_date: datetime = None) -> datetime:
    """Calculate when fee should next occur based on pattern"""
    if from_date is None:
        from_date = datetime.now()
    
    if pattern_type == "daily":
        return from_date + timedelta(days=1)
        
    elif pattern_type == "weekly":
        if not pattern_details:  # Every day
            return from_date + timedelta(days=1)
        else:
            # Specific days of the week [1=Monday, 7=Sunday]
            days = pattern_details
            current_weekday = from_date.weekday() + 1
            
            # Find next occurrence
            next_days = [d for d in days if d > current_weekday]
            if next_days:
                days_until = min(next_days) - current_weekday
            else:
                # Next week, first day
                days_until = 7 - current_weekday + min(days)
            return from_date + timedelta(days=days_until)
        
    elif pattern_type == "monthly":
        if not pattern_details:  # Every day
            return from_date + timedelta(days=1)
        else:
            # Specific days of the month
            target_dates = pattern_details
            current_day = from_date.day
            
            # Find next occurrence this month
            next_dates_this_month = [d for d in target_dates if d > current_day]
            if next_dates_this_month:
                target_date = min(next_dates_this_month)
                try:
                    return from_date.replace(day=target_date)
                except ValueError:
                    pass  # Fall through to next month
            
            # Next month, first target date
            next_month = from_date.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            target_date = min(target_dates)
            try:
                return next_month.replace(day=target_date)
            except ValueError:
                # Target date doesn't exist (e.g., Feb 31st)
                month_after = next_month.replace(day=1) + timedelta(days=32)
                last_day = (month_after.replace(day=1) - timedelta(days=1)).day
                return next_month.replace(day=min(target_date, last_day))
    
    # Default fallback
    return from_date + timedelta(days=1)

def get_fees_due_today() -> List[RecurringFee]:
    """Get fees that are due today"""
    today = datetime.now().date()
    return [fee for fee in get_active_recurring_fees() 
            if fee.next_occurrence.date() <= today]

# =============================================================================
# BUDGET PLAN OPERATIONS
# =============================================================================

def save_budget_plan(plan: BudgetPlan) -> None:
    """Save budget plan to storage"""
    BUDGET_PLANS_STORAGE[plan.name] = plan

def get_budget_plan(plan_name: str) -> Optional[BudgetPlan]:
    """Get budget plan by name"""
    return BUDGET_PLANS_STORAGE.get(plan_name)

def get_all_budget_plans() -> List[BudgetPlan]:
    """Get all budget plans"""
    return list(BUDGET_PLANS_STORAGE.values())

def get_budget_plans_by_status(status: str) -> List[BudgetPlan]:
    """Get budget plans by status"""
    return [plan for plan in BUDGET_PLANS_STORAGE.values() 
            if plan.status == status]

def delete_budget_plan(plan_name: str) -> bool:
    """Delete budget plan from storage"""
    if plan_name in BUDGET_PLANS_STORAGE:
        del BUDGET_PLANS_STORAGE[plan_name]
        return True
    return False

# =============================================================================
# CONVERSATION HISTORY OPERATIONS
# =============================================================================

def add_conversation_turn(user_input: str, agent_output: str, 
                         agent_list: List[str] = None, 
                         tool_call_list: List[str] = None) -> None:
    """Add conversation turn with memory limit"""
    if agent_list is None:
        agent_list = []
    if tool_call_list is None:
        tool_call_list = []
        
    turn = ConversationTurn(
        user_input=user_input,
        agent_output=agent_output,
        agent_list=agent_list,
        tool_call_list=tool_call_list
    )
    
    CONVERSATION_HISTORY.append(turn)
    
    # Maintain memory limit
    if len(CONVERSATION_HISTORY) > MAX_MEMORY_TURNS:
        CONVERSATION_HISTORY.pop(0)

def get_conversation_history(limit: Optional[int] = None) -> List[ConversationTurn]:
    """Get recent conversation history"""
    if limit is None:
        return CONVERSATION_HISTORY.copy()
    return CONVERSATION_HISTORY[-limit:] if limit > 0 else []

def get_agent_specific_history(agent_name: str, max_turns: int = 10) -> List[ConversationTurn]:
    """
    Retrieves the conversation history specifically for a given agent.

    Args:
        agent_name: The name of the agent to filter history for (e.g., "budget_advisor").
        max_turns: The maximum number of turns to return.

    Returns:
        A list of ConversationTurn objects where the specified agent was involved.
    """
    agent_history = [
        turn for turn in CONVERSATION_HISTORY 
        if agent_name in turn.agent_list
    ]
    return agent_history[-max_turns:]

def clear_conversation_history() -> None:
    """Clear all conversation history"""
    CONVERSATION_HISTORY.clear()

def get_conversation_context_string(limit: int = 5) -> str:
    """Get conversation history as formatted string for agent context"""
    recent_turns = get_conversation_history(limit)
    
    if not recent_turns:
        return "No conversation history."
    
    context_lines = []
    for turn in recent_turns:
        context_lines.append(f"User: {turn.user_input}")
        context_lines.append(f"Assistant: {turn.agent_output}")
        if turn.agent_list:
            context_lines.append(f"Agents: {', '.join(turn.agent_list)}")
    
    return "\n".join(context_lines)

# =============================================================================
# CALCULATION UTILITIES
# =============================================================================

def calculate_percent_from_amount(amount: float) -> float:
    """Convert dollar amount to percentage of TOTAL_INCOME"""
    return amount / TOTAL_INCOME

def calculate_amount_from_percent(percent: float) -> float:
    """Convert percentage to dollar amount based on TOTAL_INCOME"""
    return percent * TOTAL_INCOME

def format_currency(amount: float) -> str:
    """Format amount as currency string"""
    return f"${amount:,.2f}"

def format_percentage(percent: float) -> str:
    """Format percentage for display (0.15 -> 15.0%)"""
    return f"{percent * 100:.1f}%"

def validate_percentage_range(percent: float) -> bool:
    """Validate percentage is within 0.0-1.0 range"""
    return 0.0 <= percent <= 1.0

def validate_positive_amount(amount: float) -> bool:
    """Validate amount is positive"""
    return amount > 0

# =============================================================================
# DATABASE STATISTICS AND MONITORING
# =============================================================================

def get_database_stats() -> Dict[str, Any]:
    """Get comprehensive database statistics"""
    return {
        "jars": {
            "count": len(JARS_STORAGE),
            "total_allocation": f"{calculate_jar_total_allocation() * 100:.1f}%",
            "allocation_valid": validate_jar_percentages()[0]
        },
        "transactions": {
            "count": len(TRANSACTIONS_STORAGE),
            "total_amount": format_currency(sum(t.amount for t in TRANSACTIONS_STORAGE)),
            "sources": list(set(t.source for t in TRANSACTIONS_STORAGE))
        },
        "recurring_fees": {
            "count": len(FEES_STORAGE),
            "active_count": len(get_active_recurring_fees()),
            "due_today": len(get_fees_due_today())
        },
        "budget_plans": {
            "count": len(BUDGET_PLANS_STORAGE),
            "active": len(get_budget_plans_by_status("active")),
            "completed": len(get_budget_plans_by_status("completed"))
        },
        "conversation": {
            "turns": len(CONVERSATION_HISTORY),
            "active_agent_context": get_active_agent_context()
        },
        "system": {
            "total_income": format_currency(TOTAL_INCOME),
            "memory_limit": MAX_MEMORY_TURNS
        }
    }

def export_database_json() -> str:
    """Export all database contents to JSON"""
    data = {
        "jars": [jar.to_dict() for jar in JARS_STORAGE.values()],
        "transactions": [t.to_dict() for t in TRANSACTIONS_STORAGE],
        "recurring_fees": [fee.to_dict() for fee in FEES_STORAGE.values()],
        "budget_plans": [plan.to_dict() for plan in BUDGET_PLANS_STORAGE.values()],
        "conversation_history": [turn.to_dict() for turn in CONVERSATION_HISTORY],
        "active_agent_context": get_active_agent_context(),
        "total_income": TOTAL_INCOME,
        "stats": get_database_stats()
    }
    return json.dumps(data, indent=2)

# =============================================================================
# INITIALIZATION AND SETUP
# =============================================================================

def initialize_default_data() -> None:
    """Initialize T. Harv Eker's 6-jar system + comprehensive sample data (based on classifier_test/tools.py)"""
    
    # Clear existing data
    JARS_STORAGE.clear()
    TRANSACTIONS_STORAGE.clear()
    FEES_STORAGE.clear()
    BUDGET_PLANS_STORAGE.clear()
    CONVERSATION_HISTORY.clear()
    release_conversation_lock()
    
    # Initialize T. Harv Eker's 6-jar system
    default_jars = [
        Jar("necessities", "Essential living expenses (rent, utilities, groceries)", 0.55, 0.33, 1650.0, 2750.0),
        Jar("long_term_savings", "Long-term savings for major purchases", 0.10, 0.04, 200.0, 500.0),
        Jar("play", "Entertainment, dining, and fun activities", 0.10, 0.06, 300.0, 500.0),
        Jar("education", "Learning, courses, and skill development", 0.10, 0.03, 150.0, 500.0),
        Jar("financial_freedom", "Investments and passive income", 0.10, 0.015, 75.0, 500.0),
        Jar("give", "Charity, donations, and helping others", 0.05, 0.005, 25.0, 250.0)
    ]
    
    for jar in default_jars:
        save_jar(jar)
    
    # Add comprehensive sample transactions (based on classifier_test/tools.py pattern + our schema)
    sample_transactions = [
        # === January 2024 ===
        Transaction(1250.0, "necessities", "January Rent Payment", "2024-01-01", "09:00", "vpbank_api"),
        Transaction(65.0, "necessities", "Internet Bill", "2024-01-02", "14:30", "vpbank_api"),
        Transaction(15.0, "play", "Lunch at work cafe", "2024-01-02", "12:15", "manual_input"),
        Transaction(6.0, "play", "Morning coffee", "2024-01-03", "08:30", "manual_input"),
        Transaction(12.0, "play", "Sandwich for lunch", "2024-01-03", "12:45", "manual_input"),
        Transaction(85.0, "necessities", "Weekly grocery shopping", "2024-01-04", "10:30", "vpbank_api"),
        Transaction(15.99, "play", "Netflix Subscription", "2024-01-05", "16:00", "vpbank_api"),
        Transaction(45.0, "play", "Dinner with a friend", "2024-01-05", "19:30", "manual_input"),
        Transaction(55.0, "necessities", "Fill up gas tank", "2024-01-06", "08:00", "vpbank_api"),
        Transaction(35.0, "play", "New sweater", "2024-01-06", "15:20", "manual_input"),
        Transaction(22.0, "play", "Sunday brunch", "2024-01-07", "11:30", "manual_input"),
        Transaction(7.0, "play", "Coffee and a pastry", "2024-01-08", "08:45", "manual_input"),
        Transaction(14.0, "play", "Burrito bowl for lunch", "2024-01-08", "12:30", "manual_input"),
        Transaction(30.0, "play", "Pizza delivery", "2024-01-09", "19:00", "manual_input"),
        Transaction(8.0, "necessities", "Milk and bread", "2024-01-10", "17:30", "manual_input"),
        Transaction(11.99, "play", "Spotify Premium", "2024-01-10", "20:00", "vpbank_api"),
        Transaction(12.0, "necessities", "Taxi ride", "2024-01-11", "07:45", "manual_input"),
        Transaction(16.0, "play", "Sushi lunch", "2024-01-11", "12:00", "manual_input"),
        Transaction(50.0, "necessities", "Fill up tank", "2024-01-12", "07:30", "vpbank_api"),
        Transaction(38.0, "play", "Drinks with coworkers", "2024-01-12", "18:30", "manual_input"),
        Transaction(45.0, "necessities", "Weekly shopping", "2024-01-13", "10:00", "vpbank_api"),
        Transaction(30.0, "necessities", "Haircut", "2024-01-13", "14:00", "manual_input"),
        Transaction(15.0, "play", "Lunch takeout", "2024-01-14", "13:00", "manual_input"),
        Transaction(25.0, "play", "Dinner at restaurant", "2024-01-15", "19:15", "manual_input"),
        Transaction(18.0, "play", "Lunch at cafe", "2024-01-15", "12:30", "manual_input"),
        Transaction(6.0, "play", "Morning coffee", "2024-01-16", "08:15", "manual_input"),
        Transaction(15.0, "play", "Salad bar lunch", "2024-01-16", "12:45", "manual_input"),
        Transaction(28.0, "play", "Thai food delivery", "2024-01-17", "18:45", "manual_input"),
        Transaction(5.0, "play", "Coffee run", "2024-01-18", "09:00", "manual_input"),
        Transaction(20.0, "play", "Team lunch", "2024-01-19", "12:30", "manual_input"),
        Transaction(115.0, "necessities", "Big grocery haul", "2024-01-20", "11:00", "vpbank_api"),
        Transaction(32.0, "play", "Movie tickets and snacks", "2024-01-20", "19:30", "manual_input"),
        Transaction(25.0, "education", "New book", "2024-01-21", "16:00", "manual_input"),
        Transaction(52.0, "necessities", "Fill up tank", "2024-01-22", "08:15", "vpbank_api"),
        Transaction(13.0, "play", "Pho for lunch", "2024-01-22", "12:15", "manual_input"),
        Transaction(18.0, "necessities", "Pharmacy - cold medicine", "2024-01-23", "17:00", "manual_input"),
        Transaction(7.0, "play", "Coffee and bagel", "2024-01-24", "08:30", "manual_input"),
        Transaction(75.0, "necessities", "Electricity Bill", "2024-01-25", "14:00", "vpbank_api"),
        Transaction(17.0, "play", "Lunch with coworker", "2024-01-25", "12:45", "manual_input"),
        Transaction(60.0, "play", "Date night dinner", "2024-01-26", "20:00", "manual_input"),
        Transaction(25.0, "necessities", "Uber to event", "2024-01-26", "19:30", "manual_input"),
        Transaction(95.0, "necessities", "Weekly groceries", "2024-01-27", "10:30", "vpbank_api"),
        Transaction(40.0, "necessities", "Kitchen supplies", "2024-01-28", "15:00", "manual_input"),
        Transaction(6.0, "play", "Morning coffee", "2024-01-29", "08:45", "manual_input"),
        Transaction(16.0, "play", "Lunch takeout", "2024-01-29", "13:15", "manual_input"),
        Transaction(22.0, "play", "Chinese food for dinner", "2024-01-30", "19:00", "manual_input"),
        Transaction(12.0, "necessities", "Snacks and drinks", "2024-01-31", "16:30", "manual_input"),

        # === February 2024 ===
        Transaction(1250.0, "necessities", "February Rent Payment", "2024-02-01", "09:00", "vpbank_api"),
        Transaction(65.0, "necessities", "Internet Bill", "2024-02-02", "14:30", "vpbank_api"),
        Transaction(14.0, "play", "Sandwich and soup", "2024-02-02", "12:30", "manual_input"),
        Transaction(55.0, "necessities", "Fill up tank", "2024-02-03", "08:00", "vpbank_api"),
        Transaction(70.0, "necessities", "Weekend grocery run", "2024-02-03", "10:15", "vpbank_api"),
        Transaction(15.99, "play", "Netflix Subscription", "2024-02-05", "16:00", "vpbank_api"),
        Transaction(7.0, "play", "Coffee and a muffin", "2024-02-05", "08:30", "manual_input"),
        Transaction(13.0, "play", "Work cafe lunch", "2024-02-06", "12:15", "manual_input"),
        Transaction(35.0, "give", "Gift for friend's birthday", "2024-02-07", "15:30", "manual_input"),
        Transaction(26.0, "play", "Indian takeout", "2024-02-08", "19:15", "manual_input"),
        Transaction(45.0, "play", "Bowling with friends", "2024-02-09", "20:00", "manual_input"),
        Transaction(11.99, "play", "Spotify Premium", "2024-02-10", "18:00", "vpbank_api"),
        Transaction(80.0, "necessities", "Weekly shopping", "2024-02-10", "11:00", "vpbank_api"),
        Transaction(25.0, "play", "Brunch with family", "2024-02-11", "11:30", "manual_input"),
        Transaction(6.0, "play", "Morning coffee", "2024-02-12", "08:15", "manual_input"),
        Transaction(17.0, "play", "Lunch meeting", "2024-02-12", "12:45", "manual_input"),
        Transaction(48.0, "necessities", "Fill up tank", "2024-02-13", "07:45", "vpbank_api"),
        Transaction(75.0, "play", "Valentine's Day dinner", "2024-02-14", "19:30", "manual_input"),
        Transaction(15.0, "necessities", "Vitamins and supplements", "2024-02-15", "17:00", "manual_input"),
        Transaction(14.0, "play", "Lunch at sandwich shop", "2024-02-15", "12:30", "manual_input"),
        Transaction(55.0, "necessities", "Skincare products", "2024-02-16", "16:00", "manual_input"),
        Transaction(40.0, "play", "Friday night pizza", "2024-02-16", "19:00", "manual_input"),
        Transaction(120.0, "necessities", "Stock up on groceries", "2024-02-17", "10:45", "vpbank_api"),
        Transaction(18.0, "necessities", "Round trip train ticket", "2024-02-18", "08:30", "manual_input"),
        Transaction(30.0, "play", "Museum admission", "2024-02-18", "14:00", "manual_input"),
        Transaction(7.0, "play", "Coffee to go", "2024-02-19", "09:00", "manual_input"),
        Transaction(16.0, "play", "Pasta for lunch", "2024-02-19", "12:15", "manual_input"),

        # === March 2024 (Additional month for more data) ===
        Transaction(1250.0, "necessities", "March Rent Payment", "2024-03-01", "09:00", "vpbank_api"),
        Transaction(65.0, "necessities", "Internet Bill", "2024-03-02", "14:30", "vpbank_api"),
        Transaction(150.0, "education", "Online programming course", "2024-03-03", "20:00", "manual_input"),
        Transaction(85.0, "necessities", "Weekly grocery shopping", "2024-03-03", "10:30", "vpbank_api"),
        Transaction(35.0, "play", "Coffee shop work session", "2024-03-04", "14:00", "manual_input"),
        Transaction(15.99, "play", "Netflix Subscription", "2024-03-05", "16:00", "vpbank_api"),
        Transaction(200.0, "financial_freedom", "Investment account deposit", "2024-03-05", "10:00", "vpbank_api"),
        Transaction(50.0, "education", "Technical book set", "2024-03-06", "16:30", "manual_input"),
        Transaction(45.0, "play", "Weekend dinner out", "2024-03-07", "19:30", "manual_input"),
        Transaction(25.0, "give", "Monthly charity donation", "2024-03-08", "11:00", "manual_input"),
        Transaction(11.99, "play", "Spotify Premium", "2024-03-10", "18:00", "vpbank_api"),
        Transaction(300.0, "long_term_savings", "Emergency fund contribution", "2024-03-10", "12:00", "vpbank_api"),
        Transaction(60.0, "necessities", "Gas station fill-up", "2024-03-11", "08:00", "vpbank_api"),
        Transaction(75.0, "necessities", "Utility bill payment", "2024-03-12", "15:00", "vpbank_api"),
        Transaction(20.0, "play", "Lunch with colleagues", "2024-03-12", "12:30", "manual_input"),
        Transaction(95.0, "necessities", "Grocery shopping", "2024-03-13", "11:00", "vpbank_api"),
        Transaction(40.0, "education", "Workshop ticket", "2024-03-14", "19:00", "manual_input"),
        Transaction(30.0, "play", "Movie night snacks", "2024-03-15", "18:30", "manual_input"),
        Transaction(100.0, "financial_freedom", "Stock purchase", "2024-03-16", "09:30", "vpbank_api"),
        Transaction(25.0, "necessities", "Pharmacy visit", "2024-03-17", "17:00", "manual_input"),
        Transaction(80.0, "play", "Weekend entertainment", "2024-03-18", "20:00", "manual_input"),
        Transaction(120.0, "necessities", "Monthly groceries", "2024-03-20", "10:00", "vpbank_api"),
        Transaction(35.0, "education", "Online course materials", "2024-03-21", "16:00", "manual_input"),
        Transaction(55.0, "necessities", "Car maintenance", "2024-03-22", "14:00", "manual_input"),
        Transaction(15.0, "give", "Community fundraiser", "2024-03-23", "12:00", "manual_input"),
        Transaction(65.0, "play", "Date night activities", "2024-03-24", "19:00", "manual_input"),
        Transaction(90.0, "necessities", "Weekly shopping", "2024-03-25", "11:30", "vpbank_api"),
        Transaction(45.0, "education", "Professional development", "2024-03-26", "18:00", "manual_input"),
        Transaction(25.0, "play", "Coffee and cake", "2024-03-27", "15:00", "manual_input"),
        Transaction(150.0, "long_term_savings", "Vacation fund", "2024-03-28", "10:00", "vpbank_api"),
        Transaction(30.0, "necessities", "Household supplies", "2024-03-29", "16:30", "manual_input"),
        Transaction(20.0, "play", "Casual dining", "2024-03-30", "12:45", "manual_input"),
        Transaction(75.0, "financial_freedom", "Cryptocurrency investment", "2024-03-31", "14:00", "vpbank_api"),

        # === Additional education & financial freedom transactions ===
        Transaction(500.0, "education", "Professional certification course", "2024-01-15", "10:00", "vpbank_api"),
        Transaction(250.0, "financial_freedom", "Retirement account contribution", "2024-01-30", "11:00", "vpbank_api"),
        Transaction(75.0, "education", "Industry conference ticket", "2024-02-20", "14:00", "manual_input"),
        Transaction(400.0, "financial_freedom", "Index fund investment", "2024-02-28", "15:30", "vpbank_api"),
        Transaction(100.0, "give", "Annual charity donation", "2024-03-01", "09:30", "manual_input"),
        Transaction(180.0, "education", "Language learning app annual subscription", "2024-03-10", "20:00", "vpbank_api"),
        Transaction(320.0, "long_term_savings", "House down payment fund", "2024-03-15", "12:00", "vpbank_api"),
        Transaction(60.0, "give", "Friend's medical fund", "2024-03-20", "16:00", "manual_input")
    ]
    
    for transaction in sample_transactions:
        save_transaction(transaction)
    
    # Add sample recurring fee
    sample_fee = RecurringFee(
        name="Netflix Subscription",
        amount=15.99,
        description="Monthly Netflix streaming subscription",
        target_jar="play",
        pattern_type="monthly",
        pattern_details=[5],  # 5th of every month
        created_date=datetime.now(),
        next_occurrence=datetime.now() + timedelta(days=30),
        is_active=True
    )
    save_recurring_fee(sample_fee)
    
    # No budget plan

def reset_database() -> None:
    """Reset database to initial state"""
    initialize_default_data()

# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_jar_data(jar: Jar) -> Tuple[bool, List[str]]:
    """Validate jar data for consistency"""
    errors = []
    
    if not jar.name or not jar.name.strip():
        errors.append("Jar name cannot be empty")
    
    if not validate_percentage_range(jar.percent):
        errors.append(f"Percent {jar.percent} must be between 0.0 and 1.0")
    
    if not validate_percentage_range(jar.current_percent):
        errors.append(f"Current percent {jar.current_percent} must be between 0.0 and 1.0")
    
    # Check if calculated amounts match
    expected_amount = calculate_amount_from_percent(jar.percent)
    if abs(jar.amount - expected_amount) > 0.01:  # Allow small rounding differences
        errors.append(f"Amount {jar.amount} doesn't match percent calculation {expected_amount}")
    
    return len(errors) == 0, errors

def validate_transaction_data(transaction: Transaction) -> Tuple[bool, List[str]]:
    """Validate transaction data"""
    errors = []
    
    if not validate_positive_amount(transaction.amount):
        errors.append(f"Amount {transaction.amount} must be positive")
    
    if not transaction.jar or transaction.jar not in JARS_STORAGE:
        errors.append(f"Jar '{transaction.jar}' does not exist")
    
    if not transaction.description or not transaction.description.strip():
        errors.append("Description cannot be empty")
    
    # Validate date format (basic check)
    try:
        datetime.strptime(transaction.date, "%Y-%m-%d")
    except ValueError:
        errors.append(f"Invalid date format: {transaction.date}")
    
    return len(errors) == 0, errors
