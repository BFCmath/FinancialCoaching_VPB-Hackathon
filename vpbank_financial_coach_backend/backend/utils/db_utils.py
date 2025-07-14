"""
Database Utilities (Data Access Layer)
======================================

This module replaces the original, in-memory utils.py.
All functions here perform asynchronous CRUD operations on the MongoDB database.
They are designed to be used as dependencies in FastAPI endpoints.
"""

from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta
from pymongo import ReturnDocument

# Import all Pydantic models
from backend.models import user, jar, transaction, fee, plan, conversation, user_settings

# --- Collection Names ---
# Using constants for collection names is a good practice
USERS_COLLECTION = "users"
JARS_COLLECTION = "jars"
TRANSACTIONS_COLLECTION = "transactions"
FEES_COLLECTION = "fees"
PLANS_COLLECTION = "plans"
CONVERSATION_HISTORY_COLLECTION = "conversation_history"
AGENT_LOCK_COLLECTION = "agent_locks"
USER_SETTINGS_COLLECTION = "user_settings"


# =============================================================================
# USER OPERATIONS
# =============================================================================

async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> Optional[user.UserInDB]:
    """Retrieve a user from the database by their username."""
    user_doc = await db[USERS_COLLECTION].find_one({"username": username})
    if user_doc:
        return user.UserInDB(**user_doc)
    return None

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[user.UserInDB]:
    """Retrieve a user from the database by their email."""
    user_doc = await db[USERS_COLLECTION].find_one({"email": email})
    if user_doc:
        return user.UserInDB(**user_doc)
    return None

async def create_user(db: AsyncIOMotorDatabase, user_in: user.UserCreate) -> user.UserInDB:
    """Create a new user in the database."""
    from backend.services.security import get_password_hash
    
    hashed_password = get_password_hash(user_in.password)
    user_doc = user.UserInDB(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password
    )
    
    # Using .dict() is deprecated, use .model_dump()
    await db[USERS_COLLECTION].insert_one(user_doc.model_dump())
    return user_doc

# =============================================================================
# USER SETTINGS OPERATIONS
# =============================================================================

async def get_user_settings(db: AsyncIOMotorDatabase, user_id: str) -> Optional[user_settings.UserSettingsInDB]:
    """Retrieve settings for a specific user."""
    settings_doc = await db[USER_SETTINGS_COLLECTION].find_one({"user_id": user_id})
    if settings_doc:
        return user_settings.UserSettingsInDB(**settings_doc)
    return None

async def create_or_update_user_settings(db: AsyncIOMotorDatabase, user_id: str, settings_in: user_settings.UserSettingsUpdate) -> user_settings.UserSettingsInDB:
    """Create or update user settings, specifically total_income."""
    # Using .model_dump(exclude_unset=True) ensures we only update fields that were provided
    update_data = settings_in.model_dump(exclude_unset=True)
    
    if not update_data:
        # If no data is provided, just fetch the existing settings
        return await get_user_settings(db, user_id)

    result = await db[USER_SETTINGS_COLLECTION].find_one_and_update(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True, # Creates the document if it doesn't exist
        return_document=ReturnDocument.AFTER # Returns the new, updated document
    )
    return user_settings.UserSettingsInDB(**result)


# =============================================================================
# CONVERSATION LOCK (ACTIVE AGENT) OPERATIONS
# =============================================================================

async def set_agent_lock_for_user(db: AsyncIOMotorDatabase, user_id: str, agent_name: Optional[str]):
    """Sets or releases the agent lock for a user."""
    if agent_name:
        # Set a lock with a Time-To-Live (TTL) index for automatic expiration
        # Note: You must create a TTL index on the 'expireAt' field in MongoDB for this to work.
        # db.agent_locks.createIndex({ "expireAt": 1 }, { expireAfterSeconds: 0 })
        from datetime import timezone
        expire_at = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=5) # Lock expires in 5 mins
        await db[AGENT_LOCK_COLLECTION].update_one(
            {"user_id": user_id},
            {"$set": {"agent_name": agent_name, "expireAt": expire_at}},
            upsert=True
        )
    else:
        # Release the lock by deleting the document
        await db[AGENT_LOCK_COLLECTION].delete_one({"user_id": user_id})

async def get_agent_lock_for_user(db: AsyncIOMotorDatabase, user_id: str) -> Optional[str]:
    """Gets the currently locked agent for a user, if any."""
    lock_doc = await db[AGENT_LOCK_COLLECTION].find_one({"user_id": user_id})
    if lock_doc:
        return lock_doc.get("agent_name")
    return None


# =============================================================================
# CONVERSATION HISTORY OPERATIONS
# =============================================================================

async def add_conversation_turn_for_user(db: AsyncIOMotorDatabase, user_id: str, turn_data: conversation.ConversationTurnCreate) -> conversation.ConversationTurnInDB:
    """Adds a new conversation turn to the user's history."""
    turn_doc = conversation.ConversationTurnInDB(
        user_id=user_id,
        **turn_data.model_dump()
    )
    await db[CONVERSATION_HISTORY_COLLECTION].insert_one(turn_doc.model_dump())
    return turn_doc

async def get_conversation_history_for_user(db: AsyncIOMotorDatabase, user_id: str, limit: int = 10) -> List[conversation.ConversationTurnInDB]:
    """Retrieves the most recent conversation history for a user."""
    history_cursor = db[CONVERSATION_HISTORY_COLLECTION].find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(limit)
    
    history = await history_cursor.to_list(length=limit)
    # Reverse the list to have the oldest message first
    return [conversation.ConversationTurnInDB(**turn) for turn in reversed(history)]


# =============================================================================
# JAR OPERATIONS
# =============================================================================

async def get_all_jars_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[jar.JarInDB]:
    """Retrieves all jars for a specific user."""
    jars_cursor = db[JARS_COLLECTION].find({"user_id": user_id})
    return [jar.JarInDB(**j) async for j in jars_cursor]

async def get_jar_by_name(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> Optional[jar.JarInDB]:
    """Retrieves a single jar by its name for a specific user."""
    # Case-insensitive search for the name
    jar_doc = await db[JARS_COLLECTION].find_one({"user_id": user_id, "name": {"$regex": f"^{jar_name}$", "$options": "i"}})
    if jar_doc:
        return jar.JarInDB(**jar_doc)
    return None

async def create_jar_in_db(db: AsyncIOMotorDatabase, user_id: str, jar_data: jar.JarInDB) -> jar.JarInDB:
    """Creates a new jar document in the database."""
    await db[JARS_COLLECTION].insert_one(jar_data.model_dump(by_alias=True))
    return jar_data

async def update_jar_in_db(db: AsyncIOMotorDatabase, user_id: str, original_jar_name: str, update_data: Dict[str, Any]) -> Optional[jar.JarInDB]:
    """Updates an existing jar document."""
    result = await db[JARS_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": original_jar_name},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    if result:
        return jar.JarInDB(**result)
    return None

async def delete_jar_by_name(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> bool:
    """Deletes a jar by its name for a specific user."""
    result = await db[JARS_COLLECTION].delete_one({"user_id": user_id, "name": jar_name})
    return result.deleted_count > 0

# =============================================================================
# TRANSACTION OPERATIONS  
# =============================================================================

async def get_all_transactions_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[transaction.TransactionInDB]:
    """Retrieves all transactions for a specific user."""
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id})
    return [transaction.TransactionInDB(**t) async for t in transactions_cursor]

async def get_transactions_by_jar_for_user(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> List[transaction.TransactionInDB]:
    """Retrieves transactions for a specific jar and user."""
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id, "jar": jar_name})
    return [transaction.TransactionInDB(**t) async for t in transactions_cursor]

async def create_transaction_in_db(db: AsyncIOMotorDatabase, user_id: str, transaction_data: transaction.TransactionInDB) -> transaction.TransactionInDB:
    """Creates a new transaction document in the database."""
    await db[TRANSACTIONS_COLLECTION].insert_one(transaction_data.model_dump(by_alias=True))
    return transaction_data

async def delete_transaction_by_id(db: AsyncIOMotorDatabase, user_id: str, transaction_id: str) -> bool:
    """Deletes a transaction by its ID for a specific user."""
    result = await db[TRANSACTIONS_COLLECTION].delete_one({"user_id": user_id, "_id": transaction_id})
    return result.deleted_count > 0

async def get_transactions_by_date_range_for_user(db: AsyncIOMotorDatabase, user_id: str, start_date: str, end_date: str = None) -> List[transaction.TransactionInDB]:
    """Get transactions within date range for a specific user."""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": end_date}
    })
    return [transaction.TransactionInDB(**t) async for t in transactions_cursor]

# =============================================================================
# RECURRING FEE OPERATIONS
# =============================================================================

async def get_all_fees_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Retrieves all recurring fees for a specific user."""
    fees_cursor = db[FEES_COLLECTION].find({"user_id": user_id})
    return [fee.RecurringFeeInDB(**f) async for f in fees_cursor]

async def get_fee_by_name(db: AsyncIOMotorDatabase, user_id: str, fee_name: str) -> Optional[fee.RecurringFeeInDB]:
    """Retrieves a single fee by its name for a specific user."""
    fee_doc = await db[FEES_COLLECTION].find_one({"user_id": user_id, "name": {"$regex": f"^{fee_name}$", "$options": "i"}})
    if fee_doc:
        return fee.RecurringFeeInDB(**fee_doc)
    return None

async def create_fee_in_db(db: AsyncIOMotorDatabase, user_id: str, fee_data: fee.RecurringFeeInDB) -> fee.RecurringFeeInDB:
    """Creates a new recurring fee document in the database."""
    await db[FEES_COLLECTION].insert_one(fee_data.model_dump(by_alias=True))
    return fee_data

async def update_fee_in_db(db: AsyncIOMotorDatabase, user_id: str, fee_name: str, update_data: Dict[str, Any]) -> Optional[fee.RecurringFeeInDB]:
    """Updates an existing fee document."""
    result = await db[FEES_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": fee_name},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    if result:
        return fee.RecurringFeeInDB(**result)
    return None

async def delete_fee_by_name(db: AsyncIOMotorDatabase, user_id: str, fee_name: str) -> bool:
    """Deletes a fee by its name for a specific user."""
    result = await db[FEES_COLLECTION].delete_one({"user_id": user_id, "name": fee_name})
    return result.deleted_count > 0

async def get_active_fees_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Get only active recurring fees for a specific user."""
    fees_cursor = db[FEES_COLLECTION].find({"user_id": user_id, "is_active": True})
    return [fee.RecurringFeeInDB(**f) async for f in fees_cursor]

# =============================================================================
# BUDGET PLAN OPERATIONS
# =============================================================================

async def get_all_plans_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[plan.BudgetPlanInDB]:
    """Retrieves all budget plans for a specific user."""
    plans_cursor = db[PLANS_COLLECTION].find({"user_id": user_id})
    return [plan.BudgetPlanInDB(**p) async for p in plans_cursor]

async def get_plan_by_name(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> Optional[plan.BudgetPlanInDB]:
    """Retrieves a single plan by its name for a specific user."""
    plan_doc = await db[PLANS_COLLECTION].find_one({"user_id": user_id, "name": {"$regex": f"^{plan_name}$", "$options": "i"}})
    if plan_doc:
        return plan.BudgetPlanInDB(**plan_doc)
    return None

async def create_plan_in_db(db: AsyncIOMotorDatabase, user_id: str, plan_data: plan.BudgetPlanInDB) -> plan.BudgetPlanInDB:
    """Creates a new budget plan document in the database."""
    await db[PLANS_COLLECTION].insert_one(plan_data.model_dump(by_alias=True))
    return plan_data

async def update_plan_in_db(db: AsyncIOMotorDatabase, user_id: str, plan_name: str, update_data: Dict[str, Any]) -> Optional[plan.BudgetPlanInDB]:
    """Updates an existing plan document."""
    result = await db[PLANS_COLLECTION].find_one_and_update(
        {"user_id": user_id, "name": plan_name},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    if result:
        return plan.BudgetPlanInDB(**result)
    return None

async def delete_plan_by_name(db: AsyncIOMotorDatabase, user_id: str, plan_name: str) -> bool:
    """Deletes a plan by its name for a specific user."""
    result = await db[PLANS_COLLECTION].delete_one({"user_id": user_id, "name": plan_name})
    return result.deleted_count > 0

async def get_plans_by_status_for_user(db: AsyncIOMotorDatabase, user_id: str, status: str) -> List[plan.BudgetPlanInDB]:
    """Get budget plans by status for a specific user."""
    plans_cursor = db[PLANS_COLLECTION].find({"user_id": user_id, "status": status})
    return [plan.BudgetPlanInDB(**p) async for p in plans_cursor]


# =============================================================================
# EXTENDED UTILITY FUNCTIONS (from lab utils.py)
# =============================================================================

async def get_user_transactions(db: AsyncIOMotorDatabase, user_id: str, limit: int = 50) -> List[transaction.TransactionInDB]:
    """Get transactions for a specific user with limit."""
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id}).sort("_id", -1).limit(limit)
    return [transaction.TransactionInDB(**t) async for t in transactions_cursor]

async def get_user_recurring_fees(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Get recurring fees for a specific user (alias for get_all_fees_for_user)."""
    return await get_all_fees_for_user(db, user_id)

async def get_transactions_by_source_for_user(db: AsyncIOMotorDatabase, user_id: str, source: str) -> List[transaction.TransactionInDB]:
    """Get transactions by source type for a specific user."""
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id, "source": source})
    return [transaction.TransactionInDB(**t) async for t in transactions_cursor]

async def calculate_jar_spending_total(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> float:
    """Calculate total spending for a specific jar."""
    transactions = await get_transactions_by_jar_for_user(db, user_id, jar_name)
    return sum(t.amount for t in transactions)

async def get_fees_due_today(db: AsyncIOMotorDatabase, user_id: str) -> List[fee.RecurringFeeInDB]:
    """Get fees that are due today."""
    from datetime import datetime
    today = datetime.utcnow().replace(hour=23, minute=59, second=59)
    fees_cursor = db[FEES_COLLECTION].find({
        "user_id": user_id,
        "is_active": True,
        "next_occurrence": {"$lte": today}
    })
    return [fee.RecurringFeeInDB(**f) async for f in fees_cursor]

async def get_transactions_by_amount_range_for_user(db: AsyncIOMotorDatabase, user_id: str, min_amount: float = None, max_amount: float = None) -> List[transaction.TransactionInDB]:
    """Get transactions within amount range"""
    query = {"user_id": user_id}
    if min_amount is not None or max_amount is not None:
        amount_filter = {}
        if min_amount is not None:
            amount_filter["$gte"] = min_amount
        if max_amount is not None:
            amount_filter["$lte"] = max_amount
        query["amount"] = amount_filter
    
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find(query)
    return [transaction.TransactionInDB(**t) async for t in transactions_cursor]

# =============================================================================
# CALCULATION UTILITIES (from lab utils.py)
# =============================================================================

def calculate_percent_from_amount(amount: float, total_income: float = 5000.0) -> float:
    """Convert dollar amount to percentage of total income."""
    return amount / total_income if total_income > 0 else 0.0

def calculate_amount_from_percent(percent: float, total_income: float = 5000.0) -> float:
    """Convert percentage to dollar amount based on total income."""
    return percent * total_income

def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    return f"${amount:,.2f}"

def format_percentage(percent: float) -> str:
    """Format percentage for display (0.15 -> 15.0%)."""
    return f"{percent * 100:.1f}%"

def validate_percentage_range(percent: float) -> bool:
    """Validate percentage is within 0.0-1.0 range."""
    return 0.0 <= percent <= 1.0

def validate_positive_amount(amount: float) -> bool:
    """Validate amount is positive."""
    return amount > 0

# =============================================================================
# RECURRING FEE UTILITIES (from lab utils.py)
# =============================================================================

def calculate_next_fee_occurrence(pattern_type: str, pattern_details: List[int], from_date: datetime = None) -> datetime:
    """Calculate when fee should next occur based on pattern."""
    if from_date is None:
        from_date = datetime.utcnow()
    
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

# =============================================================================
# DATABASE STATISTICS AND MONITORING (from lab utils.py)
# =============================================================================

async def get_database_stats(db: AsyncIOMotorDatabase, user_id: str) -> Dict[str, Any]:
    """Get comprehensive database statistics for a user."""
    jars = await get_all_jars_for_user(db, user_id)
    transactions = await get_all_transactions_for_user(db, user_id)
    fees = await get_all_fees_for_user(db, user_id)
    plans = await get_all_plans_for_user(db, user_id)
    user_settings_doc = await get_user_settings(db, user_id)
    
    total_income = user_settings_doc.total_income if user_settings_doc else 5000.0
    total_allocation = sum(j.percent for j in jars)
    
    return {
        "jars": {
            "count": len(jars),
            "total_allocation": f"{total_allocation * 100:.1f}%",
            "allocation_valid": total_allocation <= 1.0
        },
        "transactions": {
            "count": len(transactions),
            "total_amount": format_currency(sum(t.amount for t in transactions)),
            "sources": list(set(t.source for t in transactions)) if transactions else []
        },
        "recurring_fees": {
            "count": len(fees),
            "active_count": len([f for f in fees if f.is_active]),
            "due_today": len(await get_fees_due_today(db, user_id))
        },
        "budget_plans": {
            "count": len(plans),
            "active": len([p for p in plans if p.status == "active"]),
            "completed": len([p for p in plans if p.status == "completed"])
        },
        "system": {
            "total_income": format_currency(total_income),
        }
    }

# =============================================================================
# CONVERSATION UTILITIES (from lab utils.py)
# =============================================================================

async def get_agent_specific_history(db: AsyncIOMotorDatabase, user_id: str, agent_name: str, max_turns: int = 10) -> List[conversation.ConversationTurnInDB]:
    """Get conversation history specifically for a given agent."""
    history_cursor = db[CONVERSATION_HISTORY_COLLECTION].find({
        "user_id": user_id,
        "agent_list": {"$in": [agent_name]}
    }).sort("timestamp", -1).limit(max_turns)
    
    history = await history_cursor.to_list(length=max_turns)
    # Return in chronological order (oldest first)
    return [conversation.ConversationTurnInDB(**turn) for turn in reversed(history)]

async def get_conversation_context_string(db: AsyncIOMotorDatabase, user_id: str, limit: int = 5) -> str:
    """Get conversation history as formatted string for agent context."""
    recent_turns = await get_conversation_history_for_user(db, user_id, limit)
    
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
# VALIDATION UTILITIES (from lab utils.py)
# =============================================================================

def validate_jar_data(jar_data: dict, total_income: float = 5000.0) -> Tuple[bool, List[str]]:
    """Validate jar data for consistency."""
    errors = []
    
    if not jar_data.get('name', '').strip():
        errors.append("Jar name cannot be empty")
    
    percent = jar_data.get('percent', 0.0)
    if not validate_percentage_range(percent):
        errors.append(f"Percent {percent} must be between 0.0 and 1.0")
    
    current_percent = jar_data.get('current_percent', 0.0)
    if not validate_percentage_range(current_percent):
        errors.append(f"Current percent {current_percent} must be between 0.0 and 1.0")
    
    # Check if calculated amounts match
    amount = jar_data.get('amount', 0.0)
    expected_amount = calculate_amount_from_percent(percent, total_income)
    if abs(amount - expected_amount) > 0.01:  # Allow small rounding differences
        errors.append(f"Amount {amount} doesn't match percent calculation {expected_amount}")
    
    return len(errors) == 0, errors

def validate_transaction_data(transaction_data: dict) -> Tuple[bool, List[str]]:
    """Validate transaction data."""
    errors = []
    
    amount = transaction_data.get('amount', 0.0)
    if not validate_positive_amount(amount):
        errors.append(f"Amount {amount} must be positive")
    
    jar_name = transaction_data.get('jar', '')
    if not jar_name or not jar_name.strip():
        errors.append("Jar reference cannot be empty")
    
    description = transaction_data.get('description', '')
    if not description or not description.strip():
        errors.append("Description cannot be empty")
    
    # Validate date format (basic check)
    date_str = transaction_data.get('date', '')
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        errors.append(f"Invalid date format: {date_str}")
    
    return len(errors) == 0, errors