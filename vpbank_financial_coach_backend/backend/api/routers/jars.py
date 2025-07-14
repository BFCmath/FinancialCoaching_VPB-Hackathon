from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.utils import db_utils
from backend.models import user as user_model
from vpbank_financial_coach_backend.backend.models import jar as jar_model
from backend.services.financial_services import JarManagementService

router = APIRouter()

@router.get("/", response_model=List[jar_model.JarInDB])
async def list_user_jars(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Get all jars for the current user.
    """
    user_id = str(current_user.id) if hasattr(current_user, 'id') else current_user.username
    jars = await db_utils.get_all_jars_for_user(db, user_id)
    return jars

@router.post("/", response_model=jar_model.JarInDB, status_code=status.HTTP_201_CREATED)
async def create_jar(
    jar_in: jar_model.JarCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Create a new jar for the current user.
    """
    user_id = str(current_user.id) if hasattr(current_user, 'id') else current_user.username
    
    # Check if jar already exists
    existing_jar = await db_utils.get_jar_by_name(db, user_id, jar_in.name.lower().replace(' ', '_'))
    if existing_jar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A jar with the name '{jar_in.name}' already exists."
        )
    
    # Use the service to create the jar
    result = await JarManagementService.create_jar(
        db=db,
        user_id=user_id,
        name=[jar_in.name],
        description=[jar_in.description],
        percent=[jar_in.percent] if jar_in.percent is not None else [None],
        amount=[jar_in.amount] if jar_in.amount is not None else [None]
    )
    
    # If creation was successful, return the created jar
    if "✅" in result:
        created_jar = await db_utils.get_jar_by_name(db, user_id, jar_in.name.lower().replace(' ', '_'))
        return created_jar
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )