from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

# Define the allowed sources for a transaction, matching the original database.py
TransactionSource = Literal["vpbank_api", "manual_input", "text_input", "image_input"]

class TransactionBase(BaseModel):
    """
    Base model for a transaction, matching the lab database.py structure exactly.
    """
    amount: float = Field(..., gt=0, example=75.50, description="The transaction amount, must be positive.")
    jar: str = Field(..., alias="jar", min_length=2, max_length=100, example="necessities", description="Reference to jar name (matches lab structure).")
    description: str = Field(..., max_length=1000, example="Grocery shopping at supermarket")
    date: str = Field(..., example="2025-07-14", description="Date string (YYYY-MM-DD format) - matches lab structure.")
    time: str = Field(..., example="14:30", description="Time string (HH:MM format) - matches lab structure.")
    source: TransactionSource = Field(..., example="manual_input", description="The source of the transaction entry.")
    
    # New datetime field for orchestrator compatibility
    transaction_datetime: Optional[datetime] = Field(None, example="2025-07-14T14:30:00Z", description="Datetime field for better date handling (migration from date+time).")

class TransactionCreate(TransactionBase):
    """
    Model used when creating a new transaction via the API.
    It's identical to the base model for this use case.
    """
    pass

class TransactionInDB(TransactionBase):
    """
    Model representing a transaction as it is stored in the database.
    It includes the unique ID and the user ID.
    """
    id: str = Field(alias="_id", description="The unique identifier for the transaction.", example="60d5ecf3e7b3c2a4c8f3b3a4")
    user_id: str = Field(description="The ID of the user who owns this transaction.", example="60d5ecf3e7b3c2a4c8f3b3a2")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }