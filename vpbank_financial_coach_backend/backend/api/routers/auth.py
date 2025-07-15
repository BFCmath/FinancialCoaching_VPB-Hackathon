from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.services import security
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import token as token_model
from backend.services.core_services import CalculationService

router = APIRouter()

@router.post("/register", response_model=user_model.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    user_in: user_model.UserCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db)
):
    """
    Create a new user account.
    """
    # Check if user with the same username or email already exists
    existing_user_by_username = await db_utils.get_user_by_username(db, username=user_in.username)
    if existing_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )
    
    existing_user_by_email = await db_utils.get_user_by_email(db, email=user_in.email)
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # Create the new user in the database
    new_user = await db_utils.create_user(db, user_in=user_in)
    
    await CalculationService.initialize_default_data(db=db, user_id=new_user.id)

    # Return the public representation of the user
    return user_model.UserPublic.model_validate(new_user.model_dump(by_alias=True))


@router.post("/token", response_model=token_model.Token)
async def login_for_access_token(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate a user and return a JWT access token.
    
    This uses the standard OAuth2 password flow. The client should send
    `username` and `password` in a form-data body.
    """
    user = await db_utils.get_user_by_username(db, username=form_data.username)
    
    # Check if user exists and password is correct
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the access token
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=user_model.UserPublic)
async def read_users_me(
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Get the profile of the currently authenticated user.
    This is a protected endpoint used to verify that authentication is working.
    """
    return user_model.UserPublic.model_validate(current_user.model_dump(by_alias=True))