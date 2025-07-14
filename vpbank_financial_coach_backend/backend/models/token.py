from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """
    Model for the JWT access token response.
    """
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """
    Model for the data encoded within the JWT.
    """
    username: Optional[str] = None
