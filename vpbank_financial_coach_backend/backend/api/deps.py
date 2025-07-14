from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.services import security
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import token as token_model
from backend.db.database import get_database

# This tells FastAPI that the token should be sent in the Authorization header
# as a "Bearer" token. The `tokenUrl` points to our login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency to get the database session.
    This will be injected into path operations that need database access.
    """
    return get_database()

async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> user_model.UserInDB:
    """
    FastAPI dependency to get the current user from a JWT token.

    This function will:
    1. Extract the token from the Authorization header.
    2. Decode the JWT to get the payload.
    3. Extract the username from the payload.
    4. Fetch the user from the database.
    5. Return the user object.

    If any step fails (e.g., invalid token, user not found), it raises an
    HTTPException, which immediately stops the request and sends an error
    response to the client.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    token_data = token_model.TokenData(username=username)

    user = await db_utils.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(
    current_user: user_model.UserInDB = Depends(get_current_user),
) -> user_model.UserInDB:
    """

    Optional: A dependency to check if the user is active.
    For now, we don't have an 'is_active' flag on the user model,
    so this just returns the user. It can be expanded later.
    """
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user