from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import settings

# --- Password Hashing ---
# We use passlib's CryptContext to handle password hashing.
# bcrypt is a strong and widely recommended hashing algorithm.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against its hashed version.

    Args:
        plain_password: The password as entered by the user.
        hashed_password: The password as stored in the database.

    Returns:
        True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password.

    Args:
        password: The password to hash.

    Returns:
        The hashed password string.
    """
    return pwd_context.hash(password)


# --- JWT Token Management ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.

    Args:
        data: The data to encode in the token (the "payload").
              Typically contains the user identifier (e.g., username).
        expires_delta: The lifespan of the token. If not provided,
                       it defaults to the value from settings.

    Returns:
        The encoded JWT as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes a JWT access token to get its payload.

    Args:
        token: The JWT token string.

    Returns:
        The decoded payload as a dictionary if the token is valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        # This will catch any error during decoding, such as an invalid signature
        # or an expired token.
        return None