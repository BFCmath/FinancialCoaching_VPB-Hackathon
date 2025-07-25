from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.utils import security
from backend.utils import user_utils
from backend.models import user as user_model
from backend.models import token as token_model
from backend.utils.user_setting_utils import initialize_default_data

router = APIRouter()

@router.post("/register", response_model=user_model.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    user_in: user_model.UserCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db)
):
    """
    Create a new user account.
    """
    try:
        # Create the new user in the database (includes duplicate checking)
        new_user = await user_utils.create_user(db, user_in=user_in)
        
        await initialize_default_data(db=db, user_id=new_user.id)

        # Return the public representation of the user
        return user_model.UserPublic.model_validate(new_user.model_dump(by_alias=True))
    
    except ValueError as e:
        # Handle duplicate username/email errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


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
    user = await user_utils.get_user_by_username(db, username=form_data.username)
    
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
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Get the profile of the currently authenticated user.
    This is a protected endpoint used to verify that authentication is working.
    """
    return user_model.UserPublic.model_validate(current_user.model_dump(by_alias=True))


@router.put("/me", response_model=user_model.UserPublic)
async def update_user_profile(
    user_update: user_model.UserUpdate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Update the current user's profile information.
    """
    try:
        updated_user = await user_utils.update_user(db, current_user.id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_model.UserPublic.model_validate(updated_user.model_dump(by_alias=True))
    
    except ValueError as e:
        # Handle duplicate username/email errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )