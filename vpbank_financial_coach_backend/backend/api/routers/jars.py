from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import jar as jar_model
from backend.services.financial_services import JarManagementService
from backend.services.service_responses import JarOperationResult, ServiceResult

router = APIRouter()

def _handle_service_result_error(result: ServiceResult) -> HTTPException:
    """Convert service result errors to appropriate HTTP exceptions."""
    error_code = result.get_error_code()
    error_message = result.get_error_message()
    
    # Map service error codes to HTTP status codes
    status_code_mapping = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "INVALID_PERCENTAGE": status.HTTP_400_BAD_REQUEST,
        "INVALID_NAME": status.HTTP_400_BAD_REQUEST,
        "ALLOCATION_EXCEEDED": status.HTTP_400_BAD_REQUEST,
        "MISSING_REQUIRED_FIELDS": status.HTTP_400_BAD_REQUEST,
        "PARAMETER_MISMATCH": status.HTTP_400_BAD_REQUEST,
        "EMPTY_FIELD": status.HTTP_400_BAD_REQUEST,
        "MISSING_ALLOCATION": status.HTTP_400_BAD_REQUEST,
        "CONFLICTING_ALLOCATION": status.HTTP_400_BAD_REQUEST,
    }
    
    http_status = status_code_mapping.get(error_code, status.HTTP_400_BAD_REQUEST)
    
    # If there are multiple errors, include them in the detail
    if result.errors and len(result.errors) > 1:
        error_details = [f"{err.message}" for err in result.errors]
        detail = f"{error_message}. Details: {'; '.join(error_details)}"
    else:
        detail = error_message
    
    return HTTPException(status_code=http_status, detail=detail)

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
    
    # Handle service result
    if result.is_error():
        raise _handle_service_result_error(result)
    
    # If creation was successful, return the created jar
    created_jar = await db_utils.get_jar_by_name(db, user_id, jar_in.name.lower().replace(' ', '_'))
    if not created_jar:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Jar was created but could not be retrieved"
        )
    
    return created_jar