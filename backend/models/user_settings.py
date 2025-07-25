from pydantic import BaseModel, Field
from typing import Optional

class UserSettingsBase(BaseModel):
    """
    Base model for user-specific financial settings.
    """
    total_income: float = Field(..., gt=0, example=5000.0, description="The user's total monthly income, used for all percentage-based calculations.")

class UserSettingsUpdate(BaseModel):
    """
    Model used when a user updates their settings.
    """
    total_income: Optional[float] = Field(None, gt=0, example=5500.0)

class UserSettingsInDB(UserSettingsBase):
    """
    Model representing user settings as stored in the database.
    It's linked directly to a user.
    """
    user_id: str = Field(description="The ID of the user these settings belong to.", example="60d5ecf3e7b3c2a4c8f3b3a2")

    class Config:
        orm_mode = True