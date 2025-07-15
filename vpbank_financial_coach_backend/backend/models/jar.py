from pydantic import BaseModel, Field
from typing import Optional

class JarBase(BaseModel):
    """
    Base model for a Jar, containing fields that are always required.
    """
    name: str = Field(..., min_length=2, max_length=100, example="Necessities", description="The name of the budget jar.")
    description: str = Field(..., max_length=500, example="For essential living costs like rent and groceries.", description="A brief description of the jar's purpose.")

class JarCreate(JarBase):
    """
    Model used when creating a new Jar via the API.
    The user must provide either a percentage or a fixed amount.
    The service layer will handle the calculation and validation logic.
    """
    percent: Optional[float] = Field(None, ge=0, le=1, example=0.55, description="The percentage of total income to allocate (0.0 to 1.0).")
    amount: Optional[float] = Field(None, ge=0, example=2750.00, description="The fixed dollar amount to allocate.")

class JarUpdate(BaseModel):
    """
    Model used when updating an existing Jar. All fields are optional.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100, example="Essentials")
    description: Optional[str] = Field(None, max_length=500, example="Updated description for essential costs.")
    percent: Optional[float] = Field(None, ge=0, le=1, example=0.60)
    amount: Optional[float] = Field(None, ge=0, example=3000.00)

class JarInDB(JarBase):
    """
    This is the full Jar model, representing the data as it is stored in the database
    and as it will be returned by the API.
    """
    id: str = Field(alias="_id", description="The unique identifier for the jar.", example="60d5ecf3e7b3c2a4c8f3b3a3")
    user_id: str = Field(description="The ID of the user who owns this jar.", example="60d5ecf3e7b3c2a4c8f3b3a2")

    # Allocation fields, calculated and stored definitively in the DB
    percent: float = Field(..., ge=0, le=1, example=0.55, description="The budget allocation as a percentage.")
    amount: float = Field(..., ge=0, example=2750.00, description="The budget allocation as a dollar amount.")

    # Current state fields, which will be updated by transactions
    current_percent: float = Field(default=0.0, ge=0, example=0.33, description="The current balance as a percentage: current_amount / amount.")
    current_amount: float = Field(default=0.0, ge=0, example=1650.00, description="The current balance as a dollar amount.")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
