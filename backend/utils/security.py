"""
Security Utilities - Password Hashing and JWT Management
========================================================

Handles password hashing and JWT token creation/validation.
Unchanged from backend, as no equivalent in lab.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed version.
    
    Args:
        plain_password: User-provided password
        hashed_password: Stored hashed password
        
    Returns:
        True if passwords match
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash plain password.
    
    Args:
        password: Password to hash
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)

# JWT token management
def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload data
        expires_delta: Optional token lifespan
        
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode JWT access token.
    
    Args:
        token: JWT string
        
    Returns:
        Decoded payload if valid, else None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None