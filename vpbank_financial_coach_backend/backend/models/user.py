from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    """
    Base model for a user, containing common fields.
    """
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")

class UserCreate(UserBase):
    """
    Model used when creating a new user.
    It includes the password which is required for registration.
    """
    password: str = Field(..., min_length=8, example="a_strong_password")

class UserUpdate(BaseModel):
    """
    Model used when updating a user's information.
    All fields are optional.
    """
    email: Optional[EmailStr] = Field(None, example="new_user@example.com")
    username: Optional[str] = Field(None, min_length=3, max_length=50, example="new_john_doe")

class UserInDB(UserBase):
    """
    Model representing a user as stored in the database.
    It includes the hashed_password instead of the plain password.
    """
    id: str = Field(alias="_id")
    hashed_password: str

    class Config:
        # This allows the model to be created from dictionary-like objects,
        # which is how data is retrieved from MongoDB.
        orm_mode = True
        allow_population_by_field_name = True

class UserPublic(UserBase):
    """
    Model representing a user's public information.
    This is what is safe to return from API endpoints. It never includes the password.
    """
    id: str = Field(alias="_id", example="60d5ecf3e7b3c2a4c8f3b3a2") # MongoDB uses _id

    class Config:
        orm_mode = True
        allow_population_by_field_name = True # Allows using '_id' to populate 'id'
        json_encoders = {
            # If we ever use ObjectId, this would be the place to encode it to a string
            # For now, we will store IDs as strings.
        }
