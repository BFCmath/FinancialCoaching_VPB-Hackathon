from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

# Import all Pydantic models
from backend.models import conversation
from backend.utils.general_utils import CONVERSATION_HISTORY_COLLECTION

async def add_conversation_turn_for_user(db: AsyncIOMotorDatabase, user_id: str, turn_dict: Dict[str, Any]) -> conversation.ConversationTurnInDB:
    """Creates a new conversation turn document from a dictionary in the database."""
    turn_dict["user_id"] = user_id
    turn_dict["timestamp"] = datetime.utcnow()
    
    result = await db[CONVERSATION_HISTORY_COLLECTION].insert_one(turn_dict)
    created_doc = await db[CONVERSATION_HISTORY_COLLECTION].find_one({"_id": result.inserted_id})
    if created_doc:
        created_doc["_id"] = str(created_doc["_id"])
    return conversation.ConversationTurnInDB(**created_doc)

async def get_conversation_history_for_user(db: AsyncIOMotorDatabase, user_id: str, limit: int = 10) -> List[conversation.ConversationTurnInDB]:
    """Retrieves the most recent conversation history for a user."""
    history_cursor = db[CONVERSATION_HISTORY_COLLECTION].find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(limit)
    
    history = await history_cursor.to_list(length=limit)

    try:
        result = []
        for turn in history:
            # turn: _id, user_input, agent_output, agent_list, tool_call_list, user_id, timestamp
            turn["_id"] = str(turn["_id"])  # Ensure _id is a string
            turn["user_input"] = str(turn.get("user_input"))
            turn["agent_output"] = str(turn.get("agent_output"))
            turn["agent_list"] = turn.get("agent_list")
            turn["tool_call_list"] = turn.get("tool_call_list")
            turn["user_id"] = turn["user_id"]
            turn["timestamp"] = turn["timestamp"]
            result.append(conversation.ConversationTurnInDB(**turn))
        return result
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error converting conversation history: {e}")
        return []
    
async def get_latest_conversation_turn_for_user(db: AsyncIOMotorDatabase, user_id: str) -> Optional[conversation.ConversationTurnInDB]:
    """Gets the most recent conversation turn for a user, useful for checking agent_lock and plan_stage."""
    turn_doc = await db[CONVERSATION_HISTORY_COLLECTION].find_one(
        {"user_id": user_id},
        sort=[("timestamp", -1)]
    )
    if turn_doc:
        turn_doc["_id"] = str(turn_doc["_id"])
        return conversation.ConversationTurnInDB(**turn_doc)
    return None

async def get_agent_lock_for_user(db: AsyncIOMotorDatabase, user_id: str) -> Optional[str]:
    """Gets the currently locked agent for a user from the latest conversation turn."""
    latest_turn = await get_latest_conversation_turn_for_user(db, user_id)
    if latest_turn and latest_turn.agent_lock:
        return latest_turn.agent_lock
    return None

async def get_plan_stage_for_user(db: AsyncIOMotorDatabase, user_id: str) -> Optional[str]:
    """Gets the current plan stage for a user from the latest conversation turn."""
    latest_turn = await get_latest_conversation_turn_for_user(db, user_id)
    if latest_turn and latest_turn.plan_stage:
        return latest_turn.plan_stage
    return None

