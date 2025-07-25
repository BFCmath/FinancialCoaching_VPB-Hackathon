from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.utils import user_setting_utils
from backend.models import user as user_model
from backend.models import user_settings as settings_model

router = APIRouter()

@router.get("/settings", response_model=settings_model.UserSettingsInDB)
async def get_user_settings(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Retrieve the financial settings for the current user.
    If no settings exist, it will return default values based on the model.
    """
    user_id = str(current_user.id)
    settings = await user_setting_utils.get_user_settings(db, user_id=user_id)
    
    if not settings:
        # If user has no settings yet, we can create a default entry or raise an error.
        # For this use case, let's create a default one.
        default_settings_data = settings_model.UserSettingsUpdate(total_income=5000.0) # Default income
        settings = await user_setting_utils.create_or_update_user_settings(db, user_id=user_id, settings_in=default_settings_data)

    return settings

@router.put("/settings", response_model=settings_model.UserSettingsInDB)
async def update_user_settings(
    settings_in: settings_model.UserSettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Update the financial settings for the current user (e.g., total_income).
    When total_income is updated, all jar amounts are automatically recalculated.
    """
    user_id = str(current_user.id)
    
    if not settings_in.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No settings provided to update."
        )

    try:
        # Update settings and recalculate jars if income changed
        updated_settings = await user_setting_utils.update_user_settings_with_jar_recalculation(
            db, user_id, settings_in
        )
        return updated_settings
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
