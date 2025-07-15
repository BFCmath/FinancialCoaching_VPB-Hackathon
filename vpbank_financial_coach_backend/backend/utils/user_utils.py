from backend.models import user
from typing import Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.utils.general_utils import USERS_COLLECTION
from backend.utils.security import get_password_hash

async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> Optional[user.UserInDB]:
    """Retrieve a user from the database by their username."""
    user_doc = await db[USERS_COLLECTION].find_one({"username": username})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"]) # Add this line
        return user.UserInDB(**user_doc)
    return None

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[user.UserInDB]:
    """Retrieve a user from the database by their email."""
    user_doc = await db[USERS_COLLECTION].find_one({"email": email})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"]) # Add this line
        return user.UserInDB(**user_doc)
    return None

async def create_user(db: AsyncIOMotorDatabase, user_in: user.UserCreate) -> user.UserInDB:
    """Create a new user in the database."""
    # Check for existing users first to prevent duplicates
    existing_user = await get_user_by_username(db, user_in.username)
    if existing_user:
        raise ValueError("Username already exists")
    
    existing_email = await get_user_by_email(db, user_in.email)
    if existing_email:
        raise ValueError("Email already exists")
    
    user_data = {
        "username": user_in.username,
        "email": user_in.email,
        "hashed_password": get_password_hash(user_in.password),
    }

    result = await db[USERS_COLLECTION].insert_one(user_data)

    created_doc = await db[USERS_COLLECTION].find_one({"_id": result.inserted_id})
    
    # Manually convert ObjectId to string for Pydantic validation
    created_doc["_id"] = str(created_doc["_id"])
    return user.UserInDB(**created_doc)

async def update_user(db: AsyncIOMotorDatabase, user_id: str, user_update: user.UserUpdate) -> Optional[user.UserInDB]:
    """Update an existing user's information."""
    from pymongo import ReturnDocument
    
    # Get the current user to validate the update
    current_user = await get_user_by_id(db, user_id)
    if not current_user:
        return None
    
    # Build update data, excluding unset fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    if not update_data:
        # No fields to update, return current user
        return current_user
    
    # Check for conflicts if updating username or email
    if "username" in update_data:
        existing_user = await get_user_by_username(db, update_data["username"])
        if existing_user and existing_user.id != user_id:
            raise ValueError("Username already exists")
    
    if "email" in update_data:
        existing_email = await get_user_by_email(db, update_data["email"])
        if existing_email and existing_email.id != user_id:
            raise ValueError("Email already exists")
    
    # Update the user
    result = await db[USERS_COLLECTION].find_one_and_update(
        {"_id": user_id},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    
    if result:
        result["_id"] = str(result["_id"])
        return user.UserInDB(**result)
    return None

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[user.UserInDB]:
    """Retrieve a user from the database by their ID."""
    user_doc = await db[USERS_COLLECTION].find_one({"_id": user_id})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        return user.UserInDB(**user_doc)
    return None
