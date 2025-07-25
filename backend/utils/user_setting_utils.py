from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

# Import all Pydantic models
from backend.models import user_settings
from backend.utils.general_utils import USER_SETTINGS_COLLECTION
from backend.utils.jar_utils import create_jar_in_db

async def get_user_settings(db: AsyncIOMotorDatabase, user_id: str) -> Optional[user_settings.UserSettingsInDB]:
    """Retrieve settings for a specific user."""
    settings_doc = await db[USER_SETTINGS_COLLECTION].find_one({"user_id": user_id})
    if settings_doc:
        settings_doc["_id"] = str(settings_doc["_id"])
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
    result["_id"] = str(result["_id"])
    return user_settings.UserSettingsInDB(**result)


async def get_user_total_income(db: AsyncIOMotorDatabase, user_id: str) -> float:
    """Get user's total income, defaulting to 5000.0 if not set."""
    user_settings_doc = await get_user_settings(db, user_id)
    if user_settings_doc:
        return user_settings_doc.total_income
    return 5000.0  # Default income if not set

async def initialize_default_data(db: AsyncIOMotorDatabase, user_id: str) -> None:
    """
    Sets up the default 6-jar system for a new user based on the mock data.
    """
    default_jars_data = [
        {
            "name": "necessities", 
            "description": "This is the foundation of your budget, covering essential living costs. Use it for non-negotiable expenses like rent/mortgage, utilities (electricity, water, internet), groceries, essential transportation, and insurance.", 
            "percent": 0.55
        },
        {
            "name": "long_term_savings", 
            "description": "Your safety net and goal-achiever. This jar is for saving for big-ticket items and preparing for the unexpected. Use it for your emergency fund, a down payment on a car or home, or a dream vacation.", 
            "percent": 0.10
        },
        {
            "name": "play", 
            "description": "This is your mandatory guilt-free fun money! You MUST spend this every month to pamper yourself and enjoy life. Use it for movies, dining out, hobbies, short trips, or buying something special just for you.", 
            "percent": 0.10
        },
        {
            "name": "education", 
            "description": "Invest in your greatest asset: you. This jar is for personal growth and learning new skills that can increase your knowledge and earning potential. Use it for books, online courses, seminars, workshops, or coaching.", 
            "percent": 0.10
        },
        {
            "name": "financial_freedom", 
            "description": "Your golden goose. This money is for building wealth and generating passive income so you eventually don't have to work for money. Use it for stocks, bonds, mutual funds, or other income-generating assets. You never spend this money, you only invest it.", 
            "percent": 0.10
        },
        {
            "name": "give", 
            "description": "Practice generosity and cultivate a mindset of abundance. Use this money to make a positive impact, whether through charity, donations, helping a friend in need, or buying an unexpected gift for a loved one.", 
            "percent": 0.05
        }
    ]
    
    total_income = await get_user_total_income(db, user_id)

    for jar_data in default_jars_data:
        # Create the full JarInDB model for storage
        jar_dict_to_create = {
            "user_id": user_id,
            "name": jar_data["name"],
            "description": jar_data["description"],
            "percent": jar_data["percent"],
            "amount": total_income * jar_data["percent"],
            "current_percent": 0.0,
            "current_amount": 0.0
        }
        # Use the existing database utility to create the jar
        await create_jar_in_db(db, jar_dict_to_create)

async def update_user_settings_with_jar_recalculation(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    settings_in: user_settings.UserSettingsUpdate
) -> user_settings.UserSettingsInDB:
    """
    Update user settings and automatically recalculate jar amounts if income changes.
    
    Args:
        db: Database connection
        user_id: User's ID
        settings_in: Settings update data
        
    Returns:
        Updated user settings
        
    Raises:
        ValueError: If total_income is not positive
    """
    # Get current settings to check if income is changing
    current_settings = await get_user_settings(db, user_id)
    income_is_changing = (
        settings_in.total_income is not None and 
        (not current_settings or current_settings.total_income != settings_in.total_income)
    )
    
    # Validate new income if provided
    if settings_in.total_income is not None and settings_in.total_income <= 0:
        raise ValueError("Total income must be positive")
    
    # Update the user settings
    updated_settings = await create_or_update_user_settings(db, user_id, settings_in)
    
    # If income changed, recalculate all jar amounts
    if income_is_changing and settings_in.total_income:
        from backend.utils.jar_utils import recalculate_jar_amounts_for_user
        await recalculate_jar_amounts_for_user(db, user_id, settings_in.total_income)
    
    return updated_settings