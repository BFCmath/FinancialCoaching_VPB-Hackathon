from typing import Dict, List, Any, Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

# Import all Pydantic models
from backend.models import transaction, conversation
from backend.utils.conversation_utils import get_conversation_history_for_user
from backend.utils.general_utils import TRANSACTIONS_COLLECTION, CONVERSATION_HISTORY_COLLECTION, validate_positive_amount

async def get_all_transactions_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[transaction.TransactionInDB]:
    """Retrieves all transactions for a specific user."""
    transactions = []
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id})
    async for t in transactions_cursor:
        t["_id"] = str(t["_id"])
        transactions.append(transaction.TransactionInDB(**t))
    return transactions

async def get_transactions_by_jar_for_user(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> List[transaction.TransactionInDB]:
    """Retrieves transactions for a specific jar and user."""
    transactions = []
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id, "jar": jar_name})
    async for t in transactions_cursor:
        t["_id"] = str(t["_id"])
        transactions.append(transaction.TransactionInDB(**t))
    return transactions

async def create_transaction_in_db(db: AsyncIOMotorDatabase, transaction_dict: Dict[str, Any]) -> transaction.TransactionInDB:
    """Creates a new transaction document from a dictionary in the database."""
    result = await db[TRANSACTIONS_COLLECTION].insert_one(transaction_dict)

    # Fetch the newly created document from the database
    created_doc = await db[TRANSACTIONS_COLLECTION].find_one({"_id": result.inserted_id})

    # Convert its ObjectId to a string before validation
    if created_doc and "_id" in created_doc:
        created_doc["_id"] = str(created_doc["_id"])
    
    # Return a valid Pydantic model
    return transaction.TransactionInDB(**created_doc)

async def get_transaction_by_id(db: AsyncIOMotorDatabase, user_id: str, transaction_id: str) -> Optional[transaction.TransactionInDB]:
    """Retrieves a specific transaction by its ID for a user."""
    from bson import ObjectId
    from bson.errors import InvalidId
    
    # Try to convert string to ObjectId for MongoDB query
    try:
        obj_id = ObjectId(transaction_id)
        transaction_doc = await db[TRANSACTIONS_COLLECTION].find_one({"_id": obj_id, "user_id": user_id})
    except InvalidId as e:
        transaction_doc = await db[TRANSACTIONS_COLLECTION].find_one({"_id": transaction_id, "user_id": user_id})
    
    if transaction_doc:
        transaction_doc["_id"] = str(transaction_doc["_id"])
        return transaction.TransactionInDB(**transaction_doc)
    else:
        print(f"[DEBUG] No transaction found in database")
    return None

async def delete_transaction_by_id(db: AsyncIOMotorDatabase, user_id: str, transaction_id: str) -> bool:
    """Deletes a transaction by its ID for a specific user."""
    from bson import ObjectId
    from bson.errors import InvalidId
    
    # Try to convert string to ObjectId for MongoDB query
    try:
        obj_id = ObjectId(transaction_id)
        result = await db[TRANSACTIONS_COLLECTION].delete_one({"_id": obj_id, "user_id": user_id})
    except InvalidId:
        result = await db[TRANSACTIONS_COLLECTION].delete_one({"_id": transaction_id, "user_id": user_id})
    return result.deleted_count > 0

async def get_transactions_by_date_range_for_user(db: AsyncIOMotorDatabase, user_id: str, start_date: str, end_date: str = None) -> List[transaction.TransactionInDB]:
    """Get transactions within date range for a specific user."""
    if end_date is None:
        end_date = datetime.now().isoformat()
    
    transactions = []
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({
        "user_id": user_id,
        "transaction_datetime": {"$gte": start_date, "$lte": end_date}
    })
    async for t in transactions_cursor:
        t["_id"] = str(t["_id"])
        transactions.append(transaction.TransactionInDB(**t))
    return transactions

async def get_user_transactions(db: AsyncIOMotorDatabase, user_id: str, limit: int = 50) -> List[transaction.TransactionInDB]:
    """Get transactions for a specific user with limit."""
    transactions = []
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id}).sort("transaction_datetime", -1).limit(limit)
    async for t in transactions_cursor:
        t["_id"] = str(t["_id"])
        transactions.append(transaction.TransactionInDB(**t))
    return transactions

async def get_transactions_by_source_for_user(
    db: AsyncIOMotorDatabase, user_id: str, source: str
) -> List[transaction.TransactionInDB]:
    """Get all transactions for a user by source type."""
    transactions = []
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find({"user_id": user_id, "source": source})
    async for t in transactions_cursor:
        t["_id"] = str(t["_id"])
        transactions.append(transaction.TransactionInDB(**t))
    return transactions

async def get_transactions_by_amount_range_for_user(
    db: AsyncIOMotorDatabase, user_id: str, min_amount: Optional[float], max_amount: Optional[float]
) -> List[transaction.TransactionInDB]:
    """Get all transactions for a user within amount range."""
    query = {"user_id": user_id}
    if min_amount is not None or max_amount is not None:
        amount_filter = {}
        if min_amount is not None:
            amount_filter["$gte"] = min_amount
        if max_amount is not None:
            amount_filter["$lte"] = max_amount
        query["amount"] = amount_filter
    
    transactions = []
    transactions_cursor = db[TRANSACTIONS_COLLECTION].find(query)
    async for t in transactions_cursor:
        t["_id"] = str(t["_id"])
        transactions.append(transaction.TransactionInDB(**t))
    return transactions


async def get_agent_specific_history(db: AsyncIOMotorDatabase, user_id: str, agent_name: str, max_turns: int = 10) -> List[conversation.ConversationTurnInDB]:
    """Get conversation history specifically for a given agent."""
    history_cursor = db[CONVERSATION_HISTORY_COLLECTION].find({
        "user_id": user_id,
        "agent_list": {"$in": [agent_name]}
    }).sort("timestamp", -1).limit(max_turns)
    
    history = await history_cursor.to_list(length=max_turns)
    
    # Convert ObjectId to string for all documents
    for turn in history:
        turn["_id"] = str(turn["_id"])
    
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
    
    # Validate transaction_datetime format (basic check)
    transaction_datetime = transaction_data.get('transaction_datetime', '')
    if transaction_datetime:
        try:
            if isinstance(transaction_datetime, str):
                datetime.fromisoformat(transaction_datetime.replace('Z', '+00:00'))
        except ValueError:
            errors.append(f"Invalid transaction_datetime format: {transaction_datetime}")
    else:
        errors.append("transaction_datetime is required")
    
    return len(errors) == 0, errors

async def get_transaction_statistics_for_user(db: AsyncIOMotorDatabase, user_id: str) -> dict:
    """Get transaction statistics for a user."""
    try:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_transactions": {"$sum": 1},
                "total_amount": {"$sum": "$amount"},
                "average_amount": {"$avg": "$amount"},
                "max_amount": {"$max": "$amount"},
                "min_amount": {"$min": "$amount"},
                "sources": {"$addToSet": "$source"}
            }}
        ]
        
        result = await db.transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "total_transactions": 0,
                "total_amount": 0.0,
                "average_amount": 0.0,
                "max_amount": 0.0,
                "min_amount": 0.0,
                "sources": []
            }
        
        stats = result[0]
        stats.pop("_id", None)  # Remove the _id field
        
        # Round monetary values to 2 decimal places
        stats["total_amount"] = round(stats["total_amount"], 2)
        stats["average_amount"] = round(stats["average_amount"], 2)
        stats["max_amount"] = round(stats["max_amount"], 2)
        stats["min_amount"] = round(stats["min_amount"], 2)
        
        return stats
    except Exception as e:
        print(f"Error getting transaction statistics: {str(e)}")
        return {
            "total_transactions": 0,
            "total_amount": 0.0,
            "average_amount": 0.0,
            "max_amount": 0.0,
            "min_amount": 0.0,
            "sources": []
        }