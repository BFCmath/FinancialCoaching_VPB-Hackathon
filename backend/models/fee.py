from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Define the allowed pattern types, matching the original database.py
FeePatternType = Literal["daily", "weekly", "monthly"]

class RecurringFeeBase(BaseModel):
    """
    Base model for a recurring fee.
    """
    name: str = Field(..., min_length=3, max_length=200, example="Netflix Subscription", description="The unique name for the recurring fee.")
    amount: float = Field(..., gt=0, example=15.99, description="The amount of the fee.")
    description: str = Field(..., max_length=1000, example="Monthly Netflix streaming subscription.")
    target_jar: str = Field(..., min_length=2, max_length=100, example="play", description="The name of the jar this fee is paid from.")
    pattern_type: FeePatternType = Field(..., example="monthly", description="The recurrence pattern type.")
    pattern_details: List[int] = Field(default_factory=list, example=[5], description="Details for the pattern (e.g., days of week/month) - matches lab structure.")

class RecurringFeeCreate(RecurringFeeBase):
    """
    Model used when creating a new recurring fee via the API.
    """
    pass

class RecurringFeeUpdate(BaseModel):
    """
    Model used when updating an existing recurring fee. All fields are optional.
    """
    amount: Optional[float] = Field(None, gt=0, example=16.99)
    description: Optional[str] = Field(None, max_length=1000)
    target_jar: Optional[str] = Field(None, min_length=2, max_length=100)
    pattern_type: Optional[FeePatternType] = Field(None)
    pattern_details: Optional[List[int]] = Field(None)
    is_active: Optional[bool] = Field(None, description="Set to false to disable the fee without deleting it.")

class RecurringFeeInDB(RecurringFeeBase):
    """
    Model representing a recurring fee as it is stored in the database.
    """
    id: str = Field(alias="_id", description="The unique identifier for the fee.", example="60d5ecf3e7b3c2a4c8f3b3a5")
    user_id: str = Field(description="The ID of the user who owns this fee.", example="60d5ecf3e7b3c2a4c8f3b3a2")
    created_date: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the fee was created.")
    next_occurrence: datetime = Field(..., description="The calculated next date and time this fee is due.")
    is_active: bool = Field(default=True, description="Whether the fee is currently active.")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }